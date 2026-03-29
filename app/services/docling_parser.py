from __future__ import annotations

import importlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.core.tempdir import ensure_temp_root, managed_temp_dir, safe_temp_env


@dataclass(slots=True)
class DeepParseResult:
    text: str
    metadata: dict[str, Any]
    parser_name: str


class DeepDocumentParser(Protocol):
    def parse_to_markdown(self, file_path: Path) -> DeepParseResult:
        ...


class DoclingDocumentParser:
    backend_name = "docling"

    def __init__(
        self,
        command: str = "docling",
        timeout_seconds: float = 120.0,
    ) -> None:
        self.command = command
        self.timeout_seconds = timeout_seconds

    def parse_to_markdown(self, file_path: Path) -> DeepParseResult:
        errors: list[str] = []
        try:
            return self._parse_with_python_api(file_path)
        except Exception as exc:
            errors.append(f"python-api: {exc}")
        try:
            return self._parse_with_cli(file_path)
        except Exception as exc:
            errors.append(f"cli: {exc}")
        raise RuntimeError("; ".join(errors) if errors else "Docling parser unavailable")

    def _parse_with_python_api(self, file_path: Path) -> DeepParseResult:
        module = importlib.import_module("docling.document_converter")
        converter_cls = getattr(module, "DocumentConverter")
        converter = converter_cls()
        result = converter.convert(str(file_path))
        document = getattr(result, "document", None)
        if document is None:
            raise ValueError("Docling conversion did not return a document")
        markdown = document.export_to_markdown()
        if not isinstance(markdown, str) or not markdown.strip():
            raise ValueError("Docling returned empty markdown")
        return DeepParseResult(
            text=markdown.strip(),
            metadata={"docling_method": "python-api"},
            parser_name="docling-python",
        )

    def _parse_with_cli(self, file_path: Path) -> DeepParseResult:
        executable = shutil.which(self.command)
        if executable is None:
            raise FileNotFoundError(f"Docling CLI not found: {self.command}")
        parser_temp_root = ensure_temp_root("parsers", "docling")
        with managed_temp_dir("docling", parser_temp_root) as output_dir:
            subprocess.run(
                [
                    executable,
                    str(file_path),
                    "--to",
                    "md",
                    "--output",
                    str(output_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=safe_temp_env(root=parser_temp_root),
            )
            markdown_path = output_dir / f"{file_path.stem}.md"
            if not markdown_path.exists():
                markdown_files = sorted(output_dir.glob("*.md"))
                if not markdown_files:
                    raise FileNotFoundError("Docling CLI did not produce a markdown file")
                markdown_path = markdown_files[0]
            markdown = markdown_path.read_text(encoding="utf-8")
        if not markdown.strip():
            raise ValueError("Docling CLI returned empty markdown")
        return DeepParseResult(
            text=markdown.strip(),
            metadata={"docling_method": "cli"},
            parser_name="docling-cli",
        )
