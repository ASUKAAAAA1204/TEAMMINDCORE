from __future__ import annotations

import io
from typing import Any, cast

from app.services.analysis_service import AnalysisService
from app.services.installer_service import InstallerService
from app.services.orchestrator_service import OrchestratorService
from app.services.report_service import ReportService
from app.services.retrieval_service import RetrievalService
from app.services.task_planner import TaskPlan


def _seed_document(client):
    response = client.post(
        "/ingestion/upload",
        files=[("files", ("sales.txt", io.BytesIO("Alice 2025 Q1 sales 500 625 750 900".encode("utf-8")), "text/plain"))],
        data={"team_id": "default", "tags": '["sales"]', "parse_mode": "auto"},
    )
    assert response.status_code == 200
    return response.json()["document_ids"][0]


def test_orchestrator_returns_trace(client):
    _seed_document(client)
    response = client.post(
        "/orchestrator/run",
        json={
            "main_agent": "qwen_orchestrator",
            "task": "Generate Alice report and analyze sales trends",
            "parameters": {"max_steps": 5, "timeout": 60, "stream": False},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["planning_backend"] == "heuristic"
    assert [item["action"] for item in payload["trace"]] == [
        "Invoked retrieval module",
        "Invoked report module",
        "Invoked analysis module",
    ]
    assert payload["result"]["report"]["title"].startswith("Alice")
    assert payload["result"]["report"]["sources_count"] >= 1
    assert payload["result"]["analysis"]["results"]["statistics"]["total_sales"] > 0


def test_installer_search_returns_results(client):
    response = client.post("/installer/search", json={"query": "excel analysis"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1


class _FakeRetrievalService:
    def search(self, query: str, top_k: int = 8, hybrid_alpha: float = 0.7, filters=None):
        return {"results": [], "total_found": 0}


class _FakeReportService:
    def generate(self, entity: str, report_type: str, include_sources: bool, max_sections: int):
        return {"title": f"{entity}:{report_type}", "sources_count": 0}


class _FakeAnalysisService:
    def execute(self, task: str, document_ids: list[str], output_format: str, analysis_focus: str | None = None):
        return {"task": task, "document_ids": document_ids, "analysis_focus": analysis_focus, "output_format": output_format}


class _FakeInstallerService:
    pass


class _FakePlanner:
    def plan(self, *, task: str, fallback_routes: list[str], fallback_entity: str, fallback_report_type: str) -> TaskPlan:
        return TaskPlan(
            routes=["analysis"],
            entity="Ignored",
            report_type="project_summary",
            analysis_focus="profitability focus",
            backend_name="ollama",
        )


def test_orchestrator_prefers_task_planner_for_local_route_selection() -> None:
    service = OrchestratorService(
        retrieval_service=cast(RetrievalService, _FakeRetrievalService()),
        report_service=cast(ReportService, _FakeReportService()),
        analysis_service=cast(AnalysisService, _FakeAnalysisService()),
        installer_service=cast(InstallerService, _FakeInstallerService()),
        default_agent="qwen_orchestrator",
        task_planner=cast(Any, _FakePlanner()),
        langgraph_enabled=False,
    )

    payload = service.run(
        task="Generate Alice report and analyze sales trends",
        main_agent=None,
        parameters={"stream": False},
    )

    assert payload["planning_backend"] == "ollama"
    assert [item["action"] for item in payload["trace"]] == ["Invoked analysis module"]
    assert payload["result"]["analysis"]["analysis_focus"] == "profitability focus"
