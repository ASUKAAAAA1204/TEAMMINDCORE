from __future__ import annotations

import json
from pathlib import Path


def test_installer_install_requires_confirmation(client):
    response = client.post(
        "/installer/install",
        json={"repo_url": "https://github.com/example/excel-analysis-tool", "confirm": False},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "ERR_005"
    assert payload["error"]["details"] == "confirm must be true"


def test_installer_install_persists_risk_report(client):
    installer = client.app.state.container.installer
    github = client.app.state.container.github

    github.inspect_repository = lambda repo_url: {
        "name": "excel-analysis-tool",
        "url": repo_url,
        "stars": 128,
        "description": "Excel analysis helper",
        "license": "MIT",
        "default_branch": "main",
        "archived": False,
        "fork": False,
        "open_issues_count": 12,
        "pushed_at": "2026-03-28T00:00:00Z",
    }
    installer._ensure_virtualenv = lambda venv_dir: Path(venv_dir).mkdir(parents=True, exist_ok=True)

    response = client.post(
        "/installer/install",
        json={"repo_url": "https://github.com/example/excel-analysis-tool", "confirm": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["tool_name"] == "excel_analysis_tool"

    installed_tools = client.app.state.repository.list_tools()
    assert len(installed_tools) == 1
    risk_report = installed_tools[0].metadata["risk_report"]
    assert risk_report["risk_level"] == "low"
    assert risk_report["checks"]["license"] == "MIT"

    receipt_path = Path(installed_tools[0].metadata["receipt"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["risk_report"]["risk_level"] == "low"
    assert receipt["repository_info"]["stars"] == 128
