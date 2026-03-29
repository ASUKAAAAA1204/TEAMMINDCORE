from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from app.core.errors import AppError
from app.services.docling_parser import DeepDocumentParser


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".xls",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
}

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ParsedDocument:
    text: str
    metadata: dict[str, Any]
    parser_name: str


class DocumentParserService:
    def __init__(
        self,
        deep_parser: DeepDocumentParser | None = None,
        deep_parsers: Iterable[DeepDocumentParser] | None = None,
        deep_parser_enabled: bool = True,
    ) -> None:
        parser_chain = list(deep_parsers or [])
        if deep_parser is not None:
            parser_chain.append(deep_parser)
        self.deep_parsers = parser_chain
        self.deep_parser_enabled = deep_parser_enabled

    def parse(self, file_path: Path, filename: str, parse_mode: str) -> ParsedDocument:
        suffix = file_path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise AppError(
                code="ERR_001",
                message="Document parsing failed",
                details=f"Unsupported file type: {suffix}",
                status_code=400,
            )
        if suffix == ".txt":
            return self._parse_text_file(file_path, parse_mode)
        if parse_mode == "deep":
            deep_result = self._parse_with_deep_parser(file_path, parse_mode)
            if deep_result is not None:
                return deep_result
        return self._parse_binary_file(file_path, filename, parse_mode)

    def _parse_text_file(self, file_path: Path, parse_mode: str) -> ParsedDocument:
        encodings = ("utf-8", "utf-8-sig", "gbk", "gb18030", "latin-1")
        for encoding in encodings:
            try:
                content = file_path.read_text(encoding=encoding)
                metadata = self._build_metadata(file_path, parse_mode, content)
                return ParsedDocument(
                    text=content.strip(),
                    metadata=metadata,
                    parser_name="local-text-parser",
                )
            except UnicodeDecodeError:
                continue
        raise AppError(
            code="ERR_001",
            message="Document parsing failed",
            details="Could not decode text file with supported encodings",
            status_code=400,
        )

    def _parse_binary_file(
        self,
        file_path: Path,
        filename: str,
        parse_mode: str,
    ) -> ParsedDocument:
        size_bytes = file_path.stat().st_size
        parser_hint = self._build_fallback_parser_hint(parse_mode)
        fallback_text = (
            f"Filename: {filename}\n"
            f"Extension: {file_path.suffix.lower()}\n"
            f"Parse mode: {parse_mode}\n"
            f"Suggested parser: {parser_hint}\n"
            f"File size: {size_bytes} bytes\n"
            "This is the local fallback parser. For deep parsing, plug in RAGFlow, MinerU, Docling, or OCR workers."
        )
        metadata = self._build_metadata(file_path, parse_mode, fallback_text)
        metadata["parser_hint"] = parser_hint
        return ParsedDocument(
            text=fallback_text,
            metadata=metadata,
            parser_name="local-binary-fallback",
        )

    def _parse_with_deep_parser(
        self,
        file_path: Path,
        parse_mode: str,
    ) -> ParsedDocument | None:
        if not self.deep_parser_enabled or not self.deep_parsers:
            return None
        for deep_parser in self.deep_parsers:
            try:
                deep_result = deep_parser.parse_to_markdown(file_path)
            except Exception as exc:
                logger.warning("Deep parser %s failed, trying next parser: %s", type(deep_parser).__name__, exc)
                continue
            metadata = self._build_metadata(file_path, parse_mode, deep_result.text)
            metadata.update(deep_result.metadata)
            metadata["parser_hint"] = deep_result.parser_name.split("-", maxsplit=1)[0]
            return ParsedDocument(
                text=deep_result.text,
                metadata=metadata,
                parser_name=deep_result.parser_name,
            )
        return None

    def _build_fallback_parser_hint(self, parse_mode: str) -> str:
        if parse_mode != "deep":
            return "local-fallback"
        parser_names: list[str] = []
        for parser in self.deep_parsers:
            parser_name = getattr(parser, "backend_name", "").strip().lower()
            if not parser_name:
                class_name = type(parser).__name__.lower()
                if "ragflow" in class_name:
                    parser_name = "ragflow"
                elif "mineru" in class_name:
                    parser_name = "mineru"
                elif "docling" in class_name:
                    parser_name = "docling"
                else:
                    parser_name = "deep-parser"
            if parser_name not in parser_names:
                parser_names.append(parser_name)
        return "/".join(parser_names) if parser_names else "local-fallback"

    def _build_metadata(
        self,
        file_path: Path,
        parse_mode: str,
        content: str,
    ) -> dict[str, Any]:
        lines = [line for line in content.splitlines() if line.strip()]
        return {
            "extension": file_path.suffix.lower(),
            "size_bytes": file_path.stat().st_size,
            "parse_mode": parse_mode,
            "pages": max(1, len(lines) // 40 or 1),
            "tables": 1 if "," in content or "\t" in content else 0,
            "images": 1 if file_path.suffix.lower() in {".png", ".jpg", ".jpeg"} else 0,
            "characters": len(content),
        }
