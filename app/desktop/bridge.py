from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.errors import AppError
from app.modules.analysis.schemas import AnalysisRequest, AnalysisResponse
from app.modules.ingestion.operations import (
    build_upload_response,
    delete_document_record,
    enqueue_upload,
    list_documents_response,
)
from app.modules.installer.schemas import (
    InstallRequest,
    InstallResponse,
    InstallerSearchRequest,
    InstallerSearchResponse,
)
from app.modules.integration.schemas import MergeRequest, MergeResponse
from app.modules.orchestrator.schemas import OrchestratorResponse, OrchestratorRunRequest
from app.modules.report.schemas import ReportRequest, ReportResponse
from app.modules.retrieval.schemas import SearchRequest, SearchResponse
from app.runtime import RuntimeContext, build_health_payload, build_tools_payload


@dataclass(slots=True)
class DesktopUploadFile:
    name: str
    content_base64: str


class DesktopBridge:
    __slots__ = ("_runtime",)

    def __init__(self, runtime: RuntimeContext) -> None:
        self._runtime = runtime

    def fetch_health(self) -> dict[str, object]:
        return build_health_payload(self._runtime)

    def fetch_tools(self) -> dict[str, object]:
        return build_tools_payload(self._runtime.repository)

    def fetch_documents(self, payload: dict[str, Any] | None = None) -> dict[str, object]:
        query = payload or {}
        response = list_documents_response(
            repository=self._runtime.repository,
            team_id=_nullable_string(query.get("team_id")),
            keyword=_nullable_string(query.get("keyword")),
            tags=_ensure_string_list(query.get("tags")),
            status=_nullable_string(query.get("status")),
            page=_coerce_int(query.get("page"), 1, field_name="page", minimum=1),
            page_size=_coerce_int(query.get("page_size"), 100, field_name="page_size", minimum=1, maximum=500),
        )
        return response.model_dump()

    def upload_documents(self, payload: dict[str, Any]) -> dict[str, object]:
        files = [_parse_upload_file(item) for item in payload.get("files", [])]
        if not files:
            raise AppError("ERR_001", "Document parsing failed", "at least one file is required", 400)
        team_id = _nullable_string(payload.get("team_id")) or "default"
        parse_mode = _nullable_string(payload.get("parse_mode")) or "auto"
        tags = _ensure_string_list(payload.get("tags"))
        document_ids = [
            enqueue_upload(
                filename=item.name,
                file_bytes=_decode_upload_content(item.content_base64),
                team_id=team_id,
                parse_mode=parse_mode,
                tags=tags,
                uploads_dir=self._runtime.settings.uploads_dir,
                repository=self._runtime.repository,
                container=self._runtime.container,
            )
            for item in files
        ]
        return build_upload_response(document_ids).model_dump()

    def delete_document(self, document_id: str) -> dict[str, object]:
        return delete_document_record(document_id, self._runtime.repository).model_dump()

    def run_retrieval(self, payload: dict[str, Any]) -> dict[str, object]:
        request = SearchRequest.model_validate(payload)
        result = self._runtime.container.retrieval.search(
            query=request.query,
            top_k=request.top_k,
            hybrid_alpha=request.hybrid_alpha,
            filters=request.filters.model_dump(),
        )
        return SearchResponse(**result).model_dump()

    def generate_report(self, payload: dict[str, Any]) -> dict[str, object]:
        request = ReportRequest.model_validate(payload)
        result = self._runtime.container.report.generate(
            entity=request.entity,
            report_type=request.report_type,
            include_sources=request.include_sources,
            max_sections=request.max_sections,
        )
        return ReportResponse(**result).model_dump()

    def execute_analysis(self, payload: dict[str, Any]) -> dict[str, object]:
        request = AnalysisRequest.model_validate(payload)
        result = self._runtime.container.analysis.execute(
            task=request.task,
            document_ids=request.document_ids,
            output_format=request.output_format,
        )
        return AnalysisResponse(**result).model_dump()

    def merge_documents(self, payload: dict[str, Any]) -> dict[str, object]:
        request = MergeRequest.model_validate(payload)
        result = self._runtime.container.merge.merge(
            document_ids=request.document_ids,
            rule=request.rule.model_dump(),
        )
        return MergeResponse(**result).model_dump()

    def search_repositories(self, payload: dict[str, Any]) -> dict[str, object]:
        request = InstallerSearchRequest.model_validate(payload)
        result = self._runtime.container.github.search_repositories(request.query)
        return InstallerSearchResponse(**result).model_dump()

    def install_repository(self, payload: dict[str, Any]) -> dict[str, object]:
        request = InstallRequest.model_validate(payload)
        result = self._runtime.container.installer.install(repo_url=request.repo_url, confirm=request.confirm)
        return InstallResponse(**result).model_dump()

    def run_orchestrator(self, payload: dict[str, Any]) -> dict[str, object]:
        request = OrchestratorRunRequest.model_validate(payload)
        result = self._runtime.container.orchestrator.run(
            task=request.task,
            main_agent=request.main_agent,
            parameters=request.parameters.model_dump(),
        )
        return OrchestratorResponse(**result).model_dump()

    def stream_orchestrator(self, payload: dict[str, Any]) -> dict[str, object]:
        request = OrchestratorRunRequest.model_validate(payload)
        events = []
        for chunk in self._runtime.container.orchestrator.stream(
            task=request.task,
            main_agent=request.main_agent,
            parameters=request.parameters.model_dump(),
        ):
            event = _parse_sse_chunk(chunk)
            if event is not None:
                events.append(event)
        return {"events": events}

    def reveal_data_directory(self) -> str:
        return str(self._runtime.settings.data_dir)


