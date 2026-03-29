# TeamMindHub Backend Codex Handoff

Date: 2026-03-28
Workspace: `C:\Users\33671\p2\p2`

## Latest work log

### 2026-03-29 runtime setup hardening, `.env.local` support, and Windows temp-dir workaround

- Updated `app/core/config.py` so native runs now load `.env` and `.env.local` as defaults without overriding existing shell variables.
- Added `.env.local` to `.gitignore`.
- Added a workspace-local `.env.local` with the current verified state:
  - `MINERU_ENABLED=true`
  - `MINERU_COMMAND=C:\Users\33671\p2\p2\.uvenv\Scripts\mineru.exe`
  - `DOCLING_ENABLED=false`
  - `RAGFLOW_ENABLED=false`
- Added `app/cli/runtime_setup.py` and `app/cli/__init__.py`:
  - creates or repairs `.uvenv`
  - bootstraps `pip` without relying on the broken default Windows temp flow
  - prompts for `RAGFLOW_API_KEY` only when RAGFlow is enabled
  - writes `.env.local`
  - probes `Docling` and `MinerU`
- Added `app/core/tempdir.py` and moved parser subprocess temp usage away from `tempfile.TemporaryDirectory`:
  - `app/services/docling_parser.py`
  - `app/services/mineru_parser.py`
- Updated `app/cli/runtime_setup.py` again so core setup installs:
  - base dependencies
  - dev dependencies
  - lightweight OSS dependencies
  while keeping `Docling` as a heavy optional install step handled separately.
- Updated tests:
  - `tests/test_config.py`
  - `tests/test_tempdir.py`
  - `tests/test_mineru_parser.py`
- Updated README with:
  - `.env.local` behavior
  - runtime setup CLI usage
  - Windows temp-dir caveat
  - current native startup commands

Validation:

- `python -m py_compile` on changed runtime and parser files -> passed
- `pytest -q --basetemp C:\Users\33671\p2\p2\.tmp\pytest-run\case` -> `33 passed`

Observed blocker:

- local `Docling` package installation is still not fully verified in this session because long-running install attempts exceed the current tool timeout window
- parser-chain code integration is complete, but live `Docling` and `MinerU` execution still depends on successful local package / CLI installation
- update after verification:
  - `MinerU` is now installed and probeable in `.uvenv`
  - `Docling` is still the only unresolved local parser package

### 2026-03-28 UI production polish, PWA delivery, and documentation sync

- Rebuilt the same-origin TeamMindHub UI into a production-style shell instead of keeping the earlier template remap as-is:
  - refreshed `app/ui/index.html`
  - rewrote `app/ui/app.js`
  - replaced `app/ui/app.css`
- Added installable PWA support:
  - `app/ui/manifest.webmanifest`
  - `app/ui/sw.js`
  - `app/ui/icon.svg`
  - `app/ui/icon-maskable.svg`
- The current UI now includes:
  - theme persistence
  - improved loading and skeleton states
  - offline shell messaging
  - accessibility improvements such as skip-link and stronger ARIA usage
  - SSE-driven orchestrator trace rendering through `/orchestrator/run`
- Expanded `tests/test_app.py` so `/ui/` and the shipped static assets are covered by FastAPI `TestClient`.
- Refreshed `README.md` into a shorter operator-focused guide:
  - documented the verified local environment
  - documented Docker and native Python startup paths
  - clarified that the app reads process environment variables directly and does not auto-load `.env`
  - clarified that `docker compose` already uses `.env.example`

Validation:

- `node --check app/ui/app.js` -> passed
- `pytest -q` -> `29 passed`
- `docker compose config` -> passed

### 2026-03-28 TeamMindHub UI remap and same-origin frontend delivery

- Re-scoped the project from backend-only continuation to a full UI delivery based on the provided template assets under:
  - `C:\Users\33671\p2\ui_project`
- Extracted the Sketch template previously and preserved its core visual shell:
  - `56px` left rail
  - `324px` sidebar
  - light main workspace
  - node-card canvas language
  - lime accent / dark navigation contrast
- Replaced the template's original workflow-management copy and logic with TeamMindHub-native modules:
  - document ingestion
  - hybrid retrieval
  - report generation
  - analysis execution
  - integration merge
  - GitHub installer
  - main orchestrator
  - health observability
