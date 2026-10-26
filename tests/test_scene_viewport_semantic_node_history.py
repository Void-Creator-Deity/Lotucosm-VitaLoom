"""SceneViewport single-node drag must use the Qt-free semantic history authority."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QKeyEvent, QMouseEvent
from PyQt6.QtWidgets import QApplication

from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.scene.scene_manager import get_scene_manager
from core.VitaLoom.ui.command_actions import register_editor_command_actions
from core.VitaLoom.viewports.scene_viewport import SceneViewport


class _Shortcuts:
    def __init__(self) -> None:
        self.registered: dict[str, object] = {}

    def register_shortcut(self, shortcut_id, callback, description="", context=None, key_sequence=None):
        self.registered[shortcut_id] = {
            "callback": callback,
            "description": description,
            "context": context,
            "key_sequence": key_sequence,
        }


def _mouse_event(event_type, point, button, buttons):
    return QMouseEvent(
        event_type,
        QPointF(float(point.x()), float(point.y())),
        button,
        buttons,
        Qt.KeyboardModifier.NoModifier,
    )


class SceneViewportSemanticNodeHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        workspace = Path(__file__).resolve().parents[1] / "workspace"
        self.temp_root = Path(tempfile.mkdtemp(prefix="viewport_semantic_history_", dir=str(workspace)))
        self.project = self.temp_root / "project"
        self.scene = self.project / "scenes" / "main.pond"
        self.scene.parent.mkdir(parents=True)
        (self.project / "project.json").write_text('{"name": "Viewport History"}', encoding="utf-8")
        self.scene.write_text(
            json.dumps(
                {
                    "entities": [
                        {
                            "id": "hero",
                            "name": "Hero",
                            "type": "organism",
                            "position": [100.0, 100.0],
                            "radius": 16.0,
                            "scripts": [],
                        }
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

    def _drag_hero(self, dx: int = 30, dy: int = 40) -> None:
        hero = next(node for node in self.viewport.nodes if node.id == "hero")
        start = self.viewport._world_to_screen(QPointF(hero.x, hero.y))
        end = start + self.viewport._world_to_screen(QPointF(dx, dy)) - self.viewport._world_to_screen(QPointF(0, 0))
        self.viewport.mousePressEvent(
            _mouse_event(
                QEvent.Type.MouseButtonPress,
                start,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
            )
        )
        self.viewport.mouseMoveEvent(
            _mouse_event(
                QEvent.Type.MouseMove,
                end,
                Qt.MouseButton.NoButton,
                Qt.MouseButton.LeftButton,
            )
        )
        self.viewport.mouseReleaseEvent(
            _mouse_event(
                QEvent.Type.MouseButtonRelease,
                end,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.NoButton,
            )
        )

    def _disk_position(self) -> list[float]:
        data = json.loads(self.scene.read_text(encoding="utf-8"))
        entity = next(row for row in data["entities"] if row["id"] == "hero")
        return entity["position"]

    def _viewport_position(self) -> list[float]:
        node = next(node for node in self.viewport.nodes if node.id == "hero")
        return [node.x, node.y]

    def test_single_node_drag_uses_registry_and_global_history_rehydrates_viewport(self) -> None:
        shortcuts = _Shortcuts()
        register_editor_command_actions(shortcut_manager=shortcuts, registry=self.registry)
        self.assertFalse(hasattr(self.viewport, "command_stack"))

        self._drag_hero()
        self.assertEqual(self._disk_position(), [130.0, 140.0])
        self.assertEqual(self._viewport_position(), [130.0, 140.0])

        shortcuts.registered["edit.undo"]["callback"]()
        self.assertEqual(self._disk_position(), [100.0, 100.0])
        self.assertEqual(self._viewport_position(), [100.0, 100.0])

        shortcuts.registered["edit.redo"]["callback"]()
        self.assertEqual(self._disk_position(), [130.0, 140.0])
        self.assertEqual(self._viewport_position(), [130.0, 140.0])

        self.viewport.keyPressEvent(
            QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        )
        self.assertEqual(self._disk_position(), [100.0, 100.0])
        self.assertEqual(self._viewport_position(), [100.0, 100.0])

        self.viewport.keyPressEvent(
            QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
        )
        self.assertEqual(self._disk_position(), [130.0, 140.0])
        self.assertEqual(self._viewport_position(), [130.0, 140.0])

    def test_failed_single_node_drag_restores_preview_without_emitting_success_signals(self) -> None:
        modified: list[bool] = []
        executed: list[bool] = []
        self.viewport.projectModified.connect(lambda: modified.append(True))
        self.viewport.commandExecuted.connect(lambda: executed.append(True))

        failure = {"ok": False, "result": {}, "events": [], "warnings": [], "error": {"code": "blocked"}}
        with patch.object(self.viewport, "_run_scene_transform_command", return_value=failure):
            self._drag_hero()

        self.assertFalse(hasattr(self.viewport, "command_stack"))
        self.assertEqual(self._disk_position(), [100.0, 100.0])
        self.assertEqual(self._viewport_position(), [100.0, 100.0])
        self.assertEqual(modified, [])
        self.assertEqual(executed, [])

    def test_viewport_shortcuts_route_directly_to_global_history_without_local_stack(self) -> None:
        self.assertFalse(hasattr(self.viewport, "command_stack"))
        with patch.object(
            self.viewport,
            "_run_global_scene_history_command",
            return_value=True,
        ) as semantic_history:
            self.viewport.keyPressEvent(
                QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
            )
            self.viewport.keyPressEvent(
                QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
            )

        self.assertEqual(
            [entry.args[0] for entry in semantic_history.call_args_list],
            ["command.undo", "command.redo"],
        )

    def test_invalid_transform_does_not_advance_semantic_history(self) -> None:
        failed = self.registry.run(
            "transform.set",
            {
                "scene_path": str(self.scene),
                "entity_id": "missing",
                "position": [1.0, 2.0],
            },
        )

        self.assertFalse(failed["ok"])
        undo = self.registry.run("command.undo", {})
        self.assertFalse(undo["ok"])
        self.assertEqual(undo["error"]["code"], "undo_empty")
        self.assertEqual(self._disk_position(), [100.0, 100.0])


if __name__ == "__main__":
    unittest.main()