def _parse_upload_file(payload: dict[str, Any]) -> DesktopUploadFile:
    name = _nullable_string(payload.get("name"))
    content_base64 = _nullable_string(payload.get("content_base64"))
    if not name or not content_base64:
        raise AppError("ERR_001", "Document parsing failed", "desktop upload payload is incomplete", 400)
    return DesktopUploadFile(name=name, content_base64=content_base64)


def _nullable_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _decode_upload_content(content_base64: str) -> bytes:
    try:
        return base64.b64decode(content_base64.encode("utf-8"), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AppError(
            "ERR_VALIDATION",
            "Request validation failed",
            "file content_base64 must be valid base64",
            422,
        ) from exc


def _ensure_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raise AppError("ERR_VALIDATION", "Request validation failed", "expected a list of strings", 422)


def _coerce_int(
    value: Any,
    fallback: int,
    *,
    field_name: str,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    if value is None or value == "":
        return fallback
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise AppError(
            "ERR_VALIDATION",
            "Request validation failed",
            f"{field_name} must be an integer",
            422,
        ) from exc
    if minimum is not None and parsed < minimum:
        raise AppError(
            "ERR_VALIDATION",
            "Request validation failed",
            f"{field_name} must be greater than or equal to {minimum}",
            422,
        )
    if maximum is not None and parsed > maximum:
        raise AppError(
            "ERR_VALIDATION",
            "Request validation failed",
            f"{field_name} must be less than or equal to {maximum}",
            422,
        )
    return parsed


def _parse_sse_chunk(chunk: str) -> dict[str, Any] | None:
    event_name = "message"
    data: dict[str, Any] | None = None
    for raw_line in chunk.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            try:
                data = json.loads(line.split(":", 1)[1].strip())
            except json.JSONDecodeError as exc:
                raise AppError(
                    "ERR_DESKTOP",
                    "Desktop orchestrator stream failed",
                    f"received invalid JSON event payload for '{event_name}'",
                    500,
                ) from exc
    if data is None:
        return None
    return {"event": event_name, "data": data}
