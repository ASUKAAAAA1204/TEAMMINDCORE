from __future__ import annotations

from pydantic import BaseModel


class ReportRequest(BaseModel):
    entity: str
    report_type: str
    include_sources: bool = True
    max_sections: int = 8


class ReportSection(BaseModel):
    section: str
    content: str
    sources: list[str]


class ReportResponse(BaseModel):
    title: str
    sections: list[ReportSection]
    overall_summary: str
    sources_count: int
    generated_at: str

