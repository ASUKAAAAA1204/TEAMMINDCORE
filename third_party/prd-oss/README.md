# PRD OSS Source Mirror

This directory stores shallow GitHub clones of the open-source projects referenced by the TeamMindHub backend PRD.

Downloaded on: `2026-03-28`

Clone mode:

- `git clone --depth 1`
- TLS backend forced to OpenSSL during download because the default Windows Git HTTPS path was unreliable in this session

Important:

- These repositories are downloaded for local inspection and later integration work.
- Downloaded does **not** mean integrated.
- The current backend runtime still uses local fallback implementations unless replaced in `app/`.

## Repository Lock Table

| Name | Tier | Purpose in PRD | Source | HEAD |
| --- | --- | --- | --- | --- |
| `chroma` | core | Vector database backend | `https://github.com/chroma-core/chroma.git` | `cef9508cc28ba05c53de094e63b9767f3fa70ebc` |
| `ollama` | core | Local model runtime | `https://github.com/ollama/ollama.git` | `9e7cb9697edf3782a0f763dab1a36985ae0ff6a5` |
| `ragflow` | core | Deep document parsing and structured extraction | `https://github.com/infiniflow/ragflow.git` | `cb78ce0a7be479101145ea91a59cb8061d357df6` |
| `docling` | core | Advanced PDF / Office parsing | `https://github.com/docling-project/docling.git` | `f2834848aeaa63ac51f4968e1665b6b8e77b90e4` |
| `llama_index` | core | Hybrid retrieval framework | `https://github.com/run-llama/llama_index.git` | `2fd399b086526cc0de0ab3228b809ca4b09b898c` |
| `langgraph` | core | Stateful orchestrator graph | `https://github.com/langchain-ai/langgraph.git` | `ad17e8b002ed93655ee89219a2208ea367d030c5` |
| `MinerU` | optional | Complex PDF extraction | `https://github.com/opendatalab/MinerU.git` | `61248e2ec9ed1a8b3cac2ef43b775c6e8b916d8c` |
| `RAG-Anything` | optional | Multimodal unified RAG | `https://github.com/HKUDS/RAG-Anything.git` | `0bc623641a34eccc35df169aef63db99664959ff` |
| `crewAI` | reference | Multi-role agent collaboration reference | `https://github.com/crewAIInc/crewAI.git` | `e21c50621496d4ad86eb2f3b3b8c08170b2eaf67` |
| `storm` | reference | Long-form multi-source report generation reference | `https://github.com/stanford-oval/storm.git` | `fb951af7744dab086e34962e9bc6fe878e145f83` |

## Recommended Integration Order

1. `chroma`
2. `ollama`
3. `docling`
4. `llama_index`
5. `langgraph`
6. `ragflow`

## Suggested Use

- Read local source first from this directory during integration work.
- Keep runtime adapters in `app/services/` or a new integration layer under `app/modules/`.
- Do not copy foreign source into `app/` blindly; integrate through explicit adapters and tests.
