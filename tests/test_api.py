import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from cara.api.app import app


SAMPLE_REPORT = """
测试科技股份有限公司
2025年年度报告

资产总计 1,000.00 万元
负债合计 760.00 万元
营业收入 500.00 万元
净利润 80.00 万元
经营活动产生的现金流量净额 -20.00 万元
应收账款 260.00 万元
"""


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_analyze_report_upload(self):
        response = self.client.post(
            "/api/reports/analyze",
            files={"file": ("sample_report.txt", SAMPLE_REPORT.encode("utf-8"), "text/plain")},
        )

        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["snapshot"]["company_name"], "测试科技股份有限公司")
        self.assertEqual(body["snapshot"]["source_path"], "sample_report.txt")
        self.assertLess(body["score"], 100)
        self.assertTrue(any(metric["key"] == "total_assets" for metric in body["metrics"]))
        self.assertTrue(any(finding["title"] == "资产负债率偏高" for finding in body["findings"]))
        self.assertIn("# 财报风险分析报告", body["markdown"])
        self.assertIsNone(body["ai_summary"])

    def test_analyze_report_ai_upload(self):
        with patch(
            "cara.api.app.summarize_risk_report_with_ai",
            return_value="AI 解读：存在偿债和现金流压力。",
        ) as summarize:
            response = self.client.post(
                "/api/reports/analyze/ai",
                files={"file": ("sample_report.txt", SAMPLE_REPORT.encode("utf-8"), "text/plain")},
            )

        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["snapshot"]["company_name"], "测试科技股份有限公司")
        self.assertEqual(body["ai_summary"], "AI 解读：存在偿债和现金流压力。")
        summarize.assert_called_once()

    def test_reject_unsupported_file_type(self):
        response = self.client.post(
            "/api/reports/analyze",
            files={"file": ("sample.csv", b"name,value", "text/csv")},
        )

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
