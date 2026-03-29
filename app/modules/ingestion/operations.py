from __future__ import annotations

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from fastapi import BackgroundTasks, UploadFile

from app.core.container import ServiceContainer
from app.core.errors import AppError
from app.domain.types import DocumentRecord
from app.modules.ingestion.schemas import DeleteResponse, DocumentListResponse, DocumentSummary, UploadResponse
from app.repositories.document_repository import SQLiteDocumentRepository


_UPLOAD_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="tmh-upload")


def parse_tags(raw_tags: str | None) -> list[str]:
    if not raw_tags:
        return []
    if raw_tags.startswith("["):
        return [str(item).strip() for item in json.loads(raw_tags) if str(item).strip()]
    return [item.strip() for item in raw_tags.split(",") if item.strip()]


def store_upload_bytes(content: bytes, stored_path: Path) -> None:
    stored_path.parent.mkdir(parents=True, exist_ok=True)
    stored_path.write_bytes(content)


def store_upload_file(upload: UploadFile, stored_path: Path) -> None:
    store_upload_bytes(upload.file.read(), stored_path)


def enqueue_upload(
    *,
    filename: str,
    file_bytes: bytes,
    team_id: str,
    parse_mode: str,
    tags: list[str],
    uploads_dir: Path,
    repository: SQLiteDocumentRepository,
    container: ServiceContainer,
    background_tasks: BackgroundTasks | None = None,
) -> str:
    if parse_mode not in {"auto", "deep", "fast"}:
        raise AppError("ERR_001", "Document parsing failed", "parse_mode must be auto, deep, or fast", 400)
    document_id = f"doc_{uuid.uuid4().hex[:8]}"
    stored_path = uploads_dir / team_id / document_id / filename
    store_upload_bytes(file_bytes, stored_path)
    repository.save_document(
        DocumentRecord(
            id=document_id,
            team_id=team_id,
            filename=filename,
            stored_path=str(stored_path),
            parse_status="uploaded",
            upload_time=datetime.now(timezone.utc).isoformat(),
            tags=tags,
            metadata={},
            extracted_text="",
        )
    )
    processor_args = (document_id, stored_path, filename, parse_mode, repository, container)
    if background_tasks is not None:
        background_tasks.add_task(process_document, *processor_args)
    else:
        _UPLOAD_EXECUTOR.submit(process_document, *processor_args)
    return document_id


def build_upload_response(document_ids: list[str]) -> UploadResponse:
    return UploadResponse(
        document_ids=document_ids,
        status="processing",
        progress=0.1,
        message=f"Started parsing {len(document_ids)} file(s)",
    )


def list_documents_response(
    *,
    repository: SQLiteDocumentRepository,
    team_id: str | None = None,
    keyword: str | None = None,
    tags: list[str] | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> DocumentListResponse:
    documents = repository.list_documents(
        team_id=team_id,
        keyword=keyword,
        tags=tags or [],
        status=status,
    )
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    items = [
        DocumentSummary(
            id=item.id,
            filename=item.filename,
            upload_time=item.upload_time,
            parse_status=item.parse_status,
            metadata=item.metadata,
            tags=item.tags,
        )
        for item in documents[start:end]
    ]
    return DocumentListResponse(total=len(documents), page=page, page_size=page_size, documents=items)


def delete_document_record(
    document_id: str,
    repository: SQLiteDocumentRepository,
) -> DeleteResponse:
    record = repository.delete_document(document_id)
    if record is None:
        raise AppError("ERR_001", "Document parsing failed", "Document not found", 404)
    stored_path = Path(record.stored_path)
    if stored_path.exists():
        stored_path.unlink()
        parent = stored_path.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
    return DeleteResponse(success=True, message="Document deleted")


def process_document(
    document_id: str,
    stored_path: Path,
    filename: str,
    parse_mode: str,
    repository: SQLiteDocumentRepository,
    container: ServiceContainer,
) -> None:
    parsed = container.parser.parse(stored_path, filename, parse_mode)
    repository.update_document_processing(
        document_id=document_id,
        parse_status="parsed",
        metadata={**parsed.metadata, "parser_name": parsed.parser_name},
        extracted_text=parsed.text,
    )
    record = repository.get_document(document_id)
    if record is not None:
        container.vector_store.index_document(record)
