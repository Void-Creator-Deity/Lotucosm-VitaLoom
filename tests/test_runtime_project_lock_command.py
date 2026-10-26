from __future__ import annotations

import json
from pathlib import Path

from core.VitaLoom.commands import runtime_commands


ROOT = Path(__file__).resolve().parents[1]


def _prepare(monkeypatch, tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    project = workspace / "projects" / "fixture"
    project.mkdir(parents=True)
    (project / "project.json").write_text(
        json.dumps({"name": "fixture", "loom_editor_version": "1.0.0"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(runtime_commands, "_workspace_root", lambda: workspace)
    return project


def test_project_lock_check_uses_shared_resolution_for_missing_lock(monkeypatch, tmp_path) -> None:
    project = _prepare(monkeypatch, tmp_path)
    result = runtime_commands._project_lock_check({"project_path": str(project)}, {})
    payload = result["result"]
    assert payload["exists"] is False
    assert payload["valid"] is False
    assert payload["lock_status"] == "未锁定"
    assert payload["lock_admission"] == "missing"
    assert payload["blocking_issue_codes"] == ["lock_missing"]
    assert "project.lock.json missing" in result["warnings"]


def test_project_lock_check_reports_invalid_lock_without_raw_json_fallback(monkeypatch, tmp_path) -> None:
    project = _prepare(monkeypatch, tmp_path)
    (project / "project.lock.json").write_text("{broken", encoding="utf-8")
    result = runtime_commands._project_lock_check({"project_path": str(project)}, {})
    payload = result["result"]
    assert payload["exists"] is True
    assert payload["valid"] is False
    assert payload["lock_status"] == "锁无效"
    assert payload["lock_admission"] == "invalid"
    assert payload["blocking_issue_codes"] == ["invalid"]
    assert payload["lock_error"] == "project.lock.json is invalid or unreadable"


def test_project_state_exposes_shared_lock_projection(monkeypatch, tmp_path) -> None:
    project = _prepare(monkeypatch, tmp_path)
    result = runtime_commands._project_state({"project_path": str(project)}, {})
    payload = result["result"]
    assert payload["lock_status"] == "未锁定"
    assert payload["lock_error"] == ""
    assert payload["blocking_issue_summary"] == ""


def test_plugin_resolve_returns_structured_lock_diagnostics(monkeypatch, tmp_path) -> None:
    project = _prepare(monkeypatch, tmp_path)
    result = runtime_commands._plugin_resolve({"project_path": str(project)}, {})
    assert result["ok"] is True
    payload = result["result"]
    assert payload["lock_admission"] == "missing"
    assert payload["blocking_issue_codes"] == ["lock_missing"]
