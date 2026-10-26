# -*- coding: utf-8 -*-
"""Canonical command-audit migration must preserve durable replay safety."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.project.asset_reference_transaction import (
    AssetReferenceTransactionError,
    apply_asset_reference_mutation,
    plan_asset_reference_mutation,
    plan_asset_transaction_artifact_prune,
)
from core.VitaLoom.project.command_audit import (
    canonical_command_audit_path,
    project_command_audit_paths,
    read_project_command_audit_entries,
)


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


class CommandAuditNamespaceCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="command_audit_namespace_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        self.scene = self.project / "scenes" / "main.pond"
        self.scene.parent.mkdir(parents=True)
        (self.project / "assets").mkdir()
        (self.project / "project.json").write_text(
            json.dumps({"name": "audit migration", "active_scene": "main.pond"}),
            encoding="utf-8",
        )
        (self.project / "project.lock.json").write_text("{}", encoding="utf-8")
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
                            "scripts": [],
                        }
                    ],
                    "components": [],
                }
            ),
            encoding="utf-8",
        )
        self.registry = reset_command_registry()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _hero_position(self) -> list[float]:
        scene = json.loads(self.scene.read_text(encoding="utf-8"))
        return list(scene["entities"][0]["position"])

    def _move_canonical_history_to_legacy(self) -> Path:
        canonical = canonical_command_audit_path(self.project)
        legacy = self.project / ".vitalloom" / "command_audit.jsonl"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_bytes(canonical.read_bytes())
        canonical.unlink()
        return legacy

    def test_new_mutations_write_only_to_canonical_namespace(self) -> None:
        changed = self.registry.run(
            "transform.set",
            {"scene_path": str(self.scene), "entity_id": "hero", "position": [3.0, 4.0]},
        )

        canonical, legacy = project_command_audit_paths(self.project)
        self.assertTrue(changed["ok"], changed)
        self.assertEqual(Path(changed["result"]["audit_path"]), canonical)
        self.assertTrue(canonical.is_file())
        self.assertFalse(legacy.exists())

    def test_legacy_only_history_still_supports_fresh_registry_undo_and_redo(self) -> None:
        changed = self.registry.run(
            "transform.set",
            {"scene_path": str(self.scene), "entity_id": "hero", "position": [3.0, 4.0]},
        )
        self.assertTrue(changed["ok"], changed)
        legacy = self._move_canonical_history_to_legacy()

        undone = reset_command_registry().undo_project(str(self.project))
        redone = reset_command_registry().redo_project(str(self.project))

        self.assertTrue(legacy.is_file())
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(self._hero_position(), [3.0, 4.0])
        self.assertTrue(redone["ok"], redone)
        self.assertEqual(redone["result"]["source_execute_audit_id"], changed["result"]["audit_id"])

    def test_canonical_and_legacy_history_select_latest_timestamp_deterministically(self) -> None:
        first = self.registry.run(
            "transform.set",
            {"scene_path": str(self.scene), "entity_id": "hero", "position": [3.0, 4.0]},
        )
        self.assertTrue(first["ok"], first)
        self._move_canonical_history_to_legacy()
        second = self.registry.run(
            "transform.set",
            {"scene_path": str(self.scene), "entity_id": "hero", "position": [5.0, 6.0]},
        )

        undone = reset_command_registry().undo_project(str(self.project))

        self.assertTrue(second["ok"], second)
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(undone["result"]["source_audit_id"], second["result"]["audit_id"])
        self.assertEqual(self._hero_position(), [3.0, 4.0])
        entries = read_project_command_audit_entries(self.project)
        self.assertEqual(entries[-1]["audit_id"], undone["result"]["audit_id"])

    def test_malformed_legacy_audit_cannot_prove_prune_provenance(self) -> None:
        (self.project / "assets" / "hero.bin").write_bytes(b"hero")
        self.scene.write_text(json.dumps({"asset_path": "assets/hero.bin"}), encoding="utf-8")
        source = self.registry.run(
            "asset.rename",
            {
                "project_path": str(self.project),
                "source_path": "assets/hero.bin",
                "target_path": "assets/final.bin",
            },
        )
        self.assertTrue(source["ok"], source)
        # Strict pruning must reject corrupt compatibility history rather than
        # accepting it as (or silently ignoring it for) provenance evidence.
        legacy = self.project / ".vitalloom" / "command_audit.jsonl"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_text("{not-json}\n", encoding="utf-8")
        transaction_id = source["result"]["transaction_id"]
        journal_relative = f".vitaloom/asset_transactions/{transaction_id}.json"
        journal = self.project / journal_relative

        with self.assertRaises(AssetReferenceTransactionError) as caught:
            plan_asset_transaction_artifact_prune(
                self.project,
                artifact_paths=[journal_relative],
                expected_digests={journal_relative: __import__("hashlib").sha256(journal.read_bytes()).hexdigest()},
            )
        self.assertEqual(caught.exception.code, "asset_transaction_prune_provenance_unproven")



if __name__ == "__main__":
    unittest.main()
