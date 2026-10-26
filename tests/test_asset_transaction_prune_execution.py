# -*- coding: utf-8 -*-
"""TDD contract for Phase 7I operator-confirmed transaction artifact pruning."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path
from typing import Any, Callable

from core.VitaLoom.project.asset_reference_transaction import (
    AssetReferenceTransactionError,
    apply_asset_reference_mutation,
    plan_asset_reference_mutation,
)


class AssetTransactionPruneExecutionTests(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        project = root / "project"
        (project / "assets").mkdir(parents=True)
        (project / "scenes").mkdir(parents=True)
        (project / "assets" / "hero.bin").write_bytes(b"hero")
        (project / "project.json").write_text(
            json.dumps({"name": "prune", "active_scene": "main.pond"}), encoding="utf-8"
        )
        (project / "project.lock.json").write_text("{}", encoding="utf-8")
        (project / "scenes" / "main.pond").write_text(
            json.dumps({"asset_path": "../assets/hero.bin"}), encoding="utf-8"
        )
        return project

    @staticmethod
    def _tree_bytes(root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    @staticmethod
    def _digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _assert_error_code(case: unittest.TestCase, code: str, callback: Callable[[], Any]) -> None:
        with case.assertRaises(AssetReferenceTransactionError) as caught:
            callback()
        case.assertEqual(caught.exception.code, code)

    @staticmethod
    def _prune_api() -> tuple[Callable[..., dict[str, Any]], Callable[..., dict[str, Any]]]:
        # Deliberately imported through the future public Authority seam: this is
        # the initial red-test boundary, not a private filesystem helper contract.
        from core.VitaLoom.project.asset_reference_transaction import (  # type: ignore[attr-defined]
            apply_asset_transaction_artifact_prune,
            plan_asset_transaction_artifact_prune,
        )

        return plan_asset_transaction_artifact_prune, apply_asset_transaction_artifact_prune

    def _write_exact_execute_audit(self, project: Path, receipt: dict[str, Any], command_id: str) -> None:
        audit = project / ".vitaloom" / "command_audit.jsonl"
        audit.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "schema_version": 1,
            "audit_id": "phase7i-source-audit",
            "action": "execute",
            "command_id": command_id,
            "project_path": str(project),
            "payload": {"project_path": str(project)},
            "result": {"transaction_id": receipt["transaction_id"]},
            "events": ["asset_transaction_applied"],
        }
        audit.write_text(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    def test_plan_is_read_only_and_binds_exact_terminal_journal_confirmation(self) -> None:
        plan_prune, _apply_prune = self._prune_api()
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(
                    project,
                    operation="rename",
                    source_path="assets/hero.bin",
                    target_path="assets/renamed.bin",
                ),
            )
            self._write_exact_execute_audit(project, receipt, "asset.rename")
            journal_relative = ".vitaloom/asset_transactions/" + receipt["transaction_id"] + ".json"
            journal = project / journal_relative
            before = self._tree_bytes(project)

            prune_plan = plan_prune(
                project,
                artifact_paths=[journal_relative],
                expected_digests={journal_relative: self._digest(journal)},
            )

            self.assertTrue(prune_plan["read_only"])
            self.assertFalse(prune_plan["prune_authorized"])
            self.assertEqual(prune_plan["artifact_paths"], [journal_relative])
            self.assertEqual(prune_plan["expected_digests"], {journal_relative: self._digest(journal)})
            self.assertEqual(prune_plan["transaction_id"], receipt["transaction_id"])
            self.assertTrue(prune_plan["policy_snapshot_digest"])
            self.assertTrue(prune_plan["operator_confirmation_required"])
            self.assertEqual(before, self._tree_bytes(project))

    def test_apply_rejects_missing_or_wrong_confirmation_without_any_write(self) -> None:
        plan_prune, apply_prune = self._prune_api()
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(
                    project,
                    operation="rename",
                    source_path="assets/hero.bin",
                    target_path="assets/renamed.bin",
                ),
            )
            self._write_exact_execute_audit(project, receipt, "asset.rename")
            journal_relative = ".vitaloom/asset_transactions/" + receipt["transaction_id"] + ".json"
            journal = project / journal_relative
            prune_plan = plan_prune(
                project,
                artifact_paths=[journal_relative],
                expected_digests={journal_relative: self._digest(journal)},
            )
            before = self._tree_bytes(project)

            self._assert_error_code(
                self,
                "asset_transaction_prune_confirmation_invalid",
                lambda: apply_prune(project, prune_plan, operator_confirmation="yes"),
            )

            self.assertEqual(before, self._tree_bytes(project))

    def test_delete_bundle_requires_every_exact_linked_artifact_and_rejects_stale_snapshot(self) -> None:
        plan_prune, apply_prune = self._prune_api()
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            (project / "assets" / "unused.bin").write_bytes(b"unused")
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(project, operation="delete", source_path="assets/unused.bin"),
            )
            self._write_exact_execute_audit(project, receipt, "asset.delete")
            journal_relative = ".vitaloom/asset_transactions/" + receipt["transaction_id"] + ".json"
            backup_relative = ".vitaloom/asset_transactions/" + receipt["transaction_id"] + ".asset"
            journal = project / journal_relative
            backup = project / backup_relative
            before_incomplete = self._tree_bytes(project)

            self._assert_error_code(
                self,
                "asset_transaction_prune_bundle_mismatch",
                lambda: plan_prune(
                    project,
                    artifact_paths=[journal_relative],
                    expected_digests={journal_relative: self._digest(journal)},
                ),
            )
            self.assertEqual(before_incomplete, self._tree_bytes(project))

            prune_plan = plan_prune(
                project,
                artifact_paths=[journal_relative, backup_relative],
                expected_digests={
                    journal_relative: self._digest(journal),
                    backup_relative: self._digest(backup),
                },
            )
            journal.write_bytes(journal.read_bytes() + b" ")
            before_stale_apply = self._tree_bytes(project)

            self._assert_error_code(
                self,
                "asset_transaction_prune_stale",
                lambda: apply_prune(
                    project,
                    prune_plan,
                    operator_confirmation=str(prune_plan["operator_confirmation_required"]),
                ),
            )
            self.assertEqual(before_stale_apply, self._tree_bytes(project))

    def test_protected_or_unknown_or_bulk_requests_are_rejected_before_prune_receipt_write(self) -> None:
        plan_prune, _apply_prune = self._prune_api()
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(
                    project,
                    operation="rename",
                    source_path="assets/hero.bin",
                    target_path="assets/renamed.bin",
                ),
            )
            self._write_exact_execute_audit(project, receipt, "asset.rename")
            root = project / ".vitaloom" / "asset_transactions"
            journal_relative = ".vitaloom/asset_transactions/" + receipt["transaction_id"] + ".json"
            journal = project / journal_relative
            malformed_relative = ".vitaloom/asset_transactions/not-a-receipt.json"
            (project / malformed_relative).write_text("{broken", encoding="utf-8")
            before = self._tree_bytes(project)

            self._assert_error_code(
                self,
                "asset_transaction_prune_not_reviewable",
                lambda: plan_prune(
                    project,
                    artifact_paths=[malformed_relative],
                    expected_digests={malformed_relative: self._digest(project / malformed_relative)},
                ),
            )
            self._assert_error_code(
                self,
                "asset_transaction_prune_bundle_mismatch",
                lambda: plan_prune(
                    project,
                    artifact_paths=[journal_relative, journal_relative],
                    expected_digests={journal_relative: self._digest(journal)},
                ),
            )
            self._assert_error_code(
                self,
                "asset_transaction_prune_bundle_mismatch",
                lambda: plan_prune(
                    project,
                    artifact_paths=[journal_relative, "project.json"],
                    expected_digests={
                        journal_relative: self._digest(journal),
                        "project.json": self._digest(project / "project.json"),
                    },
                ),
            )
            self.assertEqual(before, self._tree_bytes(project))
            self.assertTrue(root.is_dir())


    def test_exact_confirmation_prunes_only_journal_and_persists_minimal_terminal_receipt(self) -> None:
        plan_prune, apply_prune = self._prune_api()
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(
                    project,
                    operation="rename",
                    source_path="assets/hero.bin",
                    target_path="assets/renamed.bin",
                ),
            )
            self._write_exact_execute_audit(project, receipt, "asset.rename")
            journal_relative = ".vitaloom/asset_transactions/" + receipt["transaction_id"] + ".json"
            journal = project / journal_relative
            scene_before = (project / "scenes" / "main.pond").read_bytes()
            prune_plan = plan_prune(
                project,
                artifact_paths=[journal_relative],
                expected_digests={journal_relative: self._digest(journal)},
            )

            result = apply_prune(
                project,
                prune_plan,
                operator_confirmation=str(prune_plan["operator_confirmation_required"]),
            )

            self.assertEqual(result["state"], "pruned")
            self.assertFalse(journal.exists())
            self.assertTrue((project / "assets" / "renamed.bin").is_file())
            self.assertEqual(scene_before, (project / "scenes" / "main.pond").read_bytes())
            prune_receipt = project / result["receipt_path"]
            persisted = json.loads(prune_receipt.read_text(encoding="utf-8"))
            self.assertEqual(persisted["state"], "pruned")
            self.assertEqual(persisted["artifact_paths"], [journal_relative])
            self.assertNotIn("plan", persisted)
            self.assertNotIn("files", persisted)
            self.assertNotIn("asset_backup", persisted)

    def test_delete_bundle_prunes_journal_and_private_backup_together(self) -> None:
        plan_prune, apply_prune = self._prune_api()
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            (project / "scenes" / "main.pond").write_text(json.dumps({"asset_path": ""}), encoding="utf-8")
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(project, operation="delete", source_path="assets/hero.bin"),
            )
            self._write_exact_execute_audit(project, receipt, "asset.delete")
            journal_relative = ".vitaloom/asset_transactions/" + receipt["transaction_id"] + ".json"
            backup_relative = ".vitaloom/asset_transactions/" + receipt["transaction_id"] + ".asset"
            journal, backup = project / journal_relative, project / backup_relative
            self.assertTrue(backup.is_file())
            prune_plan = plan_prune(
                project,
                artifact_paths=[journal_relative, backup_relative],
                expected_digests={
                    journal_relative: self._digest(journal),
                    backup_relative: self._digest(backup),
                },
            )

            result = apply_prune(
                project,
                prune_plan,
                operator_confirmation=str(prune_plan["operator_confirmation_required"]),
            )

            self.assertEqual(result["state"], "pruned")
            self.assertFalse(journal.exists())
            self.assertFalse(backup.exists())
            self.assertFalse((project / "assets" / "hero.bin").exists())
            self.assertTrue((project / "scenes" / "main.pond").is_file())

    def test_stage_failure_compensates_all_artifacts_without_touching_project_state(self) -> None:
        plan_prune, apply_prune = self._prune_api()
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            (project / "scenes" / "main.pond").write_text(json.dumps({"asset_path": ""}), encoding="utf-8")
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(project, operation="delete", source_path="assets/hero.bin"),
            )
            self._write_exact_execute_audit(project, receipt, "asset.delete")
            journal_relative = ".vitaloom/asset_transactions/" + receipt["transaction_id"] + ".json"
            backup_relative = ".vitaloom/asset_transactions/" + receipt["transaction_id"] + ".asset"
            journal, backup = project / journal_relative, project / backup_relative
            prune_plan = plan_prune(
                project,
                artifact_paths=[journal_relative, backup_relative],
                expected_digests={journal_relative: self._digest(journal), backup_relative: self._digest(backup)},
            )
            before_scene = (project / "scenes" / "main.pond").read_bytes()
            from core.VitaLoom.project import asset_reference_transaction as authority

            original_move = authority._move_prune_artifact
            calls = 0

            def fail_second_move(source: Path, destination: Path) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected stage failure")
                original_move(source, destination)

            with mock.patch.object(authority, "_move_prune_artifact", side_effect=fail_second_move):
                self._assert_error_code(
                    self,
                    "asset_transaction_prune_io_failed",
                    lambda: apply_prune(
                        project,
                        prune_plan,
                        operator_confirmation=str(prune_plan["operator_confirmation_required"]),
                    ),
                )

            self.assertTrue(journal.is_file())
            self.assertTrue(backup.is_file())
            self.assertEqual(before_scene, (project / "scenes" / "main.pond").read_bytes())
            receipts = list((project / ".vitaloom" / "asset_transaction_prunes").glob("*.json"))
            self.assertEqual(len(receipts), 1)
            self.assertEqual(json.loads(receipts[0].read_text(encoding="utf-8"))["state"], "compensated")

    def test_interrupted_cleanup_is_inspectable_and_explicit_restore_returns_staged_artifacts(self) -> None:
        plan_prune, apply_prune = self._prune_api()
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            (project / "scenes" / "main.pond").write_text(json.dumps({"asset_path": ""}), encoding="utf-8")
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(project, operation="delete", source_path="assets/hero.bin"),
            )
            self._write_exact_execute_audit(project, receipt, "asset.delete")
            journal_relative = ".vitaloom/asset_transactions/" + receipt["transaction_id"] + ".json"
            backup_relative = ".vitaloom/asset_transactions/" + receipt["transaction_id"] + ".asset"
            journal, backup = project / journal_relative, project / backup_relative
            prune_plan = plan_prune(
                project,
                artifact_paths=[journal_relative, backup_relative],
                expected_digests={journal_relative: self._digest(journal), backup_relative: self._digest(backup)},
            )
            from core.VitaLoom.project import asset_reference_transaction as authority

            with mock.patch.object(authority, "_remove_prune_staged_artifact", side_effect=OSError("injected cleanup stop")):
                self._assert_error_code(
                    self,
                    "asset_transaction_prune_recovery_required",
                    lambda: apply_prune(
                        project,
                        prune_plan,
                        operator_confirmation=str(prune_plan["operator_confirmation_required"]),
                    ),
                )

            prune_receipt = next((project / ".vitaloom" / "asset_transaction_prunes").glob("*.json"))
            prune_id = prune_receipt.stem
            inspection = authority.inspect_asset_transaction_artifact_prune(project, prune_id)
            self.assertTrue(inspection["recovery_required"])
            self.assertEqual(inspection["state"], "staged_cleanup_incomplete")
            self.assertEqual(inspection["legal_actions"], ["restore_staged"])
            restored = authority.resolve_asset_transaction_artifact_prune(project, prune_id, action="restore_staged")
            self.assertEqual(restored["state"], "recovered")
            self.assertTrue(journal.is_file())
            self.assertTrue(backup.is_file())
            self.assertEqual(
                authority.inspect_asset_transaction_artifact_prune(project, prune_id)["recovery_required"],
                False,
            )


if __name__ == "__main__":
    unittest.main()
