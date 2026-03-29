from __future__ import annotations

import json
import re
import subprocess
import uuid
import venv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.errors import AppError
from app.domain.types import InstalledToolRecord
from app.repositories.document_repository import SQLiteDocumentRepository
from app.services.github_service import GitHubSearchService


GITHUB_REPOSITORY_PATTERN = re.compile(r"^https://github\.com/[^/]+/[^/]+/?$")


class InstallerService:
    def __init__(
        self,
        repository: SQLiteDocumentRepository,
        github_service: GitHubSearchService,
        tools_dir: Path,
        clone_mode: str,
    ) -> None:
        self.repository = repository
        self.github_service = github_service
        self.tools_dir = tools_dir
        self.clone_mode = clone_mode

    def install(self, repo_url: str, confirm: bool) -> dict[str, object]:
        if not confirm:
            raise AppError("ERR_005", "Tool installation failed", "confirm must be true", 400)
        if not GITHUB_REPOSITORY_PATTERN.match(repo_url):
            raise AppError(
                "ERR_005",
                "Tool installation failed",
                "Only standard GitHub repository URLs are supported",
                400,
            )
        repository_info = self.github_service.inspect_repository(repo_url)
        risk_report = self._build_risk_report(repository_info)
        tool_name = str(repository_info["name"]).replace("-", "_")
        target_dir = self.tools_dir / tool_name
        source_dir = target_dir / "source"
        venv_dir = target_dir / ".venv"
        target_dir.mkdir(parents=True, exist_ok=True)
        if self.clone_mode == "clone":
            self._clone_repository(repo_url, source_dir)
        else:
            source_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_virtualenv(venv_dir)
        receipt_path = target_dir / "install_receipt.json"
        receipt_path.write_text(
            json.dumps(
                {
                    "repo_url": repo_url,
                    "tool_name": tool_name,
                    "installed_at": datetime.now(timezone.utc).isoformat(),
                    "repository_info": repository_info,
                    "risk_report": risk_report,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        record = InstalledToolRecord(
            id=f"tool_{uuid.uuid4().hex[:8]}",
            name=tool_name,
            repo_url=repo_url,
            installed_path=str(target_dir),
            created_at=datetime.now(timezone.utc).isoformat(),
            metadata={
                "license": repository_info["license"],
                "receipt": str(receipt_path),
                "risk_report": risk_report,
            },
        )
        self.repository.save_tool(record)
        return {
            "success": True,
            "tool_name": tool_name,
            "installed_path": str(target_dir),
            "message": "Tool installation completed",
        }

    def _clone_repository(self, repo_url: str, target_dir: Path) -> None:
        if target_dir.exists() and any(target_dir.iterdir()):
            return
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except Exception as exc:
            raise AppError("ERR_005", "Tool installation failed", str(exc), 500) from exc

    def _ensure_virtualenv(self, venv_dir: Path) -> None:
        if venv_dir.exists():
            return
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(venv_dir)

    def _build_risk_report(self, repository_info: dict[str, Any]) -> dict[str, Any]:
        score = 0
        reasons: list[str] = []
        license_id = str(repository_info.get("license") or "UNKNOWN").upper()
        stars = int(repository_info.get("stars") or 0)
        archived = bool(repository_info.get("archived", False))
        fork = bool(repository_info.get("fork", False))
        open_issues_count = int(repository_info.get("open_issues_count") or 0)

        if license_id in {"UNKNOWN", "NOASSERTION"}:
            score += 35
            reasons.append("Repository license is unknown")
        elif "AGPL" in license_id:
            score += 40
            reasons.append("AGPL license may be incompatible with default backend distribution")
        elif license_id.startswith("GPL"):
            score += 30
            reasons.append("GPL-family license requires manual compatibility review")

        if archived:
            score += 25
            reasons.append("Repository is archived")
        if stars < 5:
            score += 10
            reasons.append("Repository has very low star count")
        if fork:
            score += 5
            reasons.append("Repository is marked as a fork")
        if open_issues_count > 200:
            score += 10
            reasons.append("Repository has a high open issue count")

        if score >= 50:
            risk_level = "high"
        elif score >= 20:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "risk_score": score,
            "reasons": reasons,
            "checks": {
                "license": license_id,
                "archived": archived,
                "fork": fork,
                "stars": stars,
                "open_issues_count": open_issues_count,
            },
        }
