from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ[key] = value


def _load_local_env_defaults(base_dir: Path) -> None:
    for filename in (".env", ".env.local"):
        _load_env_file(base_dir / filename)


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    return int(value)


@dataclass(slots=True)
class Settings:
    app_name: str
    base_dir: Path
    data_dir: Path
    uploads_dir: Path
    tools_dir: Path
    sqlite_path: Path
    host: str
    port: int
    rate_limit_per_minute: int
    main_orchestrator: str
    available_agents: tuple[str, ...]
    vector_store_backend: str
    chroma_host: str
    chroma_port: int
    chroma_tenant: str
    chroma_database: str
    chroma_collection_name: str
    chroma_timeout_seconds: float
    ragflow_enabled: bool
    ragflow_base_url: str
    ragflow_api_key: str
    ragflow_dataset_name: str
    ragflow_chunk_method: str
    ragflow_cleanup_documents: bool
    mineru_enabled: bool
    mineru_command: str
    mineru_method: str
    mineru_backend: str
    mineru_model_source: str
    mineru_language: str
    mineru_timeout_seconds: float
    docling_enabled: bool
    docling_command: str
    docling_timeout_seconds: float
    llamaindex_enabled: bool
    langgraph_enabled: bool
    ollama_base_url: str
    ollama_model: str
    ollama_timeout_seconds: float
    github_api_base: str
    installer_clone_mode: str
    debug: bool

    @classmethod
    def from_env(cls) -> "Settings":
        base_dir = Path(os.getenv("APP_BASE_DIR", PROJECT_ROOT))
        _load_local_env_defaults(base_dir)
        data_dir = base_dir / "data"
        uploads_dir = data_dir / "uploads"
        tools_dir = data_dir / "tools"
        sqlite_path = data_dir / "teammindhub.db"
        raw_agents = os.getenv(
            "AVAILABLE_AGENTS",
            "qwen_orchestrator,local_llama,deepseek_researcher",
        )
        agents = tuple(item.strip() for item in raw_agents.split(",") if item.strip())
        return cls(
            app_name=os.getenv("APP_NAME", "TeamMindHub Backend"),
            base_dir=base_dir,
            data_dir=data_dir,
            uploads_dir=uploads_dir,
            tools_dir=tools_dir,
            sqlite_path=sqlite_path,
            host=os.getenv("HOST", "0.0.0.0"),
            port=_parse_int(os.getenv("PORT"), 8000),
            rate_limit_per_minute=_parse_int(os.getenv("RATE_LIMIT_PER_MINUTE"), 120),
            main_orchestrator=os.getenv("MAIN_ORCHESTRATOR", "qwen_orchestrator"),
            available_agents=agents,
            vector_store_backend=os.getenv("VECTOR_STORE_BACKEND", "auto"),
            chroma_host=os.getenv("CHROMA_HOST", "chroma"),
            chroma_port=_parse_int(os.getenv("CHROMA_PORT"), 8000),
            chroma_tenant=os.getenv("CHROMA_TENANT", "default_tenant"),
            chroma_database=os.getenv("CHROMA_DATABASE", "default_database"),
            chroma_collection_name=os.getenv("CHROMA_COLLECTION_NAME", "teammindhub_chunks"),
            chroma_timeout_seconds=float(os.getenv("CHROMA_TIMEOUT_SECONDS", "5.0")),
            ragflow_enabled=_parse_bool(os.getenv("RAGFLOW_ENABLED"), False),
            ragflow_base_url=os.getenv("RAGFLOW_BASE_URL", "http://ragflow:9380"),
            ragflow_api_key=os.getenv("RAGFLOW_API_KEY", ""),
            ragflow_dataset_name=os.getenv("RAGFLOW_DATASET_NAME", "teammindhub_deep_parse"),
            ragflow_chunk_method=os.getenv("RAGFLOW_CHUNK_METHOD", "naive"),
            ragflow_cleanup_documents=_parse_bool(os.getenv("RAGFLOW_CLEANUP_DOCUMENTS"), True),
            mineru_enabled=_parse_bool(os.getenv("MINERU_ENABLED"), False),
            mineru_command=os.getenv("MINERU_COMMAND", "mineru"),
            mineru_method=os.getenv("MINERU_METHOD", "auto"),
            mineru_backend=os.getenv("MINERU_BACKEND", "pipeline"),
            mineru_model_source=os.getenv("MINERU_MODEL_SOURCE", "huggingface"),
            mineru_language=os.getenv("MINERU_LANGUAGE", "ch"),
            mineru_timeout_seconds=float(os.getenv("MINERU_TIMEOUT_SECONDS", "300.0")),
            docling_enabled=_parse_bool(os.getenv("DOCLING_ENABLED"), True),
            docling_command=os.getenv("DOCLING_COMMAND", "docling"),
            docling_timeout_seconds=float(os.getenv("DOCLING_TIMEOUT_SECONDS", "120.0")),
            llamaindex_enabled=_parse_bool(os.getenv("LLAMAINDEX_ENABLED"), True),
            langgraph_enabled=_parse_bool(os.getenv("LANGGRAPH_ENABLED"), True),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "deepseek-r1:8b"),
            ollama_timeout_seconds=float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "30.0")),
            github_api_base=os.getenv("GITHUB_API_BASE", "https://api.github.com"),
            installer_clone_mode=os.getenv("INSTALLER_CLONE_MODE", "clone"),
            debug=_parse_bool(os.getenv("DEBUG"), False),
        )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.tools_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings.from_env()
    settings.ensure_directories()
    return settings
