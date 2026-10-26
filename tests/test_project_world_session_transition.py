# -*- coding: utf-8 -*-
"""E10 Project World persistence/close authority and Host application seam."""
from __future__ import annotations

import builtins
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


_QAPPLICATION = None


class _ProjectLifecycleCapability:
    """Minimal complete Adapter for the E26 plugin Host Interface in Host tests."""

    def __init__(self, delegate) -> None:
        self._delegate = delegate

    def observe_plugins(self) -> dict:
        return {"status": "ready"}

    def reload_plugin(self, plugin_id: str) -> dict:
        return {"status": "blocked", "plugin_id": plugin_id}

    def unload_plugin(self, plugin_id: str) -> dict:
        return {"status": "blocked", "plugin_id": plugin_id}

    def scan_project_addons(self, project_path: object) -> dict:
        return self._delegate.scan_project_addons(project_path)

    def sync_plugins_for_project(
        self, project_data: dict, *, repo_root: object | None = None
    ) -> dict:
        return self._delegate.sync_plugins_for_project(project_data)


def _publish_project_lifecycle_capability(context, delegate) -> None:
    from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION

    context.services.register(
        PLUGIN_HOST_CONTROL_OBSERVATION,
        _ProjectLifecycleCapability(delegate),
    )


@pytest.fixture(autouse=True)
def _cleanup_host_state():
    """Keep the legacy PyQt Host Adapter singleton state local to each test."""

    yield
    try:
        from core.VitaLoom.core.editor_context import get_editor_context
        from core.VitaLoom.project.project_manager import ProjectManager
        from core.VitaLoom.scene.scene_manager import SceneManager

        context = get_editor_context()
        context.current_project_path = None
        context.current_project_config = None
        context.project_modified = False
        context.project_manifest_validation = None
        context.project_asset_registry_snapshot = None
        context.kernel = None
        from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION

        context.services.unregister(PLUGIN_HOST_CONTROL_OBSERVATION)
        if SceneManager._instance is not None:
            SceneManager._instance.clear_scene(notify=False)
        ProjectManager._instance = None
        SceneManager._instance = None
    except Exception:
        pass


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
    manifest: object | None = None,
) -> tuple[Path, Path]:
    scene = project / "scenes" / Path(active_scene.replace("\\", "/"))
    scene.parent.mkdir(parents=True, exist_ok=True)
    scene.write_text(
        json.dumps({"name": scene.stem, "entities": [], "connections": []}),
        encoding="utf-8",
    )
    project_data: object = (
        {"name": project.name, "active_scene": active_scene, "custom": {"keep": True}}
        if manifest is None
        else manifest
    )
    (project / "project.json").write_text(
        json.dumps(project_data, ensure_ascii=False),
        encoding="utf-8",
    )
    return project, scene


def _block_pyqt_imports(monkeypatch) -> None:
    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError(f"unexpected PyQt import: {name}")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)


def _real_host(tmp_path: Path):
    pytest.importorskip("PyQt6")
    _ensure_qapplication()

    from core.VitaLoom.core.editor_context import get_editor_context
    from core.VitaLoom.kernel.event_bus import EventBus
    from core.VitaLoom.project.project_manager import ProjectManager
    from core.VitaLoom.scene.scene_manager import SceneManager

    context = get_editor_context()
    context._ensure_qobject_initialized()
    context.event_bus = EventBus()
    context.current_project_path = None
    context.project_modified = False
    context.current_project_config = None
    context.project_manifest_validation = None
    context.project_asset_registry_snapshot = None
    context.kernel = None
    from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION

    context.services.unregister(PLUGIN_HOST_CONTROL_OBSERVATION)

    ProjectManager._instance = None
    SceneManager._instance = None
    manager = ProjectManager()
    scene_manager = SceneManager()
    manager._system_config_dir = str(tmp_path / "state" / "system")
    return manager, scene_manager, context


