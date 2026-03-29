from __future__ import annotations

import logging
from typing import Any

from app.services.llamaindex_retriever import KeywordSearchBackend
from app.services.vector_store import VectorStore


logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(
        self,
        vector_store: VectorStore,
        keyword_retriever: KeywordSearchBackend | None = None,
    ) -> None:
        self.vector_store = vector_store
        self.keyword_retriever = keyword_retriever

    def search(
        self,
        query: str,
        top_k: int = 8,
        hybrid_alpha: float = 0.7,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        filters = filters or {}
        if self.keyword_retriever is None:
            results = self.vector_store.search(
                query=query,
                top_k=top_k,
                hybrid_alpha=hybrid_alpha,
                filters=filters,
            )
        else:
            try:
                results = self._search_with_llamaindex_hybrid(
                    query=query,
                    top_k=top_k,
                    hybrid_alpha=hybrid_alpha,
                    filters=filters,
                )
            except Exception as exc:
                logger.warning("LlamaIndex retrieval failed, falling back to vector store: %s", exc)
                results = self.vector_store.search(
                    query=query,
                    top_k=top_k,
                    hybrid_alpha=hybrid_alpha,
                    filters=filters,
                )
        return {
            "results": results,
            "total_found": len(results),
        }

    def _search_with_llamaindex_hybrid(
        self,
        query: str,
        top_k: int,
        hybrid_alpha: float,
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        keyword_retriever = self.keyword_retriever
        if keyword_retriever is None:
            return self.vector_store.search(query, top_k, hybrid_alpha, filters)
        candidate_top_k = max(top_k * 4, 10)
        semantic_results = self.vector_store.search(
            query=query,
            top_k=candidate_top_k,
            hybrid_alpha=1.0,
            filters=filters,
        )
        keyword_results = keyword_retriever.search(
            query=query,
            top_k=candidate_top_k,
            filters=filters,
        )
        if not semantic_results and not keyword_results:
            return []
        return self._fuse_results(semantic_results, keyword_results, hybrid_alpha, top_k)

    def _fuse_results(
        self,
        semantic_results: list[dict[str, Any]],
        keyword_results: list[dict[str, Any]],
        hybrid_alpha: float,
        top_k: int,
    ) -> list[dict[str, Any]]:
        normalized_semantic = self._normalize_scores(semantic_results)
        normalized_keyword = self._normalize_scores(keyword_results)
        merged: dict[tuple[str, str], dict[str, Any]] = {}

        for item in normalized_semantic:
            key = self._result_key(item)
            merged[key] = {
                "text": item["text"],
                "document_id": item["document_id"],
                "metadata": item.get("metadata", {}),
                "semantic_score": item["score"],
                "keyword_score": None,
            }

        for item in normalized_keyword:
            key = self._result_key(item)
            row = merged.setdefault(
                key,
                {
                    "text": item["text"],
                    "document_id": item["document_id"],
                    "metadata": item.get("metadata", {}),
                    "semantic_score": None,
                    "keyword_score": None,
                },
            )
            row["keyword_score"] = item["score"]
            if not row["metadata"] and item.get("metadata"):
                row["metadata"] = item["metadata"]

        fused_results: list[dict[str, Any]] = []
        for row in merged.values():
            semantic_score = row["semantic_score"]
            keyword_score = row["keyword_score"]
            if isinstance(semantic_score, (int, float)) and isinstance(keyword_score, (int, float)):
                score = hybrid_alpha * float(semantic_score) + (1 - hybrid_alpha) * float(keyword_score)
            elif isinstance(semantic_score, (int, float)):
                score = float(semantic_score)
            elif isinstance(keyword_score, (int, float)):
                score = float(keyword_score)
            else:
                score = 0.0
            if score <= 0:
                continue
            fused_results.append(
                {
                    "text": row["text"],
                    "score": round(score, 4),
                    "document_id": row["document_id"],
                    "metadata": row["metadata"],
                }
            )

        return sorted(fused_results, key=lambda item: item["score"], reverse=True)[:top_k]

    def _normalize_scores(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        max_score = max(
            (
                float(item["score"])
                for item in results
                if isinstance(item.get("score"), (int, float)) and float(item["score"]) > 0
            ),
            default=0.0,
        )
        if max_score <= 0:
            return []
        normalized: list[dict[str, Any]] = []
        for item in results:
            raw_score = item.get("score")
            if not isinstance(raw_score, (int, float)) or float(raw_score) <= 0:
                continue
            normalized.append(
                {
                    **item,
                    "score": float(raw_score) / max_score,
                }
            )
        return normalized

    def _result_key(self, item: dict[str, Any]) -> tuple[str, str]:
        return (str(item.get("document_id", "")), str(item.get("text", "")))
