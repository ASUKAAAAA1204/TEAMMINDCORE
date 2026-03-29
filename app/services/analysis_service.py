from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

from app.repositories.document_repository import SQLiteDocumentRepository
from app.services.ollama_client import StructuredGenerationClient


NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")
MAX_ANALYSIS_EVIDENCE_ITEMS = 4
MAX_ANALYSIS_EVIDENCE_CHARS = 500

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(
        self,
        repository: SQLiteDocumentRepository,
        generation_client: StructuredGenerationClient | None = None,
    ) -> None:
        self.repository = repository
        self.generation_client = generation_client

    def execute(
        self,
        task: str,
        document_ids: list[str],
        output_format: str,
        analysis_focus: str | None = None,
    ) -> dict[str, Any]:
        documents = self.repository.get_documents(document_ids)
        corpus = "\n".join(document.extracted_text for document in documents)
        numbers = [float(value) for value in NUMBER_PATTERN.findall(corpus)]
        total_value = round(sum(numbers), 2) if numbers else 0.0
        quarterly_growth = self._calculate_growth(numbers[:4])
        summary = self._build_summary(task, documents, total_value, quarterly_growth)
        chart_description = "A line chart would show the extracted values over time."
        llm_summary = self._generate_with_llm(
            task=task,
            analysis_focus=analysis_focus or task,
            documents=documents,
            total_value=total_value,
            quarterly_growth=quarterly_growth,
            output_format=output_format,
        )
        if llm_summary is not None:
            summary = llm_summary["summary"]
            chart_description = llm_summary["chart_description"]
        return {
            "task_id": f"analysis_{uuid.uuid4().hex[:8]}",
            "results": {
                "summary": summary,
                "statistics": {
                    "total_sales": total_value,
                    "value_count": len(numbers),
                    "quarterly_growth": quarterly_growth,
                },
                "chart_description": chart_description,
                "output_format": output_format,
            },
        }

    def _calculate_growth(self, values: list[float]) -> list[float]:
        if len(values) < 2:
            return []
        growth = []
        for previous, current in zip(values, values[1:]):
            if previous == 0:
                growth.append(0.0)
                continue
            growth.append(round((current - previous) / previous, 4))
        return growth

    def _build_summary(
        self,
        task: str,
        documents: list[Any],
        total_value: float,
        quarterly_growth: list[float],
    ) -> str:
        if not documents:
            return f'Task "{task}" did not match any documents.'
        if not quarterly_growth:
            return f"Read {len(documents)} documents and extracted a total value of {total_value}."
        return (
            f"Read {len(documents)} documents, extracted a total value of {total_value}, "
            f"and computed quarterly growth values {quarterly_growth}."
        )

    def backend_name(self) -> str:
        return "ollama" if self.generation_client is not None else "local"

    def _generate_with_llm(
        self,
        *,
        task: str,
        analysis_focus: str,
        documents: list[Any],
        total_value: float,
        quarterly_growth: list[float],
        output_format: str,
    ) -> dict[str, str] | None:
        if self.generation_client is None or not documents:
            return None
        evidence = []
        for document in documents[:MAX_ANALYSIS_EVIDENCE_ITEMS]:
            evidence.append(
                {
                    "document_id": document.id,
                    "filename": document.filename,
                    "text": document.extracted_text[:MAX_ANALYSIS_EVIDENCE_CHARS],
                }
            )
        try:
            payload = self.generation_client.generate_json(
                system_prompt=(
                    "You are a grounded data analysis assistant. "
                    "Use only the supplied statistics and evidence snippets. "
                    "Return concise business-language JSON."
                ),
                user_prompt=json.dumps(
                    {
                        "task": task,
                        "analysis_focus": analysis_focus,
                        "output_format": output_format,
                        "statistics": {
                            "total_sales": total_value,
                            "quarterly_growth": quarterly_growth,
                            "document_count": len(documents),
                        },
                        "evidence": evidence,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                schema={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "chart_description": {"type": "string"},
                    },
                    "required": ["summary", "chart_description"],
                    "additionalProperties": False,
                },
            )
        except Exception as exc:
            logger.warning("Ollama analysis generation failed, using deterministic summary: %s", exc)
            return None
        summary = payload.get("summary")
        chart_description = payload.get("chart_description")
        if not isinstance(summary, str) or not summary.strip():
            return None
        if not isinstance(chart_description, str) or not chart_description.strip():
            return None
        return {
            "summary": summary.strip(),
            "chart_description": chart_description.strip(),
        }
