from __future__ import annotations

import json
from typing import Any

import httpx

from app.services.ollama_client import OllamaChatClient


def test_ollama_client_falls_back_to_localhost_when_service_hostname_fails(monkeypatch) -> None:
    attempted_base_urls: list[str] = []

    class FakeClient:
        def __init__(self, *, base_url: str, timeout: float) -> None:
            self.base_url = base_url

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def request(self, method: str, url: str, json: dict[str, Any] | None = None) -> httpx.Response:
            attempted_base_urls.append(self.base_url)
            request = httpx.Request(method, f"{self.base_url}{url}")
            if self.base_url == "http://ollama:11434":
                raise httpx.ConnectError("host not found", request=request)
            response = httpx.Response(
                200,
                request=request,
                json={"message": {"content": json and json_module_dumps({"status": "ok"})}},
            )
            return response

    def json_module_dumps(payload: dict[str, str]) -> str:
        return json.dumps(payload, ensure_ascii=False)

    monkeypatch.setattr(httpx, "Client", FakeClient)

    client = OllamaChatClient(base_url="http://ollama:11434", model="deepseek-r1:8b", timeout_seconds=0.2)

    payload = client.generate_json(
        system_prompt="Return JSON.",
        user_prompt="Ping",
        schema={"type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"]},
    )

    assert attempted_base_urls == ["http://ollama:11434", "http://localhost:11434"]
    assert payload == {"status": "ok"}
