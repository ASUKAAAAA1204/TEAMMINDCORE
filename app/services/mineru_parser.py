from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.core.tempdir import ensure_temp_root, managed_temp_dir, safe_temp_env
from app.services.docling_parser import DeepParseResult


class MinerUDocumentParser:
    backend_name = "mineru"

    def __init__(
        self,
        command: str = "mineru",
        method: str = "auto",
        backend: str = "pipeline",
        model_source: str = "huggingface",
        language: str = "ch",
        timeout_seconds: float = 300.0,
    ) -> None:
        self.command = command
        self.method = method
        self.backend = backend
        self.model_source = model_source
        self.language = language
        self.timeout_seconds = timeout_seconds

    def parse_to_markdown(self, file_path: Path) -> DeepParseResult:
        if file_path.suffix.lower() not in {".pdf", ".png", ".jpg", ".jpeg"}:
            raise ValueError(f"MinerU does not support file type {file_path.suffix.lower()}")
        executable = shutil.which(self.command)
        if executable is None:
            raise FileNotFoundError(f"MinerU CLI not found: {self.command}")

        parser_temp_root = ensure_temp_root("parsers", "mineru")
        with managed_temp_dir("mineru", parser_temp_root) as output_dir:
            env = safe_temp_env(root=parser_temp_root)
            env.setdefault("MINERU_MODEL_SOURCE", self.model_source)
            subprocess.run(
                [
                    executable,
                    "-p",
                    str(file_path),
                    "-o",
                    str(output_dir),
                    "-m",
                    self.method,
                    "-b",
                    self.backend,
                    "-l",
                    self.language,
                    "--source",
                    self.model_source,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=env,
            )
            markdown_path = self._find_output_file(output_dir, f"{file_path.stem}.md")
            if markdown_path is None:
                raise FileNotFoundError(f"MinerU did not produce {file_path.stem}.md")
            markdown = markdown_path.read_text(encoding="utf-8")
            if not markdown.strip():
                raise ValueError("MinerU returned empty markdown")
            content_list_path = self._find_output_file(
                output_dir,
                f"{file_path.stem}_content_list.json",
                required=False,
            )
            middle_json_path = self._find_output_file(
                output_dir,
                f"{file_path.stem}_middle.json",
                required=False,
            )
            metadata: dict[str, Any] = {
                "mineru_method": "cli",
                "mineru_parse_method": self.method,
                "mineru_backend": self.backend,
                "mineru_model_source": self.model_source,
                "mineru_language": self.language,
            }
            if content_list_path is not None:
                metadata["mineru_content_list_path"] = str(content_list_path)
                try:
                    content_list = json.loads(content_list_path.read_text(encoding="utf-8"))
                    if isinstance(content_list, list):
                        metadata["mineru_content_items"] = len(content_list)
                except json.JSONDecodeError:
                    pass
            if middle_json_path is not None:
                metadata["mineru_middle_json_path"] = str(middle_json_path)
            return DeepParseResult(
                text=markdown.strip(),
                metadata=metadata,
                parser_name="mineru-cli",
            )

    def _find_output_file(self, output_dir: Path, filename: str, required: bool = True) -> Path | None:
        matches = sorted(output_dir.rglob(filename))
        if matches:
            return matches[0]
        if required:
            raise FileNotFoundError(f"MinerU did not produce {filename}")
        return None
