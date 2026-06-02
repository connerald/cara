from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FinancialMetric:
    """从财报中抽取出的单项财务指标。"""

    key: str
    name: str
    value: float
    unit: str | None = None
    source_text: str | None = None
    line_number: int | None = None


@dataclass
class FinancialReportSnapshot:
    """从单份财报中抽取出的结构化事实。"""

    company_name: str | None = None
    report_period: str | None = None
    report_type: str | None = None
    source_path: str | None = None
    raw_text_chars: int = 0
    metrics: dict[str, FinancialMetric] = field(default_factory=dict)

    def get(self, key: str) -> float | None:
        metric = self.metrics.get(key)
        return metric.value if metric else None

    def metric_name(self, key: str) -> str:
        metric = self.metrics.get(key)
        return metric.name if metric else key


@dataclass(frozen=True)
class RiskFinding:
    """一条基于确定性规则生成的风险信号。"""

    area: str
    level: str
    title: str
    description: str
    evidence: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskReport:
    """基于财务事实生成的风险报告。"""

    snapshot: FinancialReportSnapshot
    findings: list[RiskFinding]
    score: int

    @property
    def summary_counts(self) -> dict[str, int]:
        counts = {"high": 0, "medium": 0, "low": 0}
        for finding in self.findings:
            if finding.level in counts:
                counts[finding.level] += 1
        return counts

    def to_markdown(self) -> str:
        title_parts = [
            self.snapshot.company_name or "未知公司",
            self.snapshot.report_period or "未知报告期",
            self.snapshot.report_type or "财务报告",
        ]
        counts = self.summary_counts
        lines = [
            "# 财报风险分析报告",
            "",
            f"- 分析对象：{' / '.join(title_parts)}",
            f"- 来源文件：{self.snapshot.source_path or '未提供'}",
            f"- 抽取指标数：{len(self.snapshot.metrics)}",
            f"- 风险分数：{self.score}/100",
            f"- 风险发现：高 {counts['high']}，中 {counts['medium']}，低 {counts['low']}",
            "",
        ]

        if not self.findings:
            lines.extend(
                [
                    "## 风险发现",
                    "",
                    "基于已抽取指标，暂未发现明显的规则化风险信号。",
                    "",
                ]
            )
            return "\n".join(lines)

        lines.extend(["## 风险发现", ""])
        for index, finding in enumerate(self.findings, start=1):
            lines.append(f"### {index}. [{finding.level.upper()}] {finding.title}")
            lines.append("")
            lines.append(f"- 风险领域：{finding.area}")
            lines.append(f"- 详细说明：{finding.description}")
            if finding.evidence:
                lines.append("- 证据：")
                for evidence in finding.evidence:
                    lines.append(f"  - {evidence}")
            lines.append("")

        return "\n".join(lines)
