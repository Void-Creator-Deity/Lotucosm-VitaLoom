# -*- coding: utf-8 -*-
"""CommandRegistry should provide a minimal undo/redo bridge for scene edits."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.VitaLoom.commands import runtime_commands
from core.VitaLoom.commands.registry import reset_command_registry


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


class AiCommandUndoRedoBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = reset_command_registry()
        self.tmp = Path(tempfile.mkdtemp(prefix="ai_command_undo_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        self.scene = self.project / "scenes" / "main.pond"
        self.scene.parent.mkdir(parents=True)
        (self.project / "project.json").write_text(
            json.dumps(
                {"name": "Undo Test", "active_scene": "main.pond"},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self.scene.write_text(
            json.dumps(
                {
                    "name": "Main",
                    "entities": [
                        {
                            "id": "hero",
                            "position": [1.0, 2.0],
                            "rotation": 0.0,
                            "scale": [1.0, 1.0],
                            "scripts": [
                                {
                                    "name": "brain",
                                    "type": "Brain",
                                    "properties": {"mind": {"level": 1}},
                                }
                            ],
                        }
                    ],
                    "components": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_entity_create_undo_redo_roundtrip(self) -> None:
        created = self.registry.run(
            "entity.create",
            {"scene_path": str(self.scene), "entity": {"id": "crate", "position": [3.0, 4.0]}},
        )
        self.assertTrue(created["ok"], created)
        self.assertIn("crate", self._entity_ids())

        undone = self.registry.undo_last()
        self.assertTrue(undone["ok"], undone)
        self.assertNotIn("crate", self._entity_ids())

        redone = self.registry.redo_last()
        self.assertTrue(redone["ok"], redone)
        self.assertIn("crate", self._entity_ids())

    def test_entity_create_undo_rejects_changed_snapshot_without_write_and_retains_history(self) -> None:
        created = self.registry.run(
            "entity.create",
            {"scene_path": str(self.scene), "entity": {"id": "crate", "position": [3.0, 4.0]}},
        )
        self.assertTrue(created["ok"], created)
        data = self._scene_data()
        crate = next(entity for entity in data["entities"] if entity.get("id") == "crate")
        crate["position"] = [99.0, 100.0]
        self.scene.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        stale_text = self.scene.read_text(encoding="utf-8")

        with patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
            rejected = self.registry.undo_last()

        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["code"], "stale_entity_delete")
        self.assertEqual(write_json.call_count, 0)
        self.assertEqual(self.scene.read_text(encoding="utf-8"), stale_text)
        retry = self.registry.undo_last()
        self.assertFalse(retry["ok"])
        self.assertEqual(retry["error"]["code"], "stale_entity_delete")
        redo = self.registry.redo_last()
        self.assertFalse(redo["ok"])
        self.assertEqual(redo["error"]["code"], "redo_empty")

    def test_entity_create_undo_rejects_reordered_entity_slot_without_write(self) -> None:
        created = self.registry.run(
            "entity.create",
            {"scene_path": str(self.scene), "entity": {"id": "crate", "position": [3.0, 4.0]}},
        )
        self.assertTrue(created["ok"], created)
        data = self._scene_data()
        data["entities"] = list(reversed(data["entities"]))
        self.scene.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        stale_text = self.scene.read_text(encoding="utf-8")

        with patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
            rejected = self.registry.undo_last()

        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["code"], "stale_entity_delete")
        self.assertEqual(rejected["error"]["details"]["expected_entity_index"], 1)
        self.assertEqual(rejected["error"]["details"]["actual_entity_index"], 0)
        self.assertEqual(write_json.call_count, 0)
        self.assertEqual(self.scene.read_text(encoding="utf-8"), stale_text)

    def test_entity_create_undo_rejects_new_incident_connection_without_write(self) -> None:
        created = self.registry.run(
            "entity.create",
            {"scene_path": str(self.scene), "entity": {"id": "crate", "position": [3.0, 4.0]}},
        )
        self.assertTrue(created["ok"], created)
        data = self._scene_data()
        data["connections"] = [{"start": "crate", "end": "hero", "weight": 1.0}]
        self.scene.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        stale_text = self.scene.read_text(encoding="utf-8")

        with patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
            rejected = self.registry.undo_last()

        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["code"], "stale_entity_delete")
        self.assertEqual(write_json.call_count, 0)
        self.assertEqual(self.scene.read_text(encoding="utf-8"), stale_text)

    def test_entity_delete_undo_rejects_divergent_post_delete_scene_before_write_and_retains_history(self) -> None:
        original = {
            "name": "Lifecycle",
            "entities": [
                {"id": "alpha", "position": [1.0, 1.0], "scripts": []},
                {"id": "beta", "position": [2.0, 2.0], "scripts": []},
                {"id": "gamma", "position": [3.0, 3.0], "scripts": []},
                {"id": "delta", "position": [4.0, 4.0], "scripts": []},
            ],
            "connections": [
                {"start": "alpha", "end": "beta", "weight": 1.0},
                {"start": "beta", "end": "gamma", "weight": 2.0},
                {"start": "gamma", "end": "alpha", "weight": 3.0},
                {"start": "beta", "end": "delta", "weight": 4.0},
                {"start": "gamma", "end": "delta", "weight": 5.0},
            ],
        }
        mutations = (
            "same_id_recreation",
            "survivor_edit",
            "connection_reorder",
            "restore_endpoint_removed",
        )

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.scene.write_text(json.dumps(original, ensure_ascii=False, indent=2), encoding="utf-8")
                registry = reset_command_registry()
                deleted = registry.run(
                    "entity.delete", {"scene_path": str(self.scene), "entity_id": "alpha"}
                )
                self.assertTrue(deleted["ok"], deleted)
                post_delete = self._scene_data()
                divergent = json.loads(json.dumps(post_delete))
                if mutation == "same_id_recreation":
                    divergent["entities"].append(
                        {"id": "alpha", "position": [99.0, 99.0], "scripts": []}
                    )
                elif mutation == "survivor_edit":
                    next(entity for entity in divergent["entities"] if entity["id"] == "beta")["position"] = [88.0, 77.0]
                elif mutation == "connection_reorder":
                    divergent["connections"].reverse()
                else:
                    divergent["entities"] = [
                        entity for entity in divergent["entities"] if entity["id"] != "beta"
                    ]
                self.scene.write_text(json.dumps(divergent, ensure_ascii=False, indent=2), encoding="utf-8")
                stale_text = self.scene.read_text(encoding="utf-8")

                with patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
                    rejected = registry.undo_last()

                self.assertFalse(rejected["ok"])
                self.assertEqual(rejected["error"]["code"], "stale_entity_restore_deleted_snapshot")
                self.assertEqual(write_json.call_count, 0)
                self.assertEqual(self.scene.read_text(encoding="utf-8"), stale_text)
                # The failed undo remains retryable after canonical state is restored.
                self.scene.write_text(json.dumps(post_delete, ensure_ascii=False, indent=2), encoding="utf-8")
                retried = registry.undo_last()
                self.assertTrue(retried["ok"], retried)
                self.assertEqual(self._scene_data()["entities"], original["entities"])
                self.assertEqual(self._scene_data()["connections"], original["connections"])

    def test_entity_delete_redo_rejects_divergent_post_restore_scene_before_write_and_retains_history(self) -> None:
        original = {
            "name": "Lifecycle",
            "entities": [
                {"id": "alpha", "position": [1.0, 1.0], "scripts": []},
                {"id": "beta", "position": [2.0, 2.0], "scripts": []},
                {"id": "gamma", "position": [3.0, 3.0], "scripts": []},
            ],
            "connections": [
                {"start": "alpha", "end": "beta", "weight": 1.0},
                {"start": "beta", "end": "gamma", "weight": 2.0},
                {"start": "gamma", "end": "alpha", "weight": 3.0},
                {"start": "gamma", "end": "beta", "weight": 4.0},
            ],
        }
        mutations = ("survivor_edit", "connection_reorder", "endpoint_removed")

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.scene.write_text(json.dumps(original, ensure_ascii=False, indent=2), encoding="utf-8")
                registry = reset_command_registry()
                deleted = registry.run(
                    "entity.delete", {"scene_path": str(self.scene), "entity_id": "alpha"}
                )
                self.assertTrue(deleted["ok"], deleted)
                restored = registry.undo_last()
                self.assertTrue(restored["ok"], restored)
                post_restore = self._scene_data()
                divergent = json.loads(json.dumps(post_restore))
                if mutation == "survivor_edit":
                    next(entity for entity in divergent["entities"] if entity["id"] == "beta")["position"] = [66.0, 55.0]
                elif mutation == "connection_reorder":
                    divergent["connections"].reverse()
                else:
                    divergent["entities"] = [
                        entity for entity in divergent["entities"] if entity["id"] != "beta"
                    ]
                self.scene.write_text(json.dumps(divergent, ensure_ascii=False, indent=2), encoding="utf-8")
                stale_text = self.scene.read_text(encoding="utf-8")

                with patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
                    rejected = registry.redo_last()

                self.assertFalse(rejected["ok"])
                self.assertEqual(rejected["error"]["code"], "stale_entity_delete")
                self.assertEqual(write_json.call_count, 0)
                self.assertEqual(self.scene.read_text(encoding="utf-8"), stale_text)
                # The failed redo remains retryable after its full witness is restored.
                self.scene.write_text(json.dumps(post_restore, ensure_ascii=False, indent=2), encoding="utf-8")
                retried = registry.redo_last()
                self.assertTrue(retried["ok"], retried)
                self.assertEqual([entity["id"] for entity in self._scene_data()["entities"]], ["beta", "gamma"])

    def test_transform_set_undo_redo_roundtrip(self) -> None:
        moved = self.registry.run(
            "transform.set",
            {
                "scene_path": str(self.scene),
                "entity_id": "hero",
                "position": [7.0, 8.0],
                "rotation": 15.0,
                "scale": [2.0, 2.0],
            },
        )
        self.assertTrue(moved["ok"], moved)
        self.assertEqual(self._hero()["position"], [7.0, 8.0])

        undone = self.registry.undo_last()
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(self._hero()["position"], [1.0, 2.0])
        self.assertEqual(self._hero()["rotation"], 0.0)

        redone = self.registry.redo_last()
        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._hero()["position"], [7.0, 8.0])
        self.assertEqual(self._hero()["scale"], [2.0, 2.0])

    def test_script_set_property_undo_redo_roundtrip_and_audits_actions(self) -> None:
        changed = self.registry.run(
            "script.set_property",
            {
                "scene_path": str(self.scene),
                "entity_id": "hero",
                "script": "brain",
                "property_path": "mind.level",
                "value": 5,
            },
        )
        self.assertTrue(changed["ok"], changed)
        self.assertEqual(self._brain_level(), 5)

        undone = self.registry.undo_last()
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(self._brain_level(), 1)

        redone = self.registry.redo_last()
        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._brain_level(), 5)

        audit_path = self.project / ".vitaloom" / "command_audit.jsonl"
        actions = [
            json.loads(line).get("action", "execute")
            for line in audit_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(actions, ["execute", "undo", "redo"])

    def _scene_data(self) -> dict:
        return json.loads(self.scene.read_text(encoding="utf-8"))

    def _entity_ids(self) -> list[str]:
        return [str(ent.get("id")) for ent in self._scene_data()["entities"]]

    def _hero(self) -> dict:
        return next(ent for ent in self._scene_data()["entities"] if ent.get("id") == "hero")

    def _brain_level(self) -> int:
        script = self._hero()["scripts"][0]
        return int(script["properties"]["mind"]["level"])


if __name__ == "__main__":
    unittest.main()
