from fastapi import APIRouter

from app.modules.analysis.router import router as analysis_router
from app.modules.ingestion.router import router as ingestion_router
from app.modules.installer.router import router as installer_router
from app.modules.integration.router import router as integration_router
from app.modules.orchestrator.router import router as orchestrator_router
from app.modules.report.router import router as report_router
from app.modules.retrieval.router import router as retrieval_router
from app.modules.tools.router import router as tools_router


api_router = APIRouter()
api_router.include_router(ingestion_router)
api_router.include_router(retrieval_router)
api_router.include_router(report_router)
api_router.include_router(orchestrator_router)
api_router.include_router(installer_router)
api_router.include_router(analysis_router)
api_router.include_router(integration_router)
api_router.include_router(tools_router)

