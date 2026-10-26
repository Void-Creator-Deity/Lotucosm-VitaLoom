# -*- coding: utf-8 -*-
"""Prefab placement history must be exact, guarded, and source-independent."""
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


class PrefabGuardedHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="prefab_guarded_history_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        self.scene = self.project / "scenes" / "main.pond"
        self.prefab = self.project / "assets" / "prefabs" / "crate.json"
        self.scene.parent.mkdir(parents=True)
        self.prefab.parent.mkdir(parents=True)
        (self.project / "project.json").write_text(
            json.dumps({"name": "Prefab History", "active_scene": "main.pond"}, indent=2),
            encoding="utf-8",
        )
        self.scene.write_text(
            json.dumps(
                {
                    "name": "Main",
                    "entities": [
                        {"id": "hero", "position": [1.0, 2.0], "scripts": []},
                    ],
                    "connections": [],
                    "components": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self._write_prefab(
            {
                "id": "template_crate",
                "name": "Original Crate",
                "type": "prefab",
                "scripts": [],
                "properties": {"material": "wood"},
            }
        )
        self.registry = reset_command_registry()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_memory_undo_redo_replays_exact_snapshot_without_rereading_prefab(self) -> None:
        placed = self._place()
        self.assertTrue(placed["ok"], placed)
        original = self._entity("crate")
        self.assertNotIn("radius", original)
        self.assertEqual(placed["result"]["entity"], original)
        self.assertEqual(placed["result"]["entity_index"], 1)

        undone = self.registry.undo_last()
        self.assertTrue(undone["ok"], undone)
        self.assertNotIn("crate", self._entity_ids())

        # A current prefab source is irrelevant to history redo. An invalid source
        # would make the legacy re-execution recipe fail.
        self.prefab.write_text("not valid json", encoding="utf-8")
        redone = self.registry.redo_last()

        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._entity("crate"), original)
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute", "undo", "redo"])

    def test_durable_undo_and_redo_keep_exact_snapshot_after_prefab_changes(self) -> None:
        placed = self._place()
        self.assertTrue(placed["ok"], placed)
        source_audit_id = placed["result"]["audit_id"]
        original = self._entity("crate")

        undone = reset_command_registry().run(
            "command.undo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(undone["result"]["source_audit_id"], source_audit_id)
        self.assertNotIn("crate", self._entity_ids())

        self.prefab.write_text("not valid json", encoding="utf-8")
        redone = reset_command_registry().run(
            "command.redo_project", {"project_path": str(self.project)}
        )

        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._entity("crate"), original)
        self.assertEqual(
            [entry["action"] for entry in self._audit_entries()],
            ["execute", "durable_undo", "durable_redo"],
        )

    def test_durable_undo_rejects_mutated_placed_entity_before_write_or_audit(self) -> None:
        placed = self._place()
        self.assertTrue(placed["ok"], placed)
        data = self._scene_data()
        next(entity for entity in data["entities"] if entity["id"] == "crate")["properties"]["material"] = "metal"
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

    def test_durable_redo_rejects_diverged_post_undo_scene_and_retries(self) -> None:
        placed = self._place()
        self.assertTrue(placed["ok"], placed)
        undone = reset_command_registry().run(
            "command.undo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(undone["ok"], undone)

        clean_post_undo = self._scene_data()
        divergent = json.loads(json.dumps(clean_post_undo))
        divergent["entities"].append({"id": "external", "position": [8.0, 9.0], "scripts": []})
        self.scene.write_text(json.dumps(divergent, ensure_ascii=False, indent=2), encoding="utf-8")
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

        self.scene.write_text(json.dumps(clean_post_undo, ensure_ascii=False, indent=2), encoding="utf-8")
        retried = reset_command_registry().run(
            "command.redo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(retried["ok"], retried)
        self.assertEqual(self._entity("crate"), placed["result"]["entity"])

    def _place(self) -> dict:
        return self.registry.run(
            "prefab.place",
            {
                "scene_path": str(self.scene),
                "prefab_path": str(self.prefab),
                "entity_id": "crate",
                "position": [11.0, 12.0],
            },
        )

    def _write_prefab(self, data: dict) -> None:
        self.prefab.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _scene_data(self) -> dict:
        return json.loads(self.scene.read_text(encoding="utf-8"))

    def _entity(self, entity_id: str) -> dict:
        return next(entity for entity in self._scene_data()["entities"] if entity.get("id") == entity_id)

    def _entity_ids(self) -> list[str]:
        return [str(entity.get("id")) for entity in self._scene_data()["entities"]]

    def _audit_entries(self) -> list[dict]:
        audit_path = self.project / ".vitaloom" / "command_audit.jsonl"
        return [
            json.loads(line)
            for line in audit_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


if __name__ == "__main__":
    unittest.main()
