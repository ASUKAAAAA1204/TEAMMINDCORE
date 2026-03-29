from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from pathlib import Path

from app.core.errors import AppError
from app.desktop.assets import ensure_frontend_dist
from app.desktop.installer import (
    DEFAULT_INSTALLER_BASENAME,
    OLLAMA_MODEL_PRESETS,
    build_iscc_args,
    create_windows_installer_plan,
    resolve_built_installer_path,
    run_inno_setup,
)


DEFAULT_APP_NAME = "TeamMindHub"


@dataclass(slots=True)
class DesktopBuildPlan:
    app_name: str
    entry_script: Path
    frontend_index: Path
    staged_frontend_root: Path
    build_root: Path
    dist_dir: Path
    work_dir: Path
    spec_dir: Path
    onefile: bool
    windowed: bool
    clean: bool


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    project_root = Path(args.project_root).resolve()
    frontend_index = _resolve_frontend_index(project_root, args.index_path)
    build_root = Path(args.build_root).resolve()
    plan = create_build_plan(
        project_root=project_root,
        frontend_index=frontend_index,
        build_root=build_root,
        app_name=args.app_name,
        onefile=args.onefile,
        windowed=not args.console,
        clean=not args.no_clean,
    )
    if args.print_command:
        print("\n".join(build_pyinstaller_args(plan)))
        return
    installer_script_path = None
    if args.build_installer:
        installer_script_path = _resolve_installer_script(project_root, args.installer_script)
        installer_plan = create_windows_installer_plan(
            plan,
            script_path=installer_script_path,
            iscc_path=args.iscc_path,
            output_basename=args.installer_basename,
            ollama_executable=args.ollama_exe_path,
            require_source_dir=False,
        )
        if args.print_installer_command:
            print("\n".join(build_iscc_args(installer_plan)))
            return
    run_pyinstaller(plan)
    bundle_path, manifest_path, archive_path = finalize_release(plan, archive=args.archive)
    installer_path = None
    if args.build_installer:
        installer_plan = create_windows_installer_plan(
            plan,
            script_path=installer_script_path,
            iscc_path=args.iscc_path,
            output_basename=args.installer_basename,
            ollama_executable=args.ollama_exe_path,
        )
        installer_path = run_inno_setup(installer_plan)
        update_release_manifest_with_installer(
            manifest_path,
            installer_path=installer_path,
            installer_args=build_iscc_args(installer_plan),
            ollama_executable=installer_plan.ollama_executable,
        )
    print(f"Built desktop bundle: {bundle_path}")
    print(f"Release manifest: {manifest_path}")
    if archive_path is not None:
        print(f"Release archive: {archive_path}")
    if installer_path is not None:
        print(f"Windows installer: {installer_path}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the TeamMindHub desktop application with PyInstaller.")
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--build-root", default=str(Path(__file__).resolve().parents[2] / ".tmp" / "desktop-build"))
    parser.add_argument("--index-path", default="")
    parser.add_argument("--app-name", default=DEFAULT_APP_NAME)
    parser.add_argument("--onefile", action="store_true", help="Build a single-file executable instead of onedir.")
    parser.add_argument("--console", action="store_true", help="Show a console window for desktop debugging.")
    parser.add_argument("--no-clean", action="store_true", help="Reuse previous PyInstaller work directories.")
    parser.add_argument("--archive", action="store_true", help="Zip the built desktop payload after PyInstaller completes.")
    parser.add_argument("--build-installer", action="store_true", help="Compile a Windows Setup.exe with Inno Setup after PyInstaller finishes.")
    parser.add_argument("--installer-script", default="installer/TeamMindHub.iss")
    parser.add_argument("--installer-basename", default=DEFAULT_INSTALLER_BASENAME)
    parser.add_argument("--iscc-path", default="")
    parser.add_argument("--ollama-exe-path", default="")
    parser.add_argument("--print-command", action="store_true", help="Print the resolved PyInstaller command only.")
    parser.add_argument("--print-installer-command", action="store_true", help="Print the resolved Inno Setup command only.")
    return parser.parse_args(argv)


def create_build_plan(
    *,
    project_root: Path,
    frontend_index: Path,
    build_root: Path,
    app_name: str = DEFAULT_APP_NAME,
    onefile: bool = False,
    windowed: bool = True,
    clean: bool = True,
) -> DesktopBuildPlan:
    build_root.mkdir(parents=True, exist_ok=True)
    staged_frontend_root = stage_frontend_bundle(frontend_index, build_root / "bundle")
    dist_dir = build_root / "dist"
    work_dir = build_root / "work"
    spec_dir = build_root / "spec"
    entry_script = project_root / "app" / "desktop" / "main.py"
    if not entry_script.exists():
        raise AppError(
            "ERR_DESKTOP_BUILD",
            "Desktop build failed",
            f"Desktop entry script was not found: {entry_script}",
            400,
        )
    for path in (dist_dir, work_dir, spec_dir):
        path.mkdir(parents=True, exist_ok=True)
    return DesktopBuildPlan(
        app_name=app_name,
        entry_script=entry_script,
        frontend_index=staged_frontend_root / "index.html",
        staged_frontend_root=staged_frontend_root,
        build_root=build_root,
        dist_dir=dist_dir,
        work_dir=work_dir,
        spec_dir=spec_dir,
        onefile=onefile,
        windowed=windowed,
        clean=clean,
    )


