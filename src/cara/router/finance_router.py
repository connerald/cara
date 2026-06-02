from __future__ import annotations


def route_finance_task(message: str) -> str:
    """将金融请求路由到第一个匹配的 agent 家族。"""

    normalized = message.lower()
    report_keywords = ("财报", "年报", "季报", "半年报", "financial report", "risk", "风险")
    if any(keyword in normalized for keyword in report_keywords):
        return "report_risk_agent"
    return "market_agent"