def test_session_authority_is_qt_free_and_deterministic(
    tmp_path: Path, monkeypatch
) -> None:
    _block_pyqt_imports(monkeypatch)
    sys.modules.pop("core.VitaLoom.project.project_world_report", None)
    sys.modules.pop("core.VitaLoom.project.project_world_session", None)

    from core.VitaLoom.project.project_world_session import (
        prepare_project_world_close,
        prepare_project_world_flush,
        prepare_project_world_save,
    )

    project, scene = _write_project(tmp_path / "world", active_scene="chapter/intro.pond")
    save_first = prepare_project_world_save(
        project,
        modified_at="2026-07-19 12:34:56",
    )
    save_second = prepare_project_world_save(
        project,
        modified_at="2026-07-19 12:34:56",
    )
    flush = prepare_project_world_flush(project, scene_path=scene)
    close = prepare_project_world_close(project)

    assert save_first == save_second
    assert save_first["status"] == "ready"
    assert save_first["next_project_data"]["modified_at"] == "2026-07-19 12:34:56"
    assert save_first["next_project_data"]["custom"] == {"keep": True}
    assert flush["status"] == "ready"
    assert flush["active_scene"] == "chapter/intro.pond"
    assert flush["manifest_update_required"] is True
    assert flush["scene_persistence_boundary"] == {
        "kind": "automatic_lifecycle_flush",
        "history_admission": "excluded",
        "audit_admission": "excluded",
        "reason": (
            "Project-World lifecycle persistence is not a user semantic command; "
            "it must not create user undo/redo history or command audit entries."
        ),
    }
    assert close["application_steps"] == [
        "flush_current_world",
        "teardown_project_addons",
        "clear_host_scene",
        "clear_project_context",
        "publish_project_closed",
    ]
    json.dumps(save_first, ensure_ascii=False, allow_nan=False)


@pytest.mark.parametrize(
    ("setup", "code"),
    [
        ("missing", "project_manifest_missing"),
        ("invalid", "project_manifest_invalid_json"),
        ("non_object", "project_manifest_not_object"),
    ],
)
def test_save_preparation_blocks_invalid_manifest(
    tmp_path: Path, setup: str, code: str
) -> None:
    from core.VitaLoom.project.project_world_session import prepare_project_world_save

    project = tmp_path / setup
    project.mkdir()
    if setup == "invalid":
        (project / "project.json").write_text("{broken", encoding="utf-8")
    elif setup == "non_object":
        (project / "project.json").write_text("[]", encoding="utf-8")

    report = prepare_project_world_save(
        project,
        modified_at="2026-07-19 12:34:56",
    )
    assert report["status"] == "blocked"
    assert report["code"] == code
    assert report["application_steps"] == []


@pytest.mark.parametrize("kind", ["outside", "prefix_lookalike", "not_pond"])
def test_flush_preparation_rejects_invalid_scene_containment(
    tmp_path: Path, kind: str
) -> None:
    from core.VitaLoom.project.project_world_session import prepare_project_world_flush

    project, _scene = _write_project(tmp_path / "world")
    if kind == "outside":
        candidate = tmp_path / "outside.pond"
    elif kind == "prefix_lookalike":
        candidate = tmp_path / "world-other" / "scenes" / "outside.pond"
    else:
        candidate = project / "scenes" / "notes.txt"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text("{}", encoding="utf-8")

    report = prepare_project_world_flush(project, scene_path=candidate)
    assert report["status"] == "blocked"
    expected = "active_scene_not_pond" if kind == "not_pond" else "active_scene_outside_project"
    assert report["code"] == expected


def test_manifest_commit_is_same_directory_atomic_replace(tmp_path: Path, monkeypatch) -> None:
    from core.VitaLoom.project import project_world_session

    project, _scene = _write_project(tmp_path / "world")
    lock = project / "project.lock.json"
    lock.write_bytes(b'{"schema_version": 1, "resolved_capabilities": {}}\n')
    preparation = project_world_session.prepare_project_world_save(
        project,
        modified_at="2026-07-19 12:34:56",
    )
    calls: list[tuple[Path, Path]] = []
    real_replace = os.replace

    def recording_replace(source, target):
        calls.append((Path(source), Path(target)))
        return real_replace(source, target)

    monkeypatch.setattr(project_world_session.os, "replace", recording_replace)
    report = project_world_session.commit_project_world_manifest(preparation)

    assert report["status"] == "persisted"
    assert len(calls) == 1
    source, target = calls[0]
    assert source.parent == target.parent == project
    assert target == project / "project.json"
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved["modified_at"] == "2026-07-19 12:34:56"
    assert json.loads(lock.read_text(encoding="utf-8"))["schema_version"] == 1
    assert not list(project.glob(".project.json.*.tmp"))


