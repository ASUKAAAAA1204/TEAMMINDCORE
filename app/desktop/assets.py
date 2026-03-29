from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from app.core.errors import AppError


def ensure_frontend_dist(project_root: Path) -> Path:
    override_path = _resolve_index_override()
    if override_path is not None:
        return override_path
    frontend_dir = project_root / "frontend"
    if not frontend_dir.exists():
        raise AppError(
            "ERR_DESKTOP",
            "Desktop startup failed",
            f"frontend directory was not found at {frontend_dir}",
            500,
        )
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        raise AppError(
            "ERR_DESKTOP",
            "Desktop startup failed",
            f"frontend package.json was not found at {package_json}",
            500,
        )
    dist_dir = frontend_dir / "dist"
    index_path = dist_dir / "index.html"
    if index_path.exists():
        esbuild_command = _resolve_esbuild_command(frontend_dir)
        if not _has_desktop_bundle(dist_dir) and esbuild_command is not None:
            _build_frontend_with_esbuild(frontend_dir, dist_dir, esbuild_command)
        _normalize_existing_desktop_dist(frontend_dir, dist_dir, index_path)
        return index_path
    npm_command = _resolve_npm_command()
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        if npm_command is None:
            raise AppError(
                "ERR_DESKTOP",
                "Desktop startup failed",
                "No prebuilt desktop UI was found, node_modules is missing, and npm is unavailable. Install Node.js/npm "
                "or set TMH_DESKTOP_INDEX_PATH to an existing frontend dist/index.html file.",
                500,
            )
        _run_command([npm_command, "install"], frontend_dir)
    esbuild_command = _resolve_esbuild_command(frontend_dir)
    vite_error: str | None = None
    if npm_command is not None:
        try:
            _run_command([npm_command, "run", "build"], frontend_dir)
        except AppError as exc:
            vite_error = str(exc.details or exc.message)
    if not index_path.exists():
        if esbuild_command is None:
            if vite_error is not None:
                raise AppError("ERR_DESKTOP", "Desktop startup failed", vite_error, 500)
            raise AppError(
                "ERR_DESKTOP",
                "Desktop startup failed",
                "No prebuilt desktop UI was found, and neither Vite nor esbuild fallback could be executed.",
                500,
            )
        try:
            _build_frontend_with_esbuild(frontend_dir, dist_dir, esbuild_command)
        except AppError as exc:
            if vite_error is None:
                raise
            raise AppError(
                "ERR_DESKTOP",
                "Desktop startup failed",
                f"Vite build failed:\n{vite_error}\n\nEsbuild fallback failed:\n{exc.details or exc.message}",
                500,
            ) from exc
    if not index_path.exists():
        raise AppError(
            "ERR_DESKTOP",
            "Desktop startup failed",
            f"frontend build completed without producing {index_path}",
            500,
        )
    return index_path


def _resolve_npm_command() -> str | None:
    candidates = ["npm.cmd", "npm"] if os.name == "nt" else ["npm"]
    for candidate in candidates:
        if shutil.which(candidate):
            return candidate
    return None


def _resolve_esbuild_command(frontend_dir: Path) -> str | None:
    candidates = [
        frontend_dir / "node_modules" / ".bin" / ("esbuild.cmd" if os.name == "nt" else "esbuild"),
        frontend_dir / "node_modules" / "esbuild" / "bin" / ("esbuild.exe" if os.name == "nt" else "esbuild"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    for candidate in ("esbuild.cmd", "esbuild"):
        if shutil.which(candidate):
            return candidate
    return None


def _resolve_index_override() -> Path | None:
    raw_path = os.getenv("TMH_DESKTOP_INDEX_PATH", "").strip()
    if not raw_path:
        return None
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    if candidate.is_dir():
        candidate = candidate / "index.html"
    if not candidate.exists():
        raise AppError(
            "ERR_DESKTOP",
            "Desktop startup failed",
            f"TMH_DESKTOP_INDEX_PATH points to a missing file: {candidate}",
            500,
        )
    return candidate


def _build_frontend_with_esbuild(frontend_dir: Path, dist_dir: Path, esbuild_command: str) -> None:
    assets_dir = dist_dir / "assets"
    if dist_dir.exists():
        shutil.rmtree(dist_dir, ignore_errors=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    _run_command(
        [
            esbuild_command,
            "src/main.tsx",
            "--bundle",
            "--jsx=automatic",
            "--format=iife",
            "--platform=browser",
            "--outdir=dist/assets",
            "--entry-names=app",
        ],
        frontend_dir,
    )
    _render_desktop_index(frontend_dir / "index.html", dist_dir / "index.html")


def _render_desktop_index(source_index: Path, target_index: Path) -> None:
    html = source_index.read_text(encoding="utf-8")
    html = html.replace('type="module" src="/src/main.tsx"', 'src="./assets/app.js" defer')
    html = html.replace('src="/src/main.tsx"', 'src="./assets/app.js" defer')
    html = html.replace('type="module" src="./assets/app.js"', 'src="./assets/app.js" defer')
    if "./assets/app.css" not in html:
        html = html.replace("</head>", '    <link rel="stylesheet" href="./assets/app.css" />\n  </head>')
    target_index.write_text(html, encoding="utf-8")


def _normalize_existing_desktop_dist(frontend_dir: Path, dist_dir: Path, index_path: Path) -> None:
    app_bundle = dist_dir / "assets" / "app.js"
    if not app_bundle.exists():
        return
    source_index = frontend_dir / "index.html"
    if not source_index.exists():
        return
    _render_desktop_index(source_index, index_path)


def _has_desktop_bundle(dist_dir: Path) -> bool:
    assets_dir = dist_dir / "assets"
    return (assets_dir / "app.js").exists() and (assets_dir / "app.css").exists()


def _run_command(command: list[str], workdir: Path) -> None:
    try:
        subprocess.run(
            command,
            cwd=workdir,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
    except subprocess.CalledProcessError as exc:
        raise AppError(
            "ERR_DESKTOP",
            "Desktop startup failed",
            _format_command_failure(command, workdir, exc.stderr, exc.stdout),
            500,
        ) from exc
    except Exception as exc:
        raise AppError(
            "ERR_DESKTOP",
            "Desktop startup failed",
            f"Command failed before completion: {' '.join(command)}\nWorking directory: {workdir}\nReason: {exc}",
            500,
        ) from exc


def _format_command_failure(command: list[str], workdir: Path, stderr: str, stdout: str) -> str:
    output = (stderr or "").strip() or (stdout or "").strip() or "No output captured."
    if len(output) > 4000:
        output = output[-4000:]
    return (
        f"Command failed: {' '.join(command)}\n"
        f"Working directory: {workdir}\n"
        f"Captured output:\n{output}\n\n"
        "If the frontend was built elsewhere, set TMH_DESKTOP_INDEX_PATH to the generated index.html."
    )
