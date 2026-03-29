from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.services.ragflow_parser import RAGFlowDocumentParser


class FakeChunk:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeDocument:
    def __init__(self, document_id: str, chunks: list[str]) -> None:
        self.id = document_id
        self._chunks = chunks

    def list_chunks(self, page: int = 1, page_size: int = 128):
        start = max(0, (page - 1) * page_size)
        end = start + page_size
        return [FakeChunk(content) for content in self._chunks[start:end]]


class FakeDataset:
    def __init__(self, document: FakeDocument, done: bool = True) -> None:
        self.document = document
        self.done = done
        self.upload_calls = 0
        self.deleted_ids: list[str] = []

    def upload_documents(self, document_list: list[dict[str, object]]):
        self.upload_calls += 1
        return [self.document]

    def parse_documents(self, document_ids: list[str]):
        status = "DONE" if self.done else "FAIL"
        return [(document_ids[0], status, len(self.document._chunks), 42)]

    def list_documents(self, id: str | None = None, **_: object):
        if id == self.document.id:
            return [self.document]
        return []

    def delete_documents(self, ids: list[str] | None = None, delete_all: bool = False):
        self.deleted_ids = ids or []


class FakeRAGFlowClient:
    def __init__(self, dataset: FakeDataset) -> None:
        self.dataset = dataset
        self.created = False

    def get_dataset(self, name: str):
        raise RuntimeError("dataset missing")

    def create_dataset(self, name: str, chunk_method: str = "naive"):
        self.created = True
        return self.dataset


def test_ragflow_parser_assembles_chunks_and_cleans_up_documents() -> None:
    temp_dir = _make_temp_dir()
    try:
        file_path = temp_dir / "sample.pdf"
        file_path.write_bytes(b"%PDF-1.4 fake")
        dataset = FakeDataset(FakeDocument("doc-1", ["chunk A", "chunk B"]))
        client = FakeRAGFlowClient(dataset)
        parser = RAGFlowDocumentParser(
            base_url="http://ragflow:9380",
            api_key="test-key",
            dataset_name="teammindhub_deep_parse",
            client_factory=lambda api_key, base_url: client,
        )

        result = parser.parse_to_markdown(file_path)

        assert client.created is True
        assert dataset.upload_calls == 1
        assert dataset.deleted_ids == ["doc-1"]
        assert result.parser_name == "ragflow-sdk"
        assert result.metadata["ragflow_method"] == "sdk"
        assert result.metadata["ragflow_chunk_count"] == 2
        assert result.text.startswith("# sample.pdf")
        assert "chunk A" in result.text
        assert "chunk B" in result.text
    finally:
        _cleanup_dir(temp_dir)


def test_ragflow_parser_raises_when_parse_fails() -> None:
    temp_dir = _make_temp_dir()
    try:
        file_path = temp_dir / "sample.pdf"
        file_path.write_bytes(b"%PDF-1.4 fake")
        dataset = FakeDataset(FakeDocument("doc-2", ["chunk A"]), done=False)
        client = FakeRAGFlowClient(dataset)
        parser = RAGFlowDocumentParser(
            base_url="http://ragflow:9380",
            api_key="test-key",
            dataset_name="teammindhub_deep_parse",
            client_factory=lambda api_key, base_url: client,
        )

        with pytest.raises(ValueError, match="RAGFlow parse did not finish successfully"):
            parser.parse_to_markdown(file_path)

        assert dataset.deleted_ids == ["doc-2"]
    finally:
        _cleanup_dir(temp_dir)


def _make_temp_dir() -> Path:
    temp_dir = Path(__file__).resolve().parents[1] / ".tmp" / f"ragflow-{uuid.uuid4().hex[:8]}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def _cleanup_dir(path: Path) -> None:
    for child in sorted(path.rglob("*"), reverse=True):
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    if path.exists():
        path.rmdir()
