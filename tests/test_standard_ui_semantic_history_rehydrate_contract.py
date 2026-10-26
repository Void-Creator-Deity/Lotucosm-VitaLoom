# -*- coding: utf-8 -*-
"""Standard UI respects semantic history rehydrate opt-out markers."""
from __future__ import annotations

from unittest.mock import Mock, patch


class _Registry:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.calls: list[tuple[str, dict]] = []

    def run(self, command_id: str, payload: dict) -> dict:
        self.calls.append((command_id, payload))
        if command_id in {"command.undo", "command.redo"}:
            return self.result
        return {"ok": True, "result": {}, "events": [], "warnings": [], "error": None}


def test_standard_ui_history_does_not_open_opted_out_manifest_only_scene() -> None:
    from builtin.editor_extensions.standard_ui_plugin import StandardUIPlugin

    result = {
        "ok": True,
        "result": {"scene_path": "workspace/projects/demo/scenes/main.pond", "history_rehydrate_scene": False},
        "events": [],
        "warnings": [],
        "error": None,
    }
    registry = _Registry(result)
    with patch("builtin.editor_extensions.standard_ui_plugin.get_command_registry", return_value=registry):
        observed = StandardUIPlugin()._run_semantic_history_command("command.undo")

    assert observed is result
    assert registry.calls == [("command.undo", {})]


def test_standard_ui_history_keeps_default_scene_rehydrate() -> None:
    from builtin.editor_extensions.standard_ui_plugin import StandardUIPlugin

    result = {
        "ok": True,
        "result": {"scene_path": "workspace/projects/demo/scenes/main.pond"},
        "events": [],
        "warnings": [],
        "error": None,
    }
    registry = _Registry(result)
    with patch("builtin.editor_extensions.standard_ui_plugin.get_command_registry", return_value=registry):
        StandardUIPlugin()._run_semantic_history_command("command.redo")

    assert registry.calls == [
        ("command.redo", {}),
        ("scene.open", {"scene_path": "workspace/projects/demo/scenes/main.pond"}),
    ]

def test_standard_ui_history_mirrors_scene_save_snapshot_without_scene_open() -> None:
    from builtin.editor_extensions.standard_ui_plugin import StandardUIPlugin

    scene_path = "workspace/projects/demo/scenes/main.pond"
    snapshot = {"name": "main", "nested": {"value": 3}}
    result = {
        "ok": True,
        "result": {
            "scene_path": scene_path,
            "scene_data": snapshot,
            "history_rehydrate_scene": False,
            "history_sync_host_scene": True,
        },
        "events": [],
        "warnings": [],
        "error": None,
    }
    registry = _Registry(result)
    manager = Mock()
    with (
        patch("builtin.editor_extensions.standard_ui_plugin.get_command_registry", return_value=registry),
        patch("core.VitaLoom.scene.scene_manager.get_scene_manager", return_value=manager),
    ):
        observed = StandardUIPlugin()._run_semantic_history_command("command.undo")

    assert observed is result
    assert registry.calls == [("command.undo", {})]
    manager.commit_persisted_scene.assert_called_once()
    call = manager.commit_persisted_scene.call_args
    assert call.args[0] == scene_path
    assert call.args[1] == snapshot
    assert call.args[1] is not snapshot

