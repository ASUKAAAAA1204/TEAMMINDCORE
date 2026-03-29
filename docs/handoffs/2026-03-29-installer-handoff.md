# TeamMindHub Installer Handoff

Date: 2026-03-29
Workspace: `D:\programss\p2`

## Summary

This round completed the Windows desktop installer pipeline on top of the existing desktop-first runtime:

- added Inno Setup packaging support
- added installer-time Ollama model tier selection
- added `.env.local` generation into `%LOCALAPPDATA%\TeamMindHub`
- added GitHub Actions workflow template for release publishing
- compiled a real `Setup.exe` successfully in this workspace

## Completed code changes

### Installer support

- Added [`app/desktop/installer.py`](/D:/programss/p2/app/desktop/installer.py)
  - detects `ISCC.exe`
  - detects or accepts explicit Ollama executable path
  - defines the model presets used by packaging metadata
  - compiles Inno Setup arguments
- Updated [`app/desktop/build.py`](/D:/programss/p2/app/desktop/build.py)
  - new `--build-installer`
  - new `--installer-script`
  - new `--installer-basename`
  - new `--iscc-path`
  - new `--ollama-exe-path`
  - new `--print-installer-command`
  - installer metadata is now written into the release manifest

### Installer UI and runtime configuration

- Added [`installer/TeamMindHub.iss`](/D:/programss/p2/installer/TeamMindHub.iss)
  - installs per-user into `%LOCALAPPDATA%\Programs\TeamMindHub`
  - offers three Ollama tiers:
    - lightweight -> `llama3.2:3b`
    - standard -> `deepseek-r1:8b`
    - high performance -> `deepseek-r1:14b`
  - writes `%LOCALAPPDATA%\TeamMindHub\.env.local`
  - can optionally run `ollama pull <model>` after installation

### Build automation

- Added [`scripts/build_installer.ps1`](/D:/programss/p2/scripts/build_installer.ps1)
- Added [`.github/workflows/release-desktop.yml`](/D:/programss/p2/.github/workflows/release-desktop.yml)

### Diagnostics and tests

- Updated [`app/desktop/doctor.py`](/D:/programss/p2/app/desktop/doctor.py)
  - now reports `iscc`
  - now reports `ollama_executable`
- Added [`tests/test_desktop_installer.py`](/D:/programss/p2/tests/test_desktop_installer.py)
- Updated [`tests/test_desktop_doctor.py`](/D:/programss/p2/tests/test_desktop_doctor.py)
- Updated [`README.md`](/D:/programss/p2/README.md)

## Validation completed

### Test suite

```powershell
& '.\.uvenv\Scripts\python.exe' -m pytest -q tests\test_app.py tests\test_desktop_main.py tests\test_desktop_assets.py tests\test_desktop_bridge.py tests\test_desktop_build.py tests\test_desktop_doctor.py tests\test_desktop_installer.py
```

Result:

- `36 passed`

### Doctor

```powershell
& '.\.uvenv\Scripts\python.exe' -m app.desktop.doctor --json
```

Observed:

- `pywebview = true`
- `pyinstaller = true`
- `iscc = true`
- `frontend_dist = true`

### Real packaging run

```powershell
& '.\.uvenv\Scripts\python.exe' -m app.desktop.build --build-installer --archive --ollama-exe-path "C:\Users\33671\AppData\Local\Programs\Ollama\ollama app.exe"
```

Observed outputs:

- desktop bundle: [`D:\programss\p2\.tmp\desktop-build\dist\TeamMindHub`](/D:/programss/p2/.tmp/desktop-build/dist/TeamMindHub)
- installer: [`D:\programss\p2\.tmp\desktop-build\release\TeamMindHub-Setup.exe`](/D:/programss/p2/.tmp/desktop-build/release/TeamMindHub-Setup.exe)
- archive: [`D:\programss\p2\.tmp\desktop-build\release\TeamMindHub-windows-amd64.zip`](/D:/programss/p2/.tmp/desktop-build/release/TeamMindHub-windows-amd64.zip)
- manifest: [`D:\programss\p2\.tmp\desktop-build\release\manifest.json`](/D:/programss/p2/.tmp/desktop-build/release/manifest.json)

The manifest includes:

- installer path
- explicit Ollama executable path
- model tier metadata

## Remaining external blockers

These are no longer code blockers:

- current workspace is still not a Git repository
- `gh` is still not available on PATH

That means the release workflow file exists, but actual GitHub push/release publication still has to happen from a real repo clone or initialized repo with remote configured.

## Recommended next step

1. Put `D:\programss\p2` under a real Git repository connected to GitHub.
2. Install GitHub CLI if release management from this machine is needed.
3. Commit:
   - installer support
   - workflow
   - README/doc updates
4. Push to GitHub.
5. Trigger the `Release Desktop` workflow or publish a GitHub Release.