def test_manifest_commit_rejects_target_outside_prepared_project(tmp_path: Path) -> None:
    from core.VitaLoom.project import project_world_session

    project, _scene = _write_project(tmp_path / "world")
    outside = tmp_path / "outside.json"
    preparation = project_world_session.prepare_project_world_save(
        project,
        modified_at="2026-07-19 12:34:56",
    )
    preparation["project_json_path"] = str(outside)

    report = project_world_session.commit_project_world_manifest(preparation)

    assert report["status"] == "blocked"
    assert report["code"] == "project_manifest_target_invalid"
    assert not outside.exists()


def test_manifest_replace_failure_preserves_original_and_reports_failure(
    tmp_path: Path, monkeypatch
) -> None:
    from core.VitaLoom.project import project_world_session

    project, _scene = _write_project(tmp_path / "world")
    manifest_path = project / "project.json"
    original = manifest_path.read_bytes()
    preparation = project_world_session.prepare_project_world_save(
        project,
        modified_at="2026-07-19 12:34:56",
    )

    def fail_replace(_source, _target):
        raise PermissionError("replace denied")

    monkeypatch.setattr(project_world_session.os, "replace", fail_replace)
    report = project_world_session.commit_project_world_manifest(preparation)

    assert report["status"] == "failed"
    assert report["code"] == "project_manifest_atomic_replace_failed"
    assert manifest_path.read_bytes() == original
    assert not list(project.glob(".project.json.*.tmp"))


def test_manifest_commit_rolls_back_when_lock_refresh_fails(
    tmp_path: Path, monkeypatch
) -> None:
    from core.VitaLoom.project import project_world_session

    project, _scene = _write_project(tmp_path / "world")
    manifest_path = project / "project.json"
    lock_path = project / "project.lock.json"
    original_manifest = manifest_path.read_bytes()
    original_lock = b'{"schema_version": 1, "resolved_capabilities": {}}\n'
    lock_path.write_bytes(original_lock)
    preparation = project_world_session.prepare_project_world_save(
        project,
        modified_at="2026-07-19 12:34:56",
    )
    monkeypatch.setattr(
        "core.VitaLoom.suite.project_lock.ensure_project_lock",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("lock store unavailable")),
    )

    report = project_world_session.commit_project_world_manifest(preparation)

    assert report["status"] == "failed"
    assert report["code"] == "project_lock_refresh_failed"
    assert manifest_path.read_bytes() == original_manifest
    assert lock_path.read_bytes() == original_lock


def test_generic_project_world_report_is_strict_json_safe(tmp_path: Path) -> None:
    from core.VitaLoom.project.project_world_report import finalize_project_world_report

    circular: list[object] = []
    circular.append(circular)
    report = finalize_project_world_report(
        {
            "path": tmp_path / "world",
            "tuple": ("a", "b"),
            "set": {"beta", "alpha"},
            "bytes": b"\x00\xff",
            "nan": float("nan"),
            "circular": circular,
            "unknown": SimpleNamespace(value=1),
        }
    )

    assert report["path"] == str(tmp_path / "world")
    assert report["tuple"] == ["a", "b"]
    assert report["set"] == ["alpha", "beta"]
    assert report["bytes"] == {"encoding": "hex", "value": "00ff"}
    json.dumps(report, ensure_ascii=False, allow_nan=False)
    assert report == finalize_project_world_report(report)


def test_real_host_save_emits_only_after_atomic_commit(
    tmp_path: Path, monkeypatch
) -> None:
    manager, _scene_manager, context = _real_host(tmp_path)
    project, _scene = _write_project(tmp_path / "world")
    context.current_project_path = str(project)
    context.current_project_config = {"stale": True}
    context.project_modified = True
    emitted: list[str] = []
    manager.project_saved.connect(emitted.append)

    assert manager.save_project(modified_at="2026-07-19 12:34:56") is True
    assert manager.last_project_save_report["status"] == "saved"
    assert emitted == [str(project)]
    assert context.project_modified is False
    assert context.current_project_config["modified_at"] == "2026-07-19 12:34:56"

    (project / "project.json").write_text("{broken", encoding="utf-8")
    context.project_modified = True
    assert manager.save_project(modified_at="2026-07-19 12:35:00") is False
    assert manager.last_project_save_report["status"] == "blocked"
    assert emitted == [str(project)]
    assert context.project_modified is True


