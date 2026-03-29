from __future__ import annotations

from typing import Any

from app.services.retrieval_service import RetrievalService


class FakeVectorStore:
    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results
        self.calls: list[dict[str, Any]] = []

    def index_document(self, document: Any) -> list[Any]:
        raise NotImplementedError

    def search(
        self,
        query: str,
        top_k: int,
        hybrid_alpha: float,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append(
            {
                "query": query,
                "top_k": top_k,
                "hybrid_alpha": hybrid_alpha,
                "filters": filters or {},
            }
        )
        return self.results


class FakeKeywordRetriever:
    def __init__(self, results: list[dict[str, Any]], should_fail: bool = False) -> None:
        self.results = results
        self.should_fail = should_fail
        self.calls: list[dict[str, Any]] = []

    def search(
        self,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append(
            {
                "query": query,
                "top_k": top_k,
                "filters": filters or {},
            }
        )
        if self.should_fail:
            raise RuntimeError("llamaindex unavailable")
        return self.results


def test_retrieval_service_fuses_vector_and_llamaindex_results() -> None:
    vector_store = FakeVectorStore(
        [
            {
                "text": "Alice revenue climbed to 900 in Q4",
                "score": 0.9,
                "document_id": "doc-1",
                "metadata": {"filename": "sales.txt"},
            },
            {
                "text": "Bob revenue remained flat",
                "score": 0.3,
                "document_id": "doc-2",
                "metadata": {"filename": "sales.txt"},
            },
        ]
    )
    keyword_retriever = FakeKeywordRetriever(
        [
            {
                "text": "Alice revenue climbed to 900 in Q4",
                "score": 12.0,
                "document_id": "doc-1",
                "metadata": {"filename": "sales.txt"},
            },
            {
                "text": "Alice pipeline expansion in APAC",
                "score": 6.0,
                "document_id": "doc-3",
                "metadata": {"filename": "sales.txt"},
            },
        ]
    )
    service = RetrievalService(vector_store, keyword_retriever)

    result = service.search(query="Alice revenue", top_k=3, hybrid_alpha=0.7, filters={"tags": ["sales"]})

    assert vector_store.calls[0]["hybrid_alpha"] == 1.0
    assert vector_store.calls[0]["top_k"] == 12
    assert keyword_retriever.calls[0]["top_k"] == 12
    assert result["total_found"] == 3
    assert result["results"][0]["document_id"] == "doc-1"
    assert result["results"][1]["document_id"] == "doc-3"
    assert result["results"][2]["document_id"] == "doc-2"


def test_retrieval_service_falls_back_when_llamaindex_errors() -> None:
    vector_store = FakeVectorStore(
        [
            {
                "text": "Alice revenue climbed to 900 in Q4",
                "score": 0.82,
                "document_id": "doc-1",
                "metadata": {"filename": "sales.txt"},
            }
        ]
    )
    keyword_retriever = FakeKeywordRetriever([], should_fail=True)
    service = RetrievalService(vector_store, keyword_retriever)

    result = service.search(query="Alice revenue", top_k=5, hybrid_alpha=0.6, filters={"tags": ["sales"]})

    assert vector_store.calls[-1]["hybrid_alpha"] == 0.6
    assert vector_store.calls[-1]["top_k"] == 5
    assert result["total_found"] == 1
    assert result["results"][0]["document_id"] == "doc-1"