def stage_frontend_bundle(frontend_index: Path, bundle_root: Path) -> Path:
    source_root = frontend_index.parent
    target_root = bundle_root / "frontend" / "dist"
    if target_root.exists():
        shutil.rmtree(target_root, ignore_errors=True)
    target_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_root, target_root)
    return target_root


def build_pyinstaller_args(plan: DesktopBuildPlan) -> list[str]:
    args = [
        "--noconfirm",
        "--name",
        plan.app_name,
        "--distpath",
        str(plan.dist_dir),
        "--workpath",
        str(plan.work_dir),
        "--specpath",
        str(plan.spec_dir),
        "--collect-submodules",
        "webview",
        "--collect-data",
        "webview",
        "--add-data",
        format_add_data(plan.staged_frontend_root, "frontend/dist"),
    ]
    if plan.clean:
        args.append("--clean")
    if plan.windowed:
        args.append("--windowed")
    if plan.onefile:
        args.append("--onefile")
    args.append(str(plan.entry_script))
    return args


def run_pyinstaller(plan: DesktopBuildPlan) -> None:
    try:
        from PyInstaller.__main__ import run as pyinstaller_run
    except ModuleNotFoundError as exc:
        raise AppError(
            "ERR_DESKTOP_BUILD",
            "Desktop build failed",
            "PyInstaller is not installed. Install desktop build tooling with `pip install -e .[desktop-build]`.",
            500,
        ) from exc
    pyinstaller_run(build_pyinstaller_args(plan))


def finalize_release(plan: DesktopBuildPlan, archive: bool) -> tuple[Path, Path, Path | None]:
    bundle_path = resolve_built_bundle_path(plan)
    manifest_path = write_release_manifest(plan, bundle_path)
    archive_path = archive_release_bundle(plan, bundle_path) if archive else None
    return bundle_path, manifest_path, archive_path


def resolve_built_bundle_path(plan: DesktopBuildPlan) -> Path:
    if plan.onefile:
        suffix = ".exe" if os.name == "nt" else ""
        bundle_path = plan.dist_dir / f"{plan.app_name}{suffix}"
    else:
        bundle_path = plan.dist_dir / plan.app_name
    if not bundle_path.exists():
        raise AppError(
            "ERR_DESKTOP_BUILD",
            "Desktop build failed",
            f"Expected packaged output was not found: {bundle_path}",
            500,
        )
    return bundle_path


def write_release_manifest(plan: DesktopBuildPlan, bundle_path: Path) -> Path:
    manifest_dir = plan.build_root / "release"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / "manifest.json"
    payload = {
        "app_name": plan.app_name,
        "version": resolve_project_version(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "build": {
            "onefile": plan.onefile,
            "windowed": plan.windowed,
            "entry_script": str(plan.entry_script),
            "bundle_path": str(bundle_path),
            "frontend_index": str(plan.frontend_index),
            "pyinstaller_args": build_pyinstaller_args(plan),
            "ollama_presets": [
                {
                    "key": preset.key,
                    "label": preset.label,
                    "model": preset.model,
                    "description": preset.description,
                    "hardware_hint": preset.hardware_hint,
                }
                for preset in OLLAMA_MODEL_PRESETS
            ],
        },
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def archive_release_bundle(plan: DesktopBuildPlan, bundle_path: Path) -> Path:
    archive_dir = plan.build_root / "release"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_base = archive_dir / f"{plan.app_name}-{platform.system().lower()}-{platform.machine().lower()}"
    if plan.onefile:
        archive_source = bundle_path.parent / bundle_path.stem
        if archive_source.exists():
            shutil.rmtree(archive_source, ignore_errors=True)
        archive_source.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bundle_path, archive_source / bundle_path.name)
        source = archive_source
    else:
        source = bundle_path
    archive_path = shutil.make_archive(str(archive_base), "zip", root_dir=source.parent, base_dir=source.name)
    return Path(archive_path)


def resolve_project_version() -> str:
    try:
        return importlib_metadata.version("teammindhub-backend")
    except importlib_metadata.PackageNotFoundError:
        return "0.1.0"


def format_add_data(source: Path, target: str) -> str:
    return f"{source}{data_separator_for_os_name()}{target}"


def data_separator_for_os_name(os_name: str | None = None) -> str:
    resolved = os_name or os.name
    return ";" if resolved == "nt" else ":"


def _resolve_frontend_index(project_root: Path, index_path: str) -> Path:
    if index_path.strip():
        resolved = Path(index_path).expanduser()
        if not resolved.is_absolute():
            resolved = project_root / resolved
        if resolved.is_dir():
            resolved = resolved / "index.html"
        if not resolved.exists():
            raise AppError(
                "ERR_DESKTOP_BUILD",
                "Desktop build failed",
                f"Provided frontend index path does not exist: {resolved}",
                400,
            )
        return resolved.resolve()
    return ensure_frontend_dist(project_root).resolve()


def update_release_manifest_with_installer(
    manifest_path: Path,
    *,
    installer_path: Path,
    installer_args: list[str],
    ollama_executable: Path | None,
) -> None:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload.setdefault("build", {})
    payload["build"]["installer"] = {
        "path": str(installer_path),
        "args": installer_args,
        "ollama_executable": str(ollama_executable) if ollama_executable is not None else "",
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _resolve_installer_script(project_root: Path, installer_script: str) -> Path:
    resolved = Path(installer_script).expanduser()
    if not resolved.is_absolute():
        resolved = project_root / resolved
    return resolved.resolve()


if __name__ == "__main__":
    main()
