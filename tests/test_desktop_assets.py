from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from app.core.errors import AppError
from app.desktop import assets
from app.desktop.main import resolve_project_root


def _make_temp_root() -> Path:
    root = Path(__file__).resolve().parents[1] / ".tmp" / f"desktop-assets-{uuid.uuid4().hex[:8]}"
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_ensure_frontend_dist_uses_override_index_path(monkeypatch) -> None:
    temp_root = _make_temp_root()
    index_path = temp_root / "custom-ui" / "index.html"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("<html>desktop</html>", encoding="utf-8")
    monkeypatch.setenv("TMH_DESKTOP_INDEX_PATH", str(index_path))

    resolved = assets.ensure_frontend_dist(temp_root)

    assert resolved == index_path
    shutil.rmtree(temp_root, ignore_errors=True)


def test_ensure_frontend_dist_requires_frontend_directory(monkeypatch) -> None:
    temp_root = _make_temp_root()
    monkeypatch.delenv("TMH_DESKTOP_INDEX_PATH", raising=False)

    with pytest.raises(AppError) as exc_info:
        assets.ensure_frontend_dist(temp_root)

    assert "frontend directory was not found" in exc_info.value.details
    shutil.rmtree(temp_root, ignore_errors=True)


def test_ensure_frontend_dist_reports_missing_npm_when_dist_not_built(monkeypatch) -> None:
    temp_root = _make_temp_root()
    frontend_dir = temp_root / "frontend"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    (frontend_dir / "package.json").write_text("{}", encoding="utf-8")
    monkeypatch.delenv("TMH_DESKTOP_INDEX_PATH", raising=False)
    monkeypatch.setattr(assets, "_resolve_npm_command", lambda: None)

    with pytest.raises(AppError) as exc_info:
        assets.ensure_frontend_dist(temp_root)

    assert "TMH_DESKTOP_INDEX_PATH" in exc_info.value.details
    shutil.rmtree(temp_root, ignore_errors=True)


def test_resolve_esbuild_command_prefers_local_binary() -> None:
    temp_root = _make_temp_root()
    frontend_dir = temp_root / "frontend"
    esbuild_cmd = frontend_dir / "node_modules" / ".bin" / "esbuild.cmd"
    esbuild_cmd.parent.mkdir(parents=True, exist_ok=True)
    esbuild_cmd.write_text("@echo off", encoding="utf-8")

    resolved = assets._resolve_esbuild_command(frontend_dir)

    assert resolved == str(esbuild_cmd)
    shutil.rmtree(temp_root, ignore_errors=True)


def test_render_desktop_index_rewrites_entrypoint_and_css() -> None:
    temp_root = _make_temp_root()
    source_index = temp_root / "index.html"
    target_index = temp_root / "dist" / "index.html"
    target_index.parent.mkdir(parents=True, exist_ok=True)
    source_index.write_text(
        '<html><head><title>x</title></head><body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body></html>',
        encoding="utf-8",
    )

    assets._render_desktop_index(source_index, target_index)

    rendered = target_index.read_text(encoding="utf-8")
    assert './assets/app.js' in rendered
    assert './assets/app.css' in rendered
    assert 'type="module"' not in rendered
    assert 'defer' in rendered
    shutil.rmtree(temp_root, ignore_errors=True)


def test_ensure_frontend_dist_normalizes_existing_desktop_dist(monkeypatch) -> None:
    temp_root = _make_temp_root()
    frontend_dir = temp_root / "frontend"
    dist_dir = frontend_dir / "dist"
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.delenv("TMH_DESKTOP_INDEX_PATH", raising=False)
    (frontend_dir / "package.json").write_text("{}", encoding="utf-8")
    (frontend_dir / "index.html").write_text(
        '<html><head><title>x</title></head><body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body></html>',
        encoding="utf-8",
    )
    (assets_dir / "app.js").write_text("console.log('ok')", encoding="utf-8")
    (dist_dir / "index.html").write_text("<html><body>stale</body></html>", encoding="utf-8")

    resolved = assets.ensure_frontend_dist(temp_root)

    assert resolved == dist_dir / "index.html"
    rendered = resolved.read_text(encoding="utf-8")
    assert './assets/app.js' in rendered
    assert 'type="module"' not in rendered
    shutil.rmtree(temp_root, ignore_errors=True)


