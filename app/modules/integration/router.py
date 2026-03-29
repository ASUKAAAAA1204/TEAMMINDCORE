from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_container
from app.core.container import ServiceContainer
from app.modules.integration.schemas import MergeRequest, MergeResponse


router = APIRouter(prefix="/integration", tags=["integration"])


@router.post("/merge", response_model=MergeResponse)
def merge_documents(
    payload: MergeRequest,
    container: ServiceContainer = Depends(get_container),
) -> MergeResponse:
    result = container.merge.merge(
        document_ids=payload.document_ids,
        rule=payload.rule.model_dump(),
    )
    return MergeResponse(**result)
