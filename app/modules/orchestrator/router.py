from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_container
from app.core.container import ServiceContainer
from app.modules.orchestrator.schemas import OrchestratorResponse, OrchestratorRunRequest


router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.post("/run", response_model=OrchestratorResponse)
def run_orchestrator(
    payload: OrchestratorRunRequest,
    container: ServiceContainer = Depends(get_container),
):
    parameters = payload.parameters.model_dump()
    if parameters.get("stream"):
        return StreamingResponse(
            container.orchestrator.stream(
                task=payload.task,
                main_agent=payload.main_agent,
                parameters=parameters,
            ),
            media_type="text/event-stream",
        )
    result = container.orchestrator.run(
        task=payload.task,
        main_agent=payload.main_agent,
        parameters=parameters,
    )
    return OrchestratorResponse(**result)

