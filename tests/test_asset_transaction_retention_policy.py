# -*- coding: utf-8 -*-
"""TDD coverage for read-only durable transaction retention policy Authority."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.VitaLoom.project.asset_reference_transaction import (
    analyze_asset_transaction_retention_policy,
    apply_asset_reference_mutation,
    plan_asset_reference_mutation,
    undo_asset_reference_mutation,
)


class AssetTransactionRetentionPolicyTests(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        project = root / "project"
        (project / "assets").mkdir(parents=True)
        (project / "scenes").mkdir(parents=True)
        (project / "assets" / "hero.bin").write_bytes(b"hero")
        (project / "project.json").write_text(
            json.dumps({"name": "retention", "active_scene": "main.pond"}), encoding="utf-8"
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

    def test_empty_transaction_root_is_deterministic_read_only_and_prunes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            before = self._tree_bytes(project)

            policy = analyze_asset_transaction_retention_policy(project)

            self.assertTrue(policy["read_only"])
            self.assertEqual(policy["artifacts"], [])
            self.assertEqual(policy["review_candidates"], [])
            self.assertEqual(policy["safe_prune_candidates"], [])
            self.assertFalse(policy["prune_authorized"])
            self.assertEqual(before, self._tree_bytes(project))

    def test_terminal_rename_receipt_is_retained_not_implicitly_prunable(self) -> None:
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
            before = self._tree_bytes(project)

            policy = analyze_asset_transaction_retention_policy(project)

            journal = next(item for item in policy["artifacts"] if item["kind"] == "journal")
            self.assertEqual(journal["transaction_id"], receipt["transaction_id"])
            self.assertEqual(journal["classification"], "terminal_applied")
            self.assertEqual(journal["disposition"], "retained")
            self.assertIn("terminal_receipt_retained", journal["reasons"])
            self.assertIn("explicit_prune_authorization_missing", journal["reasons"])
            self.assertEqual(policy["safe_prune_candidates"], [])
            self.assertEqual(before, self._tree_bytes(project))

    def test_recovery_required_and_malformed_evidence_is_protected(self) -> None:
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
            undo_asset_reference_mutation(project, receipt["transaction_id"])
            root = project / ".vitaloom" / "asset_transactions"
            journal = root / (receipt["transaction_id"] + ".json")
            data = json.loads(journal.read_text(encoding="utf-8"))
            data["state"] = "prepared"
            journal.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            (root / "broken.json").write_text("{not-json", encoding="utf-8")
            before = self._tree_bytes(project)

            policy = analyze_asset_transaction_retention_policy(project)

            protected = {item["path"]: item for item in policy["artifacts"] if item["disposition"] == "protected"}
            self.assertIn(".vitaloom/asset_transactions/" + receipt["transaction_id"] + ".json", protected)
            self.assertIn(".vitaloom/asset_transactions/broken.json", protected)
            self.assertIn("recovery_required", protected[".vitaloom/asset_transactions/" + receipt["transaction_id"] + ".json"]["reasons"])
            self.assertIn("malformed_or_unsupported_receipt", protected[".vitaloom/asset_transactions/broken.json"]["reasons"])
            self.assertEqual(before, self._tree_bytes(project))

    def test_private_backup_orphan_and_unknown_artifacts_are_never_safe_prune_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            (project / "assets" / "unused.bin").write_bytes(b"unused")
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(project, operation="delete", source_path="assets/unused.bin"),
            )
            root = project / ".vitaloom" / "asset_transactions"
            (root / "orphan.asset").write_bytes(b"orphan")
            (root / "foreign.tmp").write_bytes(b"foreign")
            before = self._tree_bytes(project)

            policy = analyze_asset_transaction_retention_policy(project)

            paths = [item["path"] for item in policy["artifacts"]]
            self.assertEqual(paths, sorted(paths))
            backup = next(item for item in policy["artifacts"] if item["path"].endswith(receipt["transaction_id"] + ".asset"))
            orphan = next(item for item in policy["artifacts"] if item["path"].endswith("orphan.asset"))
            foreign = next(item for item in policy["artifacts"] if item["path"].endswith("foreign.tmp"))
            self.assertEqual(backup["disposition"], "retained")
            self.assertIn("linked_terminal_journal", backup["reasons"])
            self.assertEqual(orphan["disposition"], "not_prunable")
            self.assertIn("orphan_private_backup", orphan["reasons"])
            self.assertEqual(foreign["disposition"], "not_prunable")
            self.assertIn("unknown_transaction_artifact", foreign["reasons"])
            self.assertEqual(policy["safe_prune_candidates"], [])
            self.assertEqual(before, self._tree_bytes(project))


if __name__ == "__main__":
    unittest.main()
