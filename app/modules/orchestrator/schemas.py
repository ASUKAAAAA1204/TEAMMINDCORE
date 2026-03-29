from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class OrchestratorParameters(BaseModel):
    max_steps: int = 10
    timeout: int = 300
    stream: bool = False


class OrchestratorRunRequest(BaseModel):
    main_agent: str | None = None
    task: str
    parameters: OrchestratorParameters = Field(default_factory=OrchestratorParameters)


class OrchestratorResponse(BaseModel):
    task_id: str
    status: str
    main_agent: str
    trace: list[dict[str, Any]]
    result: dict[str, Any]
    executed_at: str
    parameters: dict[str, Any]
    planning_backend: str
