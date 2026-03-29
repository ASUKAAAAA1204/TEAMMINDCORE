from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Protocol

from app.services.ollama_client import StructuredGenerationClient


REPORT_SECTION_TEMPLATES = {
    "person_profile": ["Overview", "Project and data evidence", "Key observations"],
    "project_summary": ["Project overview", "Milestones", "Risks and next actions"],
    "sales_analysis": ["Sales summary", "Trend observations", "Recommendations"],
}
MAX_EVIDENCE_ITEMS = 6
MAX_EVIDENCE_CHARS = 700


logger = logging.getLogger(__name__)


class RetrievalSearcher(Protocol):
    def search(
        self,
        query: str,
        top_k: int = 8,
        hybrid_alpha: float = 0.7,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ...


class ReportService:
    def __init__(
        self,
        retrieval_service: RetrievalSearcher,
        generation_client: StructuredGenerationClient | None = None,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.generation_client = generation_client

    def generate(
        self,
        entity: str,
        report_type: str,
        include_sources: bool,
        max_sections: int,
    ) -> dict[str, object]:
        search_result = self.retrieval_service.search(query=entity, top_k=max_sections * 2)
        items = search_result["results"]
        section_titles = REPORT_SECTION_TEMPLATES.get(
            report_type,
            REPORT_SECTION_TEMPLATES["project_summary"],
        )
        llm_result = self._generate_with_llm(
            entity=entity,
            report_type=report_type,
            include_sources=include_sources,
            max_sections=max_sections,
            section_titles=section_titles,
            items=items,
        )
        if llm_result is not None:
            return llm_result
        sections = []
        unique_sources: list[str] = []
        for index, title in enumerate(section_titles[:max_sections]):
            source_item = items[index] if index < len(items) else None
            content = source_item["text"] if source_item else f"No indexed content found for {entity}."
            sources = []
            if source_item and include_sources:
                sources = [source_item["document_id"]]
                if source_item["document_id"] not in unique_sources:
                    unique_sources.append(source_item["document_id"])
            sections.append(
                {
                    "section": title,
                    "content": content,
                    "sources": sources,
                }
            )
        overall_summary = self._build_summary(entity, report_type, items)
        return {
            "title": f"{entity}{self._title_suffix(report_type)}",
            "sections": sections,
            "overall_summary": overall_summary,
            "sources_count": len(unique_sources),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_with_llm(
        self,
        entity: str,
        report_type: str,
        include_sources: bool,
        max_sections: int,
        section_titles: list[str],
        items: list[dict[str, object]],
    ) -> dict[str, object] | None:
        if self.generation_client is None or not items:
            return None
        schema = self._report_schema()
        evidence = []
        for item in items[:MAX_EVIDENCE_ITEMS]:
            evidence.append(
                {
                    "document_id": str(item["document_id"]),
                    "text": str(item["text"])[:MAX_EVIDENCE_CHARS],
                    "metadata": item.get("metadata", {}),
                }
            )
        prompt_payload = {
            "entity": entity,
            "report_type": report_type,
            "include_sources": include_sources,
            "max_sections": max_sections,
            "allowed_section_titles": section_titles[:max_sections],
            "evidence": evidence,
        }
        try:
            payload = self.generation_client.generate_json(
                system_prompt=(
                    "You are a grounded report generator. "
                    "Use only the provided evidence. "
                    "Do not invent facts or source ids. "
                    "If evidence is thin, say so briefly and stay concise."
                ),
                user_prompt=json.dumps(prompt_payload, ensure_ascii=False, indent=2),
                schema=schema,
            )
        except Exception as exc:
            logger.warning("Ollama report generation failed, using fallback: %s", exc)
            return None
        return self._normalize_llm_report(
            entity=entity,
            report_type=report_type,
            include_sources=include_sources,
            max_sections=max_sections,
            section_titles=section_titles,
            items=items,
            payload=payload,
        )

    def _title_suffix(self, report_type: str) -> str:
        mapping = {
            "person_profile": " profile report",
            "project_summary": " project report",
            "sales_analysis": " sales analysis report",
        }
        return mapping.get(report_type, " report")

    def _build_summary(
        self,
        entity: str,
        report_type: str,
        items: list[dict[str, object]],
    ) -> str:
        if not items:
            return f"No indexed content was found for {entity}. Upload more documents before generating {report_type}."
        top_text = items[0]["text"]
        snippet = str(top_text)[:180]
        return f"Top indexed evidence for {entity}: {snippet}"

    def _report_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "overall_summary": {"type": "string"},
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "section": {"type": "string"},
                            "content": {"type": "string"},
                            "sources": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["section", "content", "sources"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["title", "overall_summary", "sections"],
            "additionalProperties": False,
        }

    def _normalize_llm_report(
        self,
        entity: str,
        report_type: str,
        include_sources: bool,
        max_sections: int,
        section_titles: list[str],
        items: list[dict[str, object]],
        payload: dict[str, Any],
    ) -> dict[str, object]:
        raw_sections = payload.get("sections")
        sections_payload = raw_sections if isinstance(raw_sections, list) else []
        allowed_sources = {str(item["document_id"]) for item in items}
        unique_sources: list[str] = []
        sections = []
        for index, default_title in enumerate(section_titles[:max_sections]):
            item = sections_payload[index] if index < len(sections_payload) and isinstance(sections_payload[index], dict) else {}
            fallback_item = items[index] if index < len(items) else items[0]
            content = self._clean_text(item.get("content"))
            if not content and fallback_item is not None:
                content = str(fallback_item["text"])
            if not content:
                content = f"No indexed content found for {entity}."
            fallback_source = (
                str(fallback_item["document_id"])
                if fallback_item is not None and include_sources
                else None
            )
            sources = self._normalize_sources(
                raw_sources=item.get("sources"),
                allowed_sources=allowed_sources,
                include_sources=include_sources,
                fallback_source=fallback_source,
            )
            for source_id in sources:
                if source_id not in unique_sources:
                    unique_sources.append(source_id)
            sections.append(
                {
                    "section": self._clean_text(item.get("section")) or default_title,
                    "content": content,
                    "sources": sources,
                }
            )
        overall_summary = self._clean_text(payload.get("overall_summary")) or self._build_summary(entity, report_type, items)
        title = self._clean_text(payload.get("title")) or f"{entity}{self._title_suffix(report_type)}"
        return {
            "title": title,
            "sections": sections,
            "overall_summary": overall_summary,
            "sources_count": len(unique_sources),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _normalize_sources(
        self,
        raw_sources: object,
        allowed_sources: set[str],
        include_sources: bool,
        fallback_source: str | None,
    ) -> list[str]:
        if not include_sources:
            return []
        normalized: list[str] = []
        if isinstance(raw_sources, list):
            for source in raw_sources:
                source_id = str(source)
                if source_id in allowed_sources and source_id not in normalized:
                    normalized.append(source_id)
        if not normalized and fallback_source and fallback_source in allowed_sources:
            normalized.append(fallback_source)
        return normalized

    def _clean_text(self, value: object) -> str:
        if not isinstance(value, str):
            return ""
        return value.strip()
