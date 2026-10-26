# -*- coding: utf-8
"""工程 manifest 校验单元测试。"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProjectManifestTests(unittest.TestCase):
    def test_collect_required_from_recommended_alias(self):
        from core.VitaLoom.project.project_manifest import collect_required_package_ids

        ids = collect_required_package_ids(
            {"recommended_packages": ["vitalloom.engine.sr2d"]}
        )
        self.assertIn("vitalloom.engine.sr2d", ids)
        self.assertIn("vitalloom.core.platform", ids)

    def test_capabilities_add_pvaec(self):
        from core.VitaLoom.project.project_manifest import collect_required_package_ids

        ids = collect_required_package_ids({"capabilities": ["pvaec", "sr2d"]})
        self.assertIn("vitalloom.pvaec.simulation", ids)
        self.assertIn("vitalloom.engine.sr2d", ids)

    def test_required_capabilities_are_required_packages(self):
        from core.VitaLoom.project.project_manifest import collect_required_package_ids

        ids = collect_required_package_ids(
            {"required_capabilities": {"vitalloom.engine.sr2d": ">=1.0.0"}}
        )
        self.assertIn("vitalloom.engine.sr2d", ids)

    def test_required_capability_version_constraint_mismatch_fails(self):
        from core.VitaLoom.project.project_manifest import validate_project_manifest

        pj = {"required_capabilities": {"vitalloom.engine.sr2d": ">=9.0.0"}}
        result = validate_project_manifest(pj, repo_root=ROOT, editor_version="1.0.0")
        self.assertIn("vitalloom.engine.sr2d", result.missing_packages)
        self.assertTrue(
            any(i.code == "capability_version_mismatch" for i in result.issues)
        )

    def test_tutorial_stack_without_pvaec_passes(self):
        from core.VitaLoom.project.project_manifest import validate_project_manifest

        pj = json.loads(
            (ROOT / "workspace" / "projects" / "samples" / "织机教程-迷你Roguelike" / "project.json").read_text(
                encoding="utf-8"
            )
        )
        result = validate_project_manifest(pj, repo_root=ROOT, editor_version="1.0.0")
        self.assertNotIn("vitalloom.pvaec.simulation", result.required_packages)
        self.assertFalse(
            any(
                i.code == "package_disabled"
                and "pvaec.simulation" in i.message
                for i in result.issues
            )
        )

    def test_pvaec_project_requires_pvaec_package(self):
        from core.VitaLoom.project.project_manifest import validate_project_manifest

        pj = json.loads(
            (ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化" / "project.json").read_text(
                encoding="utf-8"
            )
        )
        result = validate_project_manifest(pj, repo_root=ROOT, editor_version="1.0.0")
        self.assertIn("vitalloom.pvaec.simulation", result.required_packages)

    def test_disabled_plugin_disables_package(self):
        from core.VitaLoom.project.project_manifest import validate_project_manifest

        pj = {
            "required_packages": ["vitalloom.pvaec.simulation"],
            "disabled_plugins": [
                "PsExperimentPlugin",
                "EcologyDashboardPlugin",
                "SimulationControlPlugin",
            ],
        }
        result = validate_project_manifest(pj, repo_root=ROOT, editor_version="1.0.0")
        self.assertIn("vitalloom.pvaec.simulation", result.missing_packages)

    def test_version_mismatch_warning(self):
        from core.VitaLoom.project.project_manifest import validate_project_manifest

        pj = {"loom_editor_version": ">=9.0.0", "required_packages": []}
        result = validate_project_manifest(pj, repo_root=ROOT, editor_version="1.0.0")
        self.assertTrue(
            any(i.code == "editor_version_mismatch" for i in result.issues)
        )

    def test_version_constraint_invalid_clause_does_not_match(self):
        from core.VitaLoom.project.project_manifest import version_matches_constraint

        self.assertTrue(version_matches_constraint("1.0.0", "=1.0.0"))
        self.assertTrue(version_matches_constraint("1.5.0", ">=1.0.0,<2.0.0"))
        self.assertFalse(version_matches_constraint("1.5.0", ">=1.0.0,<bad"))
        self.assertFalse(version_matches_constraint("1.5.0", ">=bad"))

    def test_planned_package_fails(self):
        from core.VitaLoom.project.project_manifest import validate_project_manifest

        pj = {"required_packages": ["vitalloom.engine.3d"]}
        result = validate_project_manifest(pj, repo_root=ROOT, editor_version="1.0.0")
        self.assertIn("vitalloom.engine.3d", result.missing_packages)


if __name__ == "__main__":
    unittest.main()
