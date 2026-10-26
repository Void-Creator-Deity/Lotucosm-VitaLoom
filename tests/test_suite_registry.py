# -*- coding: utf-8 -*-
"""Suite manifest、产品版本与 project.lock 解析。"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom"


class SuiteRegistryTests(unittest.TestCase):
    def test_load_suite_manifest(self) -> None:
        from FrameCore.suite_registry import load_suite_manifest

        suite = load_suite_manifest(SUITE_ROOT)
        self.assertEqual(suite.suite_id, "lotucosm.vitaloom.suite")
        self.assertIn("lotucosm-vitaloom", suite.products)

    def test_product_registry_lists_default_version(self) -> None:
        from FrameCore.product_registry import load_product_registry

        registry = load_product_registry(SUITE_ROOT)
        default = registry.get_default_version("lotucosm-vitaloom")
        self.assertIsNotNone(default)
        self.assertEqual(default.version, "1.0.0")
        self.assertIn("runtime/core/Lotucosm", default.physical_roots)

    def test_product_version_selects_highest_matching_range(self) -> None:
        from FrameCore.product_registry import (
            ProductManifest,
            ProductRegistry,
            ProductVersion,
        )
        from core.VitaLoom.suite.product_version import select_product_version

        registry = ProductRegistry(
            suite_root=SUITE_ROOT,
            products={
                "lotucosm-vitaloom": ProductManifest(
                    product_id="lotucosm-vitaloom",
                    default_version="1.0.0",
                    versions=("1.0.0", "1.2.0", "2.0.0"),
                )
            },
            versions={
                ("lotucosm-vitaloom", "1.0.0"): ProductVersion(
                    product_id="lotucosm-vitaloom", version="1.0.0"
                ),
                ("lotucosm-vitaloom", "1.2.0"): ProductVersion(
                    product_id="lotucosm-vitaloom", version="1.2.0"
                ),
                ("lotucosm-vitaloom", "2.0.0"): ProductVersion(
                    product_id="lotucosm-vitaloom", version="2.0.0"
                ),
            },
        )
        selected = select_product_version(
            registry,
            "lotucosm-vitaloom",
            ">=1.0.0,<2.0.0",
        )
        self.assertIsNotNone(selected)
        self.assertEqual(selected.version, "1.2.0")
        self.assertIsNone(
            select_product_version(registry, "lotucosm-vitaloom", ">=bad")
        )

    def test_project_lock_resolves_without_writing(self) -> None:
        from core.VitaLoom.suite.project_lock import (
            build_project_lock,
            load_project_lock,
            resolve_project_runtime,
        )

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.json").write_text(
                json.dumps(
                    {
                        "name": "temp",
                        "loom_editor_version": ">=1.0.0,<2.0.0",
                        "required_capabilities": {
                            "vitalloom.engine.sr2d": ">=1.0.0"
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            self.assertIsNone(load_project_lock(project))
            lock = build_project_lock(
                json.loads((project / "project.json").read_text(encoding="utf-8")),
                repo_root=ROOT,
            )
            self.assertEqual(lock["resolved_product"]["id"], "lotucosm-vitaloom")
            self.assertEqual(lock["resolved_product"]["version"], "1.0.0")
            self.assertIn("vitalloom.engine.sr2d", lock["resolved_capabilities"])
            resolved = resolve_project_runtime(project, repo_root=ROOT)
            self.assertTrue(resolved.lock_missing)
            self.assertEqual(resolved.lock_status_text, "未锁定")

    def test_sample_projects_have_resolved_locks(self) -> None:
        from core.VitaLoom.suite.project_lock import resolve_project_runtime

        pvaec = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
        tutorial = ROOT / "workspace" / "projects" / "samples" / "织机教程-迷你Roguelike"
        for project in (pvaec, tutorial):
            self.assertTrue((project / "project.lock.json").is_file(), project)
            resolved = resolve_project_runtime(project, repo_root=ROOT)
            self.assertFalse(resolved.lock_missing)
            self.assertFalse(resolved.product_version_missing)
            self.assertEqual(resolved.product_id, "lotucosm-vitaloom")
            self.assertEqual(resolved.product_version, "1.0.0")

        pvaec_resolved = resolve_project_runtime(pvaec, repo_root=ROOT)
        self.assertIn("vitalloom.pvaec.simulation", pvaec_resolved.resolved_capabilities)
        tutorial_resolved = resolve_project_runtime(tutorial, repo_root=ROOT)
        self.assertNotIn(
            "vitalloom.pvaec.simulation",
            tutorial_resolved.resolved_capabilities,
        )

    def test_incomplete_project_lock_reports_missing_capability(self) -> None:
        from core.VitaLoom.suite.project_lock import resolve_project_runtime

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.json").write_text(
                json.dumps(
                    {
                        "name": "missing-cap",
                        "loom_editor_version": "1.0.0",
                        "required_capabilities": {
                            "vitalloom.engine.sr2d": ">=1.0.0"
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (project / "project.lock.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "resolved_suite": {
                            "id": "lotucosm.vitaloom.suite",
                            "version": "1.0.0",
                        },
                        "resolved_product": {
                            "id": "lotucosm-vitaloom",
                            "version": "1.0.0",
                        },
                        "resolved_capabilities": {},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            resolved = resolve_project_runtime(project, repo_root=ROOT)
            self.assertIn("vitalloom.engine.sr2d", resolved.missing_capabilities)
            self.assertEqual(resolved.lock_status_text, "能力缺失")

    def test_stale_project_lock_reports_capability_version_mismatch(self) -> None:
        from core.VitaLoom.suite.project_lock import (
            build_project_lock,
            resolve_project_runtime,
        )

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            project_data = {
                "name": "stale-cap",
                "loom_editor_version": "1.0.0",
                "required_capabilities": {"vitalloom.engine.sr2d": ">=1.0.0"},
            }
            (project / "project.json").write_text(
                json.dumps(project_data, ensure_ascii=False),
                encoding="utf-8",
            )
            lock = build_project_lock(project_data, repo_root=ROOT)
            lock["resolved_capabilities"]["vitalloom.engine.sr2d"] = "0.9.0"
            (project / "project.lock.json").write_text(
                json.dumps(lock, ensure_ascii=False),
                encoding="utf-8",
            )
            resolved = resolve_project_runtime(project, repo_root=ROOT)
            self.assertIn(
                "vitalloom.engine.sr2d",
                resolved.capability_version_mismatches,
            )
            self.assertEqual(resolved.lock_status_text, "能力版本不符")

    def test_project_lock_reports_unsatisfied_capability_constraint(self) -> None:
        from core.VitaLoom.suite.project_lock import resolve_project_runtime

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.json").write_text(
                json.dumps(
                    {
                        "name": "future-cap",
                        "loom_editor_version": "1.0.0",
                        "required_capabilities": {
                            "vitalloom.engine.sr2d": ">=9.0.0"
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            resolved = resolve_project_runtime(project, repo_root=ROOT)
            self.assertIn(
                "vitalloom.engine.sr2d",
                resolved.capability_constraint_mismatches,
            )
            self.assertTrue(resolved.has_blocking_issues)
            self.assertEqual(resolved.lock_status_text, "能力约束不符")


if __name__ == "__main__":
    unittest.main()
