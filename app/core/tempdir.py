from __future__ import annotations

import os
import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEMP_ROOT = PROJECT_ROOT / ".tmp"


def ensure_temp_root(*parts: str) -> Path:
    root = DEFAULT_TEMP_ROOT.joinpath(*parts)
    root.mkdir(parents=True, exist_ok=True)
    return root


@contextmanager
def managed_temp_dir(prefix: str, root: Path | None = None) -> Iterator[Path]:
    base_dir = root or ensure_temp_root("workspace")
    base_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = base_dir / f"{prefix}-{uuid.uuid4().hex[:12]}"
    temp_dir.mkdir(parents=True, exist_ok=False)
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def safe_temp_env(*, root: Path | None = None) -> dict[str, str]:
    temp_root = root or ensure_temp_root("workspace")
    temp_root.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    temp_path = str(temp_root)
    env["TMP"] = temp_path
    env["TEMP"] = temp_path
    return env
