# -*- coding: utf-8 -*-
"""E9 Project World open preparation and Host application seam."""
from __future__ import annotations

import builtins
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_QAPPLICATION = None


def _ensure_qapplication():
    global _QAPPLICATION
    from PyQt6.QtWidgets import QApplication

    _QAPPLICATION = QApplication.instance() or QApplication([])
    assert _QAPPLICATION is not None
    return _QAPPLICATION


def _write_project(
    project: Path,
    *,
    active_scene: str = "main_scene.pond",
    scene_exists: bool = True,
    manifest_extra: dict | None = None,
) -> Path:
    (project / "scenes").mkdir(parents=True)
    if scene_exists:
        scene = project / "scenes" / Path(active_scene.replace("\\", "/"))
        scene.parent.mkdir(parents=True, exist_ok=True)
        scene.write_text(
            json.dumps({"name": scene.stem, "entities": [], "connections": []}),
            encoding="utf-8",
        )
    manifest = {
        "name": project.name,
        "active_scene": active_scene,
        "manifest_validation_mode": "warn",
    }
    manifest.update(manifest_extra or {})
    (project / "project.json").write_text(
        json.dumps(manifest, ensure_ascii=False),
        encoding="utf-8",
    )
    return project


def _block_pyqt_imports(monkeypatch) -> None:
    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError(f"unexpected PyQt import: {name}")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)


def test_open_preparation_is_qt_free_and_deterministic(
    tmp_path: Path, monkeypatch
) -> None:
    _block_pyqt_imports(monkeypatch)
    sys.modules.pop("core.VitaLoom.project.project_world_open", None)
    from core.VitaLoom.project.project_world_open import prepare_project_world_open

    previous = _write_project(tmp_path / "previous")
    project = _write_project(
        tmp_path / "target",
        active_scene="chapter\\intro.pond",
    )
    first = prepare_project_world_open(project, previous_project_path=previous)
    second = prepare_project_world_open(project, previous_project_path=previous)

    assert first == second
    assert first["status"] == "ready"
    assert first["same_project"] is False
    assert first["flush"] == {
        "required": True,
        "project_path": str(previous.resolve()),
        "update_active_scene": True,
    }
    assert first["active_scene"] == "chapter/intro.pond"
    assert first["scene_exists"] is True
    assert first["application_steps"] == [
        "flush_previous_world",
        "clear_host_scene",
        "apply_project_context",
        "load_active_scene",
        "publish_project_opened",
        "sync_project_plugins",
        "persist_recent_world",
        "refresh_asset_registry",
        "refresh_project_browser",
    ]
    assert first["report_id"]


@pytest.mark.parametrize(
    ("setup", "code"),
    [
        ("missing_manifest", "project_manifest_missing"),
        ("invalid_json", "project_manifest_invalid_json"),
        ("outside_scene", "active_scene_outside_project"),
    ],
)
def test_open_preparation_blocks_invalid_world_before_host_application(
    tmp_path: Path, setup: str, code: str
) -> None:
    from core.VitaLoom.project.project_world_open import prepare_project_world_open

    project = tmp_path / setup
    project.mkdir()
    if setup == "invalid_json":
        (project / "project.json").write_text("{broken", encoding="utf-8")
    elif setup == "outside_scene":
        (project / "project.json").write_text(
            json.dumps({"name": "bad", "active_scene": "../outside.pond"}),
            encoding="utf-8",
        )
    report = prepare_project_world_open(project)
    assert report["status"] == "blocked"
    assert report["code"] == code
    assert report["application_steps"] == []


def test_missing_active_scene_is_ready_with_truthful_warning(tmp_path: Path) -> None:
    from core.VitaLoom.project.project_world_open import prepare_project_world_open

    project = _write_project(tmp_path / "missing-scene", scene_exists=False)
    report = prepare_project_world_open(project)
    assert report["status"] == "ready"
    assert report["scene_exists"] is False
    assert [item["code"] for item in report["warnings"]] == ["active_scene_missing"]


