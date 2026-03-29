from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture()
def test_settings() -> Settings:
    base_dir = Path(__file__).resolve().parents[1] / ".tmp" / f"test-run-{uuid.uuid4().hex[:8]}"
    if base_dir.exists():
        shutil.rmtree(base_dir)
    data_dir = base_dir / "data"
    settings = Settings(
        app_name="TeamMindHub Backend Test",
        base_dir=base_dir,
        data_dir=data_dir,
        uploads_dir=data_dir / "uploads",
        tools_dir=data_dir / "tools",
        sqlite_path=data_dir / "teammindhub.db",
        host="127.0.0.1",
        port=8000,
        rate_limit_per_minute=1000,
        main_orchestrator="qwen_orchestrator",
        available_agents=("qwen_orchestrator", "local_llama"),
        vector_store_backend="auto",
        chroma_host="localhost",
        chroma_port=8000,
        chroma_tenant="default_tenant",
        chroma_database="default_database",
        chroma_collection_name="teammindhub_chunks",
        chroma_timeout_seconds=0.2,
        ragflow_enabled=False,
        ragflow_base_url="",
        ragflow_api_key="",
        ragflow_dataset_name="teammindhub_deep_parse",
        ragflow_chunk_method="naive",
        ragflow_cleanup_documents=True,
        mineru_enabled=False,
        mineru_command="mineru",
        mineru_method="auto",
        mineru_backend="pipeline",
        mineru_model_source="huggingface",
        mineru_language="ch",
        mineru_timeout_seconds=0.2,
        docling_enabled=True,
        docling_command="docling",
        docling_timeout_seconds=0.2,
        llamaindex_enabled=True,
        langgraph_enabled=True,
        ollama_base_url="",
        ollama_model="",
        ollama_timeout_seconds=0.2,
        github_api_base="https://api.github.com",
        installer_clone_mode="manifest",
        debug=True,
    )
    yield settings
    if base_dir.exists():
        shutil.rmtree(base_dir, ignore_errors=True)


@pytest.fixture()
def client(test_settings: Settings) -> TestClient:
    settings = test_settings
    with TestClient(create_app(settings)) as test_client:
        yield test_client
