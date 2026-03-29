from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from app.core import config as config_module


def _make_temp_root() -> Path:
    root = Path(__file__).resolve().parents[1] / ".tmp" / f"config-test-{uuid.uuid4().hex[:8]}"
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_settings_from_env_reads_env_local(monkeypatch):
    tmp_path = _make_temp_root()
    monkeypatch.setattr(config_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("RAGFLOW_ENABLED", raising=False)
    monkeypatch.delenv("RAGFLOW_API_KEY", raising=False)
    (tmp_path / ".env.local").write_text(
        "RAGFLOW_ENABLED=true\nRAGFLOW_API_KEY=secret-value\n",
        encoding="utf-8",
    )

    settings = config_module.Settings.from_env()

    assert settings.ragflow_enabled is True
    assert settings.ragflow_api_key == "secret-value"
    shutil.rmtree(tmp_path, ignore_errors=True)


def test_settings_from_env_os_env_overrides_env_local(monkeypatch):
    tmp_path = _make_temp_root()
    monkeypatch.setattr(config_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("RAGFLOW_ENABLED", "false")
    monkeypatch.setenv("RAGFLOW_API_KEY", "runtime-env")
    (tmp_path / ".env.local").write_text(
        "RAGFLOW_ENABLED=true\nRAGFLOW_API_KEY=file-env\n",
        encoding="utf-8",
    )

    settings = config_module.Settings.from_env()

    assert settings.ragflow_enabled is False
    assert settings.ragflow_api_key == "runtime-env"
    shutil.rmtree(tmp_path, ignore_errors=True)
