from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Generator

from app.services.analysis_service import AnalysisService
from app.services.installer_service import InstallerService
from app.services.langgraph_orchestrator import LangGraphTaskOrchestrator
from app.services.report_service import ReportService
from app.services.retrieval_service import RetrievalService
from app.services.task_planner import TaskPlan, TaskPlanningService


logger = logging.getLogger(__name__)


class OrchestratorService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        report_service: ReportService,
        analysis_service: AnalysisService,
        installer_service: InstallerService,
        default_agent: str,
        task_planner: TaskPlanningService | None = None,
        langgraph_enabled: bool = True,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.report_service = report_service
        self.analysis_service = analysis_service
        self.installer_service = installer_service
        self.default_agent = default_agent
        self.task_planner = task_planner
        self.langgraph_enabled = langgraph_enabled
        self.langgraph_runner: LangGraphTaskOrchestrator | None = None
        if langgraph_enabled:
            try:
                self.langgraph_runner = LangGraphTaskOrchestrator(
                    retrieval_service=retrieval_service,
                    report_service=report_service,
                    analysis_service=analysis_service,
                    installer_service=installer_service,
                    default_agent=default_agent,
                    build_task_plan=self._build_task_plan,
                    decide_routes=self._decide_routes,
                    extract_entity=self._extract_entity,
                    collect_document_ids=self._collect_document_ids,
                    trace_row=self._trace_row,
                )
            except Exception as exc:
                logger.warning("LangGraph unavailable, falling back to local orchestrator: %s", exc)
                self.langgraph_runner = None

    def run(
        self,
        task: str,
        main_agent: str | None,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        if self.langgraph_runner is not None:
            try:
                return self.langgraph_runner.run(task=task, main_agent=main_agent, parameters=parameters)
            except Exception as exc:
                logger.warning("LangGraph execution failed, falling back to local orchestrator: %s", exc)
        return self._run_local(task=task, main_agent=main_agent, parameters=parameters)

    def _run_local(
        self,
        task: str,
        main_agent: str | None,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        task_id = f"task_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        agent = main_agent or self.default_agent
        trace = []
        result: dict[str, Any] = {}
        routes = self._decide_routes(task)
        plan = self._build_task_plan(task)
        retrieval_result: dict[str, Any] | None = None
        document_ids: list[str] = []
        for step, route in enumerate(plan.routes, start=1):
            trace.append(self._trace_row(step, f"Invoked {route} module"))
            if route == "retrieval":
                retrieval_result = self.retrieval_service.search(query=task, top_k=5)
                result["retrieval"] = retrieval_result
                document_ids = self._collect_document_ids(retrieval_result)
                continue
            if route == "report":
                entity = self._resolve_report_entity(task, plan.entity, retrieval_result)
                report_type = plan.report_type
                result["report"] = self.report_service.generate(entity, report_type, True, 3)
                continue
            if route == "analysis":
                result["analysis"] = self.analysis_service.execute(
                    task,
                    document_ids,
                    "json",
                    analysis_focus=plan.analysis_focus,
                )
                continue
            if route == "installer":
                result["installer"] = {
                    "message": "Installation request detected. Call /installer/search or /installer/install explicitly.",
                }
        return {
            "task_id": task_id,
            "status": "completed",
            "main_agent": agent,
            "trace": trace,
            "result": result,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "parameters": parameters,
            "planning_backend": plan.backend_name,
        }

    def stream(
        self,
        task: str,
        main_agent: str | None,
        parameters: dict[str, Any],
    ) -> Generator[str, None, None]:
        response = self.run(task=task, main_agent=main_agent, parameters=parameters)
        for row in response["trace"]:
            yield self._sse_event("trace", row)
        yield self._sse_event("result", response)

    def backend_name(self) -> str:
        return "langgraph" if self.langgraph_runner is not None else "local"

    def _decide_routes(self, task: str) -> list[str]:
        lowered = task.lower()
        routes: list[str] = []
        retrieval_terms = (
            "search",
            "retrieve",
            "find",
            "\u641c\u7d22",
            "\u68c0\u7d22",
            "\u67e5\u627e",
        )
        report_terms = (
            "report",
            "summary",
            "profile",
            "\u62a5\u544a",
            "\u603b\u7ed3",
            "\u7edf\u5408",
        )
        analysis_terms = (
            "analysis",
            "trend",
            "stats",
            "\u5206\u6790",
            "\u8d8b\u52bf",
            "\u7edf\u8ba1",
        )
        installer_terms = (
            "install",
            "github",
            "\u5b89\u88c5",
            "\u5de5\u5177",
        )
        if any(term in lowered or term in task for term in retrieval_terms):
            routes.append("retrieval")
        if any(term in lowered or term in task for term in report_terms):
            routes.append("report")
        if any(term in lowered or term in task for term in analysis_terms):
            routes.append("analysis")
        if any(term in lowered or term in task for term in installer_terms):
            routes.append("installer")
        if not routes:
            return ["retrieval"]
        if "retrieval" not in routes and any(route in routes for route in ("report", "analysis")):
            routes.insert(0, "retrieval")
        return list(dict.fromkeys(routes))

    def _build_task_plan(self, task: str) -> TaskPlan:
        fallback_routes = self._decide_routes(task)
        fallback_entity = self._extract_entity(task, None)
        fallback_report_type = self._infer_report_type(task)
        if self.task_planner is None:
            return TaskPlan(
                routes=fallback_routes,
                entity=fallback_entity,
                report_type=fallback_report_type,
                analysis_focus=task,
                backend_name="heuristic",
            )
        return self.task_planner.plan(
            task=task,
            fallback_routes=fallback_routes,
            fallback_entity=fallback_entity,
            fallback_report_type=fallback_report_type,
        )

    def _extract_entity(
        self,
        task: str,
        retrieval_result: dict[str, Any] | None = None,
    ) -> str:
        top_result = ((retrieval_result or {}).get("results") or [None])[0]
        if isinstance(top_result, dict):
            candidate = self._extract_entity_from_text(str(top_result.get("text", "")))
            if candidate:
                return candidate
        task_candidate = self._extract_entity_from_text(task)
        if task_candidate:
            return task_candidate
        markers = (
            "for ",
            "about ",
            "\u5173\u4e8e",
            "\u751f\u6210",
            "\u5206\u6790",
            "\u603b\u7ed3",
        )
        lowered = task.lower()
        for marker in markers:
            source = lowered if marker.isascii() else task
            if marker in source:
                trailing = source.split(marker, 1)[-1].strip()
                if trailing:
                    return trailing[:24]
        tokens = [token for token in task.split() if token]
        if not tokens:
            return "unknown entity"
        return " ".join(tokens[:4])

    def _resolve_report_entity(
        self,
        task: str,
        planned_entity: str,
        retrieval_result: dict[str, Any] | None,
    ) -> str:
        entity = planned_entity.strip()
        if entity and entity != "unknown entity":
            return entity
        return self._extract_entity(task, retrieval_result)

    def _extract_entity_from_text(self, text: str) -> str | None:
        english_tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]*", text)
        stopwords = {
            "report",
            "analysis",
            "sales",
            "trend",
            "trends",
            "summary",
            "project",
            "generate",
            "generated",
            "analyze",
            "analysis",
            "and",
            "q1",
            "q2",
            "q3",
            "q4",
        }
        for token in english_tokens:
            if token.lower() not in stopwords:
                return token
        cjk_tokens = re.findall(r"[\u4e00-\u9fff]{2,}", text)
        return cjk_tokens[0] if cjk_tokens else None

    def _infer_report_type(self, task: str) -> str:
        lowered = task.lower()
        if any(term in lowered or term in task for term in ("sales", "\u9500\u552e")):
            return "sales_analysis"
        if any(term in lowered or term in task for term in ("profile", "person", "\u4eba\u7269", "\u4e2a\u4eba")):
            return "person_profile"
        return "project_summary"

    def _collect_document_ids(self, retrieval_result: dict[str, Any]) -> list[str]:
        document_ids: list[str] = []
        for item in retrieval_result.get("results", []):
            document_id = item.get("document_id")
            if isinstance(document_id, str) and document_id not in document_ids:
                document_ids.append(document_id)
        return document_ids

    def _trace_row(self, step: int, action: str) -> dict[str, Any]:
        return {
            "step": step,
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _sse_event(self, event: str, data: dict[str, Any]) -> str:
        payload = json.dumps(data, ensure_ascii=False)
        return f"event: {event}\ndata: {payload}\n\n"
