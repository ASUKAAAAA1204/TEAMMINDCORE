from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DocumentRecord:
    id: str
    team_id: str
    filename: str
    stored_path: str
    parse_status: str
    upload_time: str
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    extracted_text: str = ""


@dataclass(slots=True)
class ChunkRecord:
    id: str
    document_id: str
    chunk_index: int
    text: str
    vector: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class InstalledToolRecord:
    id: str
    name: str
    repo_url: str
    installed_path: str
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

