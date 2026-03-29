from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Mapping

from app.core.errors import AppError

if TYPE_CHECKING:
    from app.desktop.build import DesktopBuildPlan


DEFAULT_INSTALLER_BASENAME = "TeamMindHub-Setup"


@dataclass(frozen=True, slots=True)
class OllamaModelPreset:
    key: str
    label: str
    model: str
    description: str
    hardware_hint: str


@dataclass(slots=True)
class WindowsInstallerPlan:
    app_name: str
    app_version: str
    project_root: Path
    script_path: Path
    source_dir: Path
    output_dir: Path
    output_basename: str
    iscc_path: Path
    app_executable_name: str
    ollama_executable: Path | None


OLLAMA_MODEL_PRESETS: tuple[OllamaModelPreset, ...] = (
    OllamaModelPreset(
        key="lightweight",
        label="lightweight",
        model="llama3.2:3b",
        description="Lower resource usage for entry-level laptops and compact PCs.",
        hardware_hint="Recommended for 8GB RAM and above",
    ),
    OllamaModelPreset(
        key="standard",
        label="standard",
        model="deepseek-r1:8b",
        description="Balanced default tier for most desktop deployments.",
        hardware_hint="Recommended for 16GB RAM",
    ),
    OllamaModelPreset(
        key="high_performance",
        label="high_performance",
        model="deepseek-r1:14b",
        description="Higher quality reasoning with heavier download and runtime cost.",
        hardware_hint="Recommended for 24GB RAM or more",
    ),
)


def find_iscc_executable(
    custom_path: str | Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> Path | None:
    env_map = dict(os.environ if env is None else env)
    candidates = [
        _normalize_candidate(custom_path),
        _normalize_candidate(env_map.get("TMH_ISCC_PATH", "")),
        _which_path("ISCC.exe"),
        _which_path("ISCC"),
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 5\ISCC.exe"),
    ]
    return _first_existing_path(candidates)


def resolve_iscc_executable(
    custom_path: str | Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> Path:
    resolved = find_iscc_executable(custom_path, env=env)
    if resolved is not None:
        return resolved
    raise AppError(
        "ERR_DESKTOP_INSTALLER",
        "Installer build failed",
        (
            "Inno Setup compiler `ISCC.exe` was not found. "
            "Install Inno Setup 6 or set TMH_ISCC_PATH to the compiler path."
        ),
        500,
    )


def find_ollama_executable(
    custom_path: str | Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> Path | None:
    env_map = dict(os.environ if env is None else env)
    local_app_data = Path(env_map.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    program_files = Path(env_map.get("ProgramFiles", r"C:\Program Files"))
    program_files_x86 = Path(env_map.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    candidates = [
        _normalize_candidate(custom_path),
        _normalize_candidate(env_map.get("TMH_OLLAMA_EXE_PATH", "")),
        _which_path("ollama.exe"),
        _which_path("ollama"),
        local_app_data / "Programs" / "Ollama" / "ollama.exe",
        local_app_data / "Programs" / "Ollama" / "ollama app.exe",
        program_files / "Ollama" / "ollama.exe",
        program_files_x86 / "Ollama" / "ollama.exe",
    ]
    return _first_existing_path(candidates)


def create_windows_installer_plan(
    desktop_plan: "DesktopBuildPlan",
    *,
    script_path: Path,
    iscc_path: str | Path | None = None,
    output_dir: Path | None = None,
    output_basename: str = DEFAULT_INSTALLER_BASENAME,
    ollama_executable: str | Path | None = None,
    require_source_dir: bool = True,
) -> WindowsInstallerPlan:
    if desktop_plan.onefile:
        raise AppError(
            "ERR_DESKTOP_INSTALLER",
            "Installer build failed",
            "Windows installer generation only supports onedir desktop builds.",
            400,
        )
    source_dir = desktop_plan.dist_dir / desktop_plan.app_name
    if require_source_dir and not source_dir.exists():
        raise AppError(
            "ERR_DESKTOP_INSTALLER",
            "Installer build failed",
            f"Packaged desktop directory does not exist yet: {source_dir}",
            500,
        )
    resolved_script_path = script_path.resolve()
    if not resolved_script_path.exists():
        raise AppError(
            "ERR_DESKTOP_INSTALLER",
            "Installer build failed",
            f"Inno Setup script was not found: {resolved_script_path}",
            400,
        )
    installer_output_dir = (output_dir or (desktop_plan.build_root / "release")).resolve()
    installer_output_dir.mkdir(parents=True, exist_ok=True)
    configured_ollama_executable = _normalize_candidate(ollama_executable)
    return WindowsInstallerPlan(
        app_name=desktop_plan.app_name,
        app_version=resolve_project_version(),
        project_root=desktop_plan.entry_script.parents[2],
        script_path=resolved_script_path,
        source_dir=source_dir.resolve(),
        output_dir=installer_output_dir,
        output_basename=output_basename,
        iscc_path=resolve_iscc_executable(iscc_path),
        app_executable_name=f"{desktop_plan.app_name}.exe",
        ollama_executable=configured_ollama_executable or find_ollama_executable(),
    )


def build_iscc_args(plan: WindowsInstallerPlan) -> list[str]:
    ollama_executable = str(plan.ollama_executable) if plan.ollama_executable is not None else ""
    return [
        str(plan.iscc_path),
        str(plan.script_path),
        f"/DMyAppName={plan.app_name}",
        f"/DMyAppVersion={plan.app_version}",
        f"/DMyAppExeName={plan.app_executable_name}",
        f"/DSourceDir={plan.source_dir}",
        f"/DBuildOutputDir={plan.output_dir}",
        f"/DBuildOutputBaseFilename={plan.output_basename}",
        f"/DOllamaExecutable={ollama_executable}",
        f"/DProjectRoot={plan.project_root}",
    ]


def resolve_built_installer_path(plan: WindowsInstallerPlan) -> Path:
    return plan.output_dir / f"{plan.output_basename}.exe"


def run_inno_setup(plan: WindowsInstallerPlan) -> Path:
    result = subprocess.run(
        build_iscc_args(plan),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or "ISCC exited with a non-zero code."
        raise AppError(
            "ERR_DESKTOP_INSTALLER",
            "Installer build failed",
            details,
            500,
        )
    built_installer = resolve_built_installer_path(plan)
    if not built_installer.exists():
        raise AppError(
            "ERR_DESKTOP_INSTALLER",
            "Installer build failed",
            f"Inno Setup completed but the installer was not found: {built_installer}",
            500,
        )
    return built_installer


def _normalize_candidate(candidate: str | Path | None) -> Path | None:
    if candidate is None:
        return None
    text = str(candidate).strip()
    if not text:
        return None
    return Path(text).expanduser()


def _which_path(command: str) -> Path | None:
    resolved = shutil.which(command)
    return Path(resolved).resolve() if resolved else None


def _first_existing_path(candidates: list[Path | None]) -> Path | None:
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate is None:
            continue
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        try:
            if resolved.exists():
                return resolved
        except OSError:
            continue
    return None


def resolve_project_version() -> str:
    try:
        return importlib_metadata.version("teammindhub-backend")
    except importlib_metadata.PackageNotFoundError:
        return "0.1.0"
