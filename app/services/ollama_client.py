from __future__ import annotations

import json
from urllib.parse import urlparse
from typing import Any, Protocol

import httpx


class StructuredGenerationClient(Protocol):
    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        ...


class OllamaChatClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.base_url = self._normalize_base_url(base_url)
        self.fallback_base_url = self._fallback_base_url(self.base_url)
        self.model = model.strip()
        self.timeout_seconds = timeout_seconds

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        payload = self._request_json(
            "post",
            "/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "format": schema,
                "stream": False,
                "options": {"temperature": 0.2},
            },
        )
        message = payload.get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Ollama returned an empty message body")
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("Ollama structured output must be a JSON object")
        return parsed

    def _request_json(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._request(method, path, json=json)
        return response.json()

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        last_error: httpx.RequestError | None = None
        for base_url in self._candidate_base_urls():
            try:
                with httpx.Client(base_url=base_url, timeout=self.timeout_seconds) as client:
                    response = client.request(method=method, url=path, json=json)
                    response.raise_for_status()
                    return response
            except httpx.RequestError as exc:
                last_error = exc
                continue
        if last_error is not None:
            raise last_error
        raise RuntimeError("Ollama request failed before a network call was made")

    def _normalize_base_url(self, base_url: str) -> str:
        normalized = base_url.strip().rstrip("/")
        if not normalized:
            return ""
        if not normalized.startswith(("http://", "https://")):
            normalized = f"http://{normalized}"
        return normalized

    def _fallback_base_url(self, base_url: str) -> str | None:
        parsed = urlparse(base_url)
        if parsed.hostname != "ollama":
            return None
        port = parsed.port or 11434
        return f"http://localhost:{port}"

    def _candidate_base_urls(self) -> list[str]:
        candidates = [self.base_url]
        if self.fallback_base_url and self.fallback_base_url not in candidates:
            candidates.append(self.fallback_base_url)
        return [candidate for candidate in candidates if candidate]
