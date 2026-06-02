import tempfile
import unittest
from pathlib import Path

from cara.reports import analyze_financial_risks, extract_financial_report
from cara.agents.reports.report_risk_agent import summarize_risk_report_with_ai
from cara.tools.reports.analyze_report_risk import analyze_report_risk


SAMPLE_REPORT = """
测试科技股份有限公司
2025年年度报告

资产总计 1,000.00 万元
负债合计 760.00 万元
营业收入 500.00 万元
净利润 80.00 万元
经营活动产生的现金流量净额 -20.00 万元
应收账款 260.00 万元
存货 280.00 万元
商誉 120.00 万元
货币资金 60.00 万元
短期借款 100.00 万元
一年内到期的非流动负债 80.00 万元
"""


class ReportRiskTest(unittest.TestCase):
    def test_extract_and_analyze_report_risk(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample_report.txt"
            path.write_text(SAMPLE_REPORT, encoding="utf-8")

            snapshot = extract_financial_report(path)
            self.assertEqual(snapshot.company_name, "测试科技股份有限公司")
            self.assertEqual(snapshot.get("total_assets"), 1000.0)
            self.assertEqual(snapshot.get("operating_cash_flow"), -20.0)

            report = analyze_financial_risks(snapshot)
            titles = {finding.title for finding in report.findings}

            self.assertIn("资产负债率偏高", titles)
            self.assertIn("盈利与经营现金流背离", titles)
            self.assertIn("应收账款占营业收入比例偏高", titles)
            self.assertLess(report.score, 100)

    def test_tool_returns_markdown(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample_report.txt"
            path.write_text(SAMPLE_REPORT, encoding="utf-8")

            markdown = analyze_report_risk(str(path))

            self.assertIn("# 财报风险分析报告", markdown)
            self.assertIn("测试科技股份有限公司", markdown)
            self.assertIn("资产负债率偏高", markdown)

    def test_ai_summary_uses_deterministic_report(self):
        class FakeMessage:
            content = "AI 摘要"

        class FakeModel:
            def __init__(self):
                self.messages = None

            def invoke(self, messages):
                self.messages = messages
                return FakeMessage()

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample_report.txt"
            path.write_text(SAMPLE_REPORT, encoding="utf-8")
            snapshot = extract_financial_report(path)
            report = analyze_financial_risks(snapshot)
            model = FakeModel()

            summary = summarize_risk_report_with_ai(report, model=model)

            self.assertEqual(summary, "AI 摘要")
            self.assertIsNotNone(model.messages)
            self.assertIn("# 财报风险分析报告", model.messages[1][1])
            self.assertIn("资产负债率偏高", model.messages[1][1])


if __name__ == "__main__":
    unittest.main()