- Added a same-origin static UI served directly by FastAPI:
  - `app/ui/index.html`
  - `app/ui/app.css`
  - `app/ui/app.js`
- Updated `app/main.py` to mount the UI at:
  - `/ui`
- The UI now calls real backend endpoints directly on the same origin:
  - `/health`
  - `/tools`
  - `/ingestion/*`
  - `/retrieval/search`
  - `/report/generate`
  - `/analysis/execute`
  - `/integration/merge`
  - `/installer/search`
  - `/installer/install`
  - `/orchestrator/run`
- Also created an initial React/Vite workspace under `frontend/`, but the local Windows environment blocks `esbuild` child-process spawning during the toolchain path.
- Engineering decision for this session:
  - ship the working same-origin FastAPI UI now
  - keep the separate frontend workspace as non-blocking future polish material

Validation:

- `node --check app/ui/app.js` -> passed
- FastAPI `TestClient`:
  - `GET /ui/` -> `200`
  - `GET /health` -> `200`

### 2026-03-28 Ollama task-planning and analysis integration

- Added `app/services/task_planner.py` as a structured task planner that can:
  - ask Ollama for route selection
  - infer report entity
  - infer report type
  - produce an analysis focus string
- Updated `app/services/orchestrator_service.py` so both local orchestration and LangGraph orchestration:
  - build a task plan before execution
  - prefer Ollama planning when configured
  - fall back to the previous heuristic plan on any runtime failure
- Updated `app/services/langgraph_orchestrator.py` to carry the planned entity, report type, and analysis focus through graph state.
- Updated `app/services/analysis_service.py` so:
  - numeric statistics remain deterministic
  - Ollama can optionally produce the analysis summary and chart description
  - failures fall back to the previous deterministic summary
- Updated `/health` to expose:
  - `task_planning_backend`
  - `analysis_generation_backend`
- Aligned the default local Ollama model in:
  - `app/core/config.py`
  - `.env.example`
  - to `deepseek-r1:8b`
- Updated `app/services/ollama_client.py` so a Docker-oriented base URL like `http://ollama:11434` now auto-falls back to `http://localhost:11434` for native local runs.
- Added tests:
  - `tests/test_task_planner.py`
  - `tests/test_analysis_service.py`
  - `tests/test_ollama_client.py`
  - updated `tests/test_orchestrator.py`
  - updated `tests/test_app.py`

Validation:

- `pytest -q` -> `27 passed`
- `npx pyright` -> passed

### 2026-03-28 installer risk assessment alignment

- Updated `app/services/github_service.py` so repository inspection now also captures:
  - `archived`
  - `fork`
  - `open_issues_count`
  - `pushed_at`
- Updated `app/services/installer_service.py` to compute a lightweight repository risk report before registering a tool.
- Persisted that risk report into:
  - the install receipt JSON
  - installed tool metadata in SQLite
- Added endpoint tests:
  - `tests/test_installer.py`
    - confirmation required failure case
    - successful install persists a low-risk report for a healthy MIT repository

Validation:

- `pytest -q` -> `21 passed`
- `npx pyright` -> passed

### 2026-03-28 MinerU parser-chain integration

- Added `app/services/mineru_parser.py` as an optional external `MinerU` CLI adapter.
- Updated `app/services/document_parser.py` so deep parsing is now a parser chain:
  - `RAGFlow` when enabled and configured
  - then `MinerU` when enabled
  - then `Docling`
  - then the previous local fallback parser
- Updated `app/main.py` to wire:
  - `mineru_enabled`
  - `deep_parser_backends`
  - the ordered deep-parser chain
- Added config fields in `app/core/config.py`:
  - `mineru_enabled`
  - `mineru_command`
  - `mineru_method`
  - `mineru_backend`
  - `mineru_model_source`
  - `mineru_language`
  - `mineru_timeout_seconds`
- Updated `.env.example` with the matching `MINERU_*` variables.
- Added tests:
  - `tests/test_mineru_parser.py`
  - updated `tests/test_app.py`
  - updated `tests/test_document_parser.py`
- Kept MinerU outside the default `pyproject.toml` dependency set because the upstream package is `AGPL-3.0`; runtime wiring assumes an explicitly installed external CLI.

Validation:

- `pytest -q` -> `19 passed`
- `npx pyright` -> passed
- `docker compose config` -> passed

### 2026-03-28 RAGFlow deep parsing integration

