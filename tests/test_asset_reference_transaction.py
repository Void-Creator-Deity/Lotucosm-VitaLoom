# -*- coding: utf-8 -*-
"""TDD coverage for Phase 7C asset-reference transaction Authority."""
from __future__ import annotations

import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from core.VitaLoom.project.asset_reference_transaction import (
    AssetReferenceTransactionError,
    apply_asset_reference_mutation,
    plan_asset_reference_mutation,
    redo_asset_reference_mutation,
    undo_asset_reference_mutation,
)
from core.VitaLoom.project.asset_registry import refresh_project_asset_registry


class AssetReferenceTransactionTests(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        project = root / "project"
        (project / "assets" / "sprites").mkdir(parents=True)
        (project / "scripts").mkdir(parents=True)
        (project / "scenes").mkdir(parents=True)
        (project / "assets" / "sprites" / "hero.png").write_bytes(b"hero")
        (project / "assets" / "sprites" / "unused.bin").write_bytes(b"unused")
        (project / "assets" / "sprites" / "replacement.png").write_bytes(b"replacement")
        (project / "scripts" / "brain.py").write_text("print('brain')\n", encoding="utf-8")
        (project / "project.json").write_text(
            json.dumps({"name": "phase7c", "active_scene": "main.pond"}), encoding="utf-8"
        )
        (project / "project.lock.json").write_text("{}", encoding="utf-8")
        (project / "scenes" / "main.pond").write_text(
            json.dumps(
                {
                    "sprite_path": "../assets/sprites/hero.png",
                    "entities": [
                        {"icon_path": "assets/sprites/hero.png", "scripts": [{"name": "brain"}]},
                        {"sprite_path": "assets/sprites/hero.png"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        return project

    @staticmethod
    def _id_for(snapshot: dict, path: str) -> str:
        return next(row["asset_id"] for row in snapshot["asset_projection"] if row["path"] == path)

    def test_rename_plan_uses_structured_locations_and_preserves_reference_style(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            plan = plan_asset_reference_mutation(
                project,
                operation="rename",
                source_path="assets/sprites/hero.png",
                target_path="assets/sprites/renamed-hero.png",
            )
            self.assertTrue(plan["ready"])
            self.assertEqual(plan["operation"], "rename")
            self.assertEqual(len(plan["reference_edits"]), 3)
            self.assertTrue(all(isinstance(edit["location_tokens"], list) for edit in plan["reference_edits"]))
            self.assertEqual(
                {edit["new_value"] for edit in plan["reference_edits"]},
                {"../assets/sprites/renamed-hero.png", "assets/sprites/renamed-hero.png"},
            )
            self.assertTrue(all(edit["json_pointer"].startswith("$") for edit in plan["reference_edits"]))

    def test_referenced_replacement_retires_source_and_restores_it_on_undo_redo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            before = refresh_project_asset_registry(project)
            source_id = self._id_for(before, "assets/sprites/hero.png")
            replacement_id = self._id_for(before, "assets/sprites/replacement.png")
            replacement = project / "assets" / "sprites" / "replacement.png"
            replacement_before = replacement.read_bytes()

            plan = plan_asset_reference_mutation(
                project,
                operation="replace_referenced",
                source_path="assets/sprites/hero.png",
                target_path="assets/sprites/replacement.png",
            )
            self.assertTrue(plan["ready"])
            self.assertEqual(plan["operation"], "replace_referenced")
            self.assertEqual(len(plan["reference_edits"]), 3)

            receipt = apply_asset_reference_mutation(project, plan)
            self.assertEqual(receipt["state"], "applied")
            self.assertEqual(receipt["asset_id"], source_id)
            self.assertFalse((project / "assets" / "sprites" / "hero.png").exists())
            self.assertEqual(replacement.read_bytes(), replacement_before)
            main = json.loads((project / "scenes" / "main.pond").read_text(encoding="utf-8"))
            self.assertEqual(main["sprite_path"], "../assets/sprites/replacement.png")
            self.assertEqual(main["entities"][0]["icon_path"], "assets/sprites/replacement.png")
            applied_registry = refresh_project_asset_registry(project)
            self.assertTrue(any(row["asset_id"] == source_id for row in applied_registry["tombstones"]))
            self.assertEqual(replacement_id, self._id_for(applied_registry, "assets/sprites/replacement.png"))

            undone = undo_asset_reference_mutation(project, receipt["transaction_id"])
            self.assertEqual(undone["state"], "undone")
            self.assertTrue((project / "assets" / "sprites" / "hero.png").is_file())
            self.assertEqual(replacement.read_bytes(), replacement_before)
            undone_main = json.loads((project / "scenes" / "main.pond").read_text(encoding="utf-8"))
            self.assertEqual(undone_main["sprite_path"], "../assets/sprites/hero.png")
            restored_registry = refresh_project_asset_registry(project)
            self.assertEqual(source_id, self._id_for(restored_registry, "assets/sprites/hero.png"))
            self.assertEqual(replacement_id, self._id_for(restored_registry, "assets/sprites/replacement.png"))

            redone = redo_asset_reference_mutation(project, receipt["transaction_id"])
            self.assertEqual(redone["state"], "applied")
            self.assertFalse((project / "assets" / "sprites" / "hero.png").exists())
            self.assertEqual(replacement.read_bytes(), replacement_before)
            self.assertEqual(
                replacement_id,
                self._id_for(refresh_project_asset_registry(project), "assets/sprites/replacement.png"),
            )


    def test_rename_apply_and_guarded_undo_redo_preserve_registry_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            before = refresh_project_asset_registry(project)
            asset_id = self._id_for(before, "assets/sprites/hero.png")
            plan = plan_asset_reference_mutation(
                project,
                operation="rename",
                source_path="assets/sprites/hero.png",
                target_path="assets/sprites/renamed-hero.png",
            )
            receipt = apply_asset_reference_mutation(project, plan)
            self.assertEqual(receipt["state"], "applied")
            self.assertEqual(receipt["asset_id"], asset_id)
            self.assertFalse((project / "assets" / "sprites" / "hero.png").exists())
            self.assertTrue((project / "assets" / "sprites" / "renamed-hero.png").is_file())
            main = json.loads((project / "scenes" / "main.pond").read_text(encoding="utf-8"))
            self.assertEqual(main["sprite_path"], "../assets/sprites/renamed-hero.png")
            self.assertEqual(main["entities"][0]["icon_path"], "assets/sprites/renamed-hero.png")
            after = refresh_project_asset_registry(project)
            self.assertEqual(asset_id, self._id_for(after, "assets/sprites/renamed-hero.png"))

            undone = undo_asset_reference_mutation(project, receipt["transaction_id"])
            self.assertEqual(undone["state"], "undone")
            self.assertTrue((project / "assets" / "sprites" / "hero.png").is_file())
            self.assertEqual(asset_id, self._id_for(refresh_project_asset_registry(project), "assets/sprites/hero.png"))

            redone = redo_asset_reference_mutation(project, receipt["transaction_id"])
            self.assertEqual(redone["state"], "applied")
            self.assertEqual(asset_id, self._id_for(refresh_project_asset_registry(project), "assets/sprites/renamed-hero.png"))

    def test_referenced_delete_is_blocked_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            plan = plan_asset_reference_mutation(
                project,
                operation="delete",
                source_path="assets/sprites/hero.png",
            )
            self.assertFalse(plan["ready"])
            self.assertEqual(len(plan["blocked_references"]), 3)
            with self.assertRaises(AssetReferenceTransactionError) as captured:
                apply_asset_reference_mutation(project, plan)
            self.assertEqual(captured.exception.code, "asset_references_blocking")
            self.assertTrue((project / "assets" / "sprites" / "hero.png").is_file())

    def test_unreferenced_delete_undo_redo_restores_tombstoned_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            before = refresh_project_asset_registry(project)
            asset_id = self._id_for(before, "assets/sprites/unused.bin")
            plan = plan_asset_reference_mutation(
                project,
                operation="delete",
                source_path="assets/sprites/unused.bin",
            )
            self.assertTrue(plan["ready"])
            receipt = apply_asset_reference_mutation(project, plan)
            self.assertFalse((project / "assets" / "sprites" / "unused.bin").exists())
            self.assertIn(asset_id, {row["asset_id"] for row in receipt["registry"]["tombstones"]})
            from core.VitaLoom.project.asset_index import build_project_asset_index

            index = build_project_asset_index(project)
            self.assertFalse(any(path.startswith(".vitaloom/asset_transactions/") for path in index["export"]["files"]))
            self.assertFalse(any(row["path"].startswith(".vitaloom/asset_transactions/") for row in index["inventory"]))
            undone = undo_asset_reference_mutation(project, receipt["transaction_id"])
            self.assertEqual(undone["state"], "undone")
            restored = refresh_project_asset_registry(project)
            self.assertEqual(asset_id, self._id_for(restored, "assets/sprites/unused.bin"))
            redone = redo_asset_reference_mutation(project, receipt["transaction_id"])
            self.assertEqual(redone["state"], "applied")
            self.assertIn(asset_id, {row["asset_id"] for row in redone["registry"]["tombstones"]})

    def test_undo_refuses_to_overwrite_a_scene_changed_after_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            plan = plan_asset_reference_mutation(
                project,
                operation="rename",
                source_path="assets/sprites/hero.png",
                target_path="assets/sprites/renamed-hero.png",
            )
            receipt = apply_asset_reference_mutation(project, plan)
            scene = project / "scenes" / "main.pond"
            scene.write_text(json.dumps({"sprite_path": "assets/other.png"}), encoding="utf-8")
            with self.assertRaises(AssetReferenceTransactionError) as captured:
                undo_asset_reference_mutation(project, receipt["transaction_id"])
            self.assertEqual(captured.exception.code, "asset_transaction_conflict")
            self.assertTrue((project / "assets" / "sprites" / "renamed-hero.png").is_file())


    def test_scene_rename_updates_project_active_scene_and_export_truth(self) -> None:
        from core.VitaLoom.project.asset_index import build_project_asset_index

        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            plan = plan_asset_reference_mutation(
                project,
                operation="rename",
                source_path="scenes/main.pond",
                target_path="scenes/renamed.pond",
            )
            self.assertTrue(plan["ready"])
            self.assertEqual(len(plan["reference_edits"]), 1)
            self.assertEqual(plan["reference_edits"][0]["kind"], "active_scene")
            apply_asset_reference_mutation(project, plan)
            self.assertEqual(json.loads((project / "project.json").read_text(encoding="utf-8"))["active_scene"], "renamed.pond")
            self.assertTrue((project / "scenes" / "renamed.pond").is_file())
            self.assertTrue(build_project_asset_index(project)["export"]["ready"])

    def test_script_shorthand_rename_rewrites_only_representable_script_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            plan = plan_asset_reference_mutation(
                project,
                operation="rename",
                source_path="scripts/brain.py",
                target_path="scripts/mind.py",
            )
            self.assertTrue(plan["ready"])
            self.assertEqual(plan["reference_edits"][0]["new_value"], "mind")
            apply_asset_reference_mutation(project, plan)
            scene = json.loads((project / "scenes" / "main.pond").read_text(encoding="utf-8"))
            self.assertEqual(scene["entities"][0]["scripts"][0]["name"], "mind")

            blocked = plan_asset_reference_mutation(
                project,
                operation="rename",
                source_path="scripts/mind.py",
                target_path="assets/mind.py",
            )
            self.assertFalse(blocked["ready"])
            self.assertEqual(blocked["blocked_references"][0]["reason"], "reference_style_not_representable")


    def test_rename_apply_failure_compensates_files_and_marks_recovery_required(self) -> None:
        from core.VitaLoom.project import asset_reference_transaction as transactions

        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            before = refresh_project_asset_registry(project)
            asset_id = self._id_for(before, "assets/sprites/hero.png")
            scene = project / "scenes" / "main.pond"
            scene_before = scene.read_bytes()
            plan = plan_asset_reference_mutation(
                project,
                operation="rename",
                source_path="assets/sprites/hero.png",
                target_path="assets/sprites/renamed-hero.png",
            )
            original_write = transactions._write_atomic
            failed = False

            def fail_scene_write(path: Path, value: bytes) -> None:
                nonlocal failed
                if Path(path).resolve() == scene.resolve() and not failed:
                    failed = True
                    raise OSError("injected scene write failure")
                original_write(path, value)

            with patch.object(transactions, "_write_atomic", side_effect=fail_scene_write):
                with self.assertRaises(AssetReferenceTransactionError) as captured:
                    apply_asset_reference_mutation(project, plan)
            self.assertEqual(captured.exception.code, "asset_transaction_apply_failed")
            self.assertTrue(failed)
            self.assertTrue((project / "assets" / "sprites" / "hero.png").is_file())
            self.assertFalse((project / "assets" / "sprites" / "renamed-hero.png").exists())
            self.assertEqual(scene.read_bytes(), scene_before)
            self.assertEqual(asset_id, self._id_for(refresh_project_asset_registry(project), "assets/sprites/hero.png"))
            recovery = transactions.recover_asset_reference_mutations(project)
            self.assertTrue(recovery["recovery_required"])
            self.assertEqual(len(recovery["pending_journals"]), 1)

    def test_delete_apply_failure_restores_asset_and_persistent_identity(self) -> None:
        from core.VitaLoom.project import asset_reference_transaction as transactions

        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            before = refresh_project_asset_registry(project)
            asset_id = self._id_for(before, "assets/sprites/unused.bin")
            plan = plan_asset_reference_mutation(
                project,
                operation="delete",
                source_path="assets/sprites/unused.bin",
            )
            original_refresh = transactions.refresh_project_asset_registry
            calls = 0

            def fail_delete_refresh(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected registry refresh failure")
                return original_refresh(*args, **kwargs)

            with patch.object(transactions, "refresh_project_asset_registry", side_effect=fail_delete_refresh):
                with self.assertRaises(AssetReferenceTransactionError) as captured:
                    apply_asset_reference_mutation(project, plan)
            self.assertEqual(captured.exception.code, "asset_transaction_apply_failed")
            self.assertTrue((project / "assets" / "sprites" / "unused.bin").is_file())
            self.assertEqual(asset_id, self._id_for(refresh_project_asset_registry(project), "assets/sprites/unused.bin"))

    def test_undo_rename_refuses_to_overwrite_recreated_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(
                    project,
                    operation="rename",
                    source_path="assets/sprites/hero.png",
                    target_path="assets/sprites/renamed-hero.png",
                ),
            )
            source = project / "assets" / "sprites" / "hero.png"
            source.write_bytes(b"user-created")
            with self.assertRaises(AssetReferenceTransactionError) as captured:
                undo_asset_reference_mutation(project, receipt["transaction_id"])
            self.assertEqual(captured.exception.code, "asset_transaction_conflict")
            self.assertEqual(source.read_bytes(), b"user-created")
            self.assertTrue((project / "assets" / "sprites" / "renamed-hero.png").is_file())

    def test_redo_rename_refuses_to_overwrite_recreated_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(
                    project,
                    operation="rename",
                    source_path="assets/sprites/hero.png",
                    target_path="assets/sprites/renamed-hero.png",
                ),
            )
            undo_asset_reference_mutation(project, receipt["transaction_id"])
            target = project / "assets" / "sprites" / "renamed-hero.png"
            target.write_bytes(b"user-created")
            with self.assertRaises(AssetReferenceTransactionError) as captured:
                redo_asset_reference_mutation(project, receipt["transaction_id"])
            self.assertEqual(captured.exception.code, "asset_transaction_conflict")
            self.assertEqual(target.read_bytes(), b"user-created")
            self.assertTrue((project / "assets" / "sprites" / "hero.png").is_file())


    def test_referenced_replacement_rechecks_new_live_references_before_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            plan = plan_asset_reference_mutation(
                project,
                operation="replace_referenced",
                source_path="assets/sprites/hero.png",
                target_path="assets/sprites/replacement.png",
            )
            late_owner = project / "scenes" / "late.pond"
            late_owner.write_text(json.dumps({"sprite_path": "assets/sprites/hero.png"}), encoding="utf-8")

            with self.assertRaises(AssetReferenceTransactionError) as captured:
                apply_asset_reference_mutation(project, plan)

            self.assertEqual(captured.exception.code, "asset_transaction_conflict")
            self.assertTrue((project / "assets" / "sprites" / "hero.png").is_file())
            self.assertEqual(json.loads(late_owner.read_text(encoding="utf-8"))["sprite_path"], "assets/sprites/hero.png")

    def test_referenced_replacement_refuses_malformed_scene_before_planning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            (project / "scenes" / "broken.pond").write_text("{not json", encoding="utf-8")
            with self.assertRaises(AssetReferenceTransactionError) as captured:
                plan_asset_reference_mutation(
                    project,
                    operation="replace_referenced",
                    source_path="assets/sprites/hero.png",
                    target_path="assets/sprites/replacement.png",
                )
            self.assertEqual(captured.exception.code, "asset_reference_owner_malformed")
            self.assertTrue((project / "assets" / "sprites" / "hero.png").is_file())


    def test_referenced_replacement_refuses_changed_target_before_apply_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            source = project / "assets" / "sprites" / "hero.png"
            replacement = project / "assets" / "sprites" / "replacement.png"
            scene = project / "scenes" / "main.pond"
            plan = plan_asset_reference_mutation(
                project,
                operation="replace_referenced",
                source_path="assets/sprites/hero.png",
                target_path="assets/sprites/replacement.png",
            )
            source_before = source.read_bytes()
            scene_before = scene.read_bytes()
            replacement.write_bytes(b"user-modified-replacement")

            with self.assertRaises(AssetReferenceTransactionError) as captured:
                apply_asset_reference_mutation(project, plan)

            self.assertEqual(captured.exception.code, "asset_transaction_conflict")
            self.assertEqual(source.read_bytes(), source_before)
            self.assertEqual(scene.read_bytes(), scene_before)
            self.assertEqual(replacement.read_bytes(), b"user-modified-replacement")

    def test_referenced_replacement_undo_and_redo_refuse_changed_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            replacement = project / "assets" / "sprites" / "replacement.png"
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(
                    project,
                    operation="replace_referenced",
                    source_path="assets/sprites/hero.png",
                    target_path="assets/sprites/replacement.png",
                ),
            )
            replacement.write_bytes(b"user-modified-after-apply")
            with self.assertRaises(AssetReferenceTransactionError) as captured:
                undo_asset_reference_mutation(project, receipt["transaction_id"])
            self.assertEqual(captured.exception.code, "asset_transaction_conflict")
            self.assertFalse((project / "assets" / "sprites" / "hero.png").exists())
            self.assertEqual(replacement.read_bytes(), b"user-modified-after-apply")

            replacement.write_bytes(b"replacement")
            undo_asset_reference_mutation(project, receipt["transaction_id"])
            replacement.write_bytes(b"user-modified-after-undo")
            with self.assertRaises(AssetReferenceTransactionError) as captured:
                redo_asset_reference_mutation(project, receipt["transaction_id"])
            self.assertEqual(captured.exception.code, "asset_transaction_conflict")
            self.assertTrue((project / "assets" / "sprites" / "hero.png").is_file())
            self.assertEqual(replacement.read_bytes(), b"user-modified-after-undo")

    def test_referenced_replacement_refuses_changed_private_backup_on_undo_and_redo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(
                    project,
                    operation="replace_referenced",
                    source_path="assets/sprites/hero.png",
                    target_path="assets/sprites/replacement.png",
                ),
            )
            backup = project / ".vitaloom" / "asset_transactions" / f"{receipt['transaction_id']}.asset"
            backup.write_bytes(b"user-modified-backup")
            with self.assertRaises(AssetReferenceTransactionError) as captured:
                undo_asset_reference_mutation(project, receipt["transaction_id"])
            self.assertEqual(captured.exception.code, "asset_transaction_backup_missing")
            self.assertFalse((project / "assets" / "sprites" / "hero.png").exists())

        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            receipt = apply_asset_reference_mutation(
                project,
                plan_asset_reference_mutation(
                    project,
                    operation="replace_referenced",
                    source_path="assets/sprites/hero.png",
                    target_path="assets/sprites/replacement.png",
                ),
            )
            undo_asset_reference_mutation(project, receipt["transaction_id"])
            backup = project / ".vitaloom" / "asset_transactions" / f"{receipt['transaction_id']}.asset"
            backup.write_bytes(b"user-modified-backup")
            with self.assertRaises(AssetReferenceTransactionError) as captured:
                redo_asset_reference_mutation(project, receipt["transaction_id"])
            self.assertEqual(captured.exception.code, "asset_transaction_backup_changed")
            self.assertTrue((project / "assets" / "sprites" / "hero.png").is_file())


    def test_referenced_replacement_rejects_same_protected_or_non_file_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            cases = [
                ("assets/sprites/hero.png", "asset_replacement_same_as_source"),
                ("project.json", "asset_path_protected"),
                ("assets/sprites", "asset_not_found"),
            ]
            for target_path, expected_code in cases:
                with self.subTest(target_path=target_path), self.assertRaises(AssetReferenceTransactionError) as captured:
                    plan_asset_reference_mutation(
                        project,
                        operation="replace_referenced",
                        source_path="assets/sprites/hero.png",
                        target_path=target_path,
                    )
                self.assertEqual(captured.exception.code, expected_code)

    def test_referenced_replacement_keeps_unrepresentable_script_shorthand_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            plan = plan_asset_reference_mutation(
                project,
                operation="replace_referenced",
                source_path="scripts/brain.py",
                target_path="assets/sprites/replacement.png",
            )
            self.assertFalse(plan["ready"])
            self.assertEqual(plan["blocked_references"][0]["reason"], "reference_style_not_representable")
            with self.assertRaises(AssetReferenceTransactionError) as captured:
                apply_asset_reference_mutation(project, plan)
            self.assertEqual(captured.exception.code, "asset_references_blocking")
            self.assertTrue((project / "scripts" / "brain.py").is_file())

    def test_referenced_replacement_apply_failure_compensates_source_owners_and_registry(self) -> None:
        from core.VitaLoom.project import asset_reference_transaction as transactions

        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            before = refresh_project_asset_registry(project)
            source_id = self._id_for(before, "assets/sprites/hero.png")
            source = project / "assets" / "sprites" / "hero.png"
            replacement = project / "assets" / "sprites" / "replacement.png"
            scene = project / "scenes" / "main.pond"
            source_before = source.read_bytes()
            replacement_before = replacement.read_bytes()
            scene_before = scene.read_bytes()
            plan = plan_asset_reference_mutation(
                project,
                operation="replace_referenced",
                source_path="assets/sprites/hero.png",
                target_path="assets/sprites/replacement.png",
            )
            original_refresh = transactions.refresh_project_asset_registry
            calls = 0

            def fail_apply_refresh(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected replacement registry failure")
                return original_refresh(*args, **kwargs)

            with patch.object(transactions, "refresh_project_asset_registry", side_effect=fail_apply_refresh):
                with self.assertRaises(AssetReferenceTransactionError) as captured:
                    apply_asset_reference_mutation(project, plan)

            self.assertEqual(captured.exception.code, "asset_transaction_apply_failed")
            self.assertEqual(source.read_bytes(), source_before)
            self.assertEqual(replacement.read_bytes(), replacement_before)
            self.assertEqual(scene.read_bytes(), scene_before)
            self.assertEqual(source_id, self._id_for(refresh_project_asset_registry(project), "assets/sprites/hero.png"))


if __name__ == "__main__":
    unittest.main()