def test_invalid_project_lock_is_rejected_before_host_application(tmp_path: Path) -> None:
    from core.VitaLoom.project.project_world_open import prepare_project_world_open

    project = _write_project(tmp_path / "invalid-lock")
    (project / "project.lock.json").write_text("{broken", encoding="utf-8")
    report = prepare_project_world_open(project)

    assert report["status"] == "blocked"
    assert report["code"] == "project_lock_admission_blocked"
    assert report["lock_admission"]["admission"] == "invalid"
    assert report["application_steps"] == []


def test_project_configuration_rolls_back_when_lock_refresh_fails(tmp_path: Path) -> None:
    pytest.importorskip("PyQt6")
    from core.VitaLoom.core.editor_context import get_editor_context
    from core.VitaLoom.kernel.event_bus import EventBus
    from core.VitaLoom.project.project_manager import ProjectManager

    app = _ensure_qapplication()
    assert app is not None
    project = _write_project(tmp_path / "config-lock-rollback")
    lock = project / "project.lock.json"
    lock.write_bytes(b'{"schema_version": 1, "resolved_capabilities": {}}\n')
    manifest_before = (project / "project.json").read_bytes()
    lock_before = lock.read_bytes()
    context = get_editor_context()
    context._ensure_qobject_initialized()
    context.event_bus = EventBus()
    context.current_project_path = str(project.resolve())
    context.current_project_config = json.loads(manifest_before.decode("utf-8"))
    manager = ProjectManager()
    try:
        with patch(
            "core.VitaLoom.suite.project_lock.ensure_project_lock",
            side_effect=OSError("lock store unavailable"),
        ):
            assert manager.update_project_config_fields({"package_version_overrides": {"a": "1.0.0"}}) is False
        assert (project / "project.json").read_bytes() == manifest_before
        assert lock.read_bytes() == lock_before
        assert context.current_project_config == json.loads(manifest_before.decode("utf-8"))
    finally:
        context.current_project_path = None
        context.current_project_config = {}


def test_blocking_manifest_is_rejected_before_real_pyqt_host_mutation(
    tmp_path: Path,
) -> None:
    pytest.importorskip("PyQt6")
    from core.VitaLoom.core.editor_context import get_editor_context
    from core.VitaLoom.kernel.event_bus import EventBus
    from core.VitaLoom.project.project_manager import ProjectManager

    app = _ensure_qapplication()
    assert app is not None
    project = _write_project(
        tmp_path / "blocked",
        manifest_extra={
            "manifest_validation_mode": "block",
            "required_capabilities": {"vitalloom.missing.capability": ">=1.0.0"},
        },
    )
    context = get_editor_context()
    context._ensure_qobject_initialized()
    context.event_bus = EventBus()
    manager = ProjectManager()
    context.current_project_path = None
    context.current_project_config = {}
    emitted: list[str] = []
    on_opened = emitted.append
    manager.project_opened.connect(on_opened)
    try:
        assert manager.open_project(str(project)) is False
        assert context.current_project_path is None
        assert context.current_project_config == {}
        assert emitted == []
        assert manager.last_project_open_report["status"] == "blocked"
        assert manager.last_project_open_report["code"] == "manifest_validation_blocked"
    finally:
        manager.project_opened.disconnect(on_opened)
        context.current_project_path = None
        context.current_project_config = {}


def test_project_open_command_requires_explicit_structural_host(
    tmp_path: Path, monkeypatch
) -> None:
    _block_pyqt_imports(monkeypatch)
    from core.VitaLoom.commands import runtime_commands

    project = _write_project(tmp_path / "command")
    monkeypatch.setattr(runtime_commands, "_resolve_workspace_path", lambda *_a, **_k: project)
    result = runtime_commands._project_open({"project_path": str(project)}, {})

    assert result["ok"] is False
    assert result["error"]["code"] == "project_host_adapter_unavailable"
    assert result["error"]["details"]["preparation"]["status"] == "ready"


