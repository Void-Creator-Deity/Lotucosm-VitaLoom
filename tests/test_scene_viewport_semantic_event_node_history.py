"""SceneViewport event-driven node mutations must use Runtime semantic history."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication

from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.scene.scene_manager import get_scene_manager
from core.VitaLoom.viewports.scene_viewport import SceneViewport


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_TEST_ROOT = ROOT / "workspace" / "state" / "test_temps"


class SceneViewportSemanticEventNodeHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        WORKSPACE_TEST_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp_root = Path(
            tempfile.mkdtemp(
                prefix="viewport_event_node_history_",
                dir=str(WORKSPACE_TEST_ROOT),
            )
        )
        self.project = self.temp_root / "project"
        self.scene = self.project / "scenes" / "main.pond"
        self.scene.parent.mkdir(parents=True)
        (self.project / "project.json").write_text('{"name": "Viewport Event Nodes"}', encoding="utf-8")
        self.scene.write_text(
            json.dumps(
                {
                    "entities": [
                        {
                            "id": "organism",
                            "name": "Organism",
                            "type": "organism",
                            "position": [100.0, 100.0],
                            "radius": 30.0,
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
        self._event_bus_sentinel = object()
        self._previous_event_bus = getattr(
            self.viewport.editor_context, "event_bus", self._event_bus_sentinel
        )
        self.viewport.editor_context.event_bus = Mock()
        self.viewport.resize(800, 600)
        self.viewport.load_scene_data(self.scene_manager.get_scene_data() or {})
        self._scene_loaded = lambda _path: self.viewport.load_scene_data(self.scene_manager.get_scene_data() or {})
        self.scene_manager.scene_loaded.connect(self._scene_loaded)

    def tearDown(self) -> None:
        try:
            self.scene_manager.scene_loaded.disconnect(self._scene_loaded)
        except (RuntimeError, TypeError):
            pass
        self.scene_manager.clear_scene(notify=False)
        if self._previous_event_bus is self._event_bus_sentinel:
            delattr(self.viewport.editor_context, "event_bus")
        else:
            self.viewport.editor_context.event_bus = self._previous_event_bus
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _scene_data(self) -> dict:
        return json.loads(self.scene.read_text(encoding="utf-8"))

    def _entity(self, entity_id: str) -> dict:
        return next(entity for entity in self._scene_data()["entities"] if entity["id"] == entity_id)

    def test_add_delete_and_history_restore_incident_connections_without_local_stack(self) -> None:
        self.assertFalse(hasattr(self.viewport, "command_stack"))
        self.assertTrue(self.viewport._add_node(QPointF(160.0, 100.0), "sensor"))
        self.assertEqual([node.id for node in self.viewport.selected_nodes], ["sensor_1"])
        self.assertEqual(self._entity("sensor_1")["position"], [160.0, 100.0])

        connected = self.registry.run(
            "connection.create",
            {
                "scene_path": str(self.scene),
                "connection": {"start": "organism", "end": "sensor_1", "weight": 2.5},
            },
        )
        self.assertTrue(connected["ok"], connected)
        self.assertTrue(self.scene_manager.load_scene(str(self.scene)))
        self.viewport.load_scene_data(self.scene_manager.get_scene_data() or {})
        self.viewport._select_rehydrated_nodes(["sensor_1"])

        self.assertTrue(self.viewport._delete_node())

        data = self._scene_data()
        self.assertEqual([entity["id"] for entity in data["entities"]], ["organism"])
        self.assertEqual(data["connections"], [])
        self.assertEqual(self.viewport.selected_nodes, [])

        self.assertTrue(self.viewport._run_global_scene_history_command("command.undo"))
        data = self._scene_data()
        self.assertEqual([entity["id"] for entity in data["entities"]], ["organism", "sensor_1"])
        self.assertEqual(data["connections"], [{"start": "organism", "end": "sensor_1", "weight": 2.5}])
        self.assertEqual([node.id for node in self.viewport.nodes], ["organism", "sensor_1"])

        self.assertTrue(self.viewport._run_global_scene_history_command("command.redo"))
        self.assertEqual([entity["id"] for entity in self._scene_data()["entities"]], ["organism"])
        self.assertEqual(self._scene_data()["connections"], [])

    def test_event_entity_creation_preserves_sprite_contract_without_local_stack(self) -> None:
        scripts = [{"name": "spin", "type": "Behaviour", "properties": {"speed": 3}}]
        self.assertFalse(hasattr(self.viewport, "command_stack"))
        self.assertTrue(
            self.viewport.create_entity_node(
                "Star",
                "sprite",
                [220.0, 180.0],
                "assets/star.png",
                scripts=scripts,
            )
        )

        self.assertEqual(len(self.viewport.selected_nodes), 1)
        created_id = self.viewport.selected_nodes[0].id
        entity = self._entity(created_id)
        self.assertEqual(entity["name"], "Star")
        self.assertEqual(entity["type"], "sprite")
        self.assertEqual(entity["position"], [220.0, 180.0])
        self.assertEqual(entity["sprite_path"], "assets/star.png")
        self.assertEqual(entity["scripts"], scripts)
        self.assertEqual(entity["radius"], 40.0)

    def test_failed_create_and_delete_emit_no_success_side_effects(self) -> None:
        created: list[bool] = []
        deleted: list[bool] = []
        modified: list[bool] = []
        executed: list[bool] = []
        self.viewport.signal_bus.object_created.connect(lambda *_args: created.append(True))
        self.viewport.signal_bus.object_deleted.connect(lambda *_args: deleted.append(True))
        self.viewport.projectModified.connect(lambda: modified.append(True))
        self.viewport.commandExecuted.connect(lambda: executed.append(True))
        self.assertFalse(hasattr(self.viewport, "command_stack"))

        with patch.object(self.viewport, "_run_scene_entity_create_command", return_value=False):
            self.assertFalse(self.viewport._add_node(QPointF(150.0, 100.0), "sensor"))
        self.assertEqual([entity["id"] for entity in self._scene_data()["entities"]], ["organism"])
        self.assertEqual(created, [])
        self.assertEqual(modified, [])
        self.assertEqual(executed, [])

        self.viewport._select_rehydrated_nodes(["organism"])
        failure = {"ok": False, "result": {}, "events": [], "warnings": [], "error": {"code": "blocked"}}
        with patch.object(self.viewport, "_run_scene_entity_delete_command", return_value=failure):
            self.assertFalse(self.viewport._delete_node())
        self.assertEqual([entity["id"] for entity in self._scene_data()["entities"]], ["organism"])
        self.assertEqual(deleted, [])
        self.assertEqual(modified, [])
        self.assertEqual(executed, [])

    def test_current_scene_command_failure_does_not_republish_create_event(self) -> None:
        with (
            patch.object(self.viewport, "_run_scene_entity_create_command", return_value=False),
            patch.object(self.viewport.editor_context.event_bus, "publish") as publish,
        ):
            self.assertFalse(
                self.viewport._create_entity_via_command_or_event("Sensor", "sensor", [120.0, 100.0])
            )
        self.assertFalse(any(call.args and call.args[0] == "create_entity" for call in publish.call_args_list))
        self.assertEqual([entity["id"] for entity in self._scene_data()["entities"]], ["organism"])



    def test_failed_scene_prefab_apply_is_terminal_without_legacy_create_event(self) -> None:
        modified: list[bool] = []
        executed: list[bool] = []
        self.viewport.projectModified.connect(lambda: modified.append(True))
        self.viewport.commandExecuted.connect(lambda: executed.append(True))

        with (
            patch.object(self.viewport, "_run_scene_placement_command", return_value=False) as place,
            patch.object(self.viewport, "_refresh_scene_after_command") as refresh,
            patch.object(self.viewport.editor_context.event_bus, "publish") as publish,
        ):
            self.assertFalse(
                self.viewport._apply_scene_prefab_placement(
                    str(self.scene),
                    str(self.project / "prefabs" / "crate.pond"),
                    "crate.pond",
                    [120.0, 100.0],
                )
            )

        self.assertEqual(place.call_args.args[0], "prefab.place")
        self.assertEqual(
            place.call_args.args[1],
            {
                "scene_path": str(self.scene),
                "prefab_path": str(self.project / "prefabs" / "crate.pond"),
                "entity_id": "crate",
                "position": [120.0, 100.0],
            },
        )
        self.assertFalse(any(call.args and call.args[0] == "create_entity" for call in publish.call_args_list))
        refresh.assert_not_called()
        self.assertEqual(modified, [])
        self.assertEqual(executed, [])
        self.assertEqual([entity["id"] for entity in self._scene_data()["entities"]], ["organism"])

    def test_successful_scene_prefab_apply_rehydrates_once_without_legacy_create_event(self) -> None:
        with (
            patch.object(self.viewport, "_run_scene_placement_command", return_value=True) as place,
            patch.object(self.viewport, "_refresh_scene_after_command") as refresh,
            patch.object(self.viewport.editor_context.event_bus, "publish") as publish,
        ):
            self.assertTrue(
                self.viewport._apply_scene_prefab_placement(
                    str(self.scene),
                    str(self.project / "prefabs" / "crate.pond"),
                    "crate.pond",
                    [120.0, 100.0],
                )
            )

        self.assertEqual(place.call_args.args[0], "prefab.place")
        refresh.assert_called_once_with(str(self.scene))
        self.assertFalse(any(call.args and call.args[0] == "create_entity" for call in publish.call_args_list))


    def test_failed_scene_asset_apply_is_terminal_without_legacy_create_event(self) -> None:
        modified: list[bool] = []
        executed: list[bool] = []
        self.viewport.projectModified.connect(lambda: modified.append(True))
        self.viewport.commandExecuted.connect(lambda: executed.append(True))

        with (
            patch.object(self.viewport, "_run_scene_placement_command", return_value=False) as apply_asset,
            patch.object(self.viewport, "_refresh_scene_after_command") as refresh,
            patch.object(self.viewport.editor_context.event_bus, "publish") as publish,
        ):
            self.assertFalse(
                self.viewport._apply_scene_asset_placement(
                    str(self.scene),
                    str(self.project / "assets" / "sprite.png"),
                    "sprite.png",
                    [120.0, 100.0],
                )
            )

        self.assertEqual(apply_asset.call_args.args[0], "asset.apply_to_scene")
        self.assertEqual(
            apply_asset.call_args.args[1],
            {
                "scene_path": str(self.scene),
                "asset_path": str(self.project / "assets" / "sprite.png"),
                "entity_id": "sprite",
                "name": "sprite.png",
                "entity_type": "asset",
                "position": [120.0, 100.0],
            },
        )
        self.assertFalse(any(call.args and call.args[0] == "create_entity" for call in publish.call_args_list))
        refresh.assert_not_called()
        self.assertEqual(modified, [])
        self.assertEqual(executed, [])
        self.assertEqual([entity["id"] for entity in self._scene_data()["entities"]], ["organism"])

    def test_successful_scene_asset_apply_rehydrates_once_without_legacy_create_event(self) -> None:
        with (
            patch.object(self.viewport, "_run_scene_placement_command", return_value=True) as apply_asset,
            patch.object(self.viewport, "_refresh_scene_after_command") as refresh,
            patch.object(self.viewport.editor_context.event_bus, "publish") as publish,
        ):
            self.assertTrue(
                self.viewport._apply_scene_asset_placement(
                    str(self.scene),
                    str(self.project / "assets" / "sprite.png"),
                    "sprite.png",
                    [120.0, 100.0],
                )
            )

        self.assertEqual(apply_asset.call_args.args[0], "asset.apply_to_scene")
        refresh.assert_called_once_with(str(self.scene))
        self.assertFalse(any(call.args and call.args[0] == "create_entity" for call in publish.call_args_list))

if __name__ == "__main__":
    unittest.main()
