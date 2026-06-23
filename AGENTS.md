# AGENTS.md

这份文件用于给后续编码 agent 和项目协作者提供 Cara 项目的工作上下文。

## 编码规则

本项目所有文本文件使用 UTF-8 编码。

## 项目目标

Cara 是一个金融分析 agent 项目，目标是识别财报、抽取结构化财务指标，并基于指标分析风险信号。

当前 MVP 聚焦于：

- 读取本地 `.txt`、`.md`、`.pdf` 财报文件。（需要支持web端或者命令行输入路径上传）
- 抽取中文财报中的关键财务指标。
- 基于确定性规则生成带证据的风险发现。
- 通过 FastAPI 后端暴露功能接口和分析能力。
- 为后续 Web 前端和 LLM 总结能力预留结构。

需要向用户说明，当前输出不能视为投资建议，风险分析结果只是筛查辅助。

## 目录结构

当前项目为敏捷开发阶段，目录结构多变，需要查看目录结构时不能依赖过去的查看结果。

## 依赖管理

本项目使用 `uv` 管理 Python 版本、依赖和运行环境。

Python 版本固定在 Python 3.11 系列。当前项目根目录的 `.python-version` 为：

```powershell
3.11.9
```

不要随意升级到 Python 3.12/3.13。创建或修复本地环境时，使用 Python 3.11：

```powershell
uv python pin 3.11.9
uv sync
```

新增依赖时，不要直接手写 `pyproject.toml` 的依赖列表。先让 `uv` 在当前 Python 3.11 环境下解析可用的最优版本：

```powershell
uv add <package>
```

如果是开发依赖：

```powershell
uv add --dev <package>
```

`uv add` 会同时更新 `pyproject.toml` 和 `uv.lock`。添加完成后，需要查看当前环境实际解析出的版本，并在说明或提交信息中给出该版本：

```powershell
uv pip list
uv tree
```

如果新增依赖需要固定版本，优先固定为当前 Python 3.11 环境下已经解析通过的版本，例如：

```powershell
uv add "fastapi==0.136.3"
uv add "uvicorn==0.48.0"
uv add "python-multipart==0.0.30"
```

如果只是探索依赖，先用不带版本号的 `uv add <package>` 解析；确认可用后，再根据当前解析结果决定是否收紧到 `==` 或兼容范围。不要凭记忆填写版本号。

如果手动修改了 `pyproject.toml` 中的非依赖配置，例如 `build-system` 或 `tool.setuptools`，需要刷新锁文件：

```powershell
uv lock
```

在项目环境中运行命令：

```powershell
uv run python -m unittest discover -s tests
```

项目使用 `src` layout，并已在 `pyproject.toml` 中配置包发现。优先使用 `uv run`，不要依赖手动设置 `PYTHONPATH`。

## 后端 API

启动 FastAPI 后端：

```powershell
uv run uvicorn cara.api.app:app --reload --host 127.0.0.1 --port 8000
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

接口响应包含：

- `snapshot`：公司名、报告期、报告类型、来源文件名、原始文本长度
- `metrics`：抽取出的财务指标，包含来源文本和行号
- `findings`：基于规则生成的风险发现和证据
- `score`：0 到 100 的风险分数
- `markdown`：渲染后的风险报告文本

## 财报分析规则

保持“抽取”和“分析”的职责分离：

- `reports/extractor.py` 只负责读取文件和抽取事实。
- `reports/risk_rules.py` 负责把抽取出的事实转成风险发现。
- `tools/reports/analyze_report_risk.py` 保持为薄包装，只作为可调用 tool。
- `api/app.py` 只处理 HTTP、上传文件和响应序列化，不放业务规则。

新增风险规则时：

- 明确规则使用的指标 key。
- 给每条风险发现附上原始指标行作为证据。
- MVP 阶段优先使用确定性阈值。
- 用代表性的财报文本补充或更新测试。
- 不要掩盖数据缺失导致的结论限制。

新增抽取逻辑时：

- 保留对 `.txt`、`.md`、`.text`、`.pdf` 的支持。
- PDF 解析通过 `pypdf` 实现。
- 如果能使用结构化或表格感知解析，优先于纯字符串拼接。
- 不要在缺少证据时静默编造数值。

## Agent 和 LLM 边界

LLM 调用不能在模块 import 时自动执行。模型构造应放在函数里，例如 `build_report_risk_agent`。

推荐流程：

1. 先抽取确定性的财务指标。
2. 再运行确定性的风险规则。
3. 如有需要，再让 LLM 基于指标和风险证据做总结或解释。

LLM 不应成为风险分类的唯一来源。

## 测试

运行全部测试：

```powershell
uv run python -m unittest discover -s tests
```

手动验证财报分析：

```powershell
uv run python -c "from cara.tools.reports.analyze_report_risk import analyze_report_risk; print(analyze_report_risk('examples/sample_report.txt'))"
```

PowerShell 中需要设置 UTF-8：

```powershell
$env:PYTHONIOENCODING='utf-8'
```

## 代码风格

- 模块保持小而聚焦。
- 财报领域数据优先使用 `reports/models.py` 中的 dataclass。
- API 响应结构通过 `api/schemas.py` 中的 Pydantic 模型显式定义。
- 不做和当前需求无关的大规模重构。
- 不提交 `__pycache__`、`src/cara.egg-info` 等生成物。
- 工作区里可能已有用户改动，不要回滚无关文件。

## Git 提交规范

提交信息使用简洁的 Conventional Commits 风格：

```text
<type>(<scope>): <summary>
```

常用 `type`：

- `feat`：新增功能或用户可见能力。
- `fix`：修复缺陷或错误行为。
- `docs`：仅修改文档。
- `test`：新增或调整测试。
- `refactor`：不改变行为的代码重构。
- `chore`：构建、配置、依赖、脚本等维护改动。

提交要求：

- `summary` 使用中文或英文均可，但要具体说明本次变更，不要只写 `update`、`fix bug` 等泛泛描述。
- `scope` 优先使用受影响模块，例如 `reports`、`api`、`tests`、`deps`、`docs`；范围不明确时可以省略。
- 一次提交只包含一个清晰主题，不混入无关格式化、临时调试代码或生成物。
- 如果新增或调整依赖，需要在提交说明或正文中写明通过 `uv` 解析后的实际版本。
- 如果没有运行测试，需要在提交说明、PR 描述或交付说明中明确原因。
- 不要提交包含密钥、令牌、真实用户隐私数据或本地环境专用路径的内容。

示例：

```text
feat(reports): 支持抽取资产负债率指标
fix(api): 返回上传文件解析失败的结构化错误
docs(agents): 添加 Git 提交规范
chore(deps): 添加 pypdf 解析依赖
```

## 前端方向

计划中的 Web 前端应调用 `POST /api/reports/analyze`，并展示：

- `.pdf`、`.txt`、`.md` 文件上传控件
- 抽取出的财务指标表格
- 按风险等级分组的风险发现
- Markdown 风险报告预览

第一屏应该是实际分析工作台，不要做成营销落地页。
