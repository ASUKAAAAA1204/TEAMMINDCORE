from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from app.services.ollama_client import StructuredGenerationClient


logger = logging.getLogger(__name__)

SUPPORTED_ROUTES = ("retrieval", "report", "analysis", "installer")
SUPPORTED_REPORT_TYPES = ("person_profile", "project_summary", "sales_analysis")


@dataclass(slots=True)
class TaskPlan:
    routes: list[str]
    entity: str
    report_type: str
    analysis_focus: str
    backend_name: str


class TaskPlanningService:
    def __init__(self, generation_client: StructuredGenerationClient | None = None) -> None:
        self.generation_client = generation_client

    def backend_name(self) -> str:
        return "ollama" if self.generation_client is not None else "heuristic"

    def plan(
        self,
        *,
        task: str,
        fallback_routes: list[str],
        fallback_entity: str,
        fallback_report_type: str,
    ) -> TaskPlan:
        fallback_analysis_focus = task.strip() or "analysis"
        fallback = TaskPlan(
            routes=self._normalize_routes(fallback_routes),
            entity=fallback_entity.strip() or "unknown entity",
            report_type=self._normalize_report_type(fallback_report_type, "project_summary"),
            analysis_focus=fallback_analysis_focus,
            backend_name="heuristic",
        )
        if self.generation_client is None:
            return fallback
        try:
            payload = self.generation_client.generate_json(
                system_prompt=(
                    "You are the TeamMindHub task planner. "
                    "Return strict JSON only. "
                    "Use only these routes: retrieval, report, analysis, installer. "
                    "If a task asks for reporting or analysis, include retrieval first. "
                    "Choose report_type from person_profile, project_summary, sales_analysis."
                ),
                user_prompt=json.dumps(
                    {
                        "task": task,
                        "fallback": {
                            "routes": fallback.routes,
                            "entity": fallback.entity,
                            "report_type": fallback.report_type,
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                schema=self._plan_schema(),
            )
        except Exception as exc:
            logger.warning("Ollama task planning failed, using heuristic plan: %s", exc)
            return fallback
        return TaskPlan(
            routes=self._normalize_routes(payload.get("routes"), fallback.routes),
            entity=self._clean_text(payload.get("entity")) or fallback.entity,
            report_type=self._normalize_report_type(payload.get("report_type"), fallback.report_type),
            analysis_focus=self._clean_text(payload.get("analysis_focus")) or fallback.analysis_focus,
            backend_name="ollama",
        )

    def _plan_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "routes": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "entity": {"type": "string"},
                "report_type": {"type": "string"},
                "analysis_focus": {"type": "string"},
            },
            "required": ["routes", "entity", "report_type", "analysis_focus"],
            "additionalProperties": False,
        }

    def _normalize_routes(
        self,
        raw_routes: object,
        fallback_routes: list[str] | None = None,
    ) -> list[str]:
        fallback = list(fallback_routes or ["retrieval"])
        if not isinstance(raw_routes, list):
            return fallback
        normalized: list[str] = []
        for route in raw_routes:
            route_name = self._clean_text(route).lower()
            if route_name in SUPPORTED_ROUTES and route_name not in normalized:
                normalized.append(route_name)
        if not normalized:
            return fallback
        if "retrieval" not in normalized and any(route in normalized for route in ("report", "analysis")):
            normalized.insert(0, "retrieval")
        return normalized

    def _normalize_report_type(self, raw_value: object, fallback: str) -> str:
        value = self._clean_text(raw_value)
        if value in SUPPORTED_REPORT_TYPES:
            return value
        return fallback if fallback in SUPPORTED_REPORT_TYPES else "project_summary"

    def _clean_text(self, value: object) -> str:
        if not isinstance(value, str):
            return ""
        return value.strip()