def test_real_host_flush_fails_closed_on_scene_save_failure(
    tmp_path: Path, monkeypatch
) -> None:
    manager, scene_manager, context = _real_host(tmp_path)
    project, scene = _write_project(tmp_path / "world", active_scene="old.pond")
    new_scene = project / "scenes" / "chapter" / "new.pond"
    new_scene.parent.mkdir(parents=True)
    new_scene.write_text("{}", encoding="utf-8")
    context.current_project_path = str(project)
    scene_manager._current_scene_path = str(new_scene)
    scene_manager._current_scene_data = {"name": "new", "entities": []}
    scene_manager._scene_modified = True
    monkeypatch.setattr(scene_manager, "save_scene", lambda *a, **k: False)

    report = manager.flush_current_project()

    assert report["status"] == "failed"
    assert report["code"] == "scene_save_failed"
    assert json.loads((project / "project.json").read_text(encoding="utf-8"))["active_scene"] == "old.pond"
    assert context.current_project_path == str(project)
def test_automatic_flush_is_explicit_non_history_non_audit_lifecycle_boundary(
    tmp_path: Path,
) -> None:
    from core.VitaLoom.commands import runtime_commands  # Registers built-in commands.
    from core.VitaLoom.commands.registry import reset_command_registry

    _ = runtime_commands
    registry = reset_command_registry()
    manager, scene_manager, context = _real_host(tmp_path)
    project, scene = _write_project(tmp_path / "world")
    expected_scene = {
        "name": "flushed-lifecycle-scene",
        "entities": [{"id": "root", "meta": {"source": "host"}}],
        "connections": [],
        "custom": {"keep": True},
    }
    context.current_project_path = str(project)
    context.current_project_config = {"name": project.name, "active_scene": "main_scene.pond"}
    scene_manager._current_scene_path = str(scene)
    scene_manager._current_scene_data = expected_scene
    scene_manager._scene_modified = True

    report = manager.flush_current_project()

    assert report["status"] == "flushed"
    assert report["scene_persistence_boundary"] == {
        "kind": "automatic_lifecycle_flush",
        "history_admission": "excluded",
        "audit_admission": "excluded",
        "reason": (
            "Project-World lifecycle persistence is not a user semantic command; "
            "it must not create user undo/redo history or command audit entries."
        ),
    }
    persisted_scene = json.loads(scene.read_text(encoding="utf-8"))
    assert persisted_scene["name"] == expected_scene["name"]
    assert persisted_scene["entities"] == expected_scene["entities"]
    assert persisted_scene["custom"] == expected_scene["custom"]
    assert persisted_scene["modified_at"]
    assert not (project / ".vitaloom" / "command_audit.jsonl").exists()
    undo = registry.run("command.undo", {})
    assert undo["ok"] is False
    assert undo["error"]["code"] == "undo_empty"
    assert json.loads((project / "project.json").read_text(encoding="utf-8"))["active_scene"] == "main_scene.pond"


def test_project_open_does_not_replace_world_after_failed_previous_flush(
    tmp_path: Path, monkeypatch
) -> None:
    manager, scene_manager, context = _real_host(tmp_path)
    previous, previous_scene = _write_project(tmp_path / "previous")
    target, _target_scene = _write_project(tmp_path / "target")
    context.current_project_path = str(previous)
    context.current_project_config = {"name": "previous"}
    scene_manager._current_scene_path = str(previous_scene)
    scene_manager._current_scene_data = {"name": "previous", "entities": []}
    scene_manager._scene_modified = True
    monkeypatch.setattr(scene_manager, "save_scene", lambda *a, **k: False)

    assert manager.open_project(str(target)) is False
    assert context.current_project_path == str(previous)
    assert context.current_project_config == {"name": "previous"}
    assert manager.last_project_open_report["code"] == "project_previous_world_flush_failed"


