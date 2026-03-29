from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import Settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RateLimitMiddleware, TraceIdMiddleware
from app.runtime import build_health_payload, create_runtime


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime = create_runtime(settings)
    resolved_settings = runtime.settings
    configure_logging(resolved_settings.debug)
    app = FastAPI(title=resolved_settings.app_name, version="0.1.0")
    app.state.settings = resolved_settings
    app.state.repository = runtime.repository
    app.state.container = runtime.container
    app.state.runtime = runtime
    app.add_middleware(TraceIdMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=resolved_settings.rate_limit_per_minute,
    )
    register_exception_handlers(app)
    app.include_router(api_router)
    ui_directory = Path(__file__).resolve().parent / "ui"
    if ui_directory.exists():
        app.mount("/ui", StaticFiles(directory=ui_directory, html=True), name="ui")
    desktop_ui_directory = Path(__file__).resolve().parents[1] / "frontend" / "dist"
    if desktop_ui_directory.exists():
        app.mount("/desktop", StaticFiles(directory=desktop_ui_directory, html=True), name="desktop_ui")

    @app.get("/")
    def root() -> dict[str, object]:
        return {
            "name": resolved_settings.app_name,
            "status": "ok",
            "docs": "/docs",
            "openapi": "/openapi.json",
            "desktop": "/desktop/",
        }

    @app.get("/health")
    def health() -> dict[str, object]:
        return build_health_payload(runtime)

    return app


app = create_app()