- Added `app/services/ragflow_parser.py` as a real `ragflow-sdk`-backed deep parsing adapter.
- Updated `app/services/document_parser.py` so deep parsing is now a parser chain:
  - `RAGFlow` when enabled and configured
  - then `Docling`
  - then the previous local fallback parser
- Updated `app/main.py` to wire:
  - `ragflow_enabled`
  - `deep_parser_backends`
  - the ordered deep-parser chain
- Added config fields in `app/core/config.py`:
  - `ragflow_enabled`
  - `ragflow_base_url`
  - `ragflow_api_key`
  - `ragflow_dataset_name`
  - `ragflow_chunk_method`
  - `ragflow_cleanup_documents`
- Updated `.env.example` with the matching `RAGFLOW_*` variables.
- Updated `pyproject.toml` to include:
  - `ragflow-sdk`
- Added tests:
  - `tests/test_ragflow_parser.py`
  - extended `tests/test_document_parser.py` for parser-chain fallback

Validation:

- `pytest -q` -> `17 passed`
- `npx pyright` -> passed
- `docker compose config` -> passed

### 2026-03-28 Python environment brought online

- Resolved the earlier Python blocker by using:
  - `C:\Users\33671\AppData\Roaming\uv\python\cpython-3.12.13-windows-x86_64-none\python.exe`
- Created a project-local runtime environment:
  - `.uvenv`
- Installed the packages needed for local validation and OSS runtime checks.
- The project test suite now runs locally.

Validation:

- `pytest -q` -> `17 passed`

### 2026-03-28 LangGraph orchestrator integration

- Added `app/services/langgraph_orchestrator.py` as a real LangGraph `StateGraph` workflow wrapper.
- Updated `app/services/orchestrator_service.py` so orchestration can:
  - use LangGraph when available
  - fall back to the previous local orchestrator logic on any import or execution failure
- Updated `app/main.py` to wire the LangGraph-enabled orchestrator.
- Added config field in `app/core/config.py`:
  - `langgraph_enabled`
- Updated `.env.example`:
  - `LANGGRAPH_ENABLED=true`
- Updated `/health` to expose:
  - `langgraph_enabled`
  - `orchestrator_backend`

Runtime confirmation in `.uvenv`:

- `/health` returned `orchestrator_backend=langgraph`

### Prior completed work still in place

- `Chroma`: partial runtime integration via HTTP adapter plus local fallback vector store
- `Docling`: partial runtime integration via deep parse adapter with API/CLI fallback
- `LlamaIndex`: partial runtime integration via BM25 keyword retrieval fused into `/retrieval/search`
- `Ollama`: partial runtime integration for task planning, `/report/generate`, and `/analysis/execute`

### 2026-03-28 packaging and install surface update

- Updated `pyproject.toml` to add an `oss` extra for:
  - `docling`
  - `langgraph`
  - `llama-index-core`
  - `llama-index-retrievers-bm25`
- Updated `Dockerfile` to install:
  - `".[oss]"`

This means OSS integration is now represented in the container install path, not only in code.

## Validation performed in this round

- `npx pyright` -> passed
- `pytest -q` -> `27 passed`
- `docker compose config` -> passed
- local `.uvenv` health check -> confirmed:
  - `retrieval_backend=llamaindex+vector`
  - `orchestrator_backend=langgraph`
  - `task_planning_backend=ollama`
  - `analysis_generation_backend=ollama`
  - `report_generation_backend=ollama`

## Validation still incomplete

- Full Docker image build and container boot were not executed in this round.
- Real RAGFlow parsing against a live server was not executed in this round because no API key / running service was configured.
- Real Docling package installation in the current local `.uvenv` failed due a transitive build-permission issue on `pylatexenc`.
- Because of that, real Docling parser execution against the installed package is still not locally verified in this session.

## Current integration verdict

- `Chroma`: partial runtime integration
- `RAGFlow`: partial runtime integration
- `Docling`: partial runtime integration
- `LlamaIndex`: partial runtime integration
- `LangGraph`: partial runtime integration
- `Ollama`: partial runtime integration
- `MinerU`: partial runtime integration
- `RAG-Anything`: deferred for current MVP scope
- `CrewAI`: reference-only
- `Storm`: reference-only

## Current status

The backend is now materially beyond the bootstrap stage.

Runtime-wired PRD components currently include:

