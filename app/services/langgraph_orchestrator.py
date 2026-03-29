from __future__ import annotations

import importlib
from datetime import datetime, timezone
from typing import Any, Callable, TypedDict

from app.services.analysis_service import AnalysisService
from app.services.installer_service import InstallerService
from app.services.report_service import ReportService
from app.services.retrieval_service import RetrievalService
from app.services.task_planner import TaskPlan


class WorkflowState(TypedDict, total=False):
    task: str
    main_agent: str
    parameters: dict[str, Any]
    routes: list[str]
    route_index: int
    trace: list[dict[str, Any]]
    result: dict[str, Any]
    retrieval_result: dict[str, Any] | None
    document_ids: list[str]
    planned_entity: str
    planned_report_type: str
    analysis_focus: str
    planning_backend: str


class LangGraphTaskOrchestrator:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        report_service: ReportService,
        analysis_service: AnalysisService,
        installer_service: InstallerService,
        default_agent: str,
        build_task_plan: Callable[[str], TaskPlan],
        decide_routes: Callable[[str], list[str]],
        extract_entity: Callable[[str, dict[str, Any] | None], str],
        collect_document_ids: Callable[[dict[str, Any]], list[str]],
        trace_row: Callable[[int, str], dict[str, Any]],
    ) -> None:
        self.retrieval_service = retrieval_service
        self.report_service = report_service
        self.analysis_service = analysis_service
        self.installer_service = installer_service
        self.default_agent = default_agent
        self.build_task_plan = build_task_plan
        self.decide_routes = decide_routes
        self.extract_entity = extract_entity
        self.collect_document_ids = collect_document_ids
        self.trace_row = trace_row
        self._compiled_graph = self._compile_graph()

    def run(
        self,
        task: str,
        main_agent: str | None,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        task_id = f"task_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        agent = main_agent or self.default_agent
        executed_at = datetime.now(timezone.utc).isoformat()
        initial_state: WorkflowState = {
            "task": task,
            "main_agent": agent,
            "parameters": parameters,
            "routes": [],
            "route_index": 0,
            "trace": [],
            "result": {},
            "retrieval_result": None,
            "document_ids": [],
        }
        final_state = self._compiled_graph.invoke(initial_state)
        return {
            "task_id": task_id,
            "status": "completed",
            "main_agent": agent,
            "trace": final_state.get("trace", []),
            "result": final_state.get("result", {}),
            "executed_at": executed_at,
            "parameters": parameters,
            "planning_backend": final_state.get("planning_backend", "heuristic"),
        }

    def _compile_graph(self) -> Any:
        graph_module = importlib.import_module("langgraph.graph")
        state_graph_cls = getattr(graph_module, "StateGraph")
        start = getattr(graph_module, "START")
        end = getattr(graph_module, "END")

        builder = state_graph_cls(WorkflowState)
        builder.add_node("prepare", self._prepare)
        builder.add_node("dispatch", self._dispatch)
        builder.add_node("retrieval", self._run_retrieval)
        builder.add_node("report", self._run_report)
        builder.add_node("analysis", self._run_analysis)
        builder.add_node("installer", self._run_installer)

        builder.add_edge(start, "prepare")
        builder.add_edge("prepare", "dispatch")
        builder.add_conditional_edges(
            "dispatch",
            self._route_next,
            {
                "retrieval": "retrieval",
                "report": "report",
                "analysis": "analysis",
                "installer": "installer",
                "end": end,
            },
        )
        builder.add_edge("retrieval", "dispatch")
        builder.add_edge("report", "dispatch")
        builder.add_edge("analysis", "dispatch")
        builder.add_edge("installer", "dispatch")
        return builder.compile()

    def _prepare(self, state: WorkflowState) -> WorkflowState:
        task = str(state.get("task", ""))
        plan = self.build_task_plan(task)
        return {
            "routes": plan.routes,
            "route_index": 0,
            "trace": [],
            "result": {},
            "retrieval_result": None,
            "document_ids": [],
            "planned_entity": plan.entity,
            "planned_report_type": plan.report_type,
            "analysis_focus": plan.analysis_focus,
            "planning_backend": plan.backend_name,
        }

    def _dispatch(self, state: WorkflowState) -> WorkflowState:
        return state

    def _route_next(self, state: WorkflowState) -> str:
        routes = state.get("routes", [])
        route_index = state.get("route_index", 0)
        if route_index >= len(routes):
            return "end"
        route = routes[route_index]
        if route in {"retrieval", "report", "analysis", "installer"}:
            return route
        return "end"

    def _run_retrieval(self, state: WorkflowState) -> WorkflowState:
        task = str(state.get("task", ""))
        retrieval_result = self.retrieval_service.search(query=task, top_k=5)
        result = dict(state.get("result", {}))
        result["retrieval"] = retrieval_result
        trace = self._next_trace(state, "retrieval")
        return {
            "result": result,
            "trace": trace,
            "retrieval_result": retrieval_result,
            "document_ids": self.collect_document_ids(retrieval_result),
            "route_index": state.get("route_index", 0) + 1,
        }

    def _run_report(self, state: WorkflowState) -> WorkflowState:
        task = str(state.get("task", ""))
        retrieval_result = state.get("retrieval_result")
        entity = str(state.get("planned_entity", "")).strip()
        if not entity or entity == "unknown entity":
            entity = self.extract_entity(task, retrieval_result if isinstance(retrieval_result, dict) else None)
        report_type = str(state.get("planned_report_type", "project_summary"))
        report = self.report_service.generate(entity, report_type, True, 3)
        result = dict(state.get("result", {}))
        result["report"] = report
        trace = self._next_trace(state, "report")
        return {
            "result": result,
            "trace": trace,
            "route_index": state.get("route_index", 0) + 1,
        }

    def _run_analysis(self, state: WorkflowState) -> WorkflowState:
        task = str(state.get("task", ""))
        document_ids = state.get("document_ids", [])
        analysis = self.analysis_service.execute(
            task,
            document_ids,
            "json",
            analysis_focus=str(state.get("analysis_focus", "")).strip() or task,
        )
        result = dict(state.get("result", {}))
        result["analysis"] = analysis
        trace = self._next_trace(state, "analysis")
        return {
            "result": result,
            "trace": trace,
            "route_index": state.get("route_index", 0) + 1,
        }

    def _run_installer(self, state: WorkflowState) -> WorkflowState:
        result = dict(state.get("result", {}))
        result["installer"] = {
            "message": "Installation request detected. Call /installer/search or /installer/install explicitly.",
        }
        trace = self._next_trace(state, "installer")
        return {
            "result": result,
            "trace": trace,
            "route_index": state.get("route_index", 0) + 1,
        }

    def _next_trace(self, state: WorkflowState, route: str) -> list[dict[str, Any]]:
        trace = list(state.get("trace", []))
        trace.append(self.trace_row(len(trace) + 1, f"Invoked {route} module"))
        return trace
