from __future__ import annotations

from typing import Any

from app.services.task_planner import TaskPlanningService


class FakeGenerationClient:
    def __init__(self, payload: dict[str, object] | None = None, should_fail: bool = False) -> None:
        self.payload = payload or {}
        self.should_fail = should_fail

    def generate_json(self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> dict[str, object]:
        assert "TeamMindHub task planner" in system_prompt
        assert "Alice" in user_prompt
        if self.should_fail:
            raise RuntimeError("ollama unavailable")
        return self.payload


def test_task_planner_prefers_ollama_when_available() -> None:
    planner = TaskPlanningService(
        FakeGenerationClient(
            payload={
                "routes": ["report", "analysis"],
                "entity": "Alice",
                "report_type": "sales_analysis",
                "analysis_focus": "quarterly sales trends",
            }
        )
    )

    plan = planner.plan(
        task="Generate Alice report and analyze sales trends",
        fallback_routes=["retrieval", "report", "analysis"],
        fallback_entity="Alice",
        fallback_report_type="sales_analysis",
    )

    assert plan.routes == ["retrieval", "report", "analysis"]
    assert plan.entity == "Alice"
    assert plan.report_type == "sales_analysis"
    assert plan.analysis_focus == "quarterly sales trends"
    assert plan.backend_name == "ollama"


def test_task_planner_falls_back_when_ollama_fails() -> None:
    planner = TaskPlanningService(FakeGenerationClient(should_fail=True))

    plan = planner.plan(
        task="Generate Alice report and analyze sales trends",
        fallback_routes=["retrieval", "report", "analysis"],
        fallback_entity="Alice",
        fallback_report_type="sales_analysis",
    )

    assert plan.routes == ["retrieval", "report", "analysis"]
    assert plan.entity == "Alice"
    assert plan.report_type == "sales_analysis"
    assert plan.backend_name == "heuristic"
