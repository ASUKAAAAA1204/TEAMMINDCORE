from __future__ import annotations

import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.errors import AppError
from app.desktop import main as desktop_main


def _make_temp_root() -> Path:
    root = Path(__file__).resolve().parents[1] / ".tmp" / f"desktop-main-{uuid.uuid4().hex[:8]}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_resolve_webview_storage_dir_creates_directory() -> None:
    root = _make_temp_root()

    storage_dir = desktop_main.resolve_webview_storage_dir(root, root)

    assert storage_dir == root / "webview"
    assert storage_dir.exists()


def test_resolve_webview_storage_dir_falls_back_to_project_tmp(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_temp_root()
    app_base_dir = root / "blocked"
    project_root = root / "project"
    project_root.mkdir(parents=True, exist_ok=True)

    original_mkdir = Path.mkdir

    def patched_mkdir(self: Path, *args, **kwargs):
        if self == app_base_dir / "webview":
            raise PermissionError("denied")
        return original_mkdir(self, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", patched_mkdir)

    storage_dir = desktop_main.resolve_webview_storage_dir(app_base_dir, project_root)

    assert storage_dir == project_root / ".tmp" / "desktop-webview"
    assert storage_dir.exists()


def test_main_uses_persistent_webview_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    temp_root = _make_temp_root()
    storage_root = temp_root / "appdata"
    index_path = temp_root / "frontend" / "dist" / "index.html"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("<html></html>", encoding="utf-8")

    calls: dict[str, object] = {}

    class WebViewStub:
        def create_window(self, *args, **kwargs):
            calls["create_window_args"] = args
            calls["create_window_kwargs"] = kwargs

        def start(self, **kwargs):
            calls["start_kwargs"] = kwargs

    monkeypatch.setitem(sys.modules, "webview", WebViewStub())
    monkeypatch.setattr(desktop_main, "resolve_project_root", lambda: temp_root)
    monkeypatch.setattr(desktop_main, "resolve_app_base_dir", lambda: storage_root)
    monkeypatch.setattr(desktop_main, "ensure_frontend_dist", lambda _: index_path)
    monkeypatch.setattr(
        desktop_main,
        "create_runtime",
        lambda _: SimpleNamespace(settings=SimpleNamespace(app_name="TeamMindHub Backend", debug=False)),
    )
    monkeypatch.setattr(desktop_main.Settings, "from_env", classmethod(lambda cls: SimpleNamespace()))
    monkeypatch.setattr(desktop_main, "DesktopBridge", lambda runtime: SimpleNamespace(runtime=runtime))

    desktop_main.main()

    assert calls["start_kwargs"] == {
        "debug": False,
        "private_mode": False,
        "storage_path": str(storage_root / "webview"),
    }
    assert (storage_root / "webview").exists()


def test_main_wraps_webview_start_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    temp_root = _make_temp_root()
    storage_root = temp_root / "appdata"
    index_path = temp_root / "frontend" / "dist" / "index.html"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("<html></html>", encoding="utf-8")

    class WebViewStub:
        def create_window(self, *args, **kwargs):
            return None

        def start(self, **kwargs):
            raise RuntimeError("webview2 init failed")

    monkeypatch.setitem(sys.modules, "webview", WebViewStub())
    monkeypatch.setattr(desktop_main, "resolve_project_root", lambda: temp_root)
    monkeypatch.setattr(desktop_main, "resolve_app_base_dir", lambda: storage_root)
    monkeypatch.setattr(desktop_main, "ensure_frontend_dist", lambda _: index_path)
    monkeypatch.setattr(
        desktop_main,
        "create_runtime",
        lambda _: SimpleNamespace(settings=SimpleNamespace(app_name="TeamMindHub Backend", debug=False)),
    )
    monkeypatch.setattr(desktop_main.Settings, "from_env", classmethod(lambda cls: SimpleNamespace()))
    monkeypatch.setattr(desktop_main, "DesktopBridge", lambda runtime: SimpleNamespace(runtime=runtime))

    with pytest.raises(AppError) as exc_info:
        desktop_main.main()

    assert "Embedded WebView failed to initialize" in str(exc_info.value.details)
    assert "Microsoft Edge WebView2 Runtime" in str(exc_info.value.details)
