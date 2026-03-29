from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from app.desktop.build import (
    archive_release_bundle,
    build_pyinstaller_args,
    create_build_plan,
    data_separator_for_os_name,
    resolve_built_bundle_path,
    stage_frontend_bundle,
    write_release_manifest,
)


def _make_temp_root() -> Path:
    root = Path(__file__).resolve().parents[1] / ".tmp" / f"desktop-build-{uuid.uuid4().hex[:8]}"
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_data_separator_for_os_name() -> None:
    assert data_separator_for_os_name("nt") == ";"
    assert data_separator_for_os_name("posix") == ":"


def test_stage_frontend_bundle_copies_dist_tree() -> None:
    temp_root = _make_temp_root()
    source_dist = temp_root / "source" / "dist"
    source_dist.mkdir(parents=True, exist_ok=True)
    (source_dist / "index.html").write_text("<html>bundle</html>", encoding="utf-8")
    (source_dist / "assets.js").write_text("console.log('bundle');", encoding="utf-8")

    staged_root = stage_frontend_bundle(source_dist / "index.html", temp_root / "bundle")

    assert (staged_root / "index.html").read_text(encoding="utf-8") == "<html>bundle</html>"
    assert (staged_root / "assets.js").exists()
    shutil.rmtree(temp_root, ignore_errors=True)


def test_build_pyinstaller_args_include_frontend_bundle() -> None:
    temp_root = _make_temp_root()
    project_root = temp_root / "project"
    entry_script = project_root / "app" / "desktop"
    entry_script.mkdir(parents=True, exist_ok=True)
    (entry_script / "main.py").write_text("print('desktop')", encoding="utf-8")

    frontend_dist = temp_root / "frontend" / "dist"
    frontend_dist.mkdir(parents=True, exist_ok=True)
    (frontend_dist / "index.html").write_text("<html>desktop</html>", encoding="utf-8")

    plan = create_build_plan(
        project_root=project_root,
        frontend_index=frontend_dist / "index.html",
        build_root=temp_root / "build-root",
        app_name="TeamMindHub",
        onefile=False,
        windowed=True,
        clean=True,
    )

    args = build_pyinstaller_args(plan)

    assert "--collect-submodules" in args
    assert "webview" in args
    assert "--add-data" in args
    add_data_value = args[args.index("--add-data") + 1]
    assert "frontend/dist" in add_data_value
    assert str(plan.entry_script) == args[-1]
    shutil.rmtree(temp_root, ignore_errors=True)


def test_release_manifest_and_archive_for_onedir_bundle() -> None:
    temp_root = _make_temp_root()
    project_root = temp_root / "project"
    entry_script = project_root / "app" / "desktop"
    entry_script.mkdir(parents=True, exist_ok=True)
    (entry_script / "main.py").write_text("print('desktop')", encoding="utf-8")

    frontend_dist = temp_root / "frontend" / "dist"
    frontend_dist.mkdir(parents=True, exist_ok=True)
    (frontend_dist / "index.html").write_text("<html>desktop</html>", encoding="utf-8")

    plan = create_build_plan(
        project_root=project_root,
        frontend_index=frontend_dist / "index.html",
        build_root=temp_root / "build-root",
        app_name="TeamMindHub",
        onefile=False,
        windowed=True,
        clean=True,
    )

    built_bundle = plan.dist_dir / plan.app_name
    built_bundle.mkdir(parents=True, exist_ok=True)
    (built_bundle / "TeamMindHub.exe").write_text("binary", encoding="utf-8")

    resolved_bundle = resolve_built_bundle_path(plan)
    manifest_path = write_release_manifest(plan, resolved_bundle)
    archive_path = archive_release_bundle(plan, resolved_bundle)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["app_name"] == "TeamMindHub"
    assert manifest["build"]["bundle_path"] == str(resolved_bundle)
    assert archive_path.exists()
    shutil.rmtree(temp_root, ignore_errors=True)
