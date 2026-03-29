from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from app.services.docling_parser import DeepParseResult
from app.services.document_parser import DocumentParserService


class FakeDeepParser:
    def __init__(
        self,
        text: str = "# Parsed by Docling",
        should_fail: bool = False,
        parser_name: str = "docling-fake",
        backend_name: str | None = None,
    ) -> None:
        self.text = text
        self.should_fail = should_fail
        self.parser_name = parser_name
        self.backend_name = backend_name or parser_name.split("-", maxsplit=1)[0]
        self.calls = 0

    def parse_to_markdown(self, file_path: Path) -> DeepParseResult:
        self.calls += 1
        if self.should_fail:
            raise RuntimeError("docling unavailable")
        return DeepParseResult(
            text=self.text,
            metadata={"docling_method": "fake"},
            parser_name=self.parser_name,
        )


def test_document_parser_uses_deep_parser_for_deep_mode() -> None:
    temp_dir = _make_temp_dir()
    try:
        file_path = temp_dir / "sample.pdf"
        file_path.write_bytes(b"%PDF-1.4 fake")
        deep_parser = FakeDeepParser(text="# Docling output\n\nConverted content")
        parser = DocumentParserService(deep_parser=deep_parser, deep_parser_enabled=True)

        result = parser.parse(file_path=file_path, filename=file_path.name, parse_mode="deep")

        assert deep_parser.calls == 1
        assert result.parser_name == "docling-fake"
        assert result.text.startswith("# Docling output")
        assert result.metadata["docling_method"] == "fake"
        assert result.metadata["parser_hint"] == "docling"
    finally:
        _cleanup_dir(temp_dir)


def test_document_parser_falls_back_when_deep_parser_fails() -> None:
    temp_dir = _make_temp_dir()
    try:
        file_path = temp_dir / "sample.pdf"
        file_path.write_bytes(b"%PDF-1.4 fake")
        deep_parser = FakeDeepParser(should_fail=True)
        parser = DocumentParserService(deep_parser=deep_parser, deep_parser_enabled=True)

        result = parser.parse(file_path=file_path, filename=file_path.name, parse_mode="deep")

        assert deep_parser.calls == 1
        assert result.parser_name == "local-binary-fallback"
        assert result.metadata["parser_hint"] == "docling"
        assert "This is the local fallback parser" in result.text
    finally:
        _cleanup_dir(temp_dir)


def test_document_parser_uses_next_deep_parser_when_first_fails() -> None:
    temp_dir = _make_temp_dir()
    try:
        file_path = temp_dir / "sample.pdf"
        file_path.write_bytes(b"%PDF-1.4 fake")
        primary_parser = FakeDeepParser(should_fail=True, parser_name="ragflow-fake")
        secondary_parser = FakeDeepParser(
            text="# Docling fallback\n\nRecovered content",
            parser_name="docling-fake",
        )
        parser = DocumentParserService(
            deep_parsers=[primary_parser, secondary_parser],
            deep_parser_enabled=True,
        )

        result = parser.parse(file_path=file_path, filename=file_path.name, parse_mode="deep")

        assert primary_parser.calls == 1
        assert secondary_parser.calls == 1
        assert result.parser_name == "docling-fake"
        assert result.metadata["parser_hint"] == "docling"
    finally:
        _cleanup_dir(temp_dir)


def _make_temp_dir() -> Path:
    temp_dir = Path(__file__).resolve().parents[1] / ".tmp" / f"parser-{uuid.uuid4().hex[:8]}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def _cleanup_dir(path: Path) -> None:
    for child in sorted(path.rglob("*"), reverse=True):
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    if path.exists():
        path.rmdir()
