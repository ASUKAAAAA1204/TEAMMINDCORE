from __future__ import annotations

from typing import Any, cast

from app.domain.types import DocumentRecord
from app.repositories.document_repository import SQLiteDocumentRepository
from app.services.analysis_service import AnalysisService


class FakeRepository:
    def __init__(self, documents: list[DocumentRecord]) -> None:
        self.documents = {document.id: document for document in documents}

    def get_documents(self, document_ids: list[str]) -> list[DocumentRecord]:
        return [self.documents[document_id] for document_id in document_ids if document_id in self.documents]


class FakeGenerationClient:
    def __init__(self, payload: dict[str, object] | None = None, should_fail: bool = False) -> None:
        self.payload = payload or {}
        self.should_fail = should_fail

    def generate_json(self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> dict[str, object]:
        assert "grounded data analysis assistant" in system_prompt
        assert "sales trends" in user_prompt
        if self.should_fail:
            raise RuntimeError("ollama unavailable")
        return self.payload


def _document() -> DocumentRecord:
    return DocumentRecord(
        id="doc_001",
        team_id="default",
        filename="sales.txt",
        stored_path="data/uploads/doc_001/sales.txt",
        parse_status="parsed",
        upload_time="2026-03-28T00:00:00Z",
        tags=["sales"],
        metadata={"parser_name": "local-text-parser"},
        extracted_text="Alice 2025 Q1 sales 500 625 750 900",
    )


def test_analysis_service_prefers_ollama_when_available() -> None:
    repository = FakeRepository([_document()])
    service = AnalysisService(
        cast(SQLiteDocumentRepository, repository),
        FakeGenerationClient(
            payload={
                "summary": "2025 年销售额持续增长，后两季增幅更高。",
                "chart_description": "折线图会显示从 500 到 900 的稳定上升。",
            }
        ),
    )

    result = service.execute(
        task="Analyze Alice sales trends",
        document_ids=["doc_001"],
        output_format="json",
        analysis_focus="sales trends",
    )

    assert result["results"]["summary"] == "2025 年销售额持续增长，后两季增幅更高。"
    assert result["results"]["chart_description"] == "折线图会显示从 500 到 900 的稳定上升。"
    assert result["results"]["statistics"]["total_sales"] == 4801.0


def test_analysis_service_falls_back_when_ollama_fails() -> None:
    repository = FakeRepository([_document()])
    service = AnalysisService(cast(SQLiteDocumentRepository, repository), FakeGenerationClient(should_fail=True))

    result = service.execute(
        task="Analyze Alice sales trends",
        document_ids=["doc_001"],
        output_format="json",
        analysis_focus="sales trends",
    )

    assert str(result["results"]["summary"]).startswith("Read 1 documents")
    assert str(result["results"]["chart_description"]).startswith("A line chart")
