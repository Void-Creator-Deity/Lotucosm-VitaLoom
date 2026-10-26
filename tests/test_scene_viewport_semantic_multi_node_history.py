# -*- coding: utf-8 -*-
"""SceneViewport multi-node drags must use one atomic Qt-free semantic history record."""
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

from core.VitaLoom.commands import runtime_commands
from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.scene.scene_manager import get_scene_manager
from core.VitaLoom.viewports.scene_viewport import SceneViewport


def _mouse_event(event_type, point, button, buttons, modifiers=Qt.KeyboardModifier.NoModifier):
    return QMouseEvent(
        event_type,
        QPointF(float(point.x()), float(point.y())),
        button,
        buttons,
        modifiers,
    )


class SceneViewportSemanticMultiNodeHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        workspace = Path(__file__).resolve().parents[1] / "workspace"
        self.temp_root = Path(tempfile.mkdtemp(prefix="viewport_multi_history_", dir=str(workspace)))
        self.project = self.temp_root / "project"
        self.scene = self.project / "scenes" / "main.pond"
        self.scene.parent.mkdir(parents=True)
        (self.project / "project.json").write_text('{"name": "Viewport Multi History"}', encoding="utf-8")
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

    def _node(self, node_id: str):
        return next(node for node in self.viewport.nodes if node.id == node_id)

    def _positions_on_disk(self) -> dict[str, list[float]]:
        data = json.loads(self.scene.read_text(encoding="utf-8"))
        return {str(entity["id"]): entity["position"] for entity in data["entities"]}

    def _positions_in_viewport(self) -> dict[str, list[float]]:
        return {str(node.id): [node.x, node.y] for node in self.viewport.nodes}

    def _drag_two_nodes(self, dx: int = 30, dy: int = 40) -> None:
        alpha = self._node("alpha")
        beta = self._node("beta")
        alpha_start = self.viewport._world_to_screen(QPointF(alpha.x, alpha.y))
        self.viewport.mousePressEvent(
            _mouse_event(
                QEvent.Type.MouseButtonPress,
                alpha_start,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
            )
        )
        self.viewport.mouseReleaseEvent(
            _mouse_event(
                QEvent.Type.MouseButtonRelease,
                alpha_start,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.NoButton,
            )
        )

        beta_start = self.viewport._world_to_screen(QPointF(beta.x, beta.y))
        self.viewport.mousePressEvent(
            _mouse_event(
                QEvent.Type.MouseButtonPress,
                beta_start,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.ControlModifier,
            )
        )
        target = beta_start + self.viewport._world_to_screen(QPointF(dx, dy)) - self.viewport._world_to_screen(QPointF(0, 0))
        self.viewport.mouseMoveEvent(
            _mouse_event(
                QEvent.Type.MouseMove,
                target,
                Qt.MouseButton.NoButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.ControlModifier,
            )
        )
        self.viewport.mouseReleaseEvent(
            _mouse_event(
                QEvent.Type.MouseButtonRelease,
                target,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.ControlModifier,
            )
        )

    def test_multi_node_drag_uses_single_semantic_batch_without_double_delta(self) -> None:
        self.assertFalse(hasattr(self.viewport, "command_stack"))
        self._drag_two_nodes()

        expected = {"alpha": [130.0, 140.0], "beta": [290.0, 140.0]}
        self.assertEqual(self._positions_on_disk(), expected)
        self.assertEqual(self._positions_in_viewport(), expected)

        self.assertTrue(self.viewport._run_global_scene_history_command("command.undo"))
        original = {"alpha": [100.0, 100.0], "beta": [260.0, 100.0]}
        self.assertEqual(self._positions_on_disk(), original)
        self.assertEqual(self._positions_in_viewport(), original)

        self.assertTrue(self.viewport._run_global_scene_history_command("command.redo"))
        self.assertEqual(self._positions_on_disk(), expected)
        self.assertEqual(self._positions_in_viewport(), expected)

    def test_failed_multi_node_drag_restores_all_preview_nodes_without_success_signals(self) -> None:
        modified: list[bool] = []
        executed: list[bool] = []
        self.viewport.projectModified.connect(lambda: modified.append(True))
        self.viewport.commandExecuted.connect(lambda: executed.append(True))
        failure = {"ok": False, "result": {}, "events": [], "warnings": [], "error": {"code": "blocked"}}
        self.assertFalse(hasattr(self.viewport, "command_stack"))

        with patch.object(self.viewport, "_run_scene_batch_transform_command", return_value=failure):
            self._drag_two_nodes()

        original = {"alpha": [100.0, 100.0], "beta": [260.0, 100.0]}
        self.assertEqual(self._positions_on_disk(), original)
        self.assertEqual(self._positions_in_viewport(), original)
        self.assertEqual(modified, [])
        self.assertEqual(executed, [])

    def test_invalid_batch_is_atomic_and_does_not_advance_history(self) -> None:
        original_text = self.scene.read_text(encoding="utf-8")
        failed = self.registry.run(
            "transform.batch_set",
            {
                "scene_path": str(self.scene),
                "transforms": [
                    {"entity_id": "alpha", "position": [130.0, 140.0]},
                    {"entity_id": "alpha", "position": [290.0, 140.0]},
                ],
            },
        )

        self.assertFalse(failed["ok"])
        self.assertEqual(failed["error"]["code"], "duplicate_entity_id")
        self.assertEqual(self.scene.read_text(encoding="utf-8"), original_text)
        undo = self.registry.run("command.undo", {})
        self.assertFalse(undo["ok"])
        self.assertEqual(undo["error"]["code"], "undo_empty")

    def test_batch_validates_all_entities_before_one_write(self) -> None:
        original_text = self.scene.read_text(encoding="utf-8")
        with patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
            failed = self.registry.run(
                "transform.batch_set",
                {
                    "scene_path": str(self.scene),
                    "transforms": [
                        {"entity_id": "alpha", "position": [130.0, 140.0]},
                        {"entity_id": "missing", "position": [290.0, 140.0]},
                    ],
                },
            )

        self.assertFalse(failed["ok"])
        self.assertEqual(failed["error"]["code"], "entity_not_found")
        self.assertEqual(write_json.call_count, 0)
        self.assertEqual(self.scene.read_text(encoding="utf-8"), original_text)
        self.assertFalse(self.registry.run("command.undo", {})["ok"])

        with patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
            changed = self.registry.run(
                "transform.batch_set",
                {
                    "scene_path": str(self.scene),
                    "transforms": [
                        {"entity_id": "alpha", "position": [130.0, 140.0]},
                        {"entity_id": "beta", "position": [290.0, 140.0]},
                    ],
                },
            )

        self.assertTrue(changed["ok"], changed)
        self.assertEqual(write_json.call_count, 1)
        self.assertEqual(self._positions_on_disk(), {"alpha": [130.0, 140.0], "beta": [290.0, 140.0]})
    def test_fresh_registry_can_durably_undo_and_redo_batch_transform(self) -> None:
        changed = self.registry.run(
            "transform.batch_set",
            {
                "scene_path": str(self.scene),
                "transforms": [
                    {"entity_id": "alpha", "position": [130.0, 140.0]},
                    {"entity_id": "beta", "position": [290.0, 140.0]},
                ],
            },
        )
        self.assertTrue(changed["ok"], changed)
        self.assertEqual(self._positions_on_disk(), {"alpha": [130.0, 140.0], "beta": [290.0, 140.0]})

        undone = reset_command_registry().run("command.undo_project", {"project_path": str(self.project)})
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(self._positions_on_disk(), {"alpha": [100.0, 100.0], "beta": [260.0, 100.0]})

        redone = reset_command_registry().run("command.redo_project", {"project_path": str(self.project)})
        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._positions_on_disk(), {"alpha": [130.0, 140.0], "beta": [290.0, 140.0]})


if __name__ == "__main__":
    unittest.main()