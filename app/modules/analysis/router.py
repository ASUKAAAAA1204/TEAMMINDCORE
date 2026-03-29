from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_container
from app.core.container import ServiceContainer
from app.modules.analysis.schemas import AnalysisRequest, AnalysisResponse


router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/execute", response_model=AnalysisResponse)
def execute_analysis(
    payload: AnalysisRequest,
    container: ServiceContainer = Depends(get_container),
) -> AnalysisResponse:
    result = container.analysis.execute(
        task=payload.task,
        document_ids=payload.document_ids,
        output_format=payload.output_format,
    )
    return AnalysisResponse(**result)

