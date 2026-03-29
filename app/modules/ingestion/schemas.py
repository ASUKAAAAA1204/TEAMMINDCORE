from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class UploadResponse(BaseModel):
    document_ids: list[str]
    status: str
    progress: float
    message: str


class DocumentSummary(BaseModel):
    id: str
    filename: str
    upload_time: str
    parse_status: str
    metadata: dict[str, Any]
    tags: list[str]


class DocumentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    documents: list[DocumentSummary]


class DeleteResponse(BaseModel):
    success: bool
    message: str

