# -*- coding: utf-8 -*-
"""TDD coverage for Phase 7E referenced-asset retirement policy Authority."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.VitaLoom.project.asset_index import build_project_asset_index
from core.VitaLoom.project.asset_reference_transaction import analyze_asset_retirement_policy
from core.VitaLoom.project.asset_registry import (
    load_project_asset_registry,
    refresh_project_asset_registry,
)


class AssetRetirementPolicyTests(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        project = root / "project"
        (project / "assets").mkdir(parents=True)
        (project / "scripts").mkdir()
        (project / "scenes").mkdir()
        (project / "assets" / "hero.png").write_bytes(b"hero")
        (project / "assets" / "replacement.png").write_bytes(b"replacement")
        (project / "assets" / "unused.bin").write_bytes(b"unused")
        (project / "scripts" / "brain.py").write_text("print('brain')\n", encoding="utf-8")
        (project / "scripts" / "mind.py").write_text("print('mind')\n", encoding="utf-8")
        (project / "project.json").write_text(
            json.dumps({"name": "phase7e", "active_scene": "main.pond"}), encoding="utf-8"
        )
        (project / "project.lock.json").write_text("{}", encoding="utf-8")
        (project / "scenes" / "main.pond").write_text(
            json.dumps(
                {
                    "sprite_path": "../assets/hero.png",
                    "entities": [
                        {"icon_path": "assets/hero.png", "scripts": [{"name": "brain"}]},
                        {"sprite_path": "assets/hero.png"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        (project / "scenes" / "replacement.pond").write_text("{}", encoding="utf-8")
        return project

    @staticmethod
    def _tree_bytes(root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    def test_replacement_analysis_preserves_reference_style_and_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            before = self._tree_bytes(project)

            result = analyze_asset_retirement_policy(
                project,
                source_path="assets/hero.png",
                replacement_path="assets/replacement.png",
            )

            self.assertEqual(result["decision"], "replacement_candidate")
            self.assertTrue(result["ready_for_future_transaction"])
            self.assertEqual(result["source"]["path"], "assets/hero.png")
            self.assertEqual(result["replacement"]["path"], "assets/replacement.png")
            self.assertEqual(len(result["proposed_reference_edits"]), 3)
            self.assertEqual(
                {item["new_value"] for item in result["proposed_reference_edits"]},
                {"../assets/replacement.png", "assets/replacement.png"},
            )
            self.assertEqual(result["blocked_references"], [])
            self.assertEqual(before, self._tree_bytes(project))
            self.assertFalse((project / ".vitaloom").exists())

    def test_script_and_active_scene_candidates_use_existing_representability_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))

            script = analyze_asset_retirement_policy(
                project,
                source_path="scripts/brain.py",
                replacement_path="scripts/mind.py",
            )
            scene = analyze_asset_retirement_policy(
                project,
                source_path="scenes/main.pond",
                replacement_path="scenes/replacement.pond",
            )

            self.assertTrue(script["ready_for_future_transaction"])
            self.assertEqual(script["proposed_reference_edits"][0]["new_value"], "mind")
            self.assertTrue(scene["ready_for_future_transaction"])
            self.assertEqual(scene["proposed_reference_edits"][0]["new_value"], "replacement.pond")

    def test_referenced_removal_without_replacement_stays_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            before = self._tree_bytes(project)

            result = analyze_asset_retirement_policy(project, source_path="assets/hero.png")

            self.assertEqual(result["decision"], "refused")
            self.assertFalse(result["ready_for_future_transaction"])
            self.assertTrue(any(item["code"] == "removal_without_replacement_unproven" for item in result["blockers"]))
            self.assertEqual(len(result["live_references"]), 3)
            self.assertEqual(before, self._tree_bytes(project))

    def test_unreferenced_asset_reports_existing_delete_route_without_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            before = self._tree_bytes(project)

            result = analyze_asset_retirement_policy(project, source_path="assets/unused.bin")

            self.assertEqual(result["decision"], "unreferenced_delete_available")
            self.assertFalse(result["ready_for_future_transaction"])
            self.assertEqual(result["live_references"], [])
            self.assertEqual(before, self._tree_bytes(project))

    def test_invalid_replacement_and_nonrepresentable_script_target_are_explicit_refusals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))

            missing = analyze_asset_retirement_policy(
                project,
                source_path="assets/hero.png",
                replacement_path="assets/missing.png",
            )
            same = analyze_asset_retirement_policy(
                project,
                source_path="assets/hero.png",
                replacement_path="assets/hero.png",
            )
            wrong_script_target = analyze_asset_retirement_policy(
                project,
                source_path="scripts/brain.py",
                replacement_path="assets/replacement.png",
            )

            self.assertEqual(missing["decision"], "refused")
            self.assertTrue(any(item["code"] == "replacement_not_found" for item in missing["blockers"]))
            self.assertEqual(same["decision"], "refused")
            self.assertTrue(any(item["code"] == "replacement_same_as_source" for item in same["blockers"]))
            self.assertEqual(wrong_script_target["decision"], "refused")
            self.assertTrue(
                any(item["reason"] == "reference_style_not_representable" for item in wrong_script_target["blocked_references"])
            )

    def test_analysis_preserves_existing_index_registry_and_export_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            refresh_project_asset_registry(project)
            before_bytes = self._tree_bytes(project)
            before_index = build_project_asset_index(project)
            before_registry = load_project_asset_registry(project)

            result = analyze_asset_retirement_policy(
                project,
                source_path="assets/hero.png",
                replacement_path="assets/replacement.png",
            )

            self.assertEqual(result["decision"], "replacement_candidate")
            self.assertEqual(before_bytes, self._tree_bytes(project))
            self.assertEqual(before_index, build_project_asset_index(project))
            self.assertEqual(before_registry, load_project_asset_registry(project))
            self.assertFalse((project / ".vitaloom" / "asset_transactions").exists())


    def test_malformed_scene_is_an_explicit_policy_blocker_not_a_hidden_scan_omission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            (project / "scenes" / "broken.pond").write_text("{bad json", encoding="utf-8")

            result = analyze_asset_retirement_policy(
                project,
                source_path="assets/hero.png",
                replacement_path="assets/replacement.png",
            )

            self.assertEqual(result["decision"], "refused")
            self.assertTrue(any(item["code"] == "reference_owner_malformed" for item in result["blockers"]))
            self.assertEqual(result["malformed_owners"][0]["scene"], "scenes/broken.pond")


if __name__ == "__main__":
    unittest.main()