def test_ensure_frontend_dist_rebuilds_existing_dist_without_desktop_bundle(monkeypatch) -> None:
    temp_root = _make_temp_root()
    frontend_dir = temp_root / "frontend"
    dist_dir = frontend_dir / "dist"
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.delenv("TMH_DESKTOP_INDEX_PATH", raising=False)
    (frontend_dir / "package.json").write_text("{}", encoding="utf-8")
    (frontend_dir / "index.html").write_text(
        '<html><head><title>x</title></head><body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body></html>',
        encoding="utf-8",
    )
    (assets_dir / "index-old.js").write_text("console.log('stale')", encoding="utf-8")
    (dist_dir / "index.html").write_text('<html><body><script src="./assets/index-old.js"></script></body></html>', encoding="utf-8")

    monkeypatch.setattr(assets, "_resolve_esbuild_command", lambda _: "esbuild")

    def fake_build(frontend_path: Path, dist_path: Path, esbuild_command: str) -> None:
        assert frontend_path == frontend_dir
        assert dist_path == dist_dir
        assert esbuild_command == "esbuild"
        (dist_dir / "assets").mkdir(parents=True, exist_ok=True)
        (dist_dir / "assets" / "app.js").write_text("console.log('desktop')", encoding="utf-8")
        (dist_dir / "assets" / "app.css").write_text("body{}", encoding="utf-8")
        assets._render_desktop_index(frontend_dir / "index.html", dist_dir / "index.html")

    monkeypatch.setattr(assets, "_build_frontend_with_esbuild", fake_build)

    resolved = assets.ensure_frontend_dist(temp_root)

    assert resolved == dist_dir / "index.html"
    rendered = resolved.read_text(encoding="utf-8")
    assert './assets/app.js' in rendered
    assert './assets/app.css' in rendered
    shutil.rmtree(temp_root, ignore_errors=True)


def test_build_frontend_with_esbuild_uses_automatic_jsx(monkeypatch) -> None:
    temp_root = _make_temp_root()
    frontend_dir = temp_root / "frontend"
    dist_dir = frontend_dir / "dist"
    source_index = frontend_dir / "index.html"
    source_index.parent.mkdir(parents=True, exist_ok=True)
    source_index.write_text(
        '<html><head><title>x</title></head><body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body></html>',
        encoding="utf-8",
    )
    captured: dict[str, object] = {}

    def fake_run(command: list[str], workdir: Path) -> None:
        captured["command"] = command
        captured["workdir"] = workdir
        assets_dir = dist_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        (assets_dir / "app.js").write_text("console.log('desktop')", encoding="utf-8")
        (assets_dir / "app.css").write_text("body{}", encoding="utf-8")

    monkeypatch.setattr(assets, "_run_command", fake_run)

    assets._build_frontend_with_esbuild(frontend_dir, dist_dir, "esbuild")

    command = captured["command"]
    assert command == [
        "esbuild",
        "src/main.tsx",
        "--bundle",
        "--jsx=automatic",
        "--format=iife",
        "--platform=browser",
        "--outdir=dist/assets",
        "--entry-names=app",
    ]
    assert captured["workdir"] == frontend_dir
    assert (dist_dir / "index.html").exists()
    shutil.rmtree(temp_root, ignore_errors=True)


def test_resolve_project_root_uses_override(monkeypatch) -> None:
    temp_root = _make_temp_root()
    project_root = temp_root / "bundle-root"
    project_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("TMH_DESKTOP_PROJECT_ROOT", str(project_root))

    resolved = resolve_project_root()

    assert resolved == Path(project_root).resolve()
    shutil.rmtree(temp_root, ignore_errors=True)
