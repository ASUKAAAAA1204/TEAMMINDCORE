# TeamMindHub Backend Bootstrap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 从空仓库搭建一个符合 PRD 的 TeamMindHub Backend FastAPI MVP 骨架，并交付首版可工作的本地默认实现。

**Architecture:** 采用 FastAPI + SQLite 的模块化后端结构，先用可运行的本地解析/检索/报告实现打通接口，再通过服务层预留 Docling、RAGFlow、Chroma、Ollama、LangGraph 的后续替换点。统一错误格式、`trace_id`、限流、工具 schema 和 Docker 运行位一并补齐。

**Tech Stack:** Python 3.12, FastAPI, httpx, SQLite, Docker Compose

---

### Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `README.md`

**Step 1: Write the failing test**

定义 `tests/test_app.py`，断言 `/health` 和 `/tools` 可访问。

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_app.py -q`

**Step 3: Write minimal implementation**

补 `app/main.py`、`app/api/router.py` 和基础路由。

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_app.py -q`

**Step 5: Commit**

```bash
git add .
git commit -m "feat: scaffold teammindhub backend"
```

### Task 2: Persistence and Ingestion

**Files:**
- Create: `app/repositories/document_repository.py`
- Create: `app/modules/ingestion/router.py`
- Create: `app/modules/ingestion/schemas.py`

**Step 1: Write the failing test**

定义上传 `.txt` 文件后，可从 `/ingestion/documents` 看到解析结果。

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ingestion.py -q`

**Step 3: Write minimal implementation**

实现 SQLite 文档表、文件沙箱存储、后台解析、文档列表和删除接口。

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_ingestion.py -q`

### Task 3: Retrieval, Report, Analysis and Integration

**Files:**
- Create: `app/services/vector_store.py`
- Create: `app/services/retrieval_service.py`
- Create: `app/services/report_service.py`
- Create: `app/services/analysis_service.py`
- Create: `app/services/merge_service.py`

**Step 1: Write the failing test**

定义上传文本后，`/retrieval/search`、`/report/generate`、`/analysis/execute`、`/integration/merge` 都返回结构化响应。

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_document_flow.py -q`

**Step 3: Write minimal implementation**

实现本地默认解析、混合打分检索、结构化报告、数字提取分析和 Markdown 合并。

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_document_flow.py -q`

### Task 4: Orchestrator and Installer

**Files:**
- Create: `app/services/orchestrator_service.py`
- Create: `app/services/github_service.py`
- Create: `app/services/installer_service.py`
- Create: `app/modules/orchestrator/router.py`
- Create: `app/modules/installer/router.py`

**Step 1: Write the failing test**

定义 `/orchestrator/run` 返回 trace，`/installer/search` 返回 GitHub 搜索结果。

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_orchestrator.py -q`

**Step 3: Write minimal implementation**

实现关键词路由编排、SSE 输出、GitHub 搜索与基础安装流程。

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_orchestrator.py -q`

### Task 5: Verification and Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/plans/2026-03-28-teammindhub-backend-bootstrap.md`
- Create: `tests/conftest.py`

**Step 1: Write the failing test**

验证 `README` 的启动命令和测试命令对应当前工程布局。

**Step 2: Run test to verify it fails**

Run: `pytest -q`

**Step 3: Write minimal implementation**

补充运行说明、已实现范围、未完成差距和验证步骤。

**Step 4: Run test to verify it passes**

Run: `pytest -q`

