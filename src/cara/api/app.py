from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from cara.api.schemas import (
    FindingResponse,
    MetricResponse,
    ReportAnalysisResponse,
    ReportSnapshotResponse,
)
from cara.agents.reports.report_risk_agent import summarize_risk_report_with_ai
from cara.reports import analyze_financial_risks, extract_financial_report
from cara.reports.models import RiskReport


app = FastAPI(
    title="Cara 金融分析 Agent API",
    description="财报抽取与风险分析 API。",
    version="0.1.0",
)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/reports/analyze", response_model=ReportAnalysisResponse)
async def analyze_report(file: UploadFile = File(...)) -> ReportAnalysisResponse:
    return await analyze_uploaded_report(file, include_ai_summary=False)


@app.post("/api/reports/analyze/ai", response_model=ReportAnalysisResponse)
async def analyze_report_with_ai(file: UploadFile = File(...)) -> ReportAnalysisResponse:
    return await analyze_uploaded_report(file, include_ai_summary=True)


async def analyze_uploaded_report(
    file: UploadFile,
    *,
    include_ai_summary: bool,
) -> ReportAnalysisResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".txt", ".md", ".text"}:
        raise HTTPException(status_code=400, detail="仅支持 .pdf、.txt、.md 和 .text 财报文件。")

    temp_path: Path | None = None
    try:
        temp_path = await save_upload_to_temp_file(file, suffix)
        snapshot = extract_financial_report(temp_path)
        snapshot.source_path = file.filename
        report = analyze_financial_risks(snapshot)
        ai_summary = summarize_risk_report_with_ai(report) if include_ai_summary else None
        return serialize_report(report, ai_summary=ai_summary)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if temp_path and temp_path.exists():
            os.unlink(temp_path)


async def save_upload_to_temp_file(file: UploadFile, suffix: str) -> Path:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="上传的财报文件为空。")

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        handle.write(content)
        return Path(handle.name)
    finally:
        handle.close()


def serialize_report(report: RiskReport, ai_summary: str | None = None) -> ReportAnalysisResponse:
    snapshot = report.snapshot
    metrics = [
        MetricResponse(
            key=metric.key,
            name=metric.name,
            value=metric.value,
            unit=metric.unit,
            source_text=metric.source_text,
            line_number=metric.line_number,
        )
        for metric in sorted(snapshot.metrics.values(), key=lambda item: item.line_number or 0)
    ]
    findings = [
        FindingResponse(
            area=finding.area,
            level=finding.level,
            title=finding.title,
            description=finding.description,
            evidence=finding.evidence,
            metrics=finding.metrics,
        )
        for finding in report.findings
    ]
    return ReportAnalysisResponse(
        snapshot=ReportSnapshotResponse(
            company_name=snapshot.company_name,
            report_period=snapshot.report_period,
            report_type=snapshot.report_type,
            source_path=snapshot.source_path,
            raw_text_chars=snapshot.raw_text_chars,
        ),
        metrics=metrics,
        findings=findings,
        score=report.score,
        summary_counts=report.summary_counts,
        markdown=report.to_markdown(),
        ai_summary=ai_summary,
    )
