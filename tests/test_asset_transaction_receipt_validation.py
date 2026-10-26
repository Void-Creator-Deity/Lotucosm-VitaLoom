# -*- coding: utf-8 -*-
"""Red/green coverage for strict durable asset transaction receipt validation."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.VitaLoom.project.asset_reference_transaction import (
    AssetReferenceTransactionError,
    apply_asset_reference_mutation,
    inspect_asset_reference_transaction,
    plan_asset_reference_mutation,
    undo_asset_reference_mutation,
)


class AssetTransactionReceiptValidationTests(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        project = root / "project"
        (project / "assets").mkdir(parents=True)
        (project / "scenes").mkdir(parents=True)
        (project / "assets" / "hero.bin").write_bytes(b"hero")
        (project / "project.json").write_text(
            json.dumps({"name": "receipt", "active_scene": "main.pond"}), encoding="utf-8"
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

    def _receipt(self, project: Path) -> tuple[str, Path]:
        receipt = apply_asset_reference_mutation(
            project,
            plan_asset_reference_mutation(
                project,
                operation="rename",
                source_path="assets/hero.bin",
                target_path="assets/renamed.bin",
            ),
        )
        journal = project / ".vitaloom" / "asset_transactions" / (receipt["transaction_id"] + ".json")
        return receipt["transaction_id"], journal

    def _assert_corrupt_receipt_is_read_only(
        self,
        mutate: object,
        *,
        expected_inspection: str = "malformed",
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            transaction_id, journal = self._receipt(project)
            data = json.loads(journal.read_text(encoding="utf-8"))
            mutate(data)
            journal.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            before = self._tree_bytes(project)

            inspection = inspect_asset_reference_transaction(project, transaction_id)
            self.assertEqual(inspection["classification"], expected_inspection)
            self.assertTrue(inspection["recovery_required"])
            self.assertEqual(inspection["legal_actions"], [])
            self.assertEqual(before, self._tree_bytes(project))

            with self.assertRaises(AssetReferenceTransactionError) as captured:
                undo_asset_reference_mutation(project, transaction_id)
            self.assertEqual(captured.exception.code, "asset_transaction_malformed")
            self.assertEqual(before, self._tree_bytes(project))

    def test_corrupt_common_receipt_facts_are_rejected_before_undo_writes(self) -> None:
        cases = {
            "id": lambda data: data.__setitem__("transaction_id", "other-receipt"),
            "unsafe-source": lambda data: data["plan"].__setitem__("source_path", "../escape.bin"),
            "bad-source-digest": lambda data: data["plan"].__setitem__("source_sha256", "not-a-sha256"),
            "unknown-state": (lambda data: data.__setitem__("state", "imaginary"), "unknown_state"),
            "unexpected-backup": lambda data: data.__setitem__("asset_backup", "assets/hero.bin"),
        }
        for name, item in cases.items():
            mutate, expected = item if isinstance(item, tuple) else (item, "malformed")
            with self.subTest(name=name):
                self._assert_corrupt_receipt_is_read_only(mutate, expected_inspection=expected)

    def test_corrupt_file_records_are_rejected_before_payload_decode_or_undo_writes(self) -> None:
        cases = {
            "invalid-base64": lambda data: data["files"][0].__setitem__("before_base64", "%%%"),
            "payload-digest-mismatch": lambda data: data["files"][0].__setitem__("after_base64", "Y2hhbmdlZA=="),
            "unsafe-owner": lambda data: data["files"][0].__setitem__("path", "../project.json"),
            "duplicate-owner": lambda data: data["files"].append(dict(data["files"][0])),
            "partial-record": lambda data: data["files"][0].pop("after_base64"),
        }
        for name, mutate in cases.items():
            with self.subTest(name=name):
                self._assert_corrupt_receipt_is_read_only(mutate)

    def test_valid_legacy_rename_receipt_remains_undoable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            transaction_id, _journal = self._receipt(project)

            result = undo_asset_reference_mutation(project, transaction_id)

            self.assertEqual(result["state"], "undone")
            self.assertTrue((project / "assets" / "hero.bin").is_file())


    def test_json_and_non_object_receipts_are_rejected_without_any_project_write(self) -> None:
        for name, raw in (("invalid-json", b"{not-json"), ("array-root", b"[]")):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                project = self._project(Path(tmp))
                transaction_id, journal = self._receipt(project)
                journal.write_bytes(raw)
                before = self._tree_bytes(project)

                inspection = inspect_asset_reference_transaction(project, transaction_id)
                self.assertEqual(inspection["classification"], "malformed")
                self.assertEqual(before, self._tree_bytes(project))
                with self.assertRaises(AssetReferenceTransactionError) as captured:
                    undo_asset_reference_mutation(project, transaction_id)
                self.assertEqual(captured.exception.code, "asset_transaction_malformed")
                self.assertEqual(before, self._tree_bytes(project))

    def test_delete_receipt_missing_or_misdirecting_private_backup_is_rejected_without_undo_write(self) -> None:
        for name, mutate in (
            ("missing", lambda data: data.pop("asset_backup")),
            ("wrong-path", lambda data: data.__setitem__("asset_backup", "assets/hero.bin")),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                project = self._project(Path(tmp))
                (project / "assets" / "unused.bin").write_bytes(b"unused")
                receipt = apply_asset_reference_mutation(
                    project,
                    plan_asset_reference_mutation(project, operation="delete", source_path="assets/unused.bin"),
                )
                journal = project / ".vitaloom" / "asset_transactions" / (receipt["transaction_id"] + ".json")
                data = json.loads(journal.read_text(encoding="utf-8"))
                mutate(data)
                journal.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                before = self._tree_bytes(project)

                self.assertEqual(inspect_asset_reference_transaction(project, receipt["transaction_id"])["classification"], "malformed")
                with self.assertRaises(AssetReferenceTransactionError) as captured:
                    undo_asset_reference_mutation(project, receipt["transaction_id"])
                self.assertEqual(captured.exception.code, "asset_transaction_malformed")
                self.assertEqual(before, self._tree_bytes(project))

    def test_replacement_receipt_missing_target_digest_is_rejected_without_undo_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            (project / "assets" / "replacement.bin").write_bytes(b"replacement")
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(
                    project,
                    operation="replace_referenced",
                    source_path="assets/hero.bin",
                    target_path="assets/replacement.bin",
                ),
            )
            journal = project / ".vitaloom" / "asset_transactions" / (receipt["transaction_id"] + ".json")
            data = json.loads(journal.read_text(encoding="utf-8"))
            data["plan"].pop("target_sha256")
            journal.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            before = self._tree_bytes(project)

            self.assertEqual(inspect_asset_reference_transaction(project, receipt["transaction_id"])["classification"], "malformed")
            with self.assertRaises(AssetReferenceTransactionError) as captured:
                undo_asset_reference_mutation(project, receipt["transaction_id"])
            self.assertEqual(captured.exception.code, "asset_transaction_malformed")
            self.assertEqual(before, self._tree_bytes(project))


if __name__ == "__main__":
    unittest.main()
