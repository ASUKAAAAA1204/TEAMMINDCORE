from __future__ import annotations

from typing import Any, cast

from app.services.report_service import ReportService


class FakeRetrievalService:
    def __init__(self, results):
        self.results = results

    def search(
        self,
        query: str,
        top_k: int = 8,
        hybrid_alpha: float = 0.7,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, object]:
        return {"results": self.results[:top_k]}


class FakeGenerationClient:
    def __init__(self, payload=None, should_fail: bool = False) -> None:
        self.payload = payload or {}
        self.should_fail = should_fail

    def generate_json(self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> dict[str, object]:
        assert "grounded report generator" in system_prompt
        assert "Alice" in user_prompt
        properties = schema.get("properties")
        assert isinstance(properties, dict)
        assert "sections" in properties
        if self.should_fail:
            raise RuntimeError("ollama unavailable")
        return self.payload


def test_report_service_prefers_ollama_when_available() -> None:
    retrieval = FakeRetrievalService(
        [
            {
                "text": "Alice led the North America sales program and improved win rate.",
                "document_id": "doc_001",
                "metadata": {"filename": "sales.txt"},
            },
            {
                "text": "Alice closed enterprise renewals and expanded revenue in Q2.",
                "document_id": "doc_002",
                "metadata": {"filename": "renewals.txt"},
            },
        ]
    )
    generation_client = FakeGenerationClient(
        payload={
            "title": "Alice strategic profile",
            "overall_summary": "Alice is the primary sales lead across multiple initiatives.",
            "sections": [
                {
                    "section": "Overview",
                    "content": "Alice owns strategic sales execution.",
                    "sources": ["doc_001"],
                },
                {
                    "section": "Project and data evidence",
                    "content": "She expanded renewals and win rate.",
                    "sources": ["doc_002", "doc_999"],
                },
                {
                    "section": "Key observations",
                    "content": "Execution quality is consistently high.",
                    "sources": [],
                },
            ],
        }
    )

    service = ReportService(retrieval, generation_client)

    result = cast(
        dict[str, Any],
        service.generate(
            entity="Alice",
            report_type="person_profile",
            include_sources=True,
            max_sections=3,
        ),
    )
    sections = cast(list[dict[str, Any]], result["sections"])

    assert result["title"] == "Alice strategic profile"
    assert str(result["overall_summary"]).startswith("Alice is the primary sales lead")
    assert sections[0]["content"] == "Alice owns strategic sales execution."
    assert sections[1]["sources"] == ["doc_002"]
    assert sections[2]["sources"] == ["doc_001"]
    assert result["sources_count"] == 2


def test_report_service_falls_back_when_ollama_fails() -> None:
    retrieval = FakeRetrievalService(
        [
            {
                "text": "Alice led the North America sales program and improved win rate.",
                "document_id": "doc_001",
                "metadata": {"filename": "sales.txt"},
            }
        ]
    )
    service = ReportService(retrieval, FakeGenerationClient(should_fail=True))

    result = cast(
        dict[str, Any],
        service.generate(
            entity="Alice",
            report_type="person_profile",
            include_sources=True,
            max_sections=3,
        ),
    )
    sections = cast(list[dict[str, Any]], result["sections"])

    assert str(result["title"]).startswith("Alice")
    assert str(sections[0]["content"]).startswith("Alice led the North America sales program")
    assert sections[0]["sources"] == ["doc_001"]
