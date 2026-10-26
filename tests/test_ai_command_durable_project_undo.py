# -*- coding: utf-8 -*-
"""Durable project undo should replay representative audit history across registries."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from core.VitaLoom.commands import mcp_adapter, runtime_commands
from core.VitaLoom.commands.registry import reset_command_registry


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


class AiCommandDurableProjectUndoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="ai_command_durable_undo_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        self.scene = self.project / "scenes" / "main.pond"
        self.scene.parent.mkdir(parents=True)
        (self.project / "project.json").write_text(
            json.dumps({"name": "Durable Undo", "active_scene": "main.pond"}, indent=2),
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
                indent=2,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_fresh_registry_can_undo_latest_transform_from_project_audit(self) -> None:
        first_registry = reset_command_registry()
        moved = first_registry.run(
            "transform.set",
            {
                "scene_path": str(self.scene),
                "entity_id": "hero",
                "position": [9.0, 10.0],
                "rotation": 25.0,
            },
        )
        self.assertTrue(moved["ok"], moved)
        source_audit_id = moved["result"]["audit_id"]
        self.assertEqual(self._hero()["position"], [9.0, 10.0])

        fresh_registry = reset_command_registry()
        undone = fresh_registry.run("command.undo_project", {"project_path": str(self.project)})

        self.assertTrue(undone["ok"], undone)
        self.assertEqual(self._hero()["position"], [1.0, 2.0])
        self.assertEqual(self._hero()["rotation"], 0.0)
        self.assertEqual(undone["result"]["source_audit_id"], source_audit_id)
        self.assertEqual(undone["result"]["durable_replay"], "project_undo")

        entries = self._audit_entries()
        self.assertEqual([entry["action"] for entry in entries], ["execute", "durable_undo"])
        self.assertEqual(entries[-1]["source_audit_id"], source_audit_id)

    def test_fresh_registry_can_redo_latest_durable_project_undo(self) -> None:
        first_registry = reset_command_registry()
        moved = first_registry.run(
            "transform.set",
            {
                "scene_path": str(self.scene),
                "entity_id": "hero",
                "position": [9.0, 10.0],
                "rotation": 25.0,
            },
        )
        self.assertTrue(moved["ok"], moved)
        execute_audit_id = moved["result"]["audit_id"]

        undo_registry = reset_command_registry()
        undone = undo_registry.run("command.undo_project", {"project_path": str(self.project)})
        self.assertTrue(undone["ok"], undone)
        undo_audit_id = undone["result"]["audit_id"]
        self.assertEqual(self._hero()["position"], [1.0, 2.0])

        redo_registry = reset_command_registry()
        redone = redo_registry.run("command.redo_project", {"project_path": str(self.project)})

        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._hero()["position"], [9.0, 10.0])
        self.assertEqual(self._hero()["rotation"], 25.0)
        self.assertEqual(redone["result"]["source_audit_id"], undo_audit_id)
        self.assertEqual(redone["result"]["source_execute_audit_id"], execute_audit_id)
        self.assertEqual(redone["result"]["durable_replay"], "project_redo")

        entries = self._audit_entries()
        self.assertEqual(
            [entry["action"] for entry in entries],
            ["execute", "durable_undo", "durable_redo"],
        )
        self.assertEqual(entries[-1]["source_audit_id"], undo_audit_id)
        self.assertEqual(entries[-1]["source_execute_audit_id"], execute_audit_id)

    def test_fresh_registry_rejects_stale_transform_position_undo_without_overwriting_later_state(self) -> None:
        source = reset_command_registry().run("transform.set", {"scene_path": str(self.scene), "entity_id": "hero", "position": [9.0, 10.0]})
        self.assertTrue(source["ok"], source)
        later_write = runtime_commands._transform_set({"scene_path": str(self.scene), "entity_id": "hero", "position": [11.0, 12.0]}, {})
        self.assertTrue(later_write["ok"], later_write)

        failed = reset_command_registry().run("command.undo_project", {"project_path": str(self.project)})

        self.assertFalse(failed["ok"])
        self.assertEqual(failed["error"]["code"], "stale_transform_position")
        self.assertEqual(self._hero()["position"], [11.0, 12.0])
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute"])

    def test_fresh_registry_rejects_stale_transform_position_redo_without_overwriting_later_state(self) -> None:
        source = reset_command_registry().run("transform.set", {"scene_path": str(self.scene), "entity_id": "hero", "position": [9.0, 10.0]})
        self.assertTrue(source["ok"], source)
        undone = reset_command_registry().run("command.undo_project", {"project_path": str(self.project)})
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(self._hero()["position"], [1.0, 2.0])
        later_write = runtime_commands._transform_set({"scene_path": str(self.scene), "entity_id": "hero", "position": [4.0, 5.0]}, {})
        self.assertTrue(later_write["ok"], later_write)

        failed = reset_command_registry().run("command.redo_project", {"project_path": str(self.project)})

        self.assertFalse(failed["ok"])
        self.assertEqual(failed["error"]["code"], "stale_transform_position")
        self.assertEqual(self._hero()["position"], [4.0, 5.0])
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute", "durable_undo"])

    def test_fresh_registry_can_undo_and_redo_generic_entity_property(self) -> None:
        first_registry = reset_command_registry()
        changed = first_registry.run(
            "entity.set_property",
            {
                "scene_path": str(self.scene),
                "entity_id": "hero",
                "property_path": "energy",
                "value": 12.5,
            },
        )
        self.assertTrue(changed["ok"], changed)
        execute_audit_id = changed["result"]["audit_id"]
        self.assertEqual(self._hero()["energy"], 12.5)

        undo_registry = reset_command_registry()
        undone = undo_registry.run("command.undo_project", {"project_path": str(self.project)})

        self.assertTrue(undone["ok"], undone)
        undo_audit_id = undone["result"]["audit_id"]
        self.assertNotIn("energy", self._hero())
        self.assertEqual(undone["result"]["source_audit_id"], execute_audit_id)
        self.assertEqual(undone["result"]["durable_replay"], "project_undo")

        redo_registry = reset_command_registry()
        redone = redo_registry.run("command.redo_project", {"project_path": str(self.project)})

        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._hero()["energy"], 12.5)
        self.assertEqual(redone["result"]["source_audit_id"], undo_audit_id)
        self.assertEqual(redone["result"]["source_execute_audit_id"], execute_audit_id)
        self.assertEqual(redone["result"]["durable_replay"], "project_redo")

        entries = self._audit_entries()
        self.assertEqual(
            [entry["action"] for entry in entries],
            ["execute", "durable_undo", "durable_redo"],
        )
        self.assertEqual(entries[-1]["source_audit_id"], undo_audit_id)
        self.assertEqual(entries[-1]["source_execute_audit_id"], execute_audit_id)

    def test_mcp_helper_delegates_to_project_undo_command(self) -> None:
        registry = reset_command_registry()
        changed = registry.run(
            "script.set_property",
            {
                "scene_path": str(self.scene),
                "entity_id": "hero",
                "script": "brain",
                "property_path": "mind.level",
                "value": 7,
            },
        )
        self.assertTrue(changed["ok"], changed)
        self.assertEqual(self._brain_level(), 7)
        reset_command_registry()

        undone = mcp_adapter.undo_project(str(self.project))

        self.assertTrue(undone["ok"], undone)
        self.assertEqual(self._brain_level(), 1)

    def test_mcp_helper_delegates_to_project_redo_command(self) -> None:
        registry = reset_command_registry()
        changed = registry.run(
            "script.set_property",
            {
                "scene_path": str(self.scene),
                "entity_id": "hero",
                "script": "brain",
                "property_path": "mind.level",
                "value": 7,
            },
        )
        self.assertTrue(changed["ok"], changed)
        self.assertEqual(self._brain_level(), 7)
        reset_command_registry().run("command.undo_project", {"project_path": str(self.project)})
        self.assertEqual(self._brain_level(), 1)
        reset_command_registry()

        redone = mcp_adapter.redo_project(str(self.project))

        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._brain_level(), 7)

    def test_fresh_registry_entity_create_undo_rejects_stale_snapshot_without_write_or_audit(self) -> None:
        created = reset_command_registry().run(
            "entity.create",
            {"scene_path": str(self.scene), "entity": {"id": "crate", "position": [3.0, 4.0]}},
        )
        self.assertTrue(created["ok"], created)
        data = self._scene_data()
        crate = next(entity for entity in data["entities"] if entity.get("id") == "crate")
        crate["radius"] = 99.0
        self.scene.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        stale_text = self.scene.read_text(encoding="utf-8")

        with patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
            rejected = reset_command_registry().run(
                "command.undo_project", {"project_path": str(self.project)}
            )

        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["code"], "stale_entity_delete")
        self.assertEqual(write_json.call_count, 0)
        self.assertEqual(self.scene.read_text(encoding="utf-8"), stale_text)
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute"])

    def test_fresh_registry_entity_create_redo_requires_post_undo_scene_witness(self) -> None:
        created = reset_command_registry().run(
            "entity.create",
            {"scene_path": str(self.scene), "entity": {"id": "crate", "position": [3.0, 4.0]}},
        )
        self.assertTrue(created["ok"], created)
        execute_audit_id = created["result"]["audit_id"]

        undone = reset_command_registry().run(
            "command.undo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(undone["result"]["source_audit_id"], execute_audit_id)
        self.assertNotIn("crate", [entity["id"] for entity in self._scene_data()["entities"]])

        data = self._scene_data()
        data["entities"].append({"id": "external", "position": [5.0, 6.0], "scripts": []})
        self.scene.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        stale_text = self.scene.read_text(encoding="utf-8")
        with patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
            rejected = reset_command_registry().run(
                "command.redo_project", {"project_path": str(self.project)}
            )

        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["code"], "stale_entity_create_scene")
        self.assertEqual(write_json.call_count, 0)
        self.assertEqual(self.scene.read_text(encoding="utf-8"), stale_text)
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute", "durable_undo"])

        data["entities"] = [entity for entity in data["entities"] if entity.get("id") != "external"]
        self.scene.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        redone = reset_command_registry().run(
            "command.redo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(redone["ok"], redone)
        self.assertIn("crate", [entity["id"] for entity in self._scene_data()["entities"]])
        self.assertEqual(
            [entry["action"] for entry in self._audit_entries()],
            ["execute", "durable_undo", "durable_redo"],
        )

    def test_fresh_registry_entity_delete_undo_rejects_stale_post_delete_scene_without_write_or_audit(self) -> None:
        original = {
            "name": "Lifecycle",
            "entities": [
                {"id": "alpha", "position": [1.0, 1.0], "scripts": []},
                {"id": "beta", "position": [2.0, 2.0], "scripts": []},
            ],
            "connections": [{"start": "alpha", "end": "beta", "weight": 1.0}],
        }
        self.scene.write_text(json.dumps(original, ensure_ascii=False, indent=2), encoding="utf-8")
        source = reset_command_registry().run(
            "entity.delete", {"scene_path": str(self.scene), "entity_id": "alpha"}
        )
        self.assertTrue(source["ok"], source)
        post_delete = self._scene_data()
        divergent = json.loads(json.dumps(post_delete))
        # A same-ID recreation must be recognized as a stale post-delete scene,
        # not silently accepted as an ordinary duplicate-entity restore failure.
        divergent["entities"].append({"id": "alpha", "position": [99.0, 99.0], "scripts": []})
        self.scene.write_text(json.dumps(divergent, ensure_ascii=False, indent=2), encoding="utf-8")
        stale_text = self.scene.read_text(encoding="utf-8")

        with patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
            rejected = reset_command_registry().run(
                "command.undo_project", {"project_path": str(self.project)}
            )

        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["code"], "stale_entity_restore_deleted_snapshot")
        self.assertEqual(write_json.call_count, 0)
        self.assertEqual(self.scene.read_text(encoding="utf-8"), stale_text)
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute"])

    def test_fresh_registry_entity_delete_redo_rejects_stale_post_restore_scene_and_retries(self) -> None:
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
            ],
        }
        self.scene.write_text(json.dumps(original, ensure_ascii=False, indent=2), encoding="utf-8")
        source = reset_command_registry().run(
            "entity.delete", {"scene_path": str(self.scene), "entity_id": "alpha"}
        )
        self.assertTrue(source["ok"], source)
        undone = reset_command_registry().run(
            "command.undo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(undone["ok"], undone)
        post_restore = self._scene_data()
        divergent = json.loads(json.dumps(post_restore))
        divergent["connections"].reverse()
        self.scene.write_text(json.dumps(divergent, ensure_ascii=False, indent=2), encoding="utf-8")
        stale_text = self.scene.read_text(encoding="utf-8")

        with patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
            rejected = reset_command_registry().run(
                "command.redo_project", {"project_path": str(self.project)}
            )

        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["code"], "stale_entity_delete")
        self.assertEqual(write_json.call_count, 0)
        self.assertEqual(self.scene.read_text(encoding="utf-8"), stale_text)
        self.assertEqual(
            [entry["action"] for entry in self._audit_entries()], ["execute", "durable_undo"]
        )

        self.scene.write_text(json.dumps(post_restore, ensure_ascii=False, indent=2), encoding="utf-8")
        retried = reset_command_registry().run(
            "command.redo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(retried["ok"], retried)
        self.assertEqual([entity["id"] for entity in self._scene_data()["entities"]], ["beta", "gamma"])
        self.assertEqual(
            [entry["action"] for entry in self._audit_entries()],
            ["execute", "durable_undo", "durable_redo"],
        )

    def test_entity_delete_restores_incident_connections_for_memory_and_durable_history(self) -> None:
        original_entities = [
            {"id": "alpha", "position": [10.0, 20.0], "scripts": []},
            {"id": "beta", "position": [30.0, 40.0], "scripts": []},
            {"id": "gamma", "position": [50.0, 60.0], "scripts": []},
        ]
        original_connections = [
            {"start": "alpha", "end": "beta", "weight": 1.0},
            {"start_id": "beta", "end_id": "gamma", "weight": 2.0},
            {"from": "gamma", "to": "alpha", "weight": 3.0},
        ]
        self.scene.write_text(
            json.dumps(
                {"name": "Main", "entities": original_entities, "connections": original_connections},
                indent=2,
            ),
            encoding="utf-8",
        )

        registry = reset_command_registry()
        deleted = registry.run(
            "entity.delete",
            {"scene_path": str(self.scene), "entity_id": "alpha"},
        )
        self.assertTrue(deleted["ok"], deleted)
        execute_audit_id = deleted["result"]["audit_id"]
        self.assertEqual(deleted["result"]["entity_index"], 0)
        self.assertEqual(
            [row["connection_index"] for row in deleted["result"]["deleted_connections"]],
            [0, 2],
        )
        self.assertEqual(
            [entity["id"] for entity in self._scene_data()["entities"]], ["beta", "gamma"]
        )
        self.assertEqual(self._scene_data()["connections"], [original_connections[1]])

        undone_in_memory = registry.run("command.undo", {})
        self.assertTrue(undone_in_memory["ok"], undone_in_memory)
        self.assertEqual(self._scene_data()["entities"], original_entities)
        self.assertEqual(self._scene_data()["connections"], original_connections)

        redone_in_memory = registry.run("command.redo", {})
        self.assertTrue(redone_in_memory["ok"], redone_in_memory)
        self.assertEqual(
            [entity["id"] for entity in self._scene_data()["entities"]], ["beta", "gamma"]
        )
        self.assertEqual(self._scene_data()["connections"], [original_connections[1]])

        # The local undo entry is intentionally recorded as a consumed audit source.
        # Re-run the same representative delete in a clean project audit to prove the
        # independent fresh-registry durable replay route.
        self.scene.write_text(
            json.dumps(
                {"name": "Main", "entities": original_entities, "connections": original_connections},
                indent=2,
            ),
            encoding="utf-8",
        )
        audit_path = self.project / ".vitaloom" / "command_audit.jsonl"
        audit_path.unlink(missing_ok=True)
        durable_source = reset_command_registry().run(
            "entity.delete",
            {"scene_path": str(self.scene), "entity_id": "alpha"},
        )
        self.assertTrue(durable_source["ok"], durable_source)
        durable_execute_audit_id = durable_source["result"]["audit_id"]

        durable_undo = reset_command_registry().run(
            "command.undo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(durable_undo["ok"], durable_undo)
        undo_audit_id = durable_undo["result"]["audit_id"]
        self.assertEqual(durable_undo["result"]["source_audit_id"], durable_execute_audit_id)
        self.assertEqual(self._scene_data()["entities"], original_entities)
        self.assertEqual(self._scene_data()["connections"], original_connections)

        durable_redo = reset_command_registry().run(
            "command.redo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(durable_redo["ok"], durable_redo)
        self.assertEqual(durable_redo["result"]["source_audit_id"], undo_audit_id)
        self.assertEqual(durable_redo["result"]["source_execute_audit_id"], durable_execute_audit_id)
        self.assertEqual(
            [entity["id"] for entity in self._scene_data()["entities"]], ["beta", "gamma"]
        )
        self.assertEqual(self._scene_data()["connections"], [original_connections[1]])

    def test_entity_restore_deleted_snapshot_validation_is_atomic_and_does_not_advance_history(self) -> None:
        original_text = self.scene.read_text(encoding="utf-8")
        cases = [
            (
                "duplicate_connection_index",
                {
                    "scene_path": str(self.scene),
                    "entity_id": "alpha",
                    "entity": {"id": "alpha", "position": [1.0, 2.0]},
                    "entity_index": 0,
                    "deleted_connections": [
                        {"connection": {"start": "alpha", "end": "hero"}, "connection_index": 0},
                        {"connection": {"start": "hero", "end": "alpha"}, "connection_index": 0},
                    ],
                },
            ),
            (
                "entity_index_out_of_range",
                {
                    "scene_path": str(self.scene),
                    "entity_id": "alpha",
                    "entity": {"id": "alpha", "position": [1.0, 2.0]},
                    "entity_index": 2,
                    "deleted_connections": [],
                },
            ),
            (
                "connection_endpoint_missing",
                {
                    "scene_path": str(self.scene),
                    "entity_id": "alpha",
                    "entity": {"id": "alpha", "position": [1.0, 2.0]},
                    "entity_index": 0,
                    "deleted_connections": [
                        {
                            "connection": {"start": "alpha", "end": "missing"},
                            "connection_index": 0,
                        }
                    ],
                },
            ),
        ]

        for expected_code, payload in cases:
            with self.subTest(error=expected_code), patch.object(
                runtime_commands, "_write_json", wraps=runtime_commands._write_json
            ) as write_json:
                registry = reset_command_registry()
                failed = registry.run("entity.restore_deleted_snapshot", payload)

            self.assertFalse(failed["ok"])
            self.assertEqual(failed["error"]["code"], expected_code)
            self.assertEqual(write_json.call_count, 0)
            self.assertEqual(self.scene.read_text(encoding="utf-8"), original_text)
            undo = registry.run("command.undo", {})
            self.assertFalse(undo["ok"])
            self.assertEqual(undo["error"]["code"], "undo_empty")

    def _scene_data(self) -> dict:
        return json.loads(self.scene.read_text(encoding="utf-8"))

    def _hero(self) -> dict:
        return next(ent for ent in self._scene_data()["entities"] if ent.get("id") == "hero")

    def _brain_level(self) -> int:
        script = self._hero()["scripts"][0]
        return int(script["properties"]["mind"]["level"])

    def _audit_entries(self) -> list[dict]:
        audit_path = self.project / ".vitaloom" / "command_audit.jsonl"
        return [
            json.loads(line)
            for line in audit_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


if __name__ == "__main__":
    unittest.main()
