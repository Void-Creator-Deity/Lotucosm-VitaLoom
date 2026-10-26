# -*- coding: utf-8 -*-
"""Asset application history must be exact, guarded, and source-independent."""
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


class AssetApplyGuardedHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="asset_apply_guarded_history_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        self.scene = self.project / "scenes" / "main.pond"
        self.asset = self.project / "assets" / "sprites" / "hero.png"
        self.scene.parent.mkdir(parents=True)
        self.asset.parent.mkdir(parents=True)
        (self.project / "project.json").write_text(
            json.dumps({"name": "Asset Apply History", "active_scene": "main.pond"}, indent=2),
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
        self.asset.write_bytes(b"original asset bytes")
        self.registry = reset_command_registry()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_memory_undo_redo_replays_exact_snapshot_without_rereading_asset(self) -> None:
        applied = self._apply()
        self.assertTrue(applied["ok"], applied)
        original = self._entity("hero_sprite")
        self.assertEqual(applied["result"]["entity"], original)
        self.assertEqual(applied["result"]["entity_index"], 1)
        self.assertEqual(original["asset_path"], "assets/sprites/hero.png")

        undone = self.registry.undo_last()
        self.assertTrue(undone["ok"], undone)
        self.assertNotIn("hero_sprite", self._entity_ids())

        # Redo inserts the captured entity snapshot. It must not need the
        # original project asset to still exist or be readable.
        self.asset.unlink()
        redone = self.registry.redo_last()

        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._entity("hero_sprite"), original)
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute", "undo", "redo"])

    def test_durable_undo_and_redo_keep_exact_snapshot_after_asset_deletion(self) -> None:
        applied = self._apply()
        self.assertTrue(applied["ok"], applied)
        source_audit_id = applied["result"]["audit_id"]
        original = self._entity("hero_sprite")

        undone = reset_command_registry().run(
            "command.undo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(undone["result"]["source_audit_id"], source_audit_id)
        self.assertNotIn("hero_sprite", self._entity_ids())

        self.asset.unlink()
        redone = reset_command_registry().run(
            "command.redo_project", {"project_path": str(self.project)}
        )

        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._entity("hero_sprite"), original)
        self.assertEqual(
            [entry["action"] for entry in self._audit_entries()],
            ["execute", "durable_undo", "durable_redo"],
        )

    def test_durable_undo_rejects_mutated_applied_entity_before_write_or_audit(self) -> None:
        applied = self._apply()
        self.assertTrue(applied["ok"], applied)
        data = self._scene_data()
        next(entity for entity in data["entities"] if entity["id"] == "hero_sprite")["sr_visual"]["sprite_path"] = "changed.png"
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

    def test_durable_redo_rejects_diverged_post_undo_entities_and_retries(self) -> None:
        applied = self._apply()
        self.assertTrue(applied["ok"], applied)
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
        self.assertEqual(self._entity("hero_sprite"), applied["result"]["entity"])

    def test_durable_redo_rejects_diverged_post_undo_connections_before_write_or_audit(self) -> None:
        applied = self._apply()
        self.assertTrue(applied["ok"], applied)
        undone = reset_command_registry().run(
            "command.undo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(undone["ok"], undone)

        clean_post_undo = self._scene_data()
        divergent = json.loads(json.dumps(clean_post_undo))
        divergent["connections"].append({"start": "hero", "end": "outside", "weight": 0.25})
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
        self.assertEqual(self._entity("hero_sprite"), applied["result"]["entity"])

    def _apply(self) -> dict:
        return self.registry.run(
            "asset.apply_to_scene",
            {
                "scene_path": str(self.scene),
                "asset_path": str(self.asset),
                "entity_id": "hero_sprite",
                "name": "Hero Sprite Ref",
                "entity_type": "sprite_reference",
                "position": [11.0, 12.0],
                "radius": 19.5,
            },
        )

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
