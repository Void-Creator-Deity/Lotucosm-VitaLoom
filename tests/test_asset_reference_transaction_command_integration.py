# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.project.asset_reference_transaction import analyze_asset_retirement_policy


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


class AssetReferenceTransactionCommandIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="asset_tx_cmd_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        (self.project / "assets").mkdir(parents=True)
        (self.project / "scenes").mkdir()
        (self.project / "project.json").write_text(json.dumps({"name": "asset-tx", "active_scene": "main.pond"}), encoding="utf-8")
        (self.project / "project.lock.json").write_text("{}", encoding="utf-8")
        (self.project / "assets" / "hero.png").write_bytes(b"hero")
        (self.project / "scenes" / "main.pond").write_text(json.dumps({"sprite_path": "assets/hero.png"}), encoding="utf-8")
        self.registry = reset_command_registry()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def _tree_bytes(root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    def test_command_rename_rewrites_references_and_generic_undo_redo_replays_receipt(self) -> None:
        renamed = self.registry.run(
            "asset.rename",
            {
                "project_path": str(self.project),
                "source_path": "assets/hero.png",
                "target_path": "assets/renamed-hero.png",
            },
        )
        self.assertTrue(renamed["ok"], renamed)
        self.assertEqual(len(renamed["result"]["reference_edits"]), 1)
        self.assertTrue((self.project / "assets" / "renamed-hero.png").is_file())
        self.assertEqual(
            json.loads((self.project / "scenes" / "main.pond").read_text(encoding="utf-8"))["sprite_path"],
            "assets/renamed-hero.png",
        )

        undone = self.registry.run("command.undo")
        self.assertTrue(undone["ok"], undone)
        self.assertTrue((self.project / "assets" / "hero.png").is_file())
        redone = self.registry.run("command.redo")
        self.assertTrue(redone["ok"], redone)
        self.assertTrue((self.project / "assets" / "renamed-hero.png").is_file())

    def test_retirement_analysis_command_matches_authority_and_remains_read_only(self) -> None:
        (self.project / "assets" / "replacement.png").write_bytes(b"replacement")
        before = self._tree_bytes(self.project)

        direct = analyze_asset_retirement_policy(
            self.project,
            source_path="assets/hero.png",
            replacement_path="assets/replacement.png",
        )
        analyzed = self.registry.run(
            "asset.retirement.analyze",
            {
                "project_path": str(self.project),
                "source_path": "assets/hero.png",
                "replacement_path": "assets/replacement.png",
            },
        )
        blocked_delete = self.registry.run(
            "asset.delete",
            {"project_path": str(self.project), "asset_path": "assets/hero.png"},
        )

        self.assertTrue(analyzed["ok"], analyzed)
        self.assertEqual(analyzed["result"], direct)
        self.assertEqual(analyzed["events"], [])
        self.assertFalse(self.registry.describe("asset.retirement.analyze")["mutates"])
        self.assertEqual(
            self.registry.describe("asset.retirement.analyze")["input_schema"]["required"],
            ["project_path", "source_path"],
        )
        self.assertFalse(blocked_delete["ok"])
        self.assertEqual(blocked_delete["error"]["code"], "asset_references_blocking")
        self.assertEqual(before, self._tree_bytes(self.project))
        self.assertFalse((self.project / ".vitaloom").exists())


    def test_referenced_replacement_command_delegates_to_transaction_authority(self) -> None:
        replacement = self.project / "assets" / "replacement.png"
        replacement.write_bytes(b"replacement")
        source_id = None
        replaced = self.registry.run(
            "asset.referenced.replace",
            {
                "project_path": str(self.project),
                "source_path": "assets/hero.png",
                "replacement_path": "assets/replacement.png",
            },
        )
        self.assertTrue(replaced["ok"], replaced)
        result = replaced["result"]
        source_id = result["asset_id"]
        self.assertFalse((self.project / "assets" / "hero.png").exists())
        self.assertEqual(replacement.read_bytes(), b"replacement")
        self.assertEqual(
            json.loads((self.project / "scenes" / "main.pond").read_text(encoding="utf-8"))["sprite_path"],
            "assets/replacement.png",
        )
        self.assertEqual(result["warnings"], ["replacement_semantic_compatibility_not_inferred"])
        self.assertIn("asset_retired", replaced["events"])
        description = self.registry.describe("asset.referenced.replace")
        self.assertTrue(description["mutates"])
        self.assertTrue(description["undoable"])
        self.assertEqual(description["input_schema"]["required"], ["project_path", "source_path", "replacement_path"])

        durable_undo = self.registry.run("command.undo_project", {"project_path": str(self.project)})
        self.assertTrue(durable_undo["ok"], durable_undo)
        self.assertTrue((self.project / "assets" / "hero.png").is_file())
        durable_redo = self.registry.run("command.redo_project", {"project_path": str(self.project)})
        self.assertTrue(durable_redo["ok"], durable_redo)
        self.assertFalse((self.project / "assets" / "hero.png").exists())

        undone = self.registry.run("command.undo")
        self.assertTrue(undone["ok"], undone)
        self.assertTrue((self.project / "assets" / "hero.png").is_file())
        self.assertEqual(replacement.read_bytes(), b"replacement")
        redone = self.registry.run("command.redo")
        self.assertTrue(redone["ok"], redone)
        self.assertFalse((self.project / "assets" / "hero.png").exists())
        self.assertEqual(replacement.read_bytes(), b"replacement")
        self.assertEqual(source_id, result["asset_id"])

        direct_undo = self.registry.run(
            "asset.transaction.undo",
            {"project_path": str(self.project), "transaction_id": result["transaction_id"]},
        )
        self.assertTrue(direct_undo["ok"], direct_undo)
        direct_redo = self.registry.run(
            "asset.transaction.redo",
            {"project_path": str(self.project), "transaction_id": result["transaction_id"]},
        )
        self.assertTrue(direct_redo["ok"], direct_redo)


    def test_command_delete_blocks_live_references_before_unlink(self) -> None:
        deleted = self.registry.run(
            "asset.delete",
            {"project_path": str(self.project), "asset_path": "assets/hero.png"},
        )
        self.assertFalse(deleted["ok"])
        self.assertEqual(deleted["error"]["code"], "asset_references_blocking")
        self.assertEqual(len(deleted["error"]["details"]["blocked_references"]), 1)
        self.assertTrue((self.project / "assets" / "hero.png").is_file())


    def test_durable_project_undo_replays_asset_transaction_receipt(self) -> None:
        renamed = self.registry.run(
            "asset.rename",
            {
                "project_path": str(self.project),
                "source_path": "assets/hero.png",
                "target_path": "assets/durable-hero.png",
            },
        )
        self.assertTrue(renamed["ok"], renamed)
        durable = self.registry.run("command.undo_project", {"project_path": str(self.project)})
        self.assertTrue(durable["ok"], durable)
        self.assertTrue((self.project / "assets" / "hero.png").is_file())


    def test_direct_transaction_commands_replay_a_rename_receipt(self) -> None:
        renamed = self.registry.run(
            "asset.rename",
            {
                "project_path": str(self.project),
                "source_path": "assets/hero.png",
                "target_path": "assets/direct-hero.png",
            },
        )
        self.assertTrue(renamed["ok"], renamed)
        transaction_id = renamed["result"]["transaction_id"]
        undone = self.registry.run(
            "asset.transaction.undo",
            {"project_path": str(self.project), "transaction_id": transaction_id},
        )
        self.assertTrue(undone["ok"], undone)
        self.assertTrue((self.project / "assets" / "hero.png").is_file())
        redone = self.registry.run(
            "asset.transaction.redo",
            {"project_path": str(self.project), "transaction_id": transaction_id},
        )
        self.assertTrue(redone["ok"], redone)
        self.assertTrue((self.project / "assets" / "direct-hero.png").is_file())

    def test_command_rename_migrates_active_scene_and_script_shorthand(self) -> None:
        (self.project / "scripts").mkdir()
        (self.project / "scripts" / "brain.py").write_text("print('brain')\n", encoding="utf-8")
        scene = self.project / "scenes" / "main.pond"
        scene.write_text(json.dumps({"entities": [{"scripts": [{"name": "brain"}]}]}), encoding="utf-8")
        script_rename = self.registry.run(
            "asset.rename",
            {
                "project_path": str(self.project),
                "source_path": "scripts/brain.py",
                "target_path": "scripts/mind.py",
            },
        )
        self.assertTrue(script_rename["ok"], script_rename)
        self.assertEqual(
            json.loads(scene.read_text(encoding="utf-8"))["entities"][0]["scripts"][0]["name"],
            "mind",
        )
        scene_rename = self.registry.run(
            "asset.rename",
            {
                "project_path": str(self.project),
                "source_path": "scenes/main.pond",
                "target_path": "scenes/renamed.pond",
            },
        )
        self.assertTrue(scene_rename["ok"], scene_rename)
        self.assertEqual(
            json.loads((self.project / "project.json").read_text(encoding="utf-8"))["active_scene"],
            "renamed.pond",
        )
        exported = self.registry.run("asset.export_closure", {"project_path": str(self.project)})
        self.assertTrue(exported["ok"], exported)
        self.assertTrue(exported["result"]["ready"])

    def test_durable_project_redo_replays_asset_transaction_receipt(self) -> None:
        renamed = self.registry.run(
            "asset.rename",
            {
                "project_path": str(self.project),
                "source_path": "assets/hero.png",
                "target_path": "assets/durable-redo-hero.png",
            },
        )
        self.assertTrue(renamed["ok"], renamed)
        durable_undo = self.registry.run("command.undo_project", {"project_path": str(self.project)})
        self.assertTrue(durable_undo["ok"], durable_undo)
        durable_redo = self.registry.run("command.redo_project", {"project_path": str(self.project)})
        self.assertTrue(durable_redo["ok"], durable_redo)
        self.assertEqual(durable_redo["result"]["durable_replay"], "project_redo")
        self.assertTrue((self.project / "assets" / "durable-redo-hero.png").is_file())


    def test_recovery_commands_delegate_to_the_transaction_authority(self) -> None:
        from core.VitaLoom.project.asset_reference_transaction import (
            apply_asset_reference_mutation,
            plan_asset_reference_mutation,
            undo_asset_reference_mutation,
        )

        plan = plan_asset_reference_mutation(
            self.project,
            operation="rename",
            source_path="assets/hero.png",
            target_path="assets/recovery-hero.png",
        )
        receipt = apply_asset_reference_mutation(self.project, plan)
        undo_asset_reference_mutation(self.project, receipt["transaction_id"])
        journal = self.project / ".vitaloom" / "asset_transactions" / f"{receipt['transaction_id']}.json"
        journal_data = json.loads(journal.read_text(encoding="utf-8"))
        journal_data["state"] = "prepared"
        journal.write_text(json.dumps(journal_data, ensure_ascii=False, indent=2), encoding="utf-8")

        listed = self.registry.run("asset.transaction.recovery.list", {"project_path": str(self.project)})
        inspected = self.registry.run(
            "asset.transaction.inspect",
            {"project_path": str(self.project), "transaction_id": receipt["transaction_id"]},
        )
        resolved = self.registry.run(
            "asset.transaction.recovery.resolve",
            {"project_path": str(self.project), "transaction_id": receipt["transaction_id"], "action": "rollback"},
        )

        self.assertTrue(listed["ok"], listed)
        self.assertTrue(listed["result"]["recovery_required"])
        self.assertEqual(listed["result"]["transactions"][0]["transaction_id"], receipt["transaction_id"])
        self.assertTrue(inspected["ok"], inspected)
        self.assertEqual(inspected["result"]["classification"], "prepared_before_state")
        self.assertTrue(resolved["ok"], resolved)
        self.assertEqual(resolved["result"]["state"], "undone")



    def test_retention_policy_command_is_read_only_and_matches_authority(self) -> None:
        from core.VitaLoom.project.asset_reference_transaction import analyze_asset_transaction_retention_policy

        before = self._tree_bytes(self.project)
        direct = analyze_asset_transaction_retention_policy(self.project)
        result = self.registry.run("asset.transaction.retention.analyze", {"project_path": str(self.project)})

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["result"], direct)
        self.assertEqual(result["events"], [])
        description = self.registry.describe("asset.transaction.retention.analyze")
        self.assertFalse(description["mutates"])
        self.assertEqual(description["input_schema"]["required"], ["project_path"])
        self.assertEqual(before, self._tree_bytes(self.project))


    def test_prune_command_requires_authority_plan_and_revokes_durable_project_undo(self) -> None:
        renamed = self.registry.run(
            "asset.rename",
            {
                "project_path": str(self.project),
                "source_path": "assets/hero.png",
                "target_path": "assets/renamed-hero.png",
            },
        )
        self.assertTrue(renamed["ok"], renamed)
        transaction_id = renamed["result"]["transaction_id"]
        journal_relative = f".vitaloom/asset_transactions/{transaction_id}.json"
        journal = self.project / journal_relative
        digest = __import__("hashlib").sha256(journal.read_bytes()).hexdigest()
        before_rejected = self._tree_bytes(self.project)

        rejected = self.registry.run(
            "asset.transaction.prune.apply",
            {
                "project_path": str(self.project),
                "artifact_paths": [journal_relative],
                "expected_digests": {journal_relative: digest},
                "policy_snapshot_digest": "0" * 64,
                "operator_confirmation": "not-the-authority-confirmation",
            },
        )
        planned = self.registry.run(
            "asset.transaction.prune.plan",
            {
                "project_path": str(self.project),
                "artifact_paths": [journal_relative],
                "expected_digests": {journal_relative: digest},
            },
        )

        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["events"], [])
        self.assertEqual(before_rejected, self._tree_bytes(self.project))
        self.assertTrue(planned["ok"], planned)
        self.assertEqual(planned["events"], [])
        self.assertFalse(self.registry.describe("asset.transaction.prune.plan")["mutates"])
        apply_description = self.registry.describe("asset.transaction.prune.apply")
        self.assertTrue(apply_description["mutates"])
        self.assertFalse(apply_description["undoable"])

        pruned = self.registry.run(
            "asset.transaction.prune.apply",
            {
                "project_path": str(self.project),
                "artifact_paths": [journal_relative],
                "expected_digests": {journal_relative: digest},
                "policy_snapshot_digest": planned["result"]["policy_snapshot_digest"],
                "operator_confirmation": planned["result"]["operator_confirmation_required"],
            },
        )
        undone = self.registry.undo_project(str(self.project))

        self.assertTrue(pruned["ok"], pruned)
        self.assertEqual(pruned["events"], ["asset_transaction_pruned"])
        self.assertIn("audit_id", pruned["result"])
        audit_path = self.project / ".vitaloom" / "command_audit.jsonl"
        audit_entries = [
            json.loads(line)
            for line in audit_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(audit_entries[-1]["command_id"], "asset.transaction.prune.apply")
        self.assertFalse(journal.exists())
        self.assertFalse(undone["ok"])
        self.assertEqual(undone["error"]["code"], "durable_undo_pruned")

    def test_forged_prune_receipt_never_revokes_durable_project_undo(self) -> None:
        renamed = self.registry.run(
            "asset.rename",
            {
                "project_path": str(self.project),
                "source_path": "assets/hero.png",
                "target_path": "assets/renamed-hero.png",
            },
        )
        self.assertTrue(renamed["ok"], renamed)
        forged_root = self.project / ".vitaloom" / "asset_transaction_prunes"
        forged_root.mkdir(parents=True, exist_ok=True)
        # An arbitrary or malformed receipt must be visible only as malformed
        # Authority data, never as permission to suppress durable replay.
        (forged_root / "forged.json").write_text("{}", encoding="utf-8")

        undone = self.registry.undo_project(str(self.project))

        self.assertTrue(undone["ok"], undone)
        self.assertEqual(undone["result"]["durable_replay"], "project_undo")
        self.assertTrue((self.project / "assets" / "hero.png").is_file())

    def test_durable_redo_honors_terminal_prune_revocation_boundary(self) -> None:
        renamed = self.registry.run(
            "asset.rename",
            {
                "project_path": str(self.project),
                "source_path": "assets/hero.png",
                "target_path": "assets/renamed-hero.png",
            },
        )
        self.assertTrue(renamed["ok"], renamed)
        undone = self.registry.undo_project(str(self.project))
        self.assertTrue(undone["ok"], undone)
        source_audit_id = renamed["result"]["audit_id"]

        from core.VitaLoom.project import asset_reference_transaction as authority

        with mock.patch.object(
            authority,
            "list_asset_transaction_artifact_prune_receipts",
            return_value={
                "project_path": str(self.project),
                "malformed_receipts": [],
                "receipts": [
                    {
                        "prune_id": "terminal-prune-boundary",
                        "state": "pruned",
                        "transaction_id": renamed["result"]["transaction_id"],
                        "source_audit_id": source_audit_id,
                        "source_command_id": "asset.rename",
                    }
                ],
            },
        ):
            redone = self.registry.redo_project(str(self.project))

        self.assertFalse(redone["ok"])
        self.assertEqual(redone["error"]["code"], "durable_redo_pruned")
        self.assertEqual(redone["error"]["details"]["source_execute_audit_id"], source_audit_id)


if __name__ == "__main__":
    unittest.main()
