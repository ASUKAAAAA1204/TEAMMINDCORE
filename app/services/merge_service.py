from __future__ import annotations

from typing import Any

from app.repositories.document_repository import SQLiteDocumentRepository


class MergeService:
    def __init__(self, repository: SQLiteDocumentRepository) -> None:
        self.repository = repository

    def merge(self, document_ids: list[str], rule: dict[str, Any]) -> dict[str, Any]:
        documents = self.repository.get_documents(document_ids)
        strategy = rule.get("strategy", "concatenate")
        output_format = rule.get("format", "markdown")
        sections = []
        for index, document in enumerate(documents, start=1):
            sections.append(
                f"## Document {index}: {document.filename}\n{document.extracted_text.strip() or 'No extracted text available'}"
            )
        merged_content = "# Merged Documents\n\n" + "\n\n".join(sections)
        if strategy != "concatenate":
            merged_content += f"\n\n> Falling back to concatenate. Requested strategy: {strategy}"
        return {
            "merged_content": merged_content if output_format == "markdown" else "\n".join(sections),
            "total_length": len(merged_content),
            "source_count": len(documents),
        }

