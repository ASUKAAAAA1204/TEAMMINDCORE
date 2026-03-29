from __future__ import annotations


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "main_orchestrator" in payload
    assert payload["vector_store_backend"] == "auto"
    assert payload["deep_parser_enabled"] is True
    assert payload["deep_parser_backends"] == ["docling"]
    assert payload["ragflow_enabled"] is False
    assert payload["mineru_enabled"] is False
    assert payload["llamaindex_enabled"] is True
    assert payload["langgraph_enabled"] is True
    assert payload["retrieval_backend"] == "llamaindex+vector"
    assert payload["orchestrator_backend"] in {"langgraph", "local"}
    assert payload["task_planning_backend"] == "heuristic"
    assert payload["analysis_generation_backend"] == "local"
    assert payload["report_generation_backend"] == "local"


def test_tools_endpoint(client):
    response = client.get("/tools")
    assert response.status_code == 200
    payload = response.json()
    tool_names = {item["name"] for item in payload["tools"]}
    assert {"retrieval_search", "report_generate", "analysis_execute"} <= tool_names


def test_ui_index_served(client):
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "TeamMindHub Command Center" in response.text
    assert "manifest.webmanifest" in response.text
    assert "app.js" in response.text


def test_ui_assets_served(client):
    assets = {
        "/ui/app.css": "color-scheme",
        "/ui/app.js": "TeamMindHub Command Center",
        "/ui/manifest.webmanifest": "\"name\": \"TeamMindHub Command Center\"",
        "/ui/sw.js": "tmh-ui-v20260328-r1",
        "/ui/icon.svg": "<svg",
        "/ui/icon-maskable.svg": "<svg",
    }
    for path, expected in assets.items():
        response = client.get(path)
        assert response.status_code == 200
        assert expected in response.text


def test_desktop_ui_index_served(client):
    response = client.get("/desktop/")
    assert response.status_code == 200
    assert "TeamMindHub" in response.text
    assert "app.js" in response.text
    assert "app.css" in response.text
