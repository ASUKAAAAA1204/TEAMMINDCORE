from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from app.core.errors import AppError
from app.desktop.build import create_build_plan
from app.desktop.installer import (
    DEFAULT_INSTALLER_BASENAME,
    build_iscc_args,
    create_windows_installer_plan,
    find_iscc_executable,
    find_ollama_executable,
    resolve_built_installer_path,
)


def _make_temp_root() -> Path:
    root = Path(__file__).resolve().parents[1] / ".tmp" / f"desktop-installer-{uuid.uuid4().hex[:8]}"
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_find_iscc_executable_prefers_custom_path() -> None:
    temp_root = _make_temp_root()
    compiler = temp_root / "ISCC.exe"
    compiler.write_text("compiler", encoding="utf-8")

    assert find_iscc_executable(compiler) == compiler.resolve()
    shutil.rmtree(temp_root, ignore_errors=True)


def test_find_ollama_executable_prefers_custom_path() -> None:
    temp_root = _make_temp_root()
    ollama = temp_root / "ollama.exe"
    ollama.write_text("ollama", encoding="utf-8")

    assert find_ollama_executable(ollama) == ollama.resolve()
    shutil.rmtree(temp_root, ignore_errors=True)


def test_create_windows_installer_plan_requires_onedir_bundle() -> None:
    temp_root = _make_temp_root()
    project_root = temp_root / "project"
    entry_script = project_root / "app" / "desktop"
    entry_script.mkdir(parents=True, exist_ok=True)
    (entry_script / "main.py").write_text("print('desktop')", encoding="utf-8")

    frontend_dist = temp_root / "frontend" / "dist"
    frontend_dist.mkdir(parents=True, exist_ok=True)
    (frontend_dist / "index.html").write_text("<html>desktop</html>", encoding="utf-8")

    desktop_plan = create_build_plan(
        project_root=project_root,
        frontend_index=frontend_dist / "index.html",
        build_root=temp_root / "build-root",
        app_name="TeamMindHub",
        onefile=True,
        windowed=True,
        clean=True,
    )
    installer_script = temp_root / "TeamMindHub.iss"
    installer_script.write_text("; script", encoding="utf-8")

    with pytest.raises(AppError):
        create_windows_installer_plan(desktop_plan, script_path=installer_script, iscc_path=installer_script)

    shutil.rmtree(temp_root, ignore_errors=True)


def test_create_windows_installer_plan_and_args_include_required_defines() -> None:
    temp_root = _make_temp_root()
    project_root = temp_root / "project"
    entry_script = project_root / "app" / "desktop"
    entry_script.mkdir(parents=True, exist_ok=True)
    (entry_script / "main.py").write_text("print('desktop')", encoding="utf-8")

    frontend_dist = temp_root / "frontend" / "dist"
    frontend_dist.mkdir(parents=True, exist_ok=True)
    (frontend_dist / "index.html").write_text("<html>desktop</html>", encoding="utf-8")

    desktop_plan = create_build_plan(
        project_root=project_root,
        frontend_index=frontend_dist / "index.html",
        build_root=temp_root / "build-root",
        app_name="TeamMindHub",
        onefile=False,
        windowed=True,
        clean=True,
    )
    built_bundle = desktop_plan.dist_dir / desktop_plan.app_name
    built_bundle.mkdir(parents=True, exist_ok=True)
    (built_bundle / "TeamMindHub.exe").write_text("binary", encoding="utf-8")

    installer_script = temp_root / "TeamMindHub.iss"
    installer_script.write_text("; script", encoding="utf-8")
    compiler = temp_root / "ISCC.exe"
    compiler.write_text("compiler", encoding="utf-8")
    ollama = temp_root / "ollama.exe"
    ollama.write_text("ollama", encoding="utf-8")

    plan = create_windows_installer_plan(
        desktop_plan,
        script_path=installer_script,
        iscc_path=compiler,
        output_basename=DEFAULT_INSTALLER_BASENAME,
        ollama_executable=ollama,
    )
    args = build_iscc_args(plan)

    assert args[0] == str(compiler.resolve())
    assert args[1] == str(installer_script.resolve())
    assert f"/DMyAppName={desktop_plan.app_name}" in args
    assert any(item.startswith("/DSourceDir=") for item in args)
    assert any(item.startswith("/DOllamaExecutable=") for item in args)
    assert resolve_built_installer_path(plan) == plan.output_dir / f"{DEFAULT_INSTALLER_BASENAME}.exe"
    shutil.rmtree(temp_root, ignore_errors=True)


def test_create_windows_installer_plan_keeps_explicit_ollama_path() -> None:
    temp_root = _make_temp_root()
    project_root = temp_root / "project"
    entry_script = project_root / "app" / "desktop"
    entry_script.mkdir(parents=True, exist_ok=True)
    (entry_script / "main.py").write_text("print('desktop')", encoding="utf-8")

    frontend_dist = temp_root / "frontend" / "dist"
    frontend_dist.mkdir(parents=True, exist_ok=True)
    (frontend_dist / "index.html").write_text("<html>desktop</html>", encoding="utf-8")

    desktop_plan = create_build_plan(
        project_root=project_root,
        frontend_index=frontend_dist / "index.html",
        build_root=temp_root / "build-root",
        app_name="TeamMindHub",
        onefile=False,
        windowed=True,
        clean=True,
    )
    built_bundle = desktop_plan.dist_dir / desktop_plan.app_name
    built_bundle.mkdir(parents=True, exist_ok=True)
    (built_bundle / "TeamMindHub.exe").write_text("binary", encoding="utf-8")

    installer_script = temp_root / "TeamMindHub.iss"
    installer_script.write_text("; script", encoding="utf-8")
    compiler = temp_root / "ISCC.exe"
    compiler.write_text("compiler", encoding="utf-8")
    explicit_ollama_path = Path(r"C:\Users\33671\AppData\Local\Programs\Ollama\ollama app.exe")

    plan = create_windows_installer_plan(
        desktop_plan,
        script_path=installer_script,
        iscc_path=compiler,
        ollama_executable=explicit_ollama_path,
    )

    assert plan.ollama_executable == explicit_ollama_path
    shutil.rmtree(temp_root, ignore_errors=True)