def test_flush_application_rejects_stale_preparation(tmp_path: Path) -> None:
    manager, scene_manager, context = _real_host(tmp_path)
    prepared_project, prepared_scene = _write_project(tmp_path / "prepared")
    current_project, current_scene = _write_project(tmp_path / "current")
    from core.VitaLoom.project.project_world_session import prepare_project_world_flush

    preparation = prepare_project_world_flush(
        prepared_project,
        scene_path=prepared_scene,
    )
    context.current_project_path = str(current_project)
    scene_manager._current_scene_path = str(current_scene)
    scene_manager._current_scene_data = {"name": "current", "entities": []}
    scene_manager._scene_modified = True

    report = manager.apply_project_world_flush(preparation)

    assert report["status"] == "blocked"
    assert report["code"] == "project_world_flush_context_changed"
    assert scene_manager.is_scene_modified() is True
    assert json.loads((prepared_project / "project.json").read_text(encoding="utf-8"))["active_scene"] == "main_scene.pond"


def test_flush_application_rejects_changed_scene_preparation(tmp_path: Path) -> None:
    manager, scene_manager, context = _real_host(tmp_path)
    project, prepared_scene = _write_project(tmp_path / "world")
    current_scene = project / "scenes" / "current.pond"
    current_scene.write_text("{}", encoding="utf-8")
    from core.VitaLoom.project.project_world_session import prepare_project_world_flush

    preparation = prepare_project_world_flush(project, scene_path=prepared_scene)
    context.current_project_path = str(project)
    scene_manager._current_scene_path = str(current_scene)
    scene_manager._current_scene_data = {"name": "current", "entities": []}
    scene_manager._scene_modified = True

    report = manager.apply_project_world_flush(preparation)

    assert report["status"] == "blocked"
    assert report["code"] == "project_world_flush_scene_changed"
    assert scene_manager.is_scene_modified() is True


def test_close_application_rejects_stale_preparation(tmp_path: Path) -> None:
    manager, scene_manager, context = _real_host(tmp_path)
    prepared_project, _prepared_scene = _write_project(tmp_path / "prepared")
    current_project, current_scene = _write_project(tmp_path / "current")
    from core.VitaLoom.project.project_world_session import prepare_project_world_close

    preparation = prepare_project_world_close(prepared_project)
    context.current_project_path = str(current_project)
    context.current_project_config = {"name": "current"}
    scene_manager._current_scene_path = str(current_scene)
    scene_manager._current_scene_data = {"name": "current", "entities": []}
    scene_manager._scene_modified = False

    report = manager.apply_project_world_close(preparation)

    assert report["status"] == "blocked"
    assert report["code"] == "project_world_close_context_changed"
    assert context.current_project_path == str(current_project)
    assert scene_manager.get_current_scene_path() == str(current_scene)


def test_open_can_abandon_unmodified_stale_previous_world(tmp_path: Path) -> None:
    manager, scene_manager, context = _real_host(tmp_path)
    previous = tmp_path / "removed-previous"
    target, _target_scene = _write_project(tmp_path / "target")
    context.current_project_path = str(previous)
    context.current_project_config = {"name": "previous"}
    scene_manager._current_scene_path = str(previous / "scenes" / "main_scene.pond")
    scene_manager._current_scene_data = {"name": "previous", "entities": []}
    scene_manager._scene_modified = False

    assert manager.open_project(str(target)) is True

    report = manager.last_project_open_report
    assert report["status"] == "opened_with_warnings"
    assert report["previous_world_flush"]["status"] == "noop"
    assert report["previous_world_flush"]["code"] == "stale_project_world_unavailable"
    assert {item["code"] for item in report["warnings"]} >= {
        "previous_project_world_unavailable"
    }
    assert context.current_project_path == str(target.resolve())


def test_open_blocks_modified_stale_previous_world(tmp_path: Path) -> None:
    manager, scene_manager, context = _real_host(tmp_path)
    previous = tmp_path / "removed-previous"
    target, _target_scene = _write_project(tmp_path / "target")
    context.current_project_path = str(previous)
    context.current_project_config = {"name": "previous"}
    scene_manager._current_scene_path = str(previous / "scenes" / "main_scene.pond")
    scene_manager._current_scene_data = {"name": "previous", "entities": []}
    scene_manager._scene_modified = True

    assert manager.open_project(str(target)) is False

    report = manager.last_project_open_report
    assert report["code"] == "project_previous_world_flush_failed"
    assert report["previous_world_flush"]["code"] == "project_manifest_missing"
    assert context.current_project_path == str(previous)
    assert scene_manager.is_scene_modified() is True


