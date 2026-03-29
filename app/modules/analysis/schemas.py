from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    task: str
    document_ids: list[str]
    output_format: str = "json"


class AnalysisResponse(BaseModel):
    task_id: str
    results: dict[str, Any]

