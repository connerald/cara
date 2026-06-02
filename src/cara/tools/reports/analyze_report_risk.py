from __future__ import annotations

from cara.reports import analyze_financial_risks, extract_financial_report


def analyze_report_risk(file_path: str) -> str:
    """从本地财报文件中分析财务风险信号。"""

    snapshot = extract_financial_report(file_path)
    report = analyze_financial_risks(snapshot)
    return report.to_markdown()
