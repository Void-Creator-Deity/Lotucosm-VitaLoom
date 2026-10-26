"""
Inspector 属性映射：组件字段与 UI 键对齐。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from core.VitaLoom.docks.inspector import InspectorPanel
from core.VitaLoom.inspector.transient_property import write_property


WORKSPACE_TEST_ROOT = (
    Path(__file__).resolve().parents[1] / "workspace" / "state" / "test_temps"
)


class _DummyConnection:
    def __init__(self, weight=1.0):
        self.start_node = object()
        self.end_node = object()
        self.weight = weight

    def to_dict(self):
        return {"start": "alpha", "end": "beta", "weight": self.weight}


class _DummyNode:
    def __init__(self):
        self.id = "node_1"
        self.x = 1.0
        self.y = 2.0
        self.name = "old_name"

    def update_position(self, x, y):
        self.x = x
        self.y = y


class _RecordingRegistry:
    """Small Registry-shaped test double that preserves transient mutation semantics."""

    def __init__(self):
        self.targets = {}
        self.calls = []

    def bind_transient_target(self, target):
        token = f"target-{len(self.targets) + 1}"
        self.targets[token] = target
        return token

    def run(self, command_id, payload):
        self.calls.append((command_id, payload))
        if command_id == "inspector.set_property":
            target = self.targets[payload["target_token"]]
            write_property(target, payload["property_path"], payload.get("value"), payload.get("present", True))
        return {"ok": True, "result": {}, "events": [], "warnings": [], "error": None}


class InspectorPropertyMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.panel = InspectorPanel()

    def test_position_x_maps_to_node_x_through_local_fallback(self):
        node = _DummyNode()

        self.panel._on_property_changed("position_x", 123.0, [node])
        self.assertEqual(node.x, 123.0)

    def test_non_scene_node_does_not_attempt_scene_registry_or_scene_sync(self):
        node = _DummyNode()
        registry_calls = []
        update_calls = []

        class _Registry(_RecordingRegistry):
            def run(self, command_id, payload):
                result = super().run(command_id, payload)
                registry_calls.append((command_id, payload))
                return result

        class _SceneManager:
            def get_current_scene_path(self):
                return "workspace/projects/demo/scenes/main.pond"

            def get_scene_data(self):
                return {"entities": [{"id": "hero", "position": [1.0, 2.0]}]}

            def update_scene_data(self, data):
                update_calls.append(data)

        with (
            patch("core.VitaLoom.docks.inspector.get_command_registry", return_value=_Registry()),
            patch("core.VitaLoom.scene.scene_manager.get_scene_manager", return_value=_SceneManager()),
        ):
            self.panel._on_property_changed("position_x", 123.0, [node])

        self.assertEqual(node.x, 123.0)
        self.assertEqual(registry_calls[0][0], "inspector.set_property")
        self.assertEqual(update_calls, [])

    def test_string_field_uses_text_submit(self):
        node = _DummyNode()
        self.panel._on_property_changed("name", "new_name", [node])
        self.assertEqual(node.name, "new_name")

    def test_dict_position_sync_routes_through_transform_command(self):
        entity = {"id": "hero", "position": [1.0, 2.0], "scripts": []}
        calls = []

        class _Registry:
            def run(self, command_id, payload):
                calls.append((command_id, payload))
                return {"ok": True, "result": {}, "events": [], "warnings": [], "error": None}

        with patch("core.VitaLoom.docks.inspector.get_command_registry", return_value=_Registry()):
            ok = self.panel._sync_scene_entity_data_via_command(
                "workspace/projects/demo/scenes/main.pond",
                entity,
                "hero",
                "position_x",
                7.5,
            )

        self.assertTrue(ok)
        self.assertEqual(calls[0][0], "transform.set")
        self.assertEqual(calls[0][1]["entity_id"], "hero")
        self.assertEqual(calls[0][1]["position"], [7.5, 2.0])

    def test_rejected_scene_entity_position_edit_does_not_fallback_or_rehydrate(self):
        entity = {"id": "hero", "position": [1.0, 2.0], "scripts": []}
        calls = []
        project_modified = []
        command_executed = []

        class _Registry:
            def run(self, command_id, payload):
                calls.append((command_id, payload))
                return {"ok": False, "result": {}, "events": [], "warnings": [], "error": {"code": "stale_transform_position", "message": "position changed elsewhere"}}

        class _SceneManager:
            def get_current_scene_path(self):
                return "workspace/projects/demo/scenes/main.pond"

            def get_scene_data(self):
                return {"entities": [entity]}

        self.panel.projectModified.connect(lambda: project_modified.append(True))
        self.panel.commandExecuted.connect(lambda: command_executed.append(True))
        with (
            patch("core.VitaLoom.docks.inspector.get_command_registry", return_value=_Registry()),
            patch("core.VitaLoom.scene.scene_manager.get_scene_manager", return_value=_SceneManager()),
        ):
            self.panel._on_property_changed("position_x", 7.5, [entity])

        self.assertEqual(entity["position"], [1.0, 2.0])
        self.assertEqual(project_modified, [])
        self.assertEqual(command_executed, [])
        self.assertEqual(calls, [("transform.set", {"scene_path": "workspace/projects/demo/scenes/main.pond", "entity_id": "hero", "position": [7.5, 2.0]})])

    def test_inspector_position_edit_rehydrates_scene_for_global_undo_redo(self):
        from core.VitaLoom.commands.registry import reset_command_registry
        from core.VitaLoom.scene.scene_manager import get_scene_manager
        from core.VitaLoom.ui.command_actions import register_editor_command_actions

        class _Shortcuts:
            def __init__(self):
                self.registered = {}

            def register_shortcut(self, shortcut_id, callback, description="", context=None, key_sequence=None):
                self.registered[shortcut_id] = callback

        WORKSPACE_TEST_ROOT.mkdir(parents=True, exist_ok=True)
        temp_root = Path(
            tempfile.mkdtemp(
                prefix="inspector_position_history_",
                dir=str(WORKSPACE_TEST_ROOT),
            )
        )
        project = temp_root / "project"
        scene = project / "scenes" / "main.pond"
        scene.parent.mkdir(parents=True)
        (project / "project.json").write_text('{"name": "Inspector Position History"}', encoding="utf-8")
        scene.write_text(json.dumps({"entities": [{"id": "hero", "position": [1.0, 2.0], "scripts": []}], "components": []}), encoding="utf-8")
        try:
            registry = reset_command_registry()
            scene_manager = get_scene_manager()
            self.assertTrue(scene_manager.load_scene(str(scene)))
            entity = scene_manager.get_scene_data()["entities"][0]

            self.panel._on_property_changed("position_x", 7.5, [entity])
            self.assertEqual(self._scene_entity(scene)["position"], [7.5, 2.0])
            self.assertEqual(scene_manager.get_scene_data()["entities"][0]["position"], [7.5, 2.0])

            shortcuts = _Shortcuts()
            register_editor_command_actions(shortcut_manager=shortcuts, registry=registry, context=self.panel)
            shortcuts.registered["edit.undo"]()
            self.assertEqual(self._scene_entity(scene)["position"], [1.0, 2.0])
            self.assertEqual(scene_manager.get_scene_data()["entities"][0]["position"], [1.0, 2.0])

            shortcuts.registered["edit.redo"]()
            self.assertEqual(self._scene_entity(scene)["position"], [7.5, 2.0])
            self.assertEqual(scene_manager.get_scene_data()["entities"][0]["position"], [7.5, 2.0])
        finally:
            reset_command_registry()
            shutil.rmtree(temp_root, ignore_errors=True)

    def test_script_field_sync_routes_through_script_command(self):
        entity = {
            "id": "hero",
            "scripts": [{"name": "brain", "properties": {"mind": {"level": 1}}}],
        }
        calls = []

        class _Registry:
            def run(self, command_id, payload):
                calls.append((command_id, payload))
                return {"ok": True, "result": {}, "events": [], "warnings": [], "error": None}

        with patch("core.VitaLoom.docks.inspector.get_command_registry", return_value=_Registry()):
            ok = self.panel._sync_scene_entity_data_via_command(
                "workspace/projects/demo/scenes/main.pond",
                entity,
                "hero",
                "script_brain_mind.level",
                3,
            )

        self.assertTrue(ok)
        self.assertEqual(calls[0][0], "script.set_property")
        self.assertEqual(calls[0][1]["entity_id"], "hero")
        self.assertEqual(calls[0][1]["script"], "brain")
        self.assertEqual(calls[0][1]["property_path"], "mind.level")
        self.assertEqual(calls[0][1]["value"], 3)

    def test_inspector_semantic_edit_rehydrates_scene_for_global_undo_redo(self):
        from core.VitaLoom.commands.registry import reset_command_registry
        from core.VitaLoom.scene.scene_manager import get_scene_manager
        from core.VitaLoom.ui.command_actions import register_editor_command_actions

        class _Shortcuts:
            def __init__(self):
                self.registered = {}

            def register_shortcut(self, shortcut_id, callback, description="", context=None, key_sequence=None):
                self.registered[shortcut_id] = callback

        workspace = Path(__file__).resolve().parents[1] / "workspace"
        temp_root = Path(tempfile.mkdtemp(prefix="inspector_semantic_history_", dir=str(workspace)))
        project = temp_root / "project"
        scene = project / "scenes" / "main.pond"
        scene.parent.mkdir(parents=True)
        (project / "project.json").write_text('{"name": "Inspector History"}', encoding="utf-8")
        scene.write_text(
            json.dumps({"entities": [{"id": "hero", "energy": 9.0, "scripts": []}], "components": []}),
            encoding="utf-8",
        )
        try:
            registry = reset_command_registry()
            scene_manager = get_scene_manager()
            self.assertTrue(scene_manager.load_scene(str(scene)))
            entity = scene_manager.get_scene_data()["entities"][0]

            self.panel._on_property_changed("energy", 12.5, [entity])
            self.assertEqual(self._scene_entity(scene)["energy"], 12.5)
            self.assertEqual(scene_manager.get_scene_data()["entities"][0]["energy"], 12.5)

            shortcuts = _Shortcuts()
            register_editor_command_actions(shortcut_manager=shortcuts, registry=registry, context=self.panel)
            shortcuts.registered["edit.undo"]()

            self.assertEqual(self._scene_entity(scene)["energy"], 9.0)
            self.assertEqual(scene_manager.get_scene_data()["entities"][0]["energy"], 9.0)

            shortcuts.registered["edit.redo"]()

            self.assertEqual(self._scene_entity(scene)["energy"], 12.5)
            self.assertEqual(scene_manager.get_scene_data()["entities"][0]["energy"], 12.5)
        finally:
            reset_command_registry()
            shutil.rmtree(temp_root, ignore_errors=True)

    @staticmethod
    def _scene_entity(scene: Path):
        data = json.loads(scene.read_text(encoding="utf-8"))
        return next(entity for entity in data["entities"] if entity.get("id") == "hero")

    def test_generic_property_change_uses_semantic_registry_without_local_command_stack(self):
        entity = {"id": "hero", "energy": 9.0, "scripts": []}
        calls = []

        class _Registry:
            def run(self, command_id, payload):
                calls.append((command_id, payload))
                return {"ok": True, "result": {}, "events": [], "warnings": [], "error": None}

        class _SceneManager:
            def get_current_scene_path(self):
                return "workspace/projects/demo/scenes/main.pond"

            def get_scene_data(self):
                return {"entities": [entity]}

        with (
            patch("core.VitaLoom.docks.inspector.get_command_registry", return_value=_Registry()),
            patch("core.VitaLoom.scene.scene_manager.get_scene_manager", return_value=_SceneManager()),
        ):
            self.panel._on_property_changed("energy", 12.5, [entity])

        self.assertEqual(
            calls,
            [
                (
                    "entity.set_property",
                    {
                        "scene_path": "workspace/projects/demo/scenes/main.pond",
                        "entity_id": "hero",
                        "property_path": "energy",
                        "value": 12.5,
                    },
                ),
                ("scene.open", {"scene_path": "workspace/projects/demo/scenes/main.pond"}),
            ],
        )

    def test_rejected_scene_entity_edit_does_not_fallback_to_local_command_stack(self):
        entity = {"id": "hero", "energy": 9.0, "scripts": []}
        calls = []
        project_modified = []
        command_executed = []

        class _Registry:
            def run(self, command_id, payload):
                calls.append((command_id, payload))
                return {
                    "ok": False,
                    "result": {},
                    "events": [],
                    "warnings": [],
                    "error": {"code": "forbidden", "message": "write denied"},
                }

        class _SceneManager:
            def get_current_scene_path(self):
                return "workspace/projects/demo/scenes/main.pond"

            def get_scene_data(self):
                return {"entities": [entity]}

        self.panel.projectModified.connect(lambda: project_modified.append(True))
        self.panel.commandExecuted.connect(lambda: command_executed.append(True))

        with (
            patch("core.VitaLoom.docks.inspector.get_command_registry", return_value=_Registry()),
            patch("core.VitaLoom.scene.scene_manager.get_scene_manager", return_value=_SceneManager()),
        ):
            self.panel._on_property_changed("energy", 12.5, [entity])

        self.assertEqual(entity["energy"], 9.0)
        self.assertEqual(project_modified, [])
        self.assertEqual(command_executed, [])
        self.assertEqual(
            calls,
            [
                (
                    "entity.set_property",
                    {
                        "scene_path": "workspace/projects/demo/scenes/main.pond",
                        "entity_id": "hero",
                        "property_path": "energy",
                        "value": 12.5,
                    },
                )
            ],
        )
    def test_generic_field_sync_routes_through_entity_property_command(self):
        entity = {"id": "hero", "energy": 9.0, "scripts": []}
        calls = []

        class _Registry:
            def run(self, command_id, payload):
                calls.append((command_id, payload))
                return {"ok": True, "result": {}, "events": [], "warnings": [], "error": None}

        with patch("core.VitaLoom.docks.inspector.get_command_registry", return_value=_Registry()):
            ok = self.panel._sync_scene_entity_data_via_command(
                "workspace/projects/demo/scenes/main.pond",
                entity,
                "hero",
                "energy",
                12.5,
            )

        self.assertTrue(ok)
        self.assertEqual(
            calls,
            [(
                "entity.set_property",
                {
                    "scene_path": "workspace/projects/demo/scenes/main.pond",
                    "entity_id": "hero",
                    "property_path": "energy",
                    "value": 12.5,
                },
            )],
        )


    def test_scene_owned_connection_weight_uses_semantic_registry_and_rehydrates(self):
        connection = _DummyConnection()
        owner = type("Owner", (), {"connections": [connection]})()
        connection._vitaloom_owner_viewport = owner
        calls = []
        project_modified = []
        command_executed = []

        class _Registry:
            def run(self, command_id, payload):
                calls.append((command_id, payload))
                return {"ok": True, "result": {}, "events": [], "warnings": [], "error": None}

        class _SceneManager:
            def get_current_scene_path(self):
                return "workspace/projects/demo/scenes/main.pond"

            def get_scene_data(self):
                return {"connections": [connection.to_dict()]}

        context = type("Context", (), {"canvas": owner})()
        self.panel.projectModified.connect(lambda: project_modified.append(True))
        self.panel.commandExecuted.connect(lambda: command_executed.append(True))
        with (
            patch("core.VitaLoom.docks.inspector.get_command_registry", return_value=_Registry()),
            patch("core.VitaLoom.docks.inspector.get_editor_context", return_value=context),
            patch("core.VitaLoom.scene.scene_manager.get_scene_manager", return_value=_SceneManager()),
        ):
            self.panel._on_property_changed("weight", 2.5, [connection])

        self.assertEqual(
            calls,
            [
                (
                    "connection.set_weight",
                    {
                        "scene_path": "workspace/projects/demo/scenes/main.pond",
                        "connection_index": 0,
                        "connection": {"start": "alpha", "end": "beta", "weight": 1.0},
                        "weight": 2.5,
                    },
                ),
                ("scene.open", {"scene_path": "workspace/projects/demo/scenes/main.pond"}),
            ],
        )
        self.assertEqual(connection.weight, 1.0)
        self.assertEqual(project_modified, [True])
        self.assertEqual(command_executed, [True])

    def test_rejected_scene_owned_connection_weight_does_not_fallback_or_emit_success(self):
        connection = _DummyConnection()
        owner = type("Owner", (), {"connections": [connection]})()
        connection._vitaloom_owner_viewport = owner
        calls = []
        project_modified = []
        command_executed = []

        class _Registry:
            def run(self, command_id, payload):
                calls.append((command_id, payload))
                return {"ok": False, "result": {}, "events": [], "warnings": [], "error": {"code": "stale"}}

        class _SceneManager:
            def get_current_scene_path(self):
                return "workspace/projects/demo/scenes/main.pond"

            def get_scene_data(self):
                return {"connections": [connection.to_dict()]}

        context = type("Context", (), {"canvas": owner})()
        self.panel.projectModified.connect(lambda: project_modified.append(True))
        self.panel.commandExecuted.connect(lambda: command_executed.append(True))
        with (
            patch("core.VitaLoom.docks.inspector.get_command_registry", return_value=_Registry()),
            patch("core.VitaLoom.docks.inspector.get_editor_context", return_value=context),
            patch("core.VitaLoom.scene.scene_manager.get_scene_manager", return_value=_SceneManager()),
        ):
            self.panel._on_property_changed("weight", 2.5, [connection])

        self.assertEqual(connection.weight, 1.0)
        self.assertEqual(project_modified, [])
        self.assertEqual(command_executed, [])
        self.assertEqual([call[0] for call in calls], ["connection.set_weight"])

    def test_unowned_connection_weight_stays_on_one_local_command_stack_fallback(self):
        connection = _DummyConnection()
        registry_calls = []

        class _Registry(_RecordingRegistry):
            def run(self, command_id, payload):
                result = super().run(command_id, payload)
                registry_calls.append((command_id, payload))
                return result

        with (
            patch("core.VitaLoom.docks.inspector.get_command_registry", return_value=_Registry()),
        ):
            self.panel._on_property_changed("weight", 2.5, [connection])

        self.assertEqual(registry_calls[0][0], "inspector.set_property")
        self.assertEqual(connection.weight, 2.5)


    def test_scene_owned_connection_non_weight_stays_local_without_registry_mutation(self):
        connection = _DummyConnection()
        connection.color = "#6688ff"
        owner = type("Owner", (), {"connections": [connection]})()
        connection._vitaloom_owner_viewport = owner
        registry_calls = []

        class _Registry(_RecordingRegistry):
            def run(self, command_id, payload):
                result = super().run(command_id, payload)
                registry_calls.append((command_id, payload))
                return result

        context = type("Context", (), {"canvas": owner})()
        with (
            patch("core.VitaLoom.docks.inspector.get_command_registry", return_value=_Registry()),
            patch("core.VitaLoom.docks.inspector.get_editor_context", return_value=context),
        ):
            self.panel._on_property_changed("color", "#ff88aa", [connection])

        self.assertEqual(registry_calls[0][0], "inspector.set_property")
        self.assertEqual(connection.color, "#ff88aa")

    def test_identity_less_script_holder_stays_local_without_registry_mutation(self):
        holder = type(
            "LegacyScriptHolder",
            (),
            {"scripts": [{"name": "brain", "properties": {"mind": {"level": 1}}}]},
        )()
        registry_calls = []

        class _Registry(_RecordingRegistry):
            def run(self, command_id, payload):
                result = super().run(command_id, payload)
                registry_calls.append((command_id, payload))
                return result

        with (
            patch("core.VitaLoom.docks.inspector.get_command_registry", return_value=_Registry()),
        ):
            self.panel._on_property_changed("script_brain_mind.level", 3, [holder])

        self.assertEqual(registry_calls[0][0], "inspector.set_property")
        self.assertEqual(holder.scripts[0]["properties"]["mind"]["level"], 3)


if __name__ == "__main__":
    unittest.main()
