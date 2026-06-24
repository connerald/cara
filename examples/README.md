# Examples

这个目录保存 Cara 财报分析的手动验证材料。

```text
examples/
  reports/
    sample_report.txt                  # 小型合成财报，用于快速手动验证
    real/
      maotai_2025_annual_report.pdf    # 真实公开年报，用于本地抽取回归检查
```

自动化测试不要直接依赖完整 PDF。请从真实 PDF 中提取代表性小片段，放到
`tests/fixtures/reports/realistic/`，这样测试更快、更稳定，也更容易定位抽取问题。
