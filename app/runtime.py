from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings, get_settings
from app.core.container import ServiceContainer
from app.repositories.document_repository import SQLiteDocumentRepository
from app.services.analysis_service import AnalysisService
from app.services.docling_parser import DoclingDocumentParser
from app.services.document_parser import DocumentParserService
from app.services.embedding import DeterministicEmbeddingService
from app.services.github_service import GitHubSearchService
from app.services.installer_service import InstallerService
from app.services.llamaindex_retriever import LlamaIndexKeywordRetriever
from app.services.merge_service import MergeService
from app.services.mineru_parser import MinerUDocumentParser
from app.services.ollama_client import OllamaChatClient, StructuredGenerationClient
from app.services.orchestrator_service import OrchestratorService
from app.services.ragflow_parser import RAGFlowDocumentParser
from app.services.report_service import ReportService
from app.services.retrieval_service import RetrievalService
from app.services.task_planner import TaskPlanningService
from app.services.vector_store import ChromaBackedVectorStore, ChromaHttpClient, LocalVectorStore, VectorStore


@dataclass(slots=True)
class RuntimeContext:
    settings: Settings
    repository: SQLiteDocumentRepository
    container: ServiceContainer
    ragflow_enabled: bool
    deep_parser_backends: list[str]
    generation_client: StructuredGenerationClient | None
    task_planner: TaskPlanningService


def create_runtime(settings: Settings | None = None) -> RuntimeContext:
    resolved_settings = settings or get_settings()
    resolved_settings.ensure_directories()
    repository = SQLiteDocumentRepository(resolved_settings.sqlite_path)
    repository.initialize()
    embedding_service = DeterministicEmbeddingService()
    ragflow_enabled = bool(
        resolved_settings.ragflow_enabled
        and resolved_settings.ragflow_base_url.strip()
        and resolved_settings.ragflow_api_key.strip()
    )
    deep_parsers = []
    deep_parser_backends: list[str] = []
    if ragflow_enabled:
        deep_parsers.append(
            RAGFlowDocumentParser(
                base_url=resolved_settings.ragflow_base_url,
                api_key=resolved_settings.ragflow_api_key,
                dataset_name=resolved_settings.ragflow_dataset_name,
                chunk_method=resolved_settings.ragflow_chunk_method,
                cleanup_documents=resolved_settings.ragflow_cleanup_documents,
            )
        )
        deep_parser_backends.append("ragflow")
    if resolved_settings.mineru_enabled:
        deep_parsers.append(
            MinerUDocumentParser(
                command=resolved_settings.mineru_command,
                method=resolved_settings.mineru_method,
                backend=resolved_settings.mineru_backend,
                model_source=resolved_settings.mineru_model_source,
                language=resolved_settings.mineru_language,
                timeout_seconds=resolved_settings.mineru_timeout_seconds,
            )
        )
        deep_parser_backends.append("mineru")
    if resolved_settings.docling_enabled:
        deep_parsers.append(
            DoclingDocumentParser(
                command=resolved_settings.docling_command,
                timeout_seconds=resolved_settings.docling_timeout_seconds,
            )
        )
        deep_parser_backends.append("docling")
    parser = DocumentParserService(
        deep_parsers=deep_parsers,
        deep_parser_enabled=bool(deep_parsers),
    )
    local_vector_store = LocalVectorStore(repository, embedding_service)
    vector_store: VectorStore = local_vector_store
    if resolved_settings.vector_store_backend != "local":
        chroma_client = ChromaHttpClient(
            base_url=f"{resolved_settings.chroma_host}:{resolved_settings.chroma_port}",
            tenant=resolved_settings.chroma_tenant,
            database=resolved_settings.chroma_database,
            collection_name=resolved_settings.chroma_collection_name,
            timeout_seconds=resolved_settings.chroma_timeout_seconds,
        )
        vector_store = ChromaBackedVectorStore(
            local_store=local_vector_store,
            embedding_service=embedding_service,
            chroma_client=chroma_client,
        )
    retrieval = RetrievalService(
        vector_store,
        keyword_retriever=LlamaIndexKeywordRetriever(repository)
        if resolved_settings.llamaindex_enabled
        else None,
    )
    generation_client: StructuredGenerationClient | None = None
    if resolved_settings.ollama_base_url.strip() and resolved_settings.ollama_model.strip():
        generation_client = OllamaChatClient(
            base_url=resolved_settings.ollama_base_url,
            model=resolved_settings.ollama_model,
            timeout_seconds=resolved_settings.ollama_timeout_seconds,
        )
    report = ReportService(retrieval, generation_client)
    analysis = AnalysisService(repository, generation_client)
    task_planner = TaskPlanningService(generation_client)
    merge = MergeService(repository)
    github = GitHubSearchService(resolved_settings.github_api_base)
    installer = InstallerService(
        repository=repository,
        github_service=github,
        tools_dir=resolved_settings.tools_dir,
        clone_mode=resolved_settings.installer_clone_mode,
    )
    orchestrator = OrchestratorService(
        retrieval_service=retrieval,
        report_service=report,
        analysis_service=analysis,
        installer_service=installer,
        default_agent=resolved_settings.main_orchestrator,
        task_planner=task_planner,
        langgraph_enabled=resolved_settings.langgraph_enabled,
    )
    container = ServiceContainer(
        parser=parser,
        vector_store=vector_store,
        retrieval=retrieval,
        report=report,
        analysis=analysis,
        merge=merge,
        github=github,
        installer=installer,
        orchestrator=orchestrator,
    )
    return RuntimeContext(
        settings=resolved_settings,
        repository=repository,
        container=container,
        ragflow_enabled=ragflow_enabled,
        deep_parser_backends=deep_parser_backends,
        generation_client=generation_client,
        task_planner=task_planner,
    )


def build_health_payload(runtime: RuntimeContext) -> dict[str, object]:
    settings = runtime.settings
    return {
        "status": "ok",
        "database": str(settings.sqlite_path),
        "main_orchestrator": settings.main_orchestrator,
        "available_agents": list(settings.available_agents),
        "vector_store_backend": settings.vector_store_backend,
        "deep_parser_enabled": bool(runtime.deep_parser_backends),
        "deep_parser_backends": runtime.deep_parser_backends,
        "ragflow_enabled": runtime.ragflow_enabled,
        "mineru_enabled": settings.mineru_enabled,
        "llamaindex_enabled": settings.llamaindex_enabled,
        "langgraph_enabled": settings.langgraph_enabled,
        "retrieval_backend": "llamaindex+vector" if settings.llamaindex_enabled else "vector-only",
        "orchestrator_backend": runtime.container.orchestrator.backend_name(),
        "task_planning_backend": runtime.task_planner.backend_name(),
        "analysis_generation_backend": runtime.container.analysis.backend_name(),
        "report_generation_backend": "ollama" if runtime.generation_client is not None else "local",
    }


def build_tools_payload(repository: SQLiteDocumentRepository) -> dict[str, object]:
    installed_tools = repository.list_tools()
    dynamic_tools = [
        {
            "name": item.name,
            "description": f"Installed tool from {item.repo_url}",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        }
        for item in installed_tools
    ]
    return {
        "tools": [
            {
                "name": "retrieval_search",
                "description": "Search indexed knowledge",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer"},
                    },
                },
            },
            {
                "name": "report_generate",
                "description": "Generate a cross-document report",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity": {"type": "string"},
                        "report_type": {"type": "string"},
                    },
                },
            },
            {
                "name": "analysis_execute",
                "description": "Run document analysis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string"},
                        "document_ids": {"type": "array"},
                    },
                },
            },
            *dynamic_tools,
        ]
    }
