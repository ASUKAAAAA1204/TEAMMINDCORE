from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile

from app.api.deps import get_container, get_repository, get_settings_dependency
from app.core.config import Settings
from app.core.container import ServiceContainer
from app.modules.ingestion.operations import (
    build_upload_response,
    delete_document_record,
    enqueue_upload,
    list_documents_response,
    parse_tags,
)
from app.modules.ingestion.schemas import DeleteResponse, DocumentListResponse, DocumentSummary, UploadResponse
from app.repositories.document_repository import SQLiteDocumentRepository


router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    team_id: str = Form("default"),
    tags: str | None = Form(default=None),
    parse_mode: str = Form(default="auto"),
    settings: Settings = Depends(get_settings_dependency),
    repository: SQLiteDocumentRepository = Depends(get_repository),
    container: ServiceContainer = Depends(get_container),
) -> UploadResponse:
    normalized_tags = parse_tags(tags)
    document_ids: list[str] = []
    for file in files:
        document_ids.append(
            enqueue_upload(
                filename=file.filename,
                file_bytes=file.file.read(),
                team_id=team_id,
                parse_mode=parse_mode,
                tags=normalized_tags,
                uploads_dir=settings.uploads_dir,
                repository=repository,
                container=container,
                background_tasks=background_tasks,
            )
        )
    return build_upload_response(document_ids)


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    team_id: str | None = None,
    keyword: str | None = None,
    tags: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 10,
    repository: SQLiteDocumentRepository = Depends(get_repository),
) -> DocumentListResponse:
    return list_documents_response(
        repository=repository,
        team_id=team_id,
        keyword=keyword,
        tags=parse_tags(tags),
        status=status,
        page=page,
        page_size=page_size,
    )


@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document(
    document_id: str,
    repository: SQLiteDocumentRepository = Depends(get_repository),
) -> DeleteResponse:
    return delete_document_record(document_id, repository)
