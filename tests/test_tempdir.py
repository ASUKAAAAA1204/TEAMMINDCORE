from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from app.core.tempdir import managed_temp_dir, safe_temp_env


def _make_temp_root(prefix: str) -> Path:
    root = Path(__file__).resolve().parents[1] / ".tmp" / f"{prefix}-{uuid.uuid4().hex[:8]}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_managed_temp_dir_creates_and_cleans_up():
    temp_root = _make_temp_root("tempdir-test")
    captured_path: Path | None = None

    try:
        with managed_temp_dir("parser", temp_root) as temp_dir:
            captured_path = temp_dir
            assert temp_dir.exists()
            assert temp_dir.is_dir()
            (temp_dir / "probe.txt").write_text("ok", encoding="utf-8")

        assert captured_path is not None
        assert not captured_path.exists()
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def test_safe_temp_env_points_tmp_and_temp_to_root():
    temp_root = _make_temp_root("tempenv-test")
    try:
        env = safe_temp_env(root=temp_root)

        assert env["TMP"] == str(temp_root)
        assert env["TEMP"] == str(temp_root)
        assert temp_root.exists()
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
