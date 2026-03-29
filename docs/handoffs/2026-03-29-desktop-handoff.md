# TeamMindHub Desktop Handoff

Date: 2026-03-29
Workspace: `D:\programss\p2`

## Summary

This round completed the code-side migration from a local HTTP-oriented app to a desktop-first app with:

- in-process Python runtime assembly
- JS/Python desktop bridge
- desktop-first frontend API path
- user-directory data storage
- desktop packaging entrypoint
- desktop diagnostics command
- frontend build fallback that works even when Vite is blocked in this environment

The remaining blockers are environment-only:

- `pywebview` is not installed in the current Python environment
- `PyInstaller` is not installed in the current Python environment

## Latest work log

### 2026-03-29 pure desktop runtime and bridge completion

- Added [`app/runtime.py`](/D:/programss/p2/app/runtime.py) to centralize runtime assembly outside FastAPI.
- Added [`app/modules/ingestion/operations.py`](/D:/programss/p2/app/modules/ingestion/operations.py) to share ingestion logic across HTTP and desktop paths.
- Added desktop runtime modules:
  - [`app/desktop/bridge.py`](/D:/programss/p2/app/desktop/bridge.py)
  - [`app/desktop/main.py`](/D:/programss/p2/app/desktop/main.py)
  - [`app/desktop/assets.py`](/D:/programss/p2/app/desktop/assets.py)
- Updated [`frontend/src/api.ts`](/D:/programss/p2/frontend/src/api.ts) to prefer `window.pywebview` and fall back to HTTP only for compatibility mode.
- Added [`frontend/src/desktop.d.ts`](/D:/programss/p2/frontend/src/desktop.d.ts).
- Updated [`app/core/config.py`](/D:/programss/p2/app/core/config.py) so desktop mode can store data under `APP_BASE_DIR` instead of the repo root.

Validation:

- desktop bridge end-to-end calls succeeded through Python without HTTP
- dedicated tests added and passing

### 2026-03-29 desktop packaging pipeline added

- Added [`app/desktop/build.py`](/D:/programss/p2/app/desktop/build.py) with:
  - PyInstaller build-plan generation
  - frontend staging into package payload
  - release manifest generation
  - optional zip archive generation
- Added project scripts in [`pyproject.toml`](/D:/programss/p2/pyproject.toml):
  - `teammindhub-desktop`
  - `teammindhub-desktop-build`
  - `teammindhub-desktop-doctor`
- Added optional dependency group:
  - `desktop-build = ["pyinstaller>=6.11.0,<7.0.0"]`

Validation:

- build-plan tests added and passing
- `python -m app.desktop.build --print-command --index-path D:\programss\p2\frontend\dist\index.html` succeeded

### 2026-03-29 desktop environment diagnostics added

- Added [`app/desktop/doctor.py`](/D:/programss/p2/app/desktop/doctor.py) to report:
  - project root
  - app base dir
  - `pywebview` availability
  - `PyInstaller` availability
  - Node/npm availability
  - frontend package presence
  - frontend dist presence
  - data directory readiness

Validation:

- `python -m app.desktop.doctor --json` succeeded

Observed result in this environment:

- `pywebview = false`
- `pyinstaller = false`
- `frontend_dist = true`

### 2026-03-29 frontend desktop build fallback added

- Updated [`app/desktop/assets.py`](/D:/programss/p2/app/desktop/assets.py) so desktop startup now:
  1. uses existing `frontend/dist` if present
  2. tries `npm run build`
  3. if Vite fails, falls back to direct `esbuild` bundling
  4. rewrites `frontend/index.html` into a `file://`-safe desktop `dist/index.html`
- Added UTF-8 tolerant subprocess decoding in the same module to avoid Windows console decoding noise.

Why this was needed:

- `npm run build` fails in this environment with Vite/esbuild `spawn EPERM`
- direct `esbuild` execution works

Validation:

- `frontend/dist/index.html` was generated successfully through `ensure_frontend_dist(...)`
- new asset fallback tests added and passing

## Files added in this round

- [`app/desktop/build.py`](/D:/programss/p2/app/desktop/build.py)
- [`app/desktop/doctor.py`](/D:/programss/p2/app/desktop/doctor.py)
- [`tests/test_desktop_bridge.py`](/D:/programss/p2/tests/test_desktop_bridge.py)
- [`tests/test_desktop_assets.py`](/D:/programss/p2/tests/test_desktop_assets.py)
- [`tests/test_desktop_build.py`](/D:/programss/p2/tests/test_desktop_build.py)
- [`tests/test_desktop_doctor.py`](/D:/programss/p2/tests/test_desktop_doctor.py)
- [`docs/handoffs/2026-03-29-desktop-handoff.md`](/D:/programss/p2/docs/handoffs/2026-03-29-desktop-handoff.md)

## Files updated in this round

- [`app/runtime.py`](/D:/programss/p2/app/runtime.py)
- [`app/main.py`](/D:/programss/p2/app/main.py)
- [`app/core/config.py`](/D:/programss/p2/app/core/config.py)
- [`app/modules/ingestion/router.py`](/D:/programss/p2/app/modules/ingestion/router.py)
- [`app/modules/tools/router.py`](/D:/programss/p2/app/modules/tools/router.py)
- [`app/desktop/assets.py`](/D:/programss/p2/app/desktop/assets.py)
- [`app/desktop/main.py`](/D:/programss/p2/app/desktop/main.py)
- [`frontend/src/api.ts`](/D:/programss/p2/frontend/src/api.ts)
- [`frontend/vite.config.ts`](/D:/programss/p2/frontend/vite.config.ts)
- [`pyproject.toml`](/D:/programss/p2/pyproject.toml)
- [`README.md`](/D:/programss/p2/README.md)
- [`desktop-pure-app.md`](/D:/programss/p2/desktop-pure-app.md)
- [`tests/conftest.py`](/D:/programss/p2/tests/conftest.py)

## Validation performed

- `& '.\.uvenv\Scripts\python.exe' -m pytest -q --basetemp D:\programss\p2\.tmp\pytest-all-phase5\case` -> `49 passed`
- `cd frontend && npx tsc -b` -> passed
- `& '.\.uvenv\Scripts\python.exe' -m app.desktop.doctor --json` -> passed
- `& '.\.uvenv\Scripts\python.exe' -m app.desktop.build --print-command --index-path D:\programss\p2\frontend\dist\index.html` -> passed
- `& '.\.uvenv\Scripts\python.exe' -c "from pathlib import Path; from app.desktop.assets import ensure_frontend_dist; print(ensure_frontend_dist(Path(r'D:\programss\p2')))"` -> produced `frontend/dist/index.html`

## Remaining blockers

These are not code gaps anymore:

- `pywebview` installation failed in this environment due temp/permission restrictions
- `PyInstaller` installation could not be completed in this environment
- `uv` CLI is not available in this environment

## Recommended next step

Run these on a machine or environment where Python package installation is permitted:

```powershell
cd D:\programss\p2
.\.uvenv\Scripts\Activate.ps1
python -m pip install -e .[desktop-build]
python -m pip install pywebview
teammindhub-desktop-doctor
teammindhub-desktop-build --archive
teammindhub-desktop
```

Expected goal for the next round:

1. verify real native webview launch
2. verify real PyInstaller packaging
3. decide whether to retire or keep the HTTP compatibility shell
