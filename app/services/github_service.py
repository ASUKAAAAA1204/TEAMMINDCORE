from __future__ import annotations

from urllib.parse import urlparse

import httpx


class GitHubSearchService:
    def __init__(self, api_base: str) -> None:
        self.api_base = api_base.rstrip("/")

    def search_repositories(self, query: str) -> dict[str, object]:
        try:
            with httpx.Client(timeout=10.0, headers={"Accept": "application/vnd.github+json"}) as client:
                response = client.get(
                    f"{self.api_base}/search/repositories",
                    params={"q": query, "sort": "stars", "per_page": 5},
                )
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return self._fallback_results(query)
        results = []
        for item in payload.get("items", []):
            results.append(
                {
                    "name": item["name"],
                    "url": item["html_url"],
                    "stars": item["stargazers_count"],
                    "description": item.get("description") or "",
                    "readme_summary": "Fetch the README content separately before installation.",
                    "license": (item.get("license") or {}).get("spdx_id") or "UNKNOWN",
                }
            )
        return {"total": len(results), "results": results}

    def inspect_repository(self, repo_url: str) -> dict[str, object]:
        owner, name = self._extract_owner_and_repo(repo_url)
        with httpx.Client(timeout=10.0, headers={"Accept": "application/vnd.github+json"}) as client:
            response = client.get(f"{self.api_base}/repos/{owner}/{name}")
            response.raise_for_status()
            item = response.json()
        return {
            "name": item["name"],
            "url": item["html_url"],
            "stars": item["stargazers_count"],
            "description": item.get("description") or "",
            "license": (item.get("license") or {}).get("spdx_id") or "UNKNOWN",
            "default_branch": item.get("default_branch", "main"),
            "archived": bool(item.get("archived", False)),
            "fork": bool(item.get("fork", False)),
            "open_issues_count": int(item.get("open_issues_count", 0)),
            "pushed_at": item.get("pushed_at") or "",
        }

    def _extract_owner_and_repo(self, repo_url: str) -> tuple[str, str]:
        parsed = urlparse(repo_url)
        path_parts = [part for part in parsed.path.split("/") if part]
        owner, name = path_parts[0], path_parts[1]
        return owner, name.removesuffix(".git")

    def _fallback_results(self, query: str) -> dict[str, object]:
        return {
            "total": 1,
            "results": [
                {
                    "name": "offline-github-search",
                    "url": "https://github.com/example/offline-github-search",
                    "stars": 0,
                    "description": f"Network search is unavailable. Original query: {query}",
                    "readme_summary": "Offline fallback result only.",
                    "license": "UNKNOWN",
                }
            ],
        }
