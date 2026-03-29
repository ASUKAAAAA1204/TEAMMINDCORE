from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_container
from app.core.container import ServiceContainer
from app.modules.retrieval.schemas import SearchRequest, SearchResponse


router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=SearchResponse)
def search_documents(
    payload: SearchRequest,
    container: ServiceContainer = Depends(get_container),
) -> SearchResponse:
    result = container.retrieval.search(
        query=payload.query,
        top_k=payload.top_k,
        hybrid_alpha=payload.hybrid_alpha,
        filters=payload.filters.model_dump(),
    )
    return SearchResponse(**result)

