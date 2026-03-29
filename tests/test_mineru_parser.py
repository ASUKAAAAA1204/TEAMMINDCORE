from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.services.mineru_parser import MinerUDocumentParser


def test_mineru_parser_reads_markdown_and_sidecars(monkeypatch: pytest.MonkeyPatch) -> None:
    temp_dir = _make_temp_dir()
    try:
        file_path = temp_dir / "sample.pdf"
        file_path.write_bytes(b"%PDF-1.4 fake")
        mineru_work_dir = temp_dir / "mineru-work"
        mineru_work_dir.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr("app.services.mineru_parser.shutil.which", lambda _: "mineru")
        monkeypatch.setattr("app.services.mineru_parser.ensure_temp_root", lambda *_: mineru_work_dir)

        def fake_run(command: list[str], **kwargs: object) -> None:
            output_index = command.index("-o") + 1
            output_dir = Path(str(command[output_index]))
            parse_dir = output_dir / "sample" / "auto"
            parse_dir.mkdir(parents=True, exist_ok=True)
            (parse_dir / "sample.md").write_text("# Sample\n\nParsed by MinerU", encoding="utf-8")
            (parse_dir / "sample_content_list.json").write_text('[{"type":"text"},{"type":"table"}]', encoding="utf-8")
            (parse_dir / "sample_middle.json").write_text('{"pdf_info": []}', encoding="utf-8")

        monkeypatch.setattr("app.services.mineru_parser.subprocess.run", fake_run)

        parser = MinerUDocumentParser(
            command="mineru",
            method="auto",
            backend="pipeline",
            model_source="huggingface",
            language="ch",
            timeout_seconds=1.0,
        )

        result = parser.parse_to_markdown(file_path)

        assert result.parser_name == "mineru-cli"
        assert result.text == "# Sample\n\nParsed by MinerU"
        assert result.metadata["mineru_method"] == "cli"
        assert result.metadata["mineru_parse_method"] == "auto"
        assert result.metadata["mineru_backend"] == "pipeline"
        assert result.metadata["mineru_model_source"] == "huggingface"
        assert result.metadata["mineru_content_items"] == 2
        assert result.metadata["mineru_content_list_path"].endswith("sample_content_list.json")
        assert result.metadata["mineru_middle_json_path"].endswith("sample_middle.json")
    finally:
        _cleanup_dir(temp_dir)


def test_mineru_parser_rejects_unsupported_file_types() -> None:
    temp_dir = _make_temp_dir()
    try:
        file_path = temp_dir / "sample.docx"
        file_path.write_bytes(b"fake")
        parser = MinerUDocumentParser()

        with pytest.raises(ValueError, match="does not support file type"):
            parser.parse_to_markdown(file_path)
    finally:
        _cleanup_dir(temp_dir)


def _make_temp_dir() -> Path:
    temp_dir = Path(__file__).resolve().parents[1] / ".tmp" / f"mineru-{uuid.uuid4().hex[:8]}"
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
