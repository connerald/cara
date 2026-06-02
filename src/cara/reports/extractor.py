from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from cara.reports.models import FinancialMetric, FinancialReportSnapshot


@dataclass(frozen=True)
class MetricSpec:
    key: str
    name: str
    aliases: tuple[str, ...]


METRIC_SPECS: tuple[MetricSpec, ...] = (
    MetricSpec("total_assets", "资产总计", ("资产总计", "总资产")),
    MetricSpec("total_liabilities", "负债合计", ("负债合计", "总负债")),
    MetricSpec("owners_equity", "所有者权益合计", ("所有者权益合计", "股东权益合计")),
    MetricSpec("revenue", "营业收入", ("营业收入", "主营业务收入")),
    MetricSpec("net_profit", "净利润", ("归属于母公司股东的净利润", "净利润")),
    MetricSpec(
        "operating_cash_flow",
        "经营活动产生的现金流量净额",
        ("经营活动产生的现金流量净额", "经营活动现金流量净额"),
    ),
    MetricSpec("accounts_receivable", "应收账款", ("应收账款",)),
    MetricSpec("inventory", "存货", ("存货",)),
    MetricSpec("goodwill", "商誉", ("商誉",)),
    MetricSpec("monetary_funds", "货币资金", ("货币资金",)),
    MetricSpec("short_term_debt", "短期借款", ("短期借款",)),
    MetricSpec("current_portion_debt", "一年内到期的非流动负债", ("一年内到期的非流动负债",)),
    MetricSpec("long_term_debt", "长期借款", ("长期借款",)),
    MetricSpec("bonds_payable", "应付债券", ("应付债券",)),
)

NUMBER_PATTERN = re.compile(r"(?<![\w.])-?\(?\d[\d,，]*(?:\.\d+)?\)?")


def extract_financial_report(path: str | Path) -> FinancialReportSnapshot:
    report_path = Path(path)
    text = read_report_text(report_path)
    snapshot = FinancialReportSnapshot(
        company_name=extract_company_name(text),
        report_period=extract_report_period(text),
        report_type=extract_report_type(text),
        source_path=str(report_path),
        raw_text_chars=len(text),
    )
    snapshot.metrics.update(extract_metrics(text))
    return snapshot


def read_report_text(path: str | Path) -> str:
    report_path = Path(path)
    suffix = report_path.suffix.lower()
    if suffix == ".pdf":
        return read_pdf_text(report_path)
    if suffix in {".txt", ".md", ".text"}:
        return report_path.read_text(encoding="utf-8")
    raise ValueError(f"不支持的财报文件类型：{suffix or '无扩展名'}")


def read_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF 解析需要 pypdf。请安装该依赖，或提供 .txt/.md 财报。") from exc

    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def extract_company_name(text: str) -> str | None:
    for line in first_non_empty_lines(text, limit=80):
        cleaned = compact_line(line)
        if "公告" in cleaned or len(cleaned) > 80:
            continue
        match = re.search(r"([\u4e00-\u9fa5A-Za-z0-9（）()·]+(?:股份有限公司|有限公司|集团有限公司))", cleaned)
        if match:
            return match.group(1)
    return None


def extract_report_period(text: str) -> str | None:
    patterns = (
        r"(\d{4}\s*年\s*(?:年度|半年度|第一季度|第三季度|一季度|三季度)报告)",
        r"(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)",
        r"(?:报告期|报告期间)[:：\s]*([\d年月日至\-—]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return compact_line(match.group(1))
    return None


def extract_report_type(text: str) -> str | None:
    candidates = (
        "年度报告",
        "半年度报告",
        "第一季度报告",
        "第三季度报告",
        "一季度报告",
        "三季度报告",
    )
    head = text[:5000]
    for candidate in candidates:
        if candidate in head:
            return candidate
    return None


def extract_metrics(text: str) -> dict[str, FinancialMetric]:
    metrics: dict[str, FinancialMetric] = {}
    lines = text.splitlines()
    for line_number, line in enumerate(lines, start=1):
        normalized = compact_line(line)
        if not normalized:
            continue
        for spec in METRIC_SPECS:
            if spec.key in metrics:
                continue
            alias = matched_alias(normalized, spec.aliases)
            if not alias:
                continue
            value = extract_first_metric_number(normalized, alias)
            if value is None:
                continue
            metrics[spec.key] = FinancialMetric(
                key=spec.key,
                name=spec.name,
                value=value,
                unit=extract_unit(normalized),
                source_text=normalized[:240],
                line_number=line_number,
            )
    return metrics


def matched_alias(line: str, aliases: tuple[str, ...]) -> str | None:
    for alias in aliases:
        if alias in line:
            return alias
    return None


def extract_first_metric_number(line: str, alias: str) -> float | None:
    segment = line[line.find(alias) + len(alias) :]
    numbers = NUMBER_PATTERN.findall(segment)
    if not numbers:
        return None
    return parse_number(numbers[0])


def parse_number(raw: str) -> float | None:
    token = raw.strip().replace(",", "").replace("，", "")
    negative = token.startswith("(") and token.endswith(")")
    token = token.strip("()")
    try:
        value = float(token)
    except ValueError:
        return None
    return -value if negative else value


def extract_unit(line: str) -> str | None:
    if "亿元" in line:
        return "亿元"
    if "万元" in line:
        return "万元"
    if "元" in line:
        return "元"
    return None


def first_non_empty_lines(text: str, limit: int) -> list[str]:
    result: list[str] = []
    for line in text.splitlines():
        if line.strip():
            result.append(line)
        if len(result) >= limit:
            break
    return result


def compact_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()
