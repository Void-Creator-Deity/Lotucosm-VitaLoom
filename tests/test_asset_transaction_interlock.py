# -*- coding: utf-8 -*-
"""Phase 7J proof for the durable asset-transaction cross-process interlock."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core.VitaLoom.project.asset_index import build_project_asset_index
from core.VitaLoom.project.asset_reference_transaction import (
    AssetReferenceTransactionError,
    analyze_asset_transaction_retention_policy,
    apply_asset_reference_mutation,
    apply_asset_transaction_artifact_prune,
    inspect_asset_reference_transaction,
    list_asset_reference_transaction_recovery,
    list_asset_transaction_artifact_prune_recovery,
    plan_asset_reference_mutation,
    redo_asset_reference_mutation,
    resolve_asset_reference_transaction,
    resolve_asset_transaction_artifact_prune,
    undo_asset_reference_mutation,
)
from core.VitaLoom.project.asset_transaction_interlock import (
    AssetTransactionInterlockError,
    acquire_asset_transaction_interlock,
    inspect_asset_transaction_interlock,
)


class AssetTransactionInterlockTests(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        project = root / "project"
        (project / "assets").mkdir(parents=True)
        (project / "assets" / "hero.bin").write_bytes(b"hero")
        (project / "project.json").write_text(json.dumps({"name": "phase7j"}), encoding="utf-8")
        (project / "project.lock.json").write_text("{}\n", encoding="utf-8")
        return project

    @staticmethod
    def _tree_bytes(project: Path) -> dict[str, bytes]:
        return {
            item.relative_to(project).as_posix(): item.read_bytes()
            for item in sorted(project.rglob("*"))
            if item.is_file() and not item.is_symlink()
        }

    def _assert_error_code(self, callback, expected: str) -> None:
        with self.assertRaises(AssetReferenceTransactionError) as captured:
            callback()
        self.assertEqual(captured.exception.code, expected)

    def test_inspect_absent_is_read_only_and_acquire_release_is_owner_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            absent = inspect_asset_transaction_interlock(project)
            self.assertEqual(absent["status"], "absent")
            self.assertFalse((project / ".vitaloom").exists())

            lease = acquire_asset_transaction_interlock(project, authority_action="test.owner")
            held = inspect_asset_transaction_interlock(project)
            self.assertTrue(held["held"])
            self.assertEqual(held["status"], "valid")
            self.assertEqual(held["record"]["owner_nonce"], lease.inspection["record"]["owner_nonce"])
            lease.release()
            self.assertEqual(inspect_asset_transaction_interlock(project)["status"], "absent")

    def test_valid_stale_malformed_and_foreign_locks_fail_closed_without_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            lock_path = project / ".vitaloom" / "asset_transaction_interlock.json"
            lock_path.parent.mkdir()
            cases = {
                "valid_old": {
                    "schema_version": 1,
                    "project_path": str(project.resolve()),
                    "owner_nonce": "a" * 64,
                    "pid": 1,
                    "created_at_utc": "2000-01-01T00:00:00.000000Z",
                    "authority_action": "interrupted.old",
                },
                "malformed": b"not-json\n",
                "foreign": {
                    "schema_version": 1,
                    "project_path": str((project.parent / "other-project").resolve()),
                    "owner_nonce": "b" * 64,
                    "pid": 2,
                    "created_at_utc": "2026-07-17T00:00:00.000000Z",
                    "authority_action": "foreign",
                },
            }
            for name, value in cases.items():
                if isinstance(value, bytes):
                    lock_path.write_bytes(value)
                else:
                    lock_path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
                before = self._tree_bytes(project)
                with self.assertRaises(AssetTransactionInterlockError) as captured:
                    acquire_asset_transaction_interlock(project, authority_action=f"test.{name}")
                self.assertEqual(captured.exception.code, "asset_transaction_interlock_held")
                self.assertEqual(before, self._tree_bytes(project), name)
                self.assertTrue(inspect_asset_transaction_interlock(project)["held"])

    def test_release_refuses_replaced_owner_evidence_without_deleting_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            lease = acquire_asset_transaction_interlock(project, authority_action="test.original")
            lock_path = project / ".vitaloom" / "asset_transaction_interlock.json"
            replacement = {
                "schema_version": 1,
                "project_path": str(project.resolve()),
                "owner_nonce": "c" * 64,
                "pid": 3,
                "created_at_utc": "2026-07-17T00:00:00.000000Z",
                "authority_action": "test.replacement",
            }
            lock_path.write_text(json.dumps(replacement, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaises(AssetTransactionInterlockError) as captured:
                lease.release()
            self.assertEqual(captured.exception.code, "asset_transaction_interlock_release_refused")
            self.assertEqual(json.loads(lock_path.read_text(encoding="utf-8")), replacement)

    def test_every_public_mutation_seam_rejects_before_any_mutation_when_held(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            plan = plan_asset_reference_mutation(
                project,
                operation="rename",
                source_path="assets/hero.bin",
                target_path="assets/renamed.bin",
            )
            self.assertTrue(plan["ready"])
            lease = acquire_asset_transaction_interlock(project, authority_action="test.holder")
            try:
                before = self._tree_bytes(project)
                blocked_calls = [
                    lambda: apply_asset_reference_mutation(project, plan),
                    lambda: undo_asset_reference_mutation(project, "missing"),
                    lambda: redo_asset_reference_mutation(project, "missing"),
                    lambda: resolve_asset_reference_transaction(project, "missing", action="rollback"),
                    lambda: apply_asset_transaction_artifact_prune(project, {}, operator_confirmation="unused"),
                    lambda: resolve_asset_transaction_artifact_prune(project, "missing", action="restore_staged"),
                ]
                for callback in blocked_calls:
                    self._assert_error_code(callback, "asset_transaction_interlock_held")
                    self.assertEqual(before, self._tree_bytes(project))
            finally:
                lease.release()

    def test_read_only_plans_inspection_index_and_policy_are_not_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            lease = acquire_asset_transaction_interlock(project, authority_action="test.holder")
            try:
                plan = plan_asset_reference_mutation(
                    project,
                    operation="rename",
                    source_path="assets/hero.bin",
                    target_path="assets/renamed.bin",
                )
                self.assertTrue(plan["ready"])
                with self.assertRaises(AssetReferenceTransactionError) as inspection_error:
                    inspect_asset_reference_transaction(project, "missing")
                self.assertEqual(inspection_error.exception.code, "asset_transaction_not_found")
                self.assertFalse(list_asset_reference_transaction_recovery(project)["recovery_required"])
                self.assertFalse(list_asset_transaction_artifact_prune_recovery(project)["recovery_required"])
                self.assertIn("artifacts", analyze_asset_transaction_retention_policy(project))
                self.assertIn("inventory", build_project_asset_index(project))
            finally:
                lease.release()

    def test_successful_mutation_releases_lock_and_allows_later_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            plan = plan_asset_reference_mutation(
                project,
                operation="rename",
                source_path="assets/hero.bin",
                target_path="assets/renamed.bin",
            )
            receipt = apply_asset_reference_mutation(project, plan)
            self.assertEqual(receipt["state"], "applied")
            self.assertEqual(inspect_asset_transaction_interlock(project)["status"], "absent")
            undo = undo_asset_reference_mutation(project, receipt["transaction_id"])
            self.assertEqual(undo["state"], "undone")
            self.assertEqual(inspect_asset_transaction_interlock(project)["status"], "absent")

    def test_real_second_process_is_refused_with_zero_project_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            lease = acquire_asset_transaction_interlock(project, authority_action="test.parent_holder")
            try:
                before = self._tree_bytes(project)
                script = '''
import json
import sys
from pathlib import Path
from core.VitaLoom.project.asset_reference_transaction import (
    AssetReferenceTransactionError,
    apply_asset_reference_mutation,
    plan_asset_reference_mutation,
)
project = Path(sys.argv[1])
plan = plan_asset_reference_mutation(
    project,
    operation="rename",
    source_path="assets/hero.bin",
    target_path="assets/renamed.bin",
)
try:
    apply_asset_reference_mutation(project, plan)
except AssetReferenceTransactionError as exc:
    print(json.dumps({"code": exc.code}, sort_keys=True))
    raise SystemExit(0)
raise SystemExit(9)
'''
                environment = dict(os.environ)
                environment["PYTHONPATH"] = os.pathsep.join(item for item in sys.path if item)
                completed = subprocess.run(
                    [sys.executable, "-c", script, str(project)],
                    cwd=str(project.parent),
                    env=environment,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(json.loads(completed.stdout)["code"], "asset_transaction_interlock_held")
                self.assertEqual(before, self._tree_bytes(project))
            finally:
                lease.release()


if __name__ == "__main__":
    unittest.main()
