from __future__ import annotations

import base64
import time

import pytest

from app.core.errors import AppError
from app.desktop.bridge import DesktopBridge
from app.runtime import create_runtime


@pytest.fixture()
def desktop_runtime(test_settings):
    runtime = create_runtime(test_settings)
    yield runtime


@pytest.fixture()
def desktop_bridge(desktop_runtime):
    return DesktopBridge(desktop_runtime)


def _encode_text_file(content: str) -> str:
    return base64.b64encode(content.encode("utf-8")).decode("utf-8")


def _upload_document(desktop_bridge: DesktopBridge) -> str:
    response = desktop_bridge.upload_documents(
        {
            "team_id": "default",
            "parse_mode": "auto",
            "tags": ["sales", "2025"],
            "files": [
                {
                    "name": "sales.txt",
                    "content_base64": _encode_text_file("Alice 2025 Q1 sales 500 625 750 900"),
                }
            ],
        }
    )
    assert response["status"] == "processing"
    return response["document_ids"][0]


def _wait_for_document(desktop_bridge: DesktopBridge, document_id: str, timeout_seconds: float = 5.0) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        payload = desktop_bridge.fetch_documents({"page": 1, "page_size": 100})
        for item in payload["documents"]:
            if item["id"] == document_id:
                if item["parse_status"] == "parsed":
                    return item
                break
        time.sleep(0.05)
    raise AssertionError(f"document {document_id} did not reach parsed state")


def test_desktop_bridge_health_tools_and_data_dir(desktop_bridge: DesktopBridge, desktop_runtime) -> None:
    health = desktop_bridge.fetch_health()
    assert health["status"] == "ok"
    assert health["database"] == str(desktop_runtime.settings.sqlite_path)
    assert health["deep_parser_backends"] == ["docling"]
    assert not hasattr(desktop_bridge, "runtime")

    tools = desktop_bridge.fetch_tools()
    tool_names = {item["name"] for item in tools["tools"]}
    assert {"retrieval_search", "report_generate", "analysis_execute"} <= tool_names

    assert desktop_bridge.reveal_data_directory() == str(desktop_runtime.settings.data_dir)


def test_desktop_bridge_upload_list_and_delete_document(desktop_bridge: DesktopBridge) -> None:
    document_id = _upload_document(desktop_bridge)
    document = _wait_for_document(desktop_bridge, document_id)
    assert document["filename"] == "sales.txt"
    assert set(document["tags"]) == {"sales", "2025"}

    filtered = desktop_bridge.fetch_documents({"status": "parsed", "tags": ["sales"]})
    filtered_ids = {item["id"] for item in filtered["documents"]}
    assert document_id in filtered_ids

    deleted = desktop_bridge.delete_document(document_id)
    assert deleted["success"] is True

    remaining = desktop_bridge.fetch_documents({"page": 1, "page_size": 100})
    remaining_ids = {item["id"] for item in remaining["documents"]}
    assert document_id not in remaining_ids


def test_desktop_bridge_upload_rejects_invalid_base64(desktop_bridge: DesktopBridge) -> None:
    with pytest.raises(AppError) as exc_info:
        desktop_bridge.upload_documents(
            {
                "files": [
                    {
                        "name": "broken.txt",
                        "content_base64": "not-valid-base64$$$",
                    }
                ]
            }
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.details == "file content_base64 must be valid base64"


def test_desktop_bridge_fetch_documents_validates_pagination(desktop_bridge: DesktopBridge) -> None:
    with pytest.raises(AppError) as exc_info:
        desktop_bridge.fetch_documents({"page": "abc", "page_size": 100})

    assert exc_info.value.status_code == 422
    assert exc_info.value.details == "page must be an integer"


def test_desktop_bridge_retrieval_report_analysis_merge_and_orchestrator(desktop_bridge: DesktopBridge) -> None:
    document_id = _upload_document(desktop_bridge)
    _wait_for_document(desktop_bridge, document_id)

    retrieval = desktop_bridge.run_retrieval(
        {
            "query": "Alice sales",
            "top_k": 5,
            "hybrid_alpha": 0.7,
            "filters": {"tags": ["sales"]},
        }
    )
    assert retrieval["total_found"] >= 1

    report = desktop_bridge.generate_report(
        {
            "entity": "Alice",
            "report_type": "person_profile",
            "include_sources": True,
            "max_sections": 3,
        }
    )
    assert report["title"].startswith("Alice")

    analysis = desktop_bridge.execute_analysis(
        {
            "task": "Analyze sales trend",
            "document_ids": [document_id],
            "output_format": "json",
        }
    )
    assert "statistics" in analysis["results"]

    merged = desktop_bridge.merge_documents(
        {
            "document_ids": [document_id],
            "rule": {"strategy": "concatenate", "format": "markdown"},
        }
    )
    assert merged["source_count"] == 1

    orchestrator = desktop_bridge.run_orchestrator(
        {
            "task": "Generate Alice sales report and analysis",
            "parameters": {"max_steps": 6, "timeout": 60},
        }
    )
    assert orchestrator["status"] == "completed"
    assert "report" in orchestrator["result"]
    assert "analysis" in orchestrator["result"]

    stream = desktop_bridge.stream_orchestrator(
        {
            "task": "Generate Alice sales report",
            "parameters": {"stream": True},
        }
    )
    event_names = [event["event"] for event in stream["events"]]
    assert "trace" in event_names
    assert "result" in event_names


def test_desktop_bridge_installer_paths(monkeypatch, desktop_bridge: DesktopBridge, desktop_runtime) -> None:
    def fake_inspect_repository(repo_url: str) -> dict[str, object]:
        return {
            "name": "sample-tool",
            "url": repo_url,
            "stars": 42,
            "description": "Desktop installer test repository",
            "license": "MIT",
            "default_branch": "main",
            "archived": False,
            "fork": False,
            "open_issues_count": 1,
            "pushed_at": "2026-03-29T00:00:00+00:00",
        }

    monkeypatch.setattr(desktop_runtime.container.github, "inspect_repository", fake_inspect_repository)
    monkeypatch.setattr(desktop_runtime.container.installer, "_ensure_virtualenv", lambda _: None)

    search = desktop_bridge.search_repositories({"query": "desktop tool"})
    assert search["total"] >= 1

    installed = desktop_bridge.install_repository(
        {
            "repo_url": "https://github.com/example/sample-tool",
            "confirm": True,
        }
    )
    assert installed["success"] is True
    assert installed["tool_name"] == "sample_tool"

    tools = desktop_bridge.fetch_tools()
    tool_names = {item["name"] for item in tools["tools"]}
    assert "sample_tool" in tool_names


def test_desktop_bridge_stream_orchestrator_rejects_invalid_json(monkeypatch, desktop_bridge: DesktopBridge) -> None:
    monkeypatch.setattr(
        desktop_bridge._runtime.container.orchestrator,
        "stream",
        lambda **_: iter(["event: trace\ndata: not-json\n\n"]),
    )

    with pytest.raises(AppError) as exc_info:
        desktop_bridge.stream_orchestrator(
            {
                "task": "Generate Alice sales report",
                "parameters": {"stream": True},
            }
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.details == "received invalid JSON event payload for 'trace'"
