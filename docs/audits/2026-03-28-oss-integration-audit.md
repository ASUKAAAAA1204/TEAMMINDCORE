# 2026-03-28 OSS Integration Audit

## Scope

This audit checks whether the PRD-listed GitHub OSS projects are actually wired into runtime, not merely referenced in docs, Docker, or mirrors.

Compared inputs:

- `TeamMindHub_Backend_PRD_v1-668ab7279f.2.md`
- `app/`
- `tests/`
- `pyproject.toml`
- `docker-compose.yml`
- `.env.example`

## Executive verdict

- Fully integrated: `0`
- Partial / runtime-wired with fallback: `7`
- Placeholder only: `0`
- Missing: `2`
- Reference-only: `2`

Six PRD components now participate in runtime:

- `Chroma` through a real HTTP adapter and fallback vector-store wrapper
- `RAGFlow` through a real SDK-backed deep parsing adapter in the document ingestion path
- `MinerU` through an optional external CLI adapter in the document ingestion path
- `Docling` through real deep parsing for `parse_mode=deep`, with API/CLI fallback logic
- `LlamaIndex` through a real BM25 keyword retriever fused into `/retrieval/search`
- `LangGraph` through a real `StateGraph`-backed orchestrator path
- `Ollama` through a real structured-generation path in `/report/generate`

The remaining PRD stack is still pending.

## Integration matrix

| Component | PRD expectation | Current status | Evidence | Confidence | Next action |
| --- | --- | --- | --- | --- | --- |
| Chroma | Runtime vector database | `partial` | `app/services/vector_store.py`, `app/main.py`, `.env.example`, `tests/test_vector_store.py` | 0.99 | Keep hardening filters, collection lifecycle, and backend observability |
| RAGFlow | Deep parsing and structured extraction pipeline | `partial` | `app/services/ragflow_parser.py`, `app/services/document_parser.py`, `app/main.py`, `.env.example`, `pyproject.toml`, `tests/test_ragflow_parser.py`, `tests/test_document_parser.py` | 0.96 | Validate against a live RAGFlow server and tune dataset/parser settings for the target corpus |
| Docling | Advanced PDF and Office parsing | `partial` | `app/services/docling_parser.py`, `app/services/document_parser.py`, `app/main.py`, `.env.example`, `pyproject.toml`, `Dockerfile`, `tests/test_document_parser.py` | 0.97 | Re-run real parser execution once a local environment can install the full Docling dependency set cleanly |
| LlamaIndex | Hybrid retrieval framework | `partial` | `app/services/llamaindex_retriever.py`, `app/services/retrieval_service.py`, `app/main.py`, `.env.example`, `pyproject.toml`, `Dockerfile`, `tests/test_retrieval_service.py` | 0.98 | Replace custom fusion with richer LlamaIndex multi-retriever orchestration later if needed |
| LangGraph | StateGraph orchestrator | `partial` | `app/services/langgraph_orchestrator.py`, `app/services/orchestrator_service.py`, `app/main.py`, `.env.example`, `pyproject.toml`, `Dockerfile`, `tests/test_orchestrator.py` | 0.99 | Extend the graph with richer conditional routing and persistence if orchestration complexity grows |
| Ollama | Local model runtime | `partial` | `app/services/ollama_client.py`, `app/services/report_service.py`, `app/main.py`, `.env.example`, `tests/test_report_service.py` | 0.99 | Extend beyond report generation into analysis and graph nodes |
| MinerU | Complex PDF extraction | `partial` | `app/services/mineru_parser.py`, `app/services/document_parser.py`, `app/main.py`, `.env.example`, `tests/test_mineru_parser.py`, `tests/test_document_parser.py` | 0.95 | Validate against a real local CLI install and decide whether to keep it external-only because of the upstream AGPL-3.0 license |
| RAG-Anything | Multimodal RAG framework | `missing` | No dependency, config, or runtime path | 0.98 | Keep out of MVP unless multimodal retrieval becomes a hard requirement |
| CrewAI | Multi-role agent collaboration reference | `reference-only` | Not used in runtime | 0.95 | Optional |
| Storm | Long-form multi-source report generation reference | `reference-only` | Not used in runtime; current report generation is bounded JSON section output | 0.96 | Optional after core pipeline is stronger |

