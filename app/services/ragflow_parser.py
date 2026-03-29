from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Callable

from app.services.docling_parser import DeepParseResult


class RAGFlowDocumentParser:
    backend_name = "ragflow"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        dataset_name: str,
        chunk_method: str = "naive",
        cleanup_documents: bool = True,
        client_factory: Callable[[str, str], Any] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.dataset_name = dataset_name
        self.chunk_method = chunk_method
        self.cleanup_documents = cleanup_documents
        self.client_factory = client_factory

    def parse_to_markdown(self, file_path: Path) -> DeepParseResult:
        client = self._build_client()
        dataset = self._get_or_create_dataset(client)
        document_ids: list[str] = []
        try:
            with file_path.open("rb") as handle:
                uploaded_documents = dataset.upload_documents(
                    [{"display_name": file_path.name, "blob": handle}]
                )
            document_ids = [
                str(getattr(document, "id", "")).strip()
                for document in uploaded_documents
                if str(getattr(document, "id", "")).strip()
            ]
            if not document_ids:
                raise ValueError("RAGFlow upload did not return document identifiers")

            statuses = dataset.parse_documents(document_ids)
            failed = [
                {"document_id": item[0], "status": item[1]}
                for item in statuses
                if len(item) >= 2 and str(item[1]).upper() != "DONE"
            ]
            if failed:
                raise ValueError(f"RAGFlow parse did not finish successfully: {failed}")

            chunk_texts: list[str] = []
            for document_id in document_ids:
                documents = dataset.list_documents(id=document_id)
                if not documents:
                    raise ValueError(f"RAGFlow could not reload document {document_id}")
                chunks = self._list_all_chunks(documents[0])
                chunk_texts.extend(
                    chunk.content.strip()
                    for chunk in chunks
                    if isinstance(getattr(chunk, "content", None), str) and chunk.content.strip()
                )
            if not chunk_texts:
                raise ValueError("RAGFlow returned no parsed chunks")

            return DeepParseResult(
                text=self._to_markdown(file_path.name, chunk_texts),
                metadata={
                    "ragflow_method": "sdk",
                    "ragflow_dataset": self.dataset_name,
                    "ragflow_chunk_method": self.chunk_method,
                    "ragflow_document_count": len(document_ids),
                    "ragflow_chunk_count": len(chunk_texts),
                },
                parser_name="ragflow-sdk",
            )
        finally:
            if self.cleanup_documents and document_ids:
                try:
                    dataset.delete_documents(ids=document_ids)
                except Exception:
                    pass

    def _build_client(self) -> Any:
        if not self.base_url.strip():
            raise ValueError("RAGFlow base URL is required")
        if not self.api_key.strip():
            raise ValueError("RAGFlow API key is required")
        if self.client_factory is not None:
            return self.client_factory(self.api_key, self.base_url)
        module = importlib.import_module("ragflow_sdk")
        client_cls = getattr(module, "RAGFlow")
        return client_cls(api_key=self.api_key, base_url=self.base_url)

    def _get_or_create_dataset(self, client: Any) -> Any:
        try:
            return client.get_dataset(name=self.dataset_name)
        except Exception:
            return client.create_dataset(
                name=self.dataset_name,
                chunk_method=self.chunk_method,
            )

    def _list_all_chunks(self, document: Any, page_size: int = 128) -> list[Any]:
        chunks: list[Any] = []
        page = 1
        while True:
            page_items = list(document.list_chunks(page=page, page_size=page_size))
            chunks.extend(page_items)
            if len(page_items) < page_size:
                break
            page += 1
        return chunks

    def _to_markdown(self, filename: str, chunk_texts: list[str]) -> str:
        return f"# {filename}\n\n" + "\n\n".join(chunk_texts)