def test_real_host_close_flushes_tears_down_clears_and_publishes(
    tmp_path: Path, monkeypatch
) -> None:
    manager, scene_manager, context = _real_host(tmp_path)
    project, scene = _write_project(tmp_path / "world")
    context.current_project_path = str(project)
    context.current_project_config = {"name": "world"}
    context.project_manifest_validation = {"ok": True}
    context.project_asset_registry_snapshot = {"generation": 1}
    scene_manager._current_scene_path = str(scene)
    scene_manager._current_scene_data = {"name": "main_scene", "entities": []}
    scene_manager._scene_modified = False
    lifecycle_calls: list[str] = []

    class Loader:
        def scan_project_addons(self, project_path):
            lifecycle_calls.append(f"scan:{project_path}")
            return {"status": "ready", "project_addons": []}

        def sync_plugins_for_project(self, project_data):
            lifecycle_calls.append("sync")
            return {
                "status": "settled",
                "completed": {"deactivated": [], "activated": []},
            }

    _publish_project_lifecycle_capability(context, Loader())
    emitted: list[bool] = []
    manager.project_closed.connect(lambda: emitted.append(True))

    report = manager.close_project()

    assert report["status"] == "closed"
    assert [item["action"] for item in report["actions"]] == [
        "flush_current_world",
        "teardown_project_addons",
        "clear_host_scene",
        "clear_project_context",
        "publish_project_closed",
    ]
    assert lifecycle_calls == ["scan:None", "sync"]
    assert context.current_project_path is None
    assert context.current_project_config is None
    assert context.project_manifest_validation is None
    assert context.project_asset_registry_snapshot is None
    assert scene_manager.get_current_scene_path() is None
    assert emitted == [True]


def test_real_host_close_is_noop_without_current_world(tmp_path: Path) -> None:
    manager, _scene_manager, context = _real_host(tmp_path)
    emitted: list[bool] = []
    manager.project_closed.connect(lambda: emitted.append(True))

    report = manager.close_project()

    assert report["status"] == "noop"
    assert report["code"] == "no_current_project_world"
    assert context.current_project_path is None
    assert emitted == []


def test_real_host_close_preserves_world_when_flush_fails(
    tmp_path: Path, monkeypatch
) -> None:
    manager, _scene_manager, context = _real_host(tmp_path)
    project, _scene = _write_project(tmp_path / "world")
    context.current_project_path = str(project)
    called: list[str] = []
    context.kernel = SimpleNamespace(
        plugin_loader=SimpleNamespace(
            scan_project_addons=lambda *_a, **_k: called.append("scan"),
            sync_plugins_for_project=lambda *_a, **_k: called.append("sync"),
        )
    )
    monkeypatch.setattr(
        manager,
        "flush_current_project",
        lambda *a, **k: {
            "status": "failed",
            "code": "scene_save_failed",
            "message": "save failed",
            "report_id": "failed-flush",
        },
    )

    report = manager.close_project()

    assert report["status"] == "blocked"
    assert report["code"] == "project_close_flush_failed"
    assert context.current_project_path == str(project)
    assert called == []


def test_real_host_close_reports_partial_plugin_teardown_without_false_close(
    tmp_path: Path, monkeypatch
) -> None:
    manager, _scene_manager, context = _real_host(tmp_path)
    project, _scene = _write_project(tmp_path / "world")
    context.current_project_path = str(project)
    monkeypatch.setattr(
        manager,
        "flush_current_project",
        lambda *a, **k: {"status": "flushed", "code": "", "report_id": "ok"},
    )

    class Loader:
        def scan_project_addons(self, _project_path):
            return {"status": "ready", "project_addons": []}

        def sync_plugins_for_project(self, _project_data):
            return {
                "status": "failed",
                "completed": {"deactivated": ["half"], "activated": []},
                "diagnostics": [{"code": "deactivate_failed"}],
            }

    _publish_project_lifecycle_capability(context, Loader())
    emitted: list[bool] = []
    manager.project_closed.connect(lambda: emitted.append(True))

    report = manager.close_project()

    assert report["status"] == "partial"
    assert report["code"] == "project_addon_teardown_unsettled"
    assert context.current_project_path == str(project)
    assert emitted == []
    assert report["plugin_lifecycle"]["completed"]["deactivated"] == ["half"]


