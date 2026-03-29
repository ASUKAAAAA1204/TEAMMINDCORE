from __future__ import annotations

from fastapi import Request

from app.core.config import Settings
from app.core.container import ServiceContainer
from app.repositories.document_repository import SQLiteDocumentRepository


def get_settings_dependency(request: Request) -> Settings:
    return request.app.state.settings


def get_repository(request: Request) -> SQLiteDocumentRepository:
    return request.app.state.repository


def get_container(request: Request) -> ServiceContainer:
    return request.app.state.container