def test_project_open_command_applies_explicit_structural_host(
    tmp_path: Path, monkeypatch
) -> None:
    from core.VitaLoom.commands import runtime_commands

    project = _write_project(tmp_path / "command-host")
    monkeypatch.setattr(runtime_commands, "_resolve_workspace_path", lambda *_a, **_k: project)

    class RecordingHost:
        def __init__(self) -> None:
            self.preparation = None

        def apply_project_world_open(self, preparation):
            self.preparation = preparation
            return {
                "status": "opened",
                "project_path": preparation["project_path"],
                "active_scene": preparation["active_scene"],
                "warnings": [],
            }

    host = RecordingHost()
    result = runtime_commands._project_open(
        {"project_path": str(project)},
        {"project_world_open_host": host},
    )
    assert result["ok"] is True
    assert result["result"]["status"] == "opened"
    assert host.preparation["status"] == "ready"


def test_finalized_open_report_is_canonical_and_json_safe(tmp_path: Path) -> None:
    from core.VitaLoom.project.project_world_open import (
        finalize_project_world_open_report,
    )

    report = finalize_project_world_open_report(
        {
            "status": "opened",
            "project_path": tmp_path / "world",
            "actions": ({"action": "load", "status": "completed"},),
            "capabilities": {"vitalloom.beta", "vitalloom.alpha"},
        }
    )

    assert report["project_path"] == str(tmp_path / "world")
    assert report["actions"] == [{"action": "load", "status": "completed"}]
    assert report["capabilities"] == ["vitalloom.alpha", "vitalloom.beta"]
    json.dumps(report, ensure_ascii=False, allow_nan=False)
    assert report == finalize_project_world_open_report(report)


def test_project_open_command_applies_real_pyqt_project_manager(
    tmp_path: Path, monkeypatch
) -> None:
    pytest.importorskip("PyQt6")
    _ensure_qapplication()

    from core.VitaLoom.commands import runtime_commands
    from core.VitaLoom.core.editor_context import get_editor_context
    from core.VitaLoom.kernel.event_bus import EventBus
    from core.VitaLoom.project.project_manager import ProjectManager

    project = _write_project(tmp_path / "real-host")
    monkeypatch.setattr(runtime_commands, "_resolve_workspace_path", lambda *_a, **_k: project)
    context = get_editor_context()
    context._ensure_qobject_initialized()
    context.event_bus = EventBus()
    context.current_project_path = None
    context.current_project_config = {}
    manager = ProjectManager()
    monkeypatch.setattr(
        manager,
        "_sync_project_plugins",
        lambda *_a, **_k: {"status": "settled", "completed": {"activated": [], "deactivated": []}},
    )
    monkeypatch.setattr(
        manager,
        "_refresh_project_asset_registry",
        lambda project_path: {
            "status": "refreshed",
            "project_path": project_path,
            "registry_revision": "test",
            "generation": 1,
            "recovery_required": False,
        },
    )

    try:
        result = runtime_commands._project_open(
            {"project_path": str(project)},
            {"project_world_open_host": manager},
        )
        assert result["ok"] is True
        assert result["result"]["status"] == "opened"
        assert result["result"]["preparation_report_id"]
        assert manager.last_project_open_report == result["result"]
        json.dumps(result, ensure_ascii=False, allow_nan=False)
    finally:
        context.current_project_path = None
        context.current_project_config = {}



def test_project_open_command_and_manager_use_authority_not_concrete_import() -> None:
    root = Path(__file__).resolve().parents[1]
    command_source = (
        root
        / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py"
    ).read_text(encoding="utf-8")
    command_block = command_source.split("def _project_open", 1)[1].split(
        "def _project_create", 1
    )[0]
    assert "project_world_open" in command_block
    assert "project_manager" not in command_block
    assert "project_world_open_host" in command_block

    manager_source = (
        root
        / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/project/project_manager.py"
    ).read_text(encoding="utf-8")
    prepare_block = manager_source.split("    def open_project", 1)[1].split(
        "    def apply_project_world_open", 1
    )[0]
    apply_block = manager_source.split("    def apply_project_world_open", 1)[1].split(
        "    def _refresh_project_asset_registry", 1
    )[0]
    assert "prepare_project_world_open" in prepare_block
    assert "get_scene_manager" not in prepare_block
    assert "apply_project_world_open" in prepare_block
    assert "get_scene_manager" in apply_block
    assert "_sync_project_plugins" in apply_block
