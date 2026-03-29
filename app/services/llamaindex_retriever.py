from __future__ import annotations

import importlib
from typing import Any, Protocol

from app.domain.types import DocumentRecord
from app.repositories.document_repository import SQLiteDocumentRepository


class KeywordSearchBackend(Protocol):
    def search(
        self,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        ...


class LlamaIndexKeywordRetriever:
    def __init__(self, repository: SQLiteDocumentRepository) -> None:
        self.repository = repository

    def search(
        self,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        documents = self._list_filtered_documents(filters)
        if not documents:
            return []

        document_ids = [document.id for document in documents]
        chunks = self.repository.list_chunks(document_ids)
        if not chunks:
            return []

        bm25_cls = self._load_symbol("llama_index.retrievers.bm25", "BM25Retriever")
        text_node_cls = self._load_symbol("llama_index.core.schema", "TextNode")
        nodes = [
            text_node_cls(
                text=chunk.text,
                id_=chunk.id,
                metadata={
                    "document_id": chunk.document_id,
                    **chunk.metadata,
                },
            )
            for chunk in chunks
        ]
        retriever = bm25_cls.from_defaults(nodes=nodes, similarity_top_k=top_k)
        retrieved_nodes = retriever.retrieve(query)

        results: list[dict[str, Any]] = []
        for item in retrieved_nodes:
            node = getattr(item, "node", None)
            if node is None:
                continue
            text = self._extract_node_text(node)
            if not text:
                continue
            metadata = getattr(node, "metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            score = getattr(item, "score", 0.0)
            if not isinstance(score, (int, float)):
                score = 0.0
            results.append(
                {
                    "text": text,
                    "score": float(score),
                    "document_id": str(metadata.get("document_id", "")),
                    "metadata": _public_metadata(metadata),
                }
            )
        return results

    def _list_filtered_documents(self, filters: dict[str, Any]) -> list[DocumentRecord]:
        tags = [tag for tag in filters.get("tags", []) if isinstance(tag, str)]
        documents = self.repository.list_documents(team_id=None, tags=tags)
        date_after = filters.get("date_after")
        if not isinstance(date_after, str) or not date_after:
            return documents
        return [
            document
            for document in documents
            if document.upload_time[:10] >= date_after
        ]

    def _load_symbol(self, module_name: str, symbol_name: str) -> Any:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            raise RuntimeError(f"Failed to import {module_name}: {exc}") from exc
        try:
            return getattr(module, symbol_name)
        except AttributeError as exc:
            raise RuntimeError(f"Missing {symbol_name} in {module_name}") from exc

    def _extract_node_text(self, node: Any) -> str:
        raw_text = getattr(node, "text", None)
        if isinstance(raw_text, str) and raw_text.strip():
            return raw_text.strip()
        get_content = getattr(node, "get_content", None)
        if callable(get_content):
            content = get_content()
            if isinstance(content, str):
                return content.strip()
        return ""


def _public_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        key: metadata[key]
        for key in ("source_page", "filename", "team_id")
        if key in metadata
    }
