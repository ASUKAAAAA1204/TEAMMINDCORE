from __future__ import annotations

import os
import sys
from pathlib import Path

from app.core.config import Settings
from app.core.errors import AppError
from app.desktop.assets import ensure_frontend_dist
from app.desktop.bridge import DesktopBridge
from app.runtime import create_runtime


def main() -> None:
    try:
        import webview
    except ModuleNotFoundError as exc:
        raise AppError(
            "ERR_DESKTOP",
            "Desktop startup failed",
            "pywebview is not installed in the current Python environment",
            500,
        ) from exc
    project_root = resolve_project_root()
    app_base_dir = resolve_app_base_dir()
    storage_dir = resolve_webview_storage_dir(app_base_dir, project_root)
    os.environ.setdefault("APP_BASE_DIR", str(app_base_dir))
    runtime = create_runtime(Settings.from_env())
    index_path = ensure_frontend_dist(project_root)
    bridge = DesktopBridge(runtime)
    webview.create_window(
        runtime.settings.app_name.replace("Backend", "Desktop"),
        url=index_path.resolve().as_uri(),
        js_api=bridge,
        width=1480,
        height=960,
        min_size=(1180, 760),
    )
    try:
        webview.start(
            debug=runtime.settings.debug,
            private_mode=False,
            storage_path=str(storage_dir),
        )
    except Exception as exc:
        raise AppError(
            "ERR_DESKTOP",
            "Desktop startup failed",
            (
                "Embedded WebView failed to initialize.\n"
                f"Storage path: {storage_dir}\n"
                f"Reason: {exc}\n\n"
                "Recommended actions:\n"
                "1. Repair or reinstall Microsoft Edge WebView2 Runtime.\n"
                "2. Close all TeamMindHub windows and retry.\n"
                "3. If the issue persists, delete the TeamMindHub WebView cache directory and relaunch."
            ),
            500,
        ) from exc


def resolve_project_root() -> Path:
    override = os.getenv("TMH_DESKTOP_PROJECT_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    if getattr(sys, "frozen", False):
        executable_root = Path(sys.executable).resolve().parent
        if (executable_root / "frontend").exists():
            return executable_root
        bundle_root = Path(getattr(sys, "_MEIPASS", executable_root)).resolve()
        if (bundle_root / "frontend").exists():
            return bundle_root
        return bundle_root
    return Path(__file__).resolve().parents[2]


def resolve_app_base_dir() -> Path:
    if os.name == "nt":
        root = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "TeamMindHub"


def resolve_webview_storage_dir(app_base_dir: Path, project_root: Path | None = None) -> Path:
    candidates: list[Path] = [app_base_dir / "webview"]
    if project_root is not None:
        candidates.append(project_root / ".tmp" / "desktop-webview")
    candidates.append(Path.cwd() / ".tmp" / "desktop-webview")

    errors: list[str] = []
    seen: set[Path] = set()
    for storage_dir in candidates:
        resolved = storage_dir.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        try:
            resolved.mkdir(parents=True, exist_ok=True)
            return resolved
        except OSError as exc:
            errors.append(f"{resolved}: {exc}")

    raise AppError(
        "ERR_DESKTOP",
        "Desktop startup failed",
        "Unable to create a writable WebView storage directory.\n" + "\n".join(errors),
        500,
    )


if __name__ == "__main__":
    main()
