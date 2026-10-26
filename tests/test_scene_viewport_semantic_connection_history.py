# -*- coding: utf-8 -*-
"""SceneViewport connection mutations must use durable Qt-free command history."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication

from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.scene.scene_manager import get_scene_manager
from core.VitaLoom.viewports.scene_viewport import SceneViewport


def _mouse_event(event_type, point, button, buttons):
    return QMouseEvent(
        event_type,
        QPointF(float(point.x()), float(point.y())),
        button,
        buttons,
        Qt.KeyboardModifier.NoModifier,
    )


class SceneViewportSemanticConnectionHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        workspace = Path(__file__).resolve().parents[1] / "workspace"
        self.temp_root = Path(tempfile.mkdtemp(prefix="viewport_connection_history_", dir=str(workspace)))
        self.project = self.temp_root / "project"
        self.scene = self.project / "scenes" / "main.pond"
        self.scene.parent.mkdir(parents=True)
        (self.project / "project.json").write_text('{"name": "Viewport Connection History"}', encoding="utf-8")
        self.scene.write_text(
            json.dumps(
                {
                    "entities": [
                        {"id": "alpha", "name": "Alpha", "type": "game_prop", "position": [100.0, 100.0], "scripts": []},
                        {"id": "beta", "name": "Beta", "type": "game_prop", "position": [260.0, 100.0], "scripts": []},
                    ],
                    "connections": [],
                    "components": [],
                }
            ),
            encoding="utf-8",
        )
        self.registry = reset_command_registry()
        self.scene_manager = get_scene_manager()
        self.assertTrue(self.scene_manager.load_scene(str(self.scene)))
        self.viewport = SceneViewport()
        self.viewport.resize(800, 600)
        self.viewport.load_scene_data(self.scene_manager.get_scene_data())
        self._scene_loaded = lambda _path: self.viewport.load_scene_data(self.scene_manager.get_scene_data() or {})
        self.scene_manager.scene_loaded.connect(self._scene_loaded)

    def tearDown(self) -> None:
        try:
            self.scene_manager.scene_loaded.disconnect(self._scene_loaded)
        except (RuntimeError, TypeError):
            pass
        self.scene_manager.clear_scene(notify=False)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _disk_connections(self) -> list[dict]:
        return json.loads(self.scene.read_text(encoding="utf-8")).get("connections", [])

    def _node(self, node_id: str):
        return next(node for node in self.viewport.nodes if node.id == node_id)

    def _create_connection_with_mouse_release(self) -> None:
        alpha = self._node("alpha")
        beta = self._node("beta")
        self.viewport.selected_node = alpha
        self.viewport.selected_nodes = [alpha]
        self.viewport._start_connection()
        target = self.viewport._world_to_screen(QPointF(beta.x, beta.y))
        self.viewport.mouseReleaseEvent(
            _mouse_event(
                QEvent.Type.MouseButtonRelease,
                target,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.NoButton,
            )
        )

    def test_connection_create_uses_registry_rehydrates_and_global_history(self) -> None:
        self.assertFalse(hasattr(self.viewport, "command_stack"))
        self._create_connection_with_mouse_release()
        self.assertEqual(self._disk_connections(), [{"start": "alpha", "end": "beta", "weight": 1.0}])
        self.assertEqual(len(self.viewport.connections), 1)

        self.assertTrue(self.viewport._run_global_scene_history_command("command.undo"))
        self.assertEqual(self._disk_connections(), [])
        self.assertEqual(len(self.viewport.connections), 0)

        self.assertTrue(self.viewport._run_global_scene_history_command("command.redo"))
        self.assertEqual(self._disk_connections(), [{"start": "alpha", "end": "beta", "weight": 1.0}])
        self.assertEqual(len(self.viewport.connections), 1)

    def test_right_click_connection_delete_uses_registry_and_global_history(self) -> None:
        created = self.registry.run(
            "connection.create",
            {"scene_path": str(self.scene), "connection": {"start": "alpha", "end": "beta", "weight": 2.5}},
        )
        self.assertTrue(created["ok"], created)
        self.assertTrue(self.scene_manager.load_scene(str(self.scene)))
        self.viewport.load_scene_data(self.scene_manager.get_scene_data())
        midpoint = self.viewport._world_to_screen(QPointF(180.0, 100.0))

        self.assertFalse(hasattr(self.viewport, "command_stack"))
        self.viewport.mousePressEvent(
            _mouse_event(
                QEvent.Type.MouseButtonPress,
                midpoint,
                Qt.MouseButton.RightButton,
                Qt.MouseButton.RightButton,
            )
        )
        self.assertEqual(self._disk_connections(), [])
        self.assertEqual(len(self.viewport.connections), 0)

        self.assertTrue(self.viewport._run_global_scene_history_command("command.undo"))
        self.assertEqual(self._disk_connections(), [{"start": "alpha", "end": "beta", "weight": 2.5}])
        self.assertEqual(len(self.viewport.connections), 1)

    def test_failed_connection_create_keeps_preview_state_and_does_not_emit_success(self) -> None:
        modified: list[bool] = []
        executed: list[bool] = []
        self.viewport.projectModified.connect(lambda: modified.append(True))
        self.viewport.commandExecuted.connect(lambda: executed.append(True))
        failure = {"ok": False, "result": {}, "events": [], "warnings": [], "error": {"code": "blocked"}}
        self.assertFalse(hasattr(self.viewport, "command_stack"))

        with patch.object(self.viewport, "_run_scene_connection_command", return_value=failure):
            self._create_connection_with_mouse_release()

        self.assertEqual(self._disk_connections(), [])
        self.assertEqual(self.viewport.connections, [])
        self.assertFalse(self.viewport.connecting)
        self.assertIsNone(self.viewport.connect_start_node)
        self.assertEqual(modified, [])
        self.assertEqual(executed, [])

    def test_connection_delete_rejects_stale_duplicate_protection_without_writing_or_history(self) -> None:
        self.scene.write_text(
            json.dumps(
                {
                    "entities": [{"id": "alpha"}, {"id": "beta"}],
                    "connections": [{"from": "alpha", "to": "beta", "weight": 1.0}],
                }
            ),
            encoding="utf-8",
        )
        failed = self.registry.run(
            "connection.delete",
            {
                "scene_path": str(self.scene),
                "connection": {"start": "alpha", "end": "beta", "weight": 9.0},
                "connection_index": 0,
            },
        )
        self.assertFalse(failed["ok"])
        self.assertEqual(failed["error"]["code"], "connection_mismatch")
        self.assertEqual(self._disk_connections(), [{"from": "alpha", "to": "beta", "weight": 1.0}])
        self.assertEqual(self.registry.run("command.undo", {})["error"]["code"], "undo_empty")

    def test_fresh_registry_durable_undo_redo_preserves_connection_index_and_legacy_entries(self) -> None:
        self.scene.write_text(
            json.dumps(
                {
                    "entities": [{"id": "alpha"}, {"id": "beta"}],
                    "connections": [{"from": "beta", "to": "alpha"}],
                }
            ),
            encoding="utf-8",
        )
        created = self.registry.run(
            "connection.create",
            {
                "scene_path": str(self.scene),
                "connection": {"start": "alpha", "end": "beta", "weight": 3.0},
            },
        )
        self.assertTrue(created["ok"], created)
        self.assertEqual(created["result"]["connection_index"], 1)

        undo_registry = reset_command_registry()
        undone = undo_registry.run("command.undo_project", {"project_path": str(self.project)})
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(self._disk_connections(), [{"from": "beta", "to": "alpha"}])

        redo_registry = reset_command_registry()
        redone = redo_registry.run("command.redo_project", {"project_path": str(self.project)})
        self.assertTrue(redone["ok"], redone)
        self.assertEqual(
            self._disk_connections(),
            [
                {"from": "beta", "to": "alpha"},
                {"start": "alpha", "end": "beta", "weight": 3.0},
            ],
        )


    def test_connection_set_weight_guards_exact_slot_and_supports_runtime_and_durable_history(self) -> None:
        self.scene.write_text(
            json.dumps(
                {
                    "entities": [{"id": "alpha"}, {"id": "beta"}],
                    "connections": [
                        {"start": "alpha", "end": "beta", "weight": 1.0},
                        {"from": "beta", "to": "alpha", "weight": 2.0},
                    ],
                }
            ),
            encoding="utf-8",
        )
        changed = self.registry.run(
            "connection.set_weight",
            {
                "scene_path": str(self.scene),
                "connection_index": 1,
                "connection": {"start": "beta", "end": "alpha", "weight": 2.0},
                "weight": 3.5,
            },
        )
        self.assertTrue(changed["ok"], changed)
        self.assertEqual(changed["result"]["old_connection"], {"start": "beta", "end": "alpha", "weight": 2.0})
        self.assertEqual(changed["result"]["new_connection"], {"start": "beta", "end": "alpha", "weight": 3.5})
        self.assertEqual(
            self._disk_connections(),
            [
                {"start": "alpha", "end": "beta", "weight": 1.0},
                {"from": "beta", "to": "alpha", "weight": 3.5},
            ],
        )

        self.assertTrue(self.registry.run("command.undo", {})["ok"])
        self.assertEqual(self._disk_connections()[1]["weight"], 2.0)
        self.assertTrue(self.registry.run("command.redo", {})["ok"])
        self.assertEqual(self._disk_connections()[1]["weight"], 3.5)

        undo_registry = reset_command_registry()
        undone = undo_registry.run("command.undo_project", {"project_path": str(self.project)})
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(self._disk_connections()[1]["weight"], 2.0)
        redo_registry = reset_command_registry()
        redone = redo_registry.run("command.redo_project", {"project_path": str(self.project)})
        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._disk_connections()[1]["weight"], 3.5)

    def test_connection_set_weight_rejects_stale_or_nonfinite_values_without_writing_history(self) -> None:
        self.scene.write_text(
            json.dumps(
                {
                    "entities": [{"id": "alpha"}, {"id": "beta"}],
                    "connections": [{"start": "alpha", "end": "beta", "weight": 1.0}],
                }
            ),
            encoding="utf-8",
        )
        original = self.scene.read_text(encoding="utf-8")
        cases = [
            ({"connection": {"start": "alpha", "end": "beta", "weight": 9.0}, "weight": 2.0}, "connection_mismatch"),
            ({"connection": {"start": "alpha", "end": "beta", "weight": 1.0}, "weight": float("nan")}, "invalid_connection_weight"),
            ({"connection": {"start": "alpha", "end": "beta", "weight": 1.0}, "weight": float("inf")}, "invalid_connection_weight"),
            ({"connection": {"start": "alpha", "end": "beta", "weight": 1.0}, "weight": True}, "invalid_connection_weight"),
        ]
        for patch_payload, error_code in cases:
            payload = {"scene_path": str(self.scene), "connection_index": 0, **patch_payload}
            failed = self.registry.run("connection.set_weight", payload)
            self.assertFalse(failed["ok"])
            self.assertEqual(failed["error"]["code"], error_code)
            self.assertEqual(self.scene.read_text(encoding="utf-8"), original)
        self.assertEqual(self.registry.run("command.undo", {})["error"]["code"], "undo_empty")


if __name__ == "__main__":
    unittest.main()