def test_editor_shutdown_discard_choice_skips_flush(tmp_path: Path, monkeypatch) -> None:
    _manager, scene_manager, _context = _real_host(tmp_path)
    from PyQt6.QtWidgets import QMessageBox
    from core.VitaLoom.kernel.editor_kernel import EditorKernel

    scene_manager._scene_modified = True
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_a, **_k: QMessageBox.StandardButton.No,
    )
    calls: list[str] = []
    fake = SimpleNamespace(
        _t=lambda _key, default="": default,
        layout_manager=SimpleNamespace(save_layout=lambda: calls.append("layout")),
        _flush_project_before_shutdown=lambda: calls.append("flush"),
        plugin_loader=SimpleNamespace(
            shutdown_plugins=lambda: calls.append("shutdown")
            or {"status": "settled", "source": "shutdown"},
        ),
    )
    event = SimpleNamespace(
        accept=lambda: calls.append("accept"),
        ignore=lambda: calls.append("ignore"),
    )

    EditorKernel.closeEvent(fake, event)

    assert calls == ["layout", "shutdown", "accept"]


def test_editor_shutdown_flush_failure_blocks_close(tmp_path: Path, monkeypatch) -> None:
    _manager, scene_manager, _context = _real_host(tmp_path)
    from PyQt6.QtWidgets import QMessageBox
    from core.VitaLoom.kernel.editor_kernel import EditorKernel

    scene_manager._scene_modified = True
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_a, **_k: QMessageBox.StandardButton.Yes,
    )
    critical: list[str] = []
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda *_a, **_k: critical.append("critical"),
    )
    calls: list[str] = []
    fake = SimpleNamespace(
        _t=lambda _key, default="": default,
        layout_manager=SimpleNamespace(save_layout=lambda: calls.append("layout")),
        _flush_project_before_shutdown=lambda: {
            "status": "failed",
            "code": "scene_save_failed",
            "message": "save failed",
        },
        plugin_loader=SimpleNamespace(
            shutdown_plugins=lambda: calls.append("shutdown")
            or {"status": "settled", "source": "shutdown"},
        ),
    )
    event = SimpleNamespace(
        accept=lambda: calls.append("accept"),
        ignore=lambda: calls.append("ignore"),
    )

    EditorKernel.closeEvent(fake, event)

    assert critical == ["critical"]
    assert calls == ["ignore"]


def test_editor_and_player_consume_explicit_project_world_host_capability() -> None:
    root = Path(__file__).resolve().parents[1]
    editor_source = (
        root
        / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/kernel/editor_kernel.py"
    ).read_text(encoding="utf-8")
    shutdown_block = editor_source.split("    def _flush_project_before_shutdown", 1)[1].split(
        "    def get_event_bus", 1
    )[0]
    assert "project_manager" not in shutdown_block
    assert "get_project_manager" not in shutdown_block
    assert "project_world_session_host" in shutdown_block

    player_source = (
        root
        / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/player/player_shell.py"
    ).read_text(encoding="utf-8")
    load_block = player_source.split("    def _load_project_scene", 1)[1].split(
        "    def _auto_start_playback", 1
    )[0]
    close_block = player_source.split("    def closeEvent", 1)[1].split(
        "def run_player_shell", 1
    )[0]
    assert "get_project_manager" not in load_block
    assert "get_project_manager" not in close_block
    assert "_project_world_host" in load_block
    assert "_project_world_host" in close_block

    standard_ui_source = (
        root
        / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/editor_extensions/standard_ui_plugin.py"
    ).read_text(encoding="utf-8")
    save_project_block = standard_ui_source.split("    def save_project(self):", 1)[1].split(
        "    def save_project_as", 1
    )[0]
    assert "get_project_manager" not in save_project_block
    assert "project_world_session_host" in save_project_block
