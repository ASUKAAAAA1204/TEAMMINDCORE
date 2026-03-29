from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RetrievalFilters(BaseModel):
    tags: list[str] = Field(default_factory=list)
    date_after: str | None = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 8
    hybrid_alpha: float = 0.7
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)


class SearchResult(BaseModel):
    text: str
    score: float
    document_id: str
    metadata: dict[str, Any]


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total_found: int

