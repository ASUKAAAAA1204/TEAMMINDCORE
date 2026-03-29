from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.domain.types import ChunkRecord, DocumentRecord, InstalledToolRecord


class SQLiteDocumentRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    team_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    stored_path TEXT NOT NULL,
                    parse_status TEXT NOT NULL,
                    upload_time TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    extracted_text TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    vector_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS installed_tools (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    repo_url TEXT NOT NULL,
                    installed_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                );
                """
            )

    def save_document(self, record: DocumentRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    id, team_id, filename, stored_path, parse_status,
                    upload_time, tags_json, metadata_json, extracted_text
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.team_id,
                    record.filename,
                    record.stored_path,
                    record.parse_status,
                    record.upload_time,
                    json.dumps(record.tags, ensure_ascii=False),
                    json.dumps(record.metadata, ensure_ascii=False),
                    record.extracted_text,
                ),
            )

    def get_document(self, document_id: str) -> DocumentRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        return self._to_document(row) if row else None

    def get_documents(self, document_ids: list[str]) -> list[DocumentRecord]:
        if not document_ids:
            return []
        placeholders = ",".join("?" for _ in document_ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM documents WHERE id IN ({placeholders})",
                tuple(document_ids),
            ).fetchall()
        return [self._to_document(row) for row in rows]

    def list_documents(
        self,
        team_id: str | None = None,
        keyword: str | None = None,
        tags: list[str] | None = None,
        status: str | None = None,
    ) -> list[DocumentRecord]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM documents").fetchall()
        documents = [self._to_document(row) for row in rows]
        return [
            item
            for item in documents
            if self._matches_document_filter(item, team_id, keyword, tags or [], status)
        ]

    def update_document_processing(
        self,
        document_id: str,
        parse_status: str,
        metadata: dict[str, Any],
        extracted_text: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE documents
                SET parse_status = ?, metadata_json = ?, extracted_text = ?
                WHERE id = ?
                """,
                (
                    parse_status,
                    json.dumps(metadata, ensure_ascii=False),
                    extracted_text,
                    document_id,
                ),
            )

    def delete_document(self, document_id: str) -> DocumentRecord | None:
        record = self.get_document(document_id)
        if record is None:
            return None
        with self._connect() as connection:
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        return record

    def replace_chunks(self, document_id: str, chunks: list[ChunkRecord]) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            connection.executemany(
                """
                INSERT INTO chunks (
                    id, document_id, chunk_index, text, vector_json, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.id,
                        chunk.document_id,
                        chunk.chunk_index,
                        chunk.text,
                        json.dumps(chunk.vector),
                        json.dumps(chunk.metadata, ensure_ascii=False),
                    )
                    for chunk in chunks
                ],
            )

    def list_chunks(self, document_ids: list[str] | None = None) -> list[ChunkRecord]:
        query = "SELECT * FROM chunks"
        params: tuple[Any, ...] = ()
        if document_ids:
            placeholders = ",".join("?" for _ in document_ids)
            query = f"{query} WHERE document_id IN ({placeholders})"
            params = tuple(document_ids)
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._to_chunk(row) for row in rows]

    def save_tool(self, record: InstalledToolRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO installed_tools (
                    id, name, repo_url, installed_path, created_at, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.name,
                    record.repo_url,
                    record.installed_path,
                    record.created_at,
                    json.dumps(record.metadata, ensure_ascii=False),
                ),
            )

    def list_tools(self) -> list[InstalledToolRecord]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM installed_tools").fetchall()
        return [self._to_tool(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _matches_document_filter(
        self,
        record: DocumentRecord,
        team_id: str | None,
        keyword: str | None,
        tags: list[str],
        status: str | None,
    ) -> bool:
        if team_id and record.team_id != team_id:
            return False
        if status and record.parse_status != status:
            return False
        if keyword:
            haystack = f"{record.filename}\n{record.extracted_text}".lower()
            if keyword.lower() not in haystack:
                return False
        if tags and not all(tag in record.tags for tag in tags):
            return False
        return True

    def _to_document(self, row: sqlite3.Row) -> DocumentRecord:
        return DocumentRecord(
            id=row["id"],
            team_id=row["team_id"],
            filename=row["filename"],
            stored_path=row["stored_path"],
            parse_status=row["parse_status"],
            upload_time=row["upload_time"],
            tags=json.loads(row["tags_json"]),
            metadata=json.loads(row["metadata_json"]),
            extracted_text=row["extracted_text"],
        )

    def _to_chunk(self, row: sqlite3.Row) -> ChunkRecord:
        return ChunkRecord(
            id=row["id"],
            document_id=row["document_id"],
            chunk_index=row["chunk_index"],
            text=row["text"],
            vector=json.loads(row["vector_json"]),
            metadata=json.loads(row["metadata_json"]),
        )

    def _to_tool(self, row: sqlite3.Row) -> InstalledToolRecord:
        return InstalledToolRecord(
            id=row["id"],
            name=row["name"],
            repo_url=row["repo_url"],
            installed_path=row["installed_path"],
            created_at=row["created_at"],
            metadata=json.loads(row["metadata_json"]),
        )