- vector database path via `Chroma`
- deep parsing path via `RAGFlow`
- deep parsing path via `MinerU`
- deep parsing path via `Docling`
- retrieval framework participation via `LlamaIndex`
- orchestrator graph path via `LangGraph`
- task planning path via `Ollama`
- report generation path via `Ollama`
- analysis summarization path via `Ollama`

The remaining clear PRD OSS question is `RAG-Anything`, but the current engineering decision is to defer it for MVP because the PRD API surface does not yet require a dedicated multimodal retrieval endpoint beyond the already-wired document parsing and retrieval stack.

## Important runtime behavior

### Deep parsing

Files:

- `app/services/docling_parser.py`
- `app/services/document_parser.py`

Behavior:

- `parse_mode=deep` tries RAGFlow first when it is enabled and configured
- then MinerU when `MINERU_ENABLED=true`
- then Docling Python API
- then Docling CLI
- then the existing local fallback parser

### Retrieval

Files:

- `app/services/llamaindex_retriever.py`
- `app/services/retrieval_service.py`

Behavior:

- dense side remains the existing vector store path
- sparse keyword side is now LlamaIndex BM25
- both paths are fused in `RetrievalService`
- failures fall back to the old vector-store-only behavior

### Orchestration

Files:

- `app/services/langgraph_orchestrator.py`
- `app/services/orchestrator_service.py`

Behavior:

- Ollama can provide a structured task plan before execution
- LangGraph runs the route-driven workflow when available
- failures fall back to the previous local orchestrator logic

### Analysis

Files:

- `app/services/analysis_service.py`

Behavior:

- numeric statistics are still computed locally
- Ollama can optionally generate the final summary and chart description
- failures fall back to the previous deterministic summary builder

### Report generation

Files:

- `app/services/ollama_client.py`
- `app/services/report_service.py`

Behavior:

- `/report/generate` attempts a structured JSON call to Ollama
- invalid or unavailable model responses fall back to the deterministic report builder

## Key files touched in the latest round

- `app/main.py`
- `app/core/config.py`
- `app/services/mineru_parser.py`
- `app/services/ragflow_parser.py`
- `app/services/document_parser.py`
- `app/services/langgraph_orchestrator.py`
- `app/services/orchestrator_service.py`
- `app/services/task_planner.py`
- `app/services/analysis_service.py`
- `pyproject.toml`
- `Dockerfile`
- `.env.example`
- `tests/conftest.py`
- `tests/test_analysis_service.py`
- `tests/test_app.py`
- `tests/test_mineru_parser.py`
- `tests/test_installer.py`
- `tests/test_task_planner.py`
- `README.md`
- `docs/audits/2026-03-28-oss-integration-audit.md`

## Environment notes

### Python

Usable local runtime for validation:

- `C:\Users\33671\AppData\Roaming\uv\python\cpython-3.12.13-windows-x86_64-none\python.exe`
- `.uvenv\Scripts\python.exe`

### Docker

Docker server is available now.

Observed:

- `docker info` succeeded in the user environment
- `docker compose config` also succeeded in this workspace

### Ollama

Observed in the user environment:

- `deepseek-r1:8b` is available

Current `.env.example` and default config now point to:

- `OLLAMA_MODEL=deepseek-r1:8b`

## PRD OSS audit state

Audit file:

- `docs/audits/2026-03-28-oss-integration-audit.md`

High-level verdict:

- partial runtime integration count: `7`
- next recommended major target: validate the external `MinerU` CLI path on real documents, validate `RAGFlow` live, then open a separate track only if the product really needs `RAG-Anything` multimodal retrieval

## Downloaded upstream OSS mirrors

Directory:

- `third_party/prd-oss/`

Included:

- `chroma`
- `ollama`
- `ragflow`
- `docling`
- `MinerU`
- `RAG-Anything`
- `llama_index`
- `langgraph`
- `crewAI`
- `storm`

These mirrors are for source inspection and integration work only. They are not all wired into runtime yet.

## Recommended next engineering step

1. Validate `RAGFlow` against a live server and real documents.
2. Validate `MinerU` against a real local CLI install and representative PDFs.
3. If the product roadmap adds a true multimodal retrieval path, open a dedicated `RAG-Anything` integration track.

## Why this handoff exists

This file is the shortest reliable state transfer for the next Codex, so the next session can continue without re-auditing the same integration work and environment state.
