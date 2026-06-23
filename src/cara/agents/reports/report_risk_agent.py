from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from cara.reports import analyze_financial_risks, extract_financial_report
from cara.reports.models import RiskReport
from cara.tools.reports.analyze_report_risk import analyze_report_risk


REPORT_RISK_SYSTEM_PROMPT = """
你是 Cara，一个财报风险分析 agent。

请先使用工具抽取确定性的财务风险信号，再用简洁、基于证据的方式解释结果。
不要提供投资建议。如果关键指标缺失，需要说明结论受抽取质量限制。
""".strip()


def build_default_model() -> Any:
    from langchain_openai import ChatOpenAI

    load_dotenv(override=True)
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 DEEPSEEK_API_KEY 环境变量，无法调用 DeepSeek。")

    return ChatOpenAI(
        model=os.getenv("CARA_MODEL", "deepseek-v4-pro"),
        api_key=api_key,
        base_url=os.getenv("CARA_MODEL_BASE_URL", "https://api.deepseek.com"),
        extra_body={"thinking": {"type": "disabled"}},
    )


def build_report_risk_agent(model: Any | None = None):
    from langchain.agents import create_agent

    return create_agent(
        model=model or build_default_model(),
        tools=[analyze_report_risk],
        system_prompt=REPORT_RISK_SYSTEM_PROMPT,
    )


def invoke_report_risk_agent(file_path: str, model: Any | None = None):
    agent = build_report_risk_agent(model=model)
    return agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"请分析这个文件中的财报风险信号：{file_path}",
                }
            ]
        }
    )


def summarize_risk_report_with_ai(report: RiskReport, model: Any | None = None) -> str:
    """用 LLM 基于确定性风险报告生成面向用户的摘要。"""

    chat_model = model or build_default_model()
    result = chat_model.invoke(
        [
            (
                "system",
                "\n".join(
                    [
                        REPORT_RISK_SYSTEM_PROMPT,
                        "你只能基于用户提供的指标、风险发现和证据进行总结。",
                        "输出中文，结构简洁，明确说明这不是投资建议。",
                    ]
                ),
            ),
            (
                "user",
                "\n".join(
                    [
                        "请基于下面的确定性财报风险报告，生成一段简洁的 AI 解读。",
                        "需要覆盖主要风险、证据强度、数据缺失限制和建议关注点。",
                        "",
                        report.to_markdown(),
                    ]
                ),
            ),
        ]
    )
    return _message_content_to_text(result)


def analyze_report_risk_with_ai(file_path: str, model: Any | None = None) -> tuple[RiskReport, str]:
    snapshot = extract_financial_report(file_path)
    report = analyze_financial_risks(snapshot)
    return report, summarize_risk_report_with_ai(report, model=model)


def _message_content_to_text(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text") or block.get("content")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts).strip()
    return str(content).strip()
