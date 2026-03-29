from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_container
from app.core.container import ServiceContainer
from app.modules.installer.schemas import (
    InstallRequest,
    InstallResponse,
    InstallerSearchRequest,
    InstallerSearchResponse,
)


router = APIRouter(prefix="/installer", tags=["installer"])


@router.post("/search", response_model=InstallerSearchResponse)
def search_tools(
    payload: InstallerSearchRequest,
    container: ServiceContainer = Depends(get_container),
) -> InstallerSearchResponse:
    result = container.github.search_repositories(payload.query)
    return InstallerSearchResponse(**result)


@router.post("/install", response_model=InstallResponse)
def install_tool(
    payload: InstallRequest,
    container: ServiceContainer = Depends(get_container),
) -> InstallResponse:
    result = container.installer.install(repo_url=payload.repo_url, confirm=payload.confirm)
    return InstallResponse(**result)

