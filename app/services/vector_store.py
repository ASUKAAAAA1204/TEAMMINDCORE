from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.domain.types import ChunkRecord, DocumentRecord
from app.repositories.document_repository import SQLiteDocumentRepository
from app.services.embedding import DeterministicEmbeddingService


logger = logging.getLogger(__name__)


class VectorStore(Protocol):
    def index_document(self, document: DocumentRecord) -> list[ChunkRecord]:
        ...

    def search(
        self,
        query: str,
        top_k: int,
        hybrid_alpha: float,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        ...


class ChromaClient(Protocol):
    def heartbeat(self) -> bool:
        ...

    def get_or_create_collection(self) -> ChromaCollection:
        ...

    def upsert(self, collection_id: str, chunks: list[ChunkRecord]) -> None:
        ...

    def query(
        self,
        collection_id: str,
        query_embedding: list[float],
        n_results: int,
    ) -> dict[str, Any]:
        ...


@dataclass(slots=True)
class ChromaCollection:
    id: str
    name: str


class ChromaHttpClient:
    def __init__(
        self,
        base_url: str,
        tenant: str,
        database: str,
        collection_name: str,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.base_url = self._normalize_base_url(base_url)
        self.tenant = tenant
        self.database = database
        self.collection_name = collection_name
        self.timeout_seconds = timeout_seconds

    def heartbeat(self) -> bool:
        try:
            self._request("get", "/heartbeat")
            return True
        except Exception:
            return False

    def get_or_create_collection(self) -> ChromaCollection:
        payload = self._request_json(
            "post",
            f"/tenants/{self.tenant}/databases/{self.database}/collections",
            json={
                "name": self.collection_name,
                "metadata": {"source": "teammindhub"},
                "get_or_create": True,
            },
        )
        return ChromaCollection(id=str(payload["id"]), name=str(payload["name"]))

    def upsert(self, collection_id: str, chunks: list[ChunkRecord]) -> None:
        self._request(
            "post",
            f"/tenants/{self.tenant}/databases/{self.database}/collections/{collection_id}/upsert",
            json={
                "ids": [chunk.id for chunk in chunks],
                "embeddings": [chunk.vector for chunk in chunks],
                "metadatas": [chunk.metadata for chunk in chunks],
                "documents": [chunk.text for chunk in chunks],
            },
        )

    def query(
        self,
        collection_id: str,
        query_embedding: list[float],
        n_results: int,
    ) -> dict[str, Any]:
        return self._request_json(
            "post",
            f"/tenants/{self.tenant}/databases/{self.database}/collections/{collection_id}/query",
            json={
                "query_embeddings": [query_embedding],
                "n_results": n_results,
                "include": ["metadatas", "documents", "distances"],
            },
        )

    def _request_json(self, method: str, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self._request(method, path, json=json)
        return response.json()

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        with httpx.Client(base_url=self.base_url, timeout=self.timeout_seconds) as client:
            response = client.request(method=method, url=path, json=json)
            response.raise_for_status()
            return response

    def _normalize_base_url(self, base_url: str) -> str:
        normalized = base_url.strip().rstrip("/")
        if not normalized.startswith(("http://", "https://")):
            normalized = f"http://{normalized}"
        if not normalized.endswith("/api/v2"):
            normalized = f"{normalized}/api/v2"
        return normalized


class LocalVectorStore:
    def __init__(
        self,
        repository: SQLiteDocumentRepository,
        embedding_service: DeterministicEmbeddingService,
    ) -> None:
        self.repository = repository
        self.embedding_service = embedding_service

    def index_document(self, document: DocumentRecord) -> list[ChunkRecord]:
        chunks = []
        for index, chunk_text in enumerate(self._chunk_text(document.extracted_text)):
            chunks.append(
                ChunkRecord(
                    id=_stable_chunk_id(document.id, index),
                    document_id=document.id,
                    chunk_index=index,
                    text=chunk_text,
                    vector=self.embedding_service.embed_text(chunk_text),
                    metadata=_build_chunk_metadata(document, index),
                )
            )
        self.repository.replace_chunks(document.id, chunks)
        return chunks

    def search(
        self,
        query: str,
        top_k: int,
        hybrid_alpha: float,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        tags = filters.get("tags", [])
        document_map = {
            document.id: document
            for document in self.repository.list_documents(team_id=None, tags=tags)
        }
        chunks = [
            chunk
            for chunk in self.repository.list_chunks()
            if chunk.document_id in document_map
            and self._matches_date_filter(document_map[chunk.document_id], filters)
        ]
        query_vector = self.embedding_service.embed_text(query)
        results = []
        for chunk in chunks:
            semantic = self.embedding_service.cosine_similarity(query_vector, chunk.vector)
            keyword = self.embedding_service.keyword_overlap(query, chunk.text)
            score = max(0.0, min(1.0, hybrid_alpha * semantic + (1 - hybrid_alpha) * keyword))
            if score == 0:
                continue
            results.append(
                {
                    "text": chunk.text,
                    "score": round(score, 4),
                    "document_id": chunk.document_id,
                    "metadata": _public_metadata(chunk.metadata),
                }
            )
        return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]

    def _chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
        stripped = text.strip()
        if not stripped:
            return ["empty document placeholder"]
        if len(stripped) <= chunk_size:
            return [stripped]
        chunks: list[str] = []
        start = 0
        while start < len(stripped):
            end = min(len(stripped), start + chunk_size)
            chunks.append(stripped[start:end])
            if end == len(stripped):
                break
            start = max(0, end - overlap)
        return chunks

    def _matches_date_filter(self, document: DocumentRecord, filters: dict[str, Any]) -> bool:
        date_after = filters.get("date_after")
        if not date_after:
            return True
        return document.upload_time[:10] >= date_after


class ChromaBackedVectorStore:
    def __init__(
        self,
        local_store: LocalVectorStore,
        embedding_service: DeterministicEmbeddingService,
        chroma_client: ChromaClient,
    ) -> None:
        self.local_store = local_store
        self.embedding_service = embedding_service
        self.chroma_client = chroma_client
        self._collection: ChromaCollection | None = None

    def index_document(self, document: DocumentRecord) -> list[ChunkRecord]:
        chunks = self.local_store.index_document(document)
        if not chunks or not self._ensure_collection():
            return chunks
        collection = self._collection
        if collection is None:
            return chunks
        try:
            self.chroma_client.upsert(collection.id, chunks)
        except Exception as exc:
            self._collection = None
            logger.warning("Chroma upsert failed, local index retained: %s", exc)
        return chunks

    def search(
        self,
        query: str,
        top_k: int,
        hybrid_alpha: float,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        if not self._ensure_collection():
            return self.local_store.search(query, top_k, hybrid_alpha, filters)
        collection = self._collection
        if collection is None:
            return self.local_store.search(query, top_k, hybrid_alpha, filters)
        try:
            payload = self.chroma_client.query(
                collection_id=collection.id,
                query_embedding=self.embedding_service.embed_text(query),
                n_results=max(top_k * 5, 10),
            )
            results = self._build_results_from_query(payload, query, hybrid_alpha, filters)
            if results:
                return results[:top_k]
        except Exception as exc:
            self._collection = None
            logger.warning("Chroma query failed, falling back to local search: %s", exc)
        return self.local_store.search(query, top_k, hybrid_alpha, filters)

    def _ensure_collection(self) -> bool:
        if self._collection is not None:
            return True
        if not self.chroma_client.heartbeat():
            return False
        try:
            self._collection = self.chroma_client.get_or_create_collection()
            return True
        except Exception as exc:
            logger.warning("Chroma collection bootstrap failed: %s", exc)
            self._collection = None
            return False

    def _build_results_from_query(
        self,
        payload: dict[str, Any],
        query: str,
        hybrid_alpha: float,
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        documents = _first_result_batch(payload.get("documents"))
        metadatas = _first_result_batch(payload.get("metadatas"))
        distances = _first_result_batch(payload.get("distances"))
        results: list[dict[str, Any]] = []
        for index, text in enumerate(documents):
            if not isinstance(text, str):
                continue
            metadata = metadatas[index] if index < len(metadatas) and isinstance(metadatas[index], dict) else {}
            if not _matches_metadata_filters(metadata, filters):
                continue
            semantic = _distance_to_score(distances[index] if index < len(distances) else None)
            keyword = self.embedding_service.keyword_overlap(query, text)
            score = max(0.0, min(1.0, hybrid_alpha * semantic + (1 - hybrid_alpha) * keyword))
            if score == 0:
                continue
            results.append(
                {
                    "text": text,
                    "score": round(score, 4),
                    "document_id": str(metadata.get("document_id", "")),
                    "metadata": _public_metadata(metadata),
                }
            )
        return sorted(results, key=lambda item: item["score"], reverse=True)


def _stable_chunk_id(document_id: str, chunk_index: int) -> str:
    seed = f"{document_id}:{chunk_index}".encode("utf-8")
    return f"chunk_{hashlib.blake2b(seed, digest_size=8).hexdigest()}"


def _build_chunk_metadata(document: DocumentRecord, chunk_index: int) -> dict[str, Any]:
    return {
        "document_id": document.id,
        "source_page": chunk_index + 1,
        "filename": document.filename,
        "team_id": document.team_id,
        "upload_date": document.upload_time[:10],
        "tags_json": json.dumps(document.tags, ensure_ascii=False),
    }


def _public_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        key: metadata[key]
        for key in ("source_page", "filename", "team_id")
        if key in metadata
    }


def _matches_metadata_filters(metadata: dict[str, Any], filters: dict[str, Any]) -> bool:
    requested_tags = [tag for tag in filters.get("tags", []) if isinstance(tag, str)]
    if requested_tags:
        serialized_tags = str(metadata.get("tags_json", "[]"))
        try:
            indexed_tags = json.loads(serialized_tags)
        except json.JSONDecodeError:
            indexed_tags = []
        if not all(tag in indexed_tags for tag in requested_tags):
            return False
    date_after = filters.get("date_after")
    if isinstance(date_after, str):
        upload_date = str(metadata.get("upload_date", ""))
        if upload_date and upload_date < date_after:
            return False
    return True


def _distance_to_score(distance: Any) -> float:
    if not isinstance(distance, (int, float)):
        return 0.0
    return 1.0 / (1.0 + max(float(distance), 0.0))


def _first_result_batch(payload: Any) -> list[Any]:
    if isinstance(payload, list) and payload:
        first = payload[0]
        if isinstance(first, list):
            return first
    return []