## What changed in the latest round

### RAGFlow

RAGFlow is no longer a placeholder.

Current behavior:

- `RAGFLOW_ENABLED=true` plus a configured `RAGFLOW_BASE_URL` and `RAGFLOW_API_KEY` enables a real SDK-backed deep parser
- `parse_mode=deep` now tries `RAGFlow` first, then the optional `MinerU` CLI, then `Docling`, then the previous local fallback parser
- the RAGFlow adapter creates or reuses a dataset, uploads the document, waits for parsing, assembles chunk output, and optionally cleans up uploaded documents afterward
- current health output reports `ragflow_enabled`, `mineru_enabled`, and `deep_parser_backends`

Validation confirmed in this workspace:

- `tests/test_ragflow_parser.py` verifies successful chunk assembly and cleanup behavior
- `tests/test_document_parser.py` verifies parser-chain fallback from a failed primary parser to the next deep parser

### Python runtime and tests

The Python blocker is resolved for local validation.

Current behavior:

- a local `.uvenv` was created with Python 3.12
- the relevant runtime packages for testing were installed there
- the test suite now executes successfully

Validation confirmed:

- `pytest -q` -> `21 passed`

### Installation surface

The OSS integration path is no longer code-only.

Changes:

- `pyproject.toml` now defines an `oss` extra for `ragflow-sdk`, `docling`, `langgraph`, and LlamaIndex runtime packages
- `Dockerfile` now installs `".[oss]"` so the container build path includes the integrated OSS modules

## Local replacements still in use

- Embedding fallback:
  - `app/services/embedding.py`
- Retrieval fusion logic:
  - `app/services/retrieval_service.py`
- Parsing fallback after Docling failure:
  - `app/services/document_parser.py`

## Highest-priority gaps

1. Live RAGFlow connectivity is still unverified because no running RAGFlow server and API key were available in this workspace.
2. Retrieval still relies on deterministic local embeddings instead of model-generated embeddings.
3. Ollama is still only used in report generation, not the wider agent flow.
4. `RAG-Anything` is still not runtime-wired.
5. `MinerU` is intentionally kept out of the default dependency set because the upstream package is `AGPL-3.0`.
6. Docling installation still failed in the current local `.uvenv` because one transitive dependency (`pylatexenc`) hit sandbox build-permission issues.

## Recommended next integration order

1. Validate the external `MinerU` CLI path against a real local install and representative PDFs
2. `RAG-Anything` only if multimodal retrieval becomes a hard product requirement
3. Expand `Ollama` into analysis and LangGraph nodes

## Validation state for this audit

Confirmed in this workspace:

- `npx pyright` -> passed
- `pytest -q` -> `21 passed`
- `docker compose config` -> passed
- `/health` in local `.uvenv` confirmed:
  - `retrieval_backend=llamaindex+vector`
  - `orchestrator_backend=langgraph`
  - `deep_parser_backends=['docling']` under the current default test settings
  - `mineru_enabled=false` under the current default test settings

Not yet confirmed in this workspace:

- full Docker image build and container boot
- successful local MinerU CLI install and a real parse round-trip
- successful local Docling package install
- real Docling parsing against the installed package
- real RAGFlow parsing against a running service

## Bottom line

As of 2026-03-28:

- `Chroma` is partially integrated into the runtime path
- `RAGFlow` is partially integrated into the runtime path
- `MinerU` is partially integrated into the runtime path
- `Docling` is partially integrated into the runtime path
- `LlamaIndex` is partially integrated into the runtime path
- `LangGraph` is partially integrated into the runtime path
- `Ollama` is partially integrated into the runtime path
- `RAG-Anything` is now the remaining clear PRD OSS runtime gap
