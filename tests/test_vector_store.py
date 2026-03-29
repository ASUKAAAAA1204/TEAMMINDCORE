from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from app.domain.types import DocumentRecord
from app.repositories.document_repository import SQLiteDocumentRepository
from app.services.embedding import DeterministicEmbeddingService
from app.services.vector_store import ChromaBackedVectorStore, ChromaCollection, LocalVectorStore


class FakeChromaClient:
    def __init__(self, available: bool = True) -> None:
        self.available = available
        self.collection = ChromaCollection(id="collection-1", name="teammindhub_chunks")
        self.upsert_calls = 0
        self._chunks = []

    def heartbeat(self) -> bool:
        return self.available

    def get_or_create_collection(self) -> ChromaCollection:
        return self.collection

    def upsert(self, collection_id: str, chunks) -> None:
        assert collection_id == self.collection.id
        self.upsert_calls += 1
        self._chunks = list(chunks)

    def query(self, collection_id: str, query_embedding: list[float], n_results: int) -> dict:
        assert collection_id == self.collection.id
        documents = [chunk.text for chunk in self._chunks][:n_results]
        metadatas = [chunk.metadata for chunk in self._chunks][:n_results]
        distances = [0.1 for _ in documents]
        return {
            "documents": [documents],
            "metadatas": [metadatas],
            "distances": [distances],
        }


def test_chroma_backed_vector_store_indexes_and_queries_via_chroma() -> None:
    repository, base_dir = _build_repository()
    try:
        document = _build_document()
        repository.save_document(document)
        embedding_service = DeterministicEmbeddingService()
        local_store = LocalVectorStore(repository, embedding_service)
        chroma_client = FakeChromaClient(available=True)
        vector_store = ChromaBackedVectorStore(local_store, embedding_service, chroma_client)

        chunks = vector_store.index_document(document)
        results = vector_store.search("Alice sales", top_k=3, hybrid_alpha=0.7, filters={"tags": ["sales"]})

        assert chunks
        assert chroma_client.upsert_calls == 1
        assert results
        assert results[0]["document_id"] == document.id
        assert results[0]["metadata"]["filename"] == document.filename
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


def test_chroma_backed_vector_store_falls_back_to_local_search() -> None:
    repository, base_dir = _build_repository()
    try:
        document = _build_document()
        repository.save_document(document)
        embedding_service = DeterministicEmbeddingService()
        local_store = LocalVectorStore(repository, embedding_service)
        vector_store = ChromaBackedVectorStore(local_store, embedding_service, FakeChromaClient(available=False))

        vector_store.index_document(document)
        results = vector_store.search("Alice sales", top_k=3, hybrid_alpha=0.7, filters={"tags": ["sales"]})

        assert results
        assert results[0]["document_id"] == document.id
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


def _build_repository() -> tuple[SQLiteDocumentRepository, Path]:
    base_dir = Path(__file__).resolve().parents[1] / ".tmp" / f"vector-store-{uuid.uuid4().hex[:8]}"
    base_dir.mkdir(parents=True, exist_ok=True)
    repository = SQLiteDocumentRepository(base_dir / "teammindhub.db")
    repository.initialize()
    return repository, base_dir


def _build_document() -> DocumentRecord:
    return DocumentRecord(
        id=f"doc_{uuid.uuid4().hex[:8]}",
        team_id="default",
        filename="sales.txt",
        stored_path="sales.txt",
        parse_status="parsed",
        upload_time="2026-03-28T15:00:00Z",
        tags=["sales"],
        metadata={},
        extracted_text="Alice 2025 Q1 sales 500 625 750 900",
    )
