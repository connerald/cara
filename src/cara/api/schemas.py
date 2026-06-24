from __future__ import annotations

from pydantic import BaseModel, Field


class MetricResponse(BaseModel):
    key: str
    name: str
    value: float
    unit: str | None = None
    source_text: str | None = None
    line_number: int | None = None


class FindingResponse(BaseModel):
    area: str
    level: str
    title: str
    description: str
    evidence: list[str] = Field(default_factory=list)
    metrics: dict[str, float | int | str] = Field(default_factory=dict)


class ReportSnapshotResponse(BaseModel):
    company_name: str | None = None
    report_period: str | None = None
    report_type: str | None = None
    source_path: str | None = None
    raw_text_chars: int
    raw_text_preview: str | None = None


class ReportAnalysisResponse(BaseModel):
    snapshot: ReportSnapshotResponse
    metrics: list[MetricResponse]
    findings: list[FindingResponse]
    score: int
    summary_counts: dict[str, int]
    markdown: str
    ai_summary: str | None = None
