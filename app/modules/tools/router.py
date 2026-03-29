from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_repository
from app.runtime import build_tools_payload
from app.repositories.document_repository import SQLiteDocumentRepository


router = APIRouter(tags=["tools"])


@router.get("/tools")
def list_tool_schemas(repository: SQLiteDocumentRepository = Depends(get_repository)) -> dict[str, object]:
    return build_tools_payload(repository)
