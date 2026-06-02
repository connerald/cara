from __future__ import annotations

from cara.reports.models import FinancialReportSnapshot, RiskFinding, RiskReport


def analyze_financial_risks(snapshot: FinancialReportSnapshot) -> RiskReport:
    findings: list[RiskFinding] = []
    findings.extend(check_leverage(snapshot))
    findings.extend(check_cash_profit_quality(snapshot))
    findings.extend(check_receivable_pressure(snapshot))
    findings.extend(check_inventory_pressure(snapshot))
    findings.extend(check_goodwill_pressure(snapshot))
    findings.extend(check_short_term_liquidity(snapshot))
    findings.extend(check_missing_core_metrics(snapshot))
    return RiskReport(snapshot=snapshot, findings=findings, score=calculate_score(findings))


def check_leverage(snapshot: FinancialReportSnapshot) -> list[RiskFinding]:
    assets = snapshot.get("total_assets")
    liabilities = snapshot.get("total_liabilities")
    if not assets or liabilities is None:
        return []
    ratio = liabilities / assets
    if ratio >= 0.7:
        level = "high"
    elif ratio >= 0.6:
        level = "medium"
    else:
        return []
    return [
        RiskFinding(
            area="solvency",
            level=level,
            title="资产负债率偏高",
            description=f"资产负债率约为 {ratio:.1%}，债务压力可能削弱抗风险能力。",
            evidence=metric_evidence(snapshot, "total_assets", "total_liabilities"),
            metrics={"debt_to_asset": ratio},
        )
    ]


def check_cash_profit_quality(snapshot: FinancialReportSnapshot) -> list[RiskFinding]:
    net_profit = snapshot.get("net_profit")
    ocf = snapshot.get("operating_cash_flow")
    if net_profit is None or ocf is None or net_profit <= 0:
        return []
    ratio = ocf / net_profit
    if ocf < 0:
        level = "high"
        title = "盈利与经营现金流背离"
        description = "公司实现盈利但经营活动现金流为负，利润含金量存在疑问。"
    elif ratio < 0.5:
        level = "medium"
        title = "经营现金流覆盖净利润不足"
        description = f"经营现金流/净利润约为 {ratio:.1%}，盈利质量需要进一步核查。"
    else:
        return []
    return [
        RiskFinding(
            area="cash_flow",
            level=level,
            title=title,
            description=description,
            evidence=metric_evidence(snapshot, "net_profit", "operating_cash_flow"),
            metrics={"operating_cash_flow_to_net_profit": ratio},
        )
    ]


def check_receivable_pressure(snapshot: FinancialReportSnapshot) -> list[RiskFinding]:
    receivables = snapshot.get("accounts_receivable")
    revenue = snapshot.get("revenue")
    if receivables is None or not revenue:
        return []
    ratio = receivables / revenue
    if ratio >= 0.5:
        level = "high"
    elif ratio >= 0.3:
        level = "medium"
    else:
        return []
    return [
        RiskFinding(
            area="asset_quality",
            level=level,
            title="应收账款占营业收入比例偏高",
            description=f"应收账款/营业收入约为 {ratio:.1%}，可能存在回款压力或收入确认质量风险。",
            evidence=metric_evidence(snapshot, "accounts_receivable", "revenue"),
            metrics={"receivables_to_revenue": ratio},
        )
    ]


def check_inventory_pressure(snapshot: FinancialReportSnapshot) -> list[RiskFinding]:
    inventory = snapshot.get("inventory")
    revenue = snapshot.get("revenue")
    if inventory is None or not revenue:
        return []
    ratio = inventory / revenue
    if ratio < 0.5:
        return []
    level = "high" if ratio >= 1 else "medium"
    return [
        RiskFinding(
            area="asset_quality",
            level=level,
            title="存货规模相对收入偏高",
            description=f"存货/营业收入约为 {ratio:.1%}，需关注跌价准备、周转效率和滞销风险。",
            evidence=metric_evidence(snapshot, "inventory", "revenue"),
            metrics={"inventory_to_revenue": ratio},
        )
    ]


def check_goodwill_pressure(snapshot: FinancialReportSnapshot) -> list[RiskFinding]:
    goodwill = snapshot.get("goodwill")
    assets = snapshot.get("total_assets")
    if goodwill is None or not assets:
        return []
    ratio = goodwill / assets
    if ratio >= 0.2:
        level = "high"
    elif ratio >= 0.1:
        level = "medium"
    else:
        return []
    return [
        RiskFinding(
            area="impairment",
            level=level,
            title="商誉占总资产比例偏高",
            description=f"商誉/总资产约为 {ratio:.1%}，并购资产若业绩不达预期可能触发减值。",
            evidence=metric_evidence(snapshot, "goodwill", "total_assets"),
            metrics={"goodwill_to_assets": ratio},
        )
    ]


def check_short_term_liquidity(snapshot: FinancialReportSnapshot) -> list[RiskFinding]:
    cash = snapshot.get("monetary_funds")
    short_debt = sum_metric_values(snapshot, "short_term_debt", "current_portion_debt")
    if cash is None or short_debt is None or short_debt <= 0:
        return []
    ratio = cash / short_debt
    if ratio >= 0.8:
        return []
    level = "high" if ratio < 0.5 else "medium"
    return [
        RiskFinding(
            area="liquidity",
            level=level,
            title="货币资金对短期有息债务覆盖不足",
            description=f"货币资金/短期有息债务约为 {ratio:.1%}，短期偿债安排需要重点关注。",
            evidence=metric_evidence(snapshot, "monetary_funds", "short_term_debt", "current_portion_debt"),
            metrics={"cash_to_short_debt": ratio},
        )
    ]


def check_missing_core_metrics(snapshot: FinancialReportSnapshot) -> list[RiskFinding]:
    required = {
        "total_assets": "资产总计",
        "total_liabilities": "负债合计",
        "revenue": "营业收入",
        "net_profit": "净利润",
        "operating_cash_flow": "经营活动现金流量净额",
    }
    missing = [name for key, name in required.items() if key not in snapshot.metrics]
    if not missing:
        return []
    return [
        RiskFinding(
            area="data_quality",
            level="low",
            title="核心财务指标抽取不完整",
            description="部分关键指标未从报告文本中抽取到，风险结论应结合原始财报复核。",
            evidence=[f"缺失指标：{', '.join(missing)}"],
            metrics={"missing_count": len(missing)},
        )
    ]


def calculate_score(findings: list[RiskFinding]) -> int:
    score = 100
    penalty = {"high": 25, "medium": 12, "low": 5}
    for finding in findings:
        score -= penalty.get(finding.level, 0)
    return max(score, 0)


def metric_evidence(snapshot: FinancialReportSnapshot, *keys: str) -> list[str]:
    evidence: list[str] = []
    for key in keys:
        metric = snapshot.metrics.get(key)
        if metric is None:
            continue
        value = format_metric(metric.value, metric.unit)
        location = f"第 {metric.line_number} 行" if metric.line_number else "未知行号"
        evidence.append(f"{metric.name}: {value} ({location}; {metric.source_text})")
    return evidence


def sum_metric_values(snapshot: FinancialReportSnapshot, *keys: str) -> float | None:
    values = [snapshot.get(key) for key in keys if snapshot.get(key) is not None]
    if not values:
        return None
    return sum(values)


def format_metric(value: float, unit: str | None) -> str:
    formatted = f"{value:,.2f}".rstrip("0").rstrip(".")
    return f"{formatted}{unit or ''}"
