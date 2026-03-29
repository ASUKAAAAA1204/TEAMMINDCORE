from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from importlib import util as importlib_util
from pathlib import Path

from app.core.config import Settings
from app.desktop.installer import find_iscc_executable, find_ollama_executable
from app.desktop.main import resolve_app_base_dir, resolve_project_root


@dataclass(slots=True)
class DoctorCheck:
    name: str
    ok: bool
    details: str


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Inspect the TeamMindHub desktop runtime environment.")
    parser.add_argument("--json", action="store_true", help="Print results as JSON.")
    args = parser.parse_args(argv)

    report = run_doctor()
    if args.json:
        print(json.dumps([asdict(item) for item in report], ensure_ascii=False, indent=2))
        return
    for item in report:
        status = "OK" if item.ok else "FAIL"
        print(f"[{status}] {item.name}: {item.details}")


def run_doctor() -> list[DoctorCheck]:
    project_root = resolve_project_root()
    app_base_dir = resolve_app_base_dir()
    frontend_dir = project_root / "frontend"
    frontend_dist_index = frontend_dir / "dist" / "index.html"
    settings = Settings.from_env()
    iscc_path = find_iscc_executable()
    ollama_path = find_ollama_executable()
    return [
        DoctorCheck("project_root", project_root.exists(), str(project_root)),
        DoctorCheck("app_base_dir", True, str(app_base_dir)),
        DoctorCheck("pywebview", importlib_util.find_spec("webview") is not None, "Python package 'webview' import availability"),
        DoctorCheck("pyinstaller", importlib_util.find_spec("PyInstaller") is not None, "Python package 'PyInstaller' import availability"),
        DoctorCheck("iscc", iscc_path is not None, str(iscc_path or "ISCC.exe not found")),
        DoctorCheck("ollama_executable", ollama_path is not None, str(ollama_path or "Ollama executable not found")),
        DoctorCheck("node", shutil.which("node") is not None, "Node.js executable availability"),
        DoctorCheck("npm", _resolve_npm_command() is not None, "npm executable availability"),
        DoctorCheck("frontend_package", (frontend_dir / "package.json").exists(), str(frontend_dir / "package.json")),
        DoctorCheck("frontend_dist", frontend_dist_index.exists(), str(frontend_dist_index)),
        DoctorCheck("data_dir", settings.data_dir.exists() or settings.base_dir.exists(), str(settings.data_dir)),
    ]


def _resolve_npm_command() -> str | None:
    for candidate in ("npm.cmd", "npm"):
        if shutil.which(candidate):
            return candidate
    return None


if __name__ == "__main__":
    main()
