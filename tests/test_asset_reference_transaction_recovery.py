# -*- coding: utf-8 -*-
"""TDD coverage for Phase 7D asset transaction recovery inspection Authority."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.VitaLoom.project.asset_reference_transaction import (
    AssetReferenceTransactionError,
    apply_asset_reference_mutation,
    inspect_asset_reference_transaction,
    list_asset_reference_transaction_recovery,
    plan_asset_reference_mutation,
    redo_asset_reference_mutation,
    resolve_asset_reference_transaction,
    undo_asset_reference_mutation,
)


class AssetReferenceTransactionRecoveryInspectionTests(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        project = root / "project"
        (project / "assets" / "sprites").mkdir(parents=True)
        (project / "scenes").mkdir(parents=True)
        (project / "assets" / "sprites" / "hero.png").write_bytes(b"hero")
        (project / "project.json").write_text(
            json.dumps({"name": "phase7d", "active_scene": "main.pond"}), encoding="utf-8"
        )
        (project / "project.lock.json").write_text("{}", encoding="utf-8")
        (project / "scenes" / "main.pond").write_text(
            json.dumps({"sprite_path": "../assets/sprites/hero.png"}), encoding="utf-8"
        )
        return project

    @staticmethod
    def _tree_bytes(root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    def _prepared_rename_journal(self, project: Path) -> tuple[str, Path]:
        plan = plan_asset_reference_mutation(
            project,
            operation="rename",
            source_path="assets/sprites/hero.png",
            target_path="assets/sprites/renamed-hero.png",
        )
        receipt = apply_asset_reference_mutation(project, plan)
        undo_asset_reference_mutation(project, receipt["transaction_id"])
        journal = project / ".vitaloom" / "asset_transactions" / f"{receipt['transaction_id']}.json"
        data = json.loads(journal.read_text(encoding="utf-8"))
        data["state"] = "prepared"
        journal.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return receipt["transaction_id"], journal

    def test_inspect_valid_prepared_journal_is_deterministic_read_only_and_exposes_safe_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            transaction_id, _journal = self._prepared_rename_journal(project)
            before = self._tree_bytes(project)

            inspection = inspect_asset_reference_transaction(project, transaction_id)

            self.assertEqual(inspection["transaction_id"], transaction_id)
            self.assertEqual(inspection["journal_state"], "prepared")
            self.assertEqual(inspection["classification"], "prepared_before_state")
            self.assertTrue(inspection["recovery_required"])
            self.assertEqual(inspection["legal_actions"], ["rollback"])
            self.assertEqual(inspection["conflicts"], [])
            self.assertEqual(inspection["affected_paths"], sorted(inspection["affected_paths"]))
            self.assertEqual(
                inspection["journal_path"], f".vitaloom/asset_transactions/{transaction_id}.json"
            )
            self.assertEqual(before, self._tree_bytes(project))

    def test_compensated_failure_before_state_is_recovery_required_but_not_reported_as_applied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            transaction_id, journal = self._prepared_rename_journal(project)
            data = json.loads(journal.read_text(encoding="utf-8"))
            data["state"] = "failed_recoverable"
            journal.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

            inspection = inspect_asset_reference_transaction(project, transaction_id)

            self.assertEqual(inspection["classification"], "failed_recoverable_before_state")
            self.assertTrue(inspection["recovery_required"])
            self.assertNotEqual(inspection["classification"], "terminal_applied")
            self.assertEqual(inspection["legal_actions"], ["acknowledge_failure"])

    def test_malformed_and_unsupported_journals_are_deterministic_and_never_mutable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            root = project / ".vitaloom" / "asset_transactions"
            root.mkdir(parents=True)
            malformed = root / "broken.json"
            malformed.write_text("{not json", encoding="utf-8")
            unsupported = root / "future.json"
            unsupported.write_text(json.dumps({"schema_version": 99, "state": "prepared"}), encoding="utf-8")

            before = self._tree_bytes(project)
            broken = inspect_asset_reference_transaction(project, "broken")
            future = inspect_asset_reference_transaction(project, "future")
            listing = list_asset_reference_transaction_recovery(project)

            self.assertEqual(broken["classification"], "malformed")
            self.assertEqual(broken["legal_actions"], [])
            self.assertTrue(broken["recovery_required"])
            self.assertEqual(future["classification"], "unsupported_schema")
            self.assertEqual(future["legal_actions"], [])
            self.assertTrue(future["recovery_required"])
            self.assertEqual([item["transaction_id"] for item in listing["transactions"]], ["broken", "future"])
            self.assertEqual(before, self._tree_bytes(project))

    def test_unknown_state_is_recovery_required_and_has_no_mutation_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            transaction_id, journal = self._prepared_rename_journal(project)
            data = json.loads(journal.read_text(encoding="utf-8"))
            data["state"] = "waiting_for_magic"
            journal.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

            inspection = inspect_asset_reference_transaction(project, transaction_id)

            self.assertEqual(inspection["classification"], "unknown_state")
            self.assertTrue(inspection["recovery_required"])
            self.assertEqual(inspection["legal_actions"], [])

    def test_changed_delete_backup_is_an_explicit_conflict_with_no_recovery_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            unused = project / "assets" / "sprites" / "unused.bin"
            unused.write_bytes(b"unused")
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(project, operation="delete", source_path="assets/sprites/unused.bin"),
            )
            undo_asset_reference_mutation(project, receipt["transaction_id"])
            journal = project / ".vitaloom" / "asset_transactions" / f"{receipt['transaction_id']}.json"
            data = json.loads(journal.read_text(encoding="utf-8"))
            data["state"] = "prepared"
            journal.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            backup = project / ".vitaloom" / "asset_transactions" / f"{receipt['transaction_id']}.asset"
            backup.write_bytes(b"user-edited-backup")
            before = self._tree_bytes(project)

            inspection = inspect_asset_reference_transaction(project, receipt["transaction_id"])

            self.assertEqual(inspection["classification"], "conflict")
            self.assertEqual(inspection["legal_actions"], [])
            self.assertTrue(any(item["role"] == "asset_backup" for item in inspection["conflicts"]))
            self.assertEqual(before, self._tree_bytes(project))

    def test_current_user_digest_conflict_removes_all_recovery_actions_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            transaction_id, _journal = self._prepared_rename_journal(project)
            source = project / "assets" / "sprites" / "hero.png"
            source.write_bytes(b"user-rebuilt-hero")
            before = self._tree_bytes(project)

            inspection = inspect_asset_reference_transaction(project, transaction_id)

            self.assertEqual(inspection["classification"], "conflict")
            self.assertEqual(inspection["legal_actions"], [])
            self.assertTrue(inspection["recovery_required"])
            source_conflict = next(item for item in inspection["conflicts"] if item["path"] == "assets/sprites/hero.png")
            self.assertEqual(source_conflict["expected_sha256"], inspection["plan"]["source_sha256"])
            self.assertNotEqual(source_conflict["current_sha256"], source_conflict["expected_sha256"])
            self.assertEqual(before, self._tree_bytes(project))

    def test_guarded_rollback_finalizes_only_a_proven_before_state_and_preserves_redo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            transaction_id, journal = self._prepared_rename_journal(project)
            before = self._tree_bytes(project)

            result = resolve_asset_reference_transaction(project, transaction_id, action="rollback")

            self.assertEqual(result["state"], "undone")
            self.assertEqual(result["action"], "rollback")
            self.assertEqual(before["assets/sprites/hero.png"], (project / "assets" / "sprites" / "hero.png").read_bytes())
            self.assertEqual(before["scenes/main.pond"], (project / "scenes" / "main.pond").read_bytes())
            resolved = json.loads(journal.read_text(encoding="utf-8"))
            self.assertEqual(resolved["state"], "undone")
            self.assertEqual(resolved["recovery_resolution"]["reason"], "filesystem_before_state")
            self.assertFalse(inspect_asset_reference_transaction(project, transaction_id)["recovery_required"])
            self.assertEqual(redo_asset_reference_mutation(project, transaction_id)["state"], "applied")

    def test_acknowledging_proven_compensated_failure_preserves_files_and_ends_recovery_attention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            transaction_id, journal = self._prepared_rename_journal(project)
            data = json.loads(journal.read_text(encoding="utf-8"))
            data["state"] = "failed_recoverable"
            journal.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            before = self._tree_bytes(project)

            result = resolve_asset_reference_transaction(project, transaction_id, action="acknowledge_failure")

            self.assertEqual(result["state"], "failed_acknowledged")
            after = self._tree_bytes(project)
            self.assertEqual(before["assets/sprites/hero.png"], after["assets/sprites/hero.png"])
            self.assertEqual(before["scenes/main.pond"], after["scenes/main.pond"])
            inspection = inspect_asset_reference_transaction(project, transaction_id)
            self.assertEqual(inspection["classification"], "terminal_failed_acknowledged")
            self.assertFalse(inspection["recovery_required"])

    def test_resolver_refuses_conflict_and_never_overwrites_user_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            transaction_id, _journal = self._prepared_rename_journal(project)
            source = project / "assets" / "sprites" / "hero.png"
            source.write_bytes(b"user-rebuilt-hero")
            before = self._tree_bytes(project)

            with self.assertRaises(AssetReferenceTransactionError) as captured:
                resolve_asset_reference_transaction(project, transaction_id, action="rollback")

            self.assertEqual(captured.exception.code, "asset_transaction_recovery_action_not_safe")
            self.assertEqual(before, self._tree_bytes(project))

    def test_delete_redo_refuses_to_overwrite_a_changed_private_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            (project / "assets" / "sprites" / "unused.bin").write_bytes(b"unused")
            plan = plan_asset_reference_mutation(project, operation="delete", source_path="assets/sprites/unused.bin")
            receipt = apply_asset_reference_mutation(project, plan)
            undo_asset_reference_mutation(project, receipt["transaction_id"])
            backup = project / ".vitaloom" / "asset_transactions" / f"{receipt['transaction_id']}.asset"
            backup.write_bytes(b"user-edited-backup")
            before = self._tree_bytes(project)

            with self.assertRaises(AssetReferenceTransactionError) as captured:
                redo_asset_reference_mutation(project, receipt["transaction_id"])

            self.assertEqual(captured.exception.code, "asset_transaction_backup_changed")
            self.assertEqual(before, self._tree_bytes(project))

    def test_terminal_applied_and_undone_journals_are_not_recovery_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            plan = plan_asset_reference_mutation(
                project,
                operation="rename",
                source_path="assets/sprites/hero.png",
                target_path="assets/sprites/renamed-hero.png",
            )
            receipt = apply_asset_reference_mutation(project, plan)
            applied = inspect_asset_reference_transaction(project, receipt["transaction_id"])
            undo_asset_reference_mutation(project, receipt["transaction_id"])
            undone = inspect_asset_reference_transaction(project, receipt["transaction_id"])
            listing = list_asset_reference_transaction_recovery(project)

            self.assertEqual(applied["classification"], "terminal_applied")
            self.assertFalse(applied["recovery_required"])
            self.assertEqual(undone["classification"], "terminal_undone")
            self.assertFalse(undone["recovery_required"])
            self.assertFalse(listing["recovery_required"])
            self.assertEqual(listing["transactions"], [])


    def test_recovery_rejects_referenced_replacement_journal_without_target_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            replacement = project / "assets" / "sprites" / "replacement.png"
            replacement.write_bytes(b"replacement")
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(
                    project,
                    operation="replace_referenced",
                    source_path="assets/sprites/hero.png",
                    target_path="assets/sprites/replacement.png",
                ),
            )
            journal = project / ".vitaloom" / "asset_transactions" / f"{receipt['transaction_id']}.json"
            data = json.loads(journal.read_text(encoding="utf-8"))
            data["plan"].pop("target_sha256")
            journal.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

            inspection = inspect_asset_reference_transaction(project, receipt["transaction_id"])
            self.assertEqual(inspection["classification"], "malformed")
            self.assertTrue(inspection["recovery_required"])
            self.assertEqual(inspection["legal_actions"], [])


    def test_inspect_referenced_replacement_tracks_immutable_replacement_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            replacement = project / "assets" / "sprites" / "replacement.png"
            replacement.write_bytes(b"replacement")
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(
                    project,
                    operation="replace_referenced",
                    source_path="assets/sprites/hero.png",
                    target_path="assets/sprites/replacement.png",
                ),
            )
            inspection = inspect_asset_reference_transaction(project, receipt["transaction_id"])
            self.assertEqual(inspection["classification"], "terminal_applied")
            self.assertFalse(inspection["recovery_required"])
            replacement_fact = next(item for item in inspection["file_facts"] if item["role"] == "replacement_asset")
            self.assertEqual(replacement_fact["status"], "before")
            self.assertEqual(replacement_fact["current_sha256"], inspection["plan"]["target_sha256"])

            replacement.write_bytes(b"user-modified-replacement")
            conflict = inspect_asset_reference_transaction(project, receipt["transaction_id"])
            self.assertEqual(conflict["classification"], "terminal_conflict")
            self.assertTrue(any(item["role"] == "replacement_asset" for item in conflict["file_facts"]))
            self.assertTrue(any(item["path"] == "assets/sprites/replacement.png" for item in conflict["conflicts"]))


if __name__ == "__main__":
    unittest.main()
