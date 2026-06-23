# cara

Cara 是一个早期阶段的金融分析 agent 项目。当前 MVP 聚焦于识别财报文件，
从关键财务指标中抽取结构化事实，并基于确定性规则生成风险发现。

## 当前能力

- 读取本地 `.txt`、`.md`、`.text` 和 `.pdf` 财报文件。
- 抽取中文财报中的常见财务指标，包括资产、负债、营业收入、净利润、
  经营现金流、应收账款、存货、商誉、货币资金和短期债务等。
- 生成确定性的风险发现，覆盖：
  - 偿债压力
  - 现金流与利润背离
  - 应收账款压力
  - 存货压力
  - 商誉减值暴露
  - 短期流动性压力
  - 核心指标抽取不完整
- 通过可调用 tool、LangChain agent 入口和 FastAPI 后端暴露分析能力。

## 快速开始

运行确定性财报风险分析，不调用 LLM：

```powershell
uv run python -c "from cara.tools.reports.analyze_report_risk import analyze_report_risk; print(analyze_report_risk('examples/sample_report.txt'))"
```

构建 LangChain 财报风险 agent：

```python
from cara.agents.reports.report_risk_agent import invoke_report_risk_agent

result = invoke_report_risk_agent("examples/sample_report.txt")
print(result["messages"][-1].content)
```

如需调用 LLM，设置：

```powershell
$env:DEEPSEEK_API_KEY = "..."
```

也可以在项目根目录创建 `.env` 文件；项目会优先读取该文件中的值，缺失时再使用系统环境变量。

最小配置只需要 DeepSeek API key：

```env
DEEPSEEK_API_KEY=...
```

如需覆盖默认模型或 API 地址，可以添加以下可选变量：

```env
CARA_MODEL=deepseek-v4-pro
CARA_MODEL_BASE_URL=https://api.deepseek.com
```

PDF 解析通过 `pypdf` 实现。

## FastAPI 后端

启动后端 API：

```powershell
uv run uvicorn cara.api.app:app --reload
```

健康检查：

```powershell
curl http://127.0.0.1:8000/api/health
```

上传并分析财报：

```powershell
curl.exe -X POST `
  -F "file=@examples/sample_report.txt" `
  http://127.0.0.1:8000/api/reports/analyze
```

上传并生成 AI 解读：

```powershell
curl.exe -X POST `
  -F "file=@examples/sample_report.txt" `
  http://127.0.0.1:8000/api/reports/analyze/ai
```

接口响应包含：

- `snapshot`：公司名、报告期、报告类型、来源文件名、原始文本长度
- `metrics`：抽取出的财务指标，包含来源文本和行号
- `findings`：基于规则生成的风险发现和证据
- `score`：0 到 100 的风险分数
- `markdown`：渲染后的风险报告文本
- `ai_summary`：仅 `/api/reports/analyze/ai` 返回，基于确定性报告生成的 AI 解读

## Web 前端

前端位于 `frontend/`，使用 Vite、TypeScript 和 React。

安装依赖：

```powershell
cd frontend
npm install
```

启动开发服务：

```powershell
npm run dev
```

默认访问地址：

```text
http://127.0.0.1:5173/
```

开发环境已配置 `/api` 代理到 `http://127.0.0.1:8000`。如需使用其他后端地址，可设置 `VITE_API_BASE_URL`。

## 后续方向

- 增加面向多列表格财报的结构化抽取能力。
- 增加 A 股财报下载来源连接器。
- 增加跨报告期趋势分析。
- 增加新闻和行情数据上下文，用于解释风险事件。
- 增加基于规则发现和抽取证据的 LLM 总结能力。
