from __future__ import annotations

from pydantic import BaseModel, Field


class MergeRule(BaseModel):
    strategy: str = "concatenate"
    format: str = "markdown"


class MergeRequest(BaseModel):
    document_ids: list[str]
    rule: MergeRule = Field(default_factory=MergeRule)


class MergeResponse(BaseModel):
    merged_content: str
    total_length: int
    source_count: int

