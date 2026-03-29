from __future__ import annotations

from pydantic import BaseModel


class InstallerSearchRequest(BaseModel):
    query: str


class InstallerSearchResult(BaseModel):
    name: str
    url: str
    stars: int
    description: str
    readme_summary: str
    license: str


class InstallerSearchResponse(BaseModel):
    total: int
    results: list[InstallerSearchResult]


class InstallRequest(BaseModel):
    repo_url: str
    confirm: bool


class InstallResponse(BaseModel):
    success: bool
    tool_name: str
    installed_path: str
    message: str

