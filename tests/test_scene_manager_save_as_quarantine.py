# -*- coding: utf-8 -*-
"""E202 regression: latent legacy Save As is failure-atomic and non-semantic."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.scene.scene_manager import SceneManager
from core.VitaLoom.scene.scene_persistence import ScenePersistenceError


def _legacy_host(scene_path: Path, scene_data: dict) -> SimpleNamespace:
    host = SimpleNamespace(
        _current_scene_path=str(scene_path),
        _current_scene_data=scene_data,
        _scene_modified=True,
        editor_context=SimpleNamespace(current_scene=scene_data),
        scene_saved=Mock(),
        scene_modified=Mock(),
        signal_bus=SimpleNamespace(emit_scene_saved=Mock()),
    )
    host.commit_persisted_scene = SceneManager.commit_persisted_scene.__get__(host, type(host))
    host.save_scene = SceneManager.save_scene.__get__(host, type(host))
    return host


def test_latent_save_as_leaves_legacy_host_untouched_when_persistence_fails(tmp_path: Path) -> None:
    source = tmp_path / "source.pond"
    original = {"name": "source", "entities": [{"id": "entity-1"}]}
    host = _legacy_host(source, original)

    with patch(
        "core.VitaLoom.scene.scene_persistence.persist_scene_snapshot",
        side_effect=ScenePersistenceError("scene_write_failed", "no write"),
    ):
        ok = SceneManager.save_scene_as(host, str(tmp_path / "copy.pond"))

    assert ok is False
    assert host._current_scene_path == str(source)
    assert host._current_scene_data is original
    assert host._current_scene_data == original
    assert host.editor_context.current_scene is original
    assert host._scene_modified is True
    host.scene_saved.emit.assert_not_called()
    host.scene_modified.emit.assert_not_called()
    host.signal_bus.emit_scene_saved.assert_not_called()


def test_latent_save_as_persists_detached_target_then_updates_host_without_history_or_audit(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    scenes = project / "scenes"
    scenes.mkdir(parents=True)
    (project / "project.json").write_text('{"name": "Save As Contract"}', encoding="utf-8")
    source = scenes / "source.pond"
    source_data = {"name": "source", "entities": [{"id": "entity-1"}]}
    source.write_text(json.dumps(source_data, ensure_ascii=False), encoding="utf-8")
    target = scenes / "copy.pond"
    host = _legacy_host(source, source_data)
    registry = reset_command_registry()

    ok = SceneManager.save_scene_as(host, str(target))

    assert ok is True
    assert host._current_scene_path == str(target)
    assert host._current_scene_data is host.editor_context.current_scene
    assert host._current_scene_data is not source_data
    assert host._current_scene_data["name"] == "copy"
    assert host._current_scene_data["entities"] == source_data["entities"]
    assert host._current_scene_data["modified_at"]
    assert host._scene_modified is False
    host.scene_saved.emit.assert_called_once_with(str(target))
    host.scene_modified.emit.assert_called_once_with(False)
    host.signal_bus.emit_scene_saved.assert_called_once_with(str(target))

    persisted = json.loads(target.read_text(encoding="utf-8"))
    assert persisted == host._current_scene_data
    assert json.loads(source.read_text(encoding="utf-8")) == source_data
    assert not (project / ".vitaloom" / "command_audit.jsonl").exists()
    undo = registry.run("command.undo", {})
    assert undo["ok"] is False
    assert undo["error"]["code"] == "undo_empty"
