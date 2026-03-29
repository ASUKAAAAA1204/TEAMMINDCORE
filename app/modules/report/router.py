from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_container
from app.core.container import ServiceContainer
from app.modules.report.schemas import ReportRequest, ReportResponse


router = APIRouter(prefix="/report", tags=["report"])


@router.post("/generate", response_model=ReportResponse)
def generate_report(
    payload: ReportRequest,
    container: ServiceContainer = Depends(get_container),
) -> ReportResponse:
    result = container.report.generate(
        entity=payload.entity,
        report_type=payload.report_type,
        include_sources=payload.include_sources,
        max_sections=payload.max_sections,
    )
    return ReportResponse(**result)

