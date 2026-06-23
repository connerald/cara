import unittest
from pathlib import Path

from cara.reports import analyze_financial_risks, extract_financial_report


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "reports"


class ReportScenarioTest(unittest.TestCase):
    def assert_report_scenario(
        self,
        fixture_name: str,
        *,
        expected_titles: set[str],
        absent_titles: set[str] | None = None,
    ):
        snapshot = extract_financial_report(FIXTURE_DIR / fixture_name)
        report = analyze_financial_risks(snapshot)
        titles = {finding.title for finding in report.findings}

        self.assertGreater(snapshot.raw_text_chars, 0)
        self.assertTrue(expected_titles.issubset(titles), titles)
        if absent_titles:
            self.assertTrue(titles.isdisjoint(absent_titles), titles)
        return snapshot, report

    def test_normal_report_has_no_rule_based_risk_findings(self):
        snapshot, report = self.assert_report_scenario("normal_report.txt", expected_titles=set())

        self.assertEqual(snapshot.company_name, "稳健制造股份有限公司")
        self.assertEqual(snapshot.get("total_assets"), 1000.0)
        self.assertEqual(report.score, 100)
        self.assertEqual(report.findings, [])

    def test_profit_with_negative_operating_cash_flow_triggers_cash_quality_risk(self):
        snapshot, report = self.assert_report_scenario(
            "profitable_but_cashflow_negative.txt",
            expected_titles={"盈利与经营现金流背离"},
            absent_titles={"资产负债率偏高", "应收账款占营业收入比例偏高"},
        )

        cash_finding = next(f for f in report.findings if f.title == "盈利与经营现金流背离")
        self.assertEqual(cash_finding.level, "high")
        self.assertLess(cash_finding.metrics["operating_cash_flow_to_net_profit"], 0)
        self.assert_finding_has_source_lines(cash_finding.evidence)
        self.assertEqual(snapshot.get("operating_cash_flow"), -30.0)

    def test_high_receivables_triggers_asset_quality_risk(self):
        _, report = self.assert_report_scenario(
            "high_receivables.txt",
            expected_titles={"应收账款占营业收入比例偏高"},
            absent_titles={"盈利与经营现金流背离", "货币资金对短期有息债务覆盖不足"},
        )

        finding = next(f for f in report.findings if f.title == "应收账款占营业收入比例偏高")
        self.assertEqual(finding.level, "high")
        self.assertAlmostEqual(finding.metrics["receivables_to_revenue"], 0.5)
        self.assert_finding_has_source_lines(finding.evidence)

    def test_low_cash_coverage_triggers_short_term_liquidity_risk(self):
        _, report = self.assert_report_scenario(
            "high_debt_low_cash.txt",
            expected_titles={"货币资金对短期有息债务覆盖不足"},
            absent_titles={"资产负债率偏高", "盈利与经营现金流背离"},
        )

        finding = next(f for f in report.findings if f.title == "货币资金对短期有息债务覆盖不足")
        self.assertEqual(finding.level, "high")
        self.assertAlmostEqual(finding.metrics["cash_to_short_debt"], 0.2)
        self.assert_finding_has_source_lines(finding.evidence)

    def test_missing_core_metrics_creates_data_quality_limitation(self):
        snapshot, report = self.assert_report_scenario(
            "missing_core_metrics.txt",
            expected_titles={"核心财务指标抽取不完整"},
        )

        finding = next(f for f in report.findings if f.title == "核心财务指标抽取不完整")
        self.assertEqual(finding.level, "low")
        self.assertEqual(snapshot.get("revenue"), 300.0)
        self.assertIn("资产总计", finding.evidence[0])
        self.assertGreaterEqual(finding.metrics["missing_count"], 4)

    def test_every_non_data_quality_finding_keeps_auditable_evidence(self):
        for path in FIXTURE_DIR.glob("*.txt"):
            with self.subTest(path=path.name):
                report = analyze_financial_risks(extract_financial_report(path))
                for finding in report.findings:
                    if finding.area == "data_quality":
                        continue
                    self.assert_finding_has_source_lines(finding.evidence)

    def assert_finding_has_source_lines(self, evidence: list[str]):
        self.assertGreaterEqual(len(evidence), 1)
        for item in evidence:
            self.assertIn("第 ", item)
            self.assertIn("行", item)


if __name__ == "__main__":
    unittest.main()
