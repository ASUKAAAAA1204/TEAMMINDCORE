from __future__ import annotations

from dataclasses import asdict

from app.desktop import doctor


def test_run_doctor_returns_named_checks() -> None:
    report = doctor.run_doctor()
    names = {item.name for item in report}
    assert {
        "project_root",
        "app_base_dir",
        "pywebview",
        "pyinstaller",
        "iscc",
        "ollama_executable",
        "node",
        "npm",
        "frontend_package",
        "frontend_dist",
        "data_dir",
    } <= names


def test_run_doctor_can_be_serialized() -> None:
    report = doctor.run_doctor()
    payload = [asdict(item) for item in report]
    assert all("name" in item and "ok" in item and "details" in item for item in payload)
