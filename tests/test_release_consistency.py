# -*- coding: utf-8 -*-
"""Release metadata and repository contract regression tests."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseConsistencyTests(unittest.TestCase):
    def test_worldbridge_admission_ci_contract(self):
        from tools.check_release_consistency import _check_worldbridge_admission_ci_contract

        errors = []
        _check_worldbridge_admission_ci_contract(errors)
        self.assertEqual(errors, [])

    def test_check_release_consistency_script(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "check_release_consistency.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=proc.stdout + proc.stderr,
        )
        self.assertNotIn("Cosmos", proc.stdout + proc.stderr)

    def test_loom_constant_matches_pyproject(self):
        import re

        from core.VitaLoom.project.project_manifest import (
            LOOM_EDITOR_VERSION,
            get_loom_editor_version_from_pyproject,
        )

        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        m = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        self.assertTrue(m)
        pv = m.group(1).strip()
        self.assertEqual(LOOM_EDITOR_VERSION, pv)
        self.assertEqual(get_loom_editor_version_from_pyproject(ROOT), pv)

    def test_python_version_contract_matches_runtime_floor(self):
        from tools.check_release_consistency import _read_pyproject_requires_python

        self.assertEqual(_read_pyproject_requires_python(), ">=3.11")
        self.assertTrue((ROOT / ".python-version").read_text(encoding="utf-8").strip().startswith("3.11"))

    def test_suite_product_manifests_are_closed(self):
        from FrameCore.product_registry import load_product_registry
        from FrameCore.suite_registry import load_suite_manifest

        suite_root = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom"
        suite = load_suite_manifest(suite_root)
        registry = load_product_registry(suite_root)
        self.assertTrue((suite_root / suite.capability_catalog).is_file())
        for product_id in suite.products:
            self.assertIn(product_id, registry.products)
        for product_id, product in registry.products.items():
            self.assertIn(product.default_version, product.versions)
            for version in product.versions:
                pv = registry.get_version(product_id, version)
                self.assertIsNotNone(pv)
                self.assertEqual([], pv.missing_physical_roots())
                for command in pv.entrypoints.values():
                    self.assertTrue((pv.version_root / command.split(" ", 1)[0]).exists())
                self.assertTrue((pv.version_root / pv.builtin_capability_index).is_file())

    def test_no_forbidden_repository_references(self):
        from tools.check_release_consistency import (
            _check_forbidden_repository_references,
        )

        errors: list[str] = []
        _check_forbidden_repository_references(errors)
        self.assertEqual(errors, [])

    def test_no_tracked_local_history_snapshots(self):
        from tools.check_release_consistency import _check_no_tracked_local_history

        errors: list[str] = []
        _check_no_tracked_local_history(errors)
        self.assertEqual(errors, [])

    def test_plugin_layout_has_no_flat_legacy_dirs(self):
        from tools.check_release_consistency import _check_plugin_layout

        errors: list[str] = []
        _check_plugin_layout(errors)
        self.assertEqual(errors, [])

    def test_catalog_plugin_ids_are_discoverable_classes(self):
        import json

        from tools.check_release_consistency import _discover_plugin_class_names

        catalog = (
            ROOT
            / "FrameCore"
            / "plugins"
            / "lotucosm-vitaloom"
            / "versions"
            / "1.0.0"
            / "runtime"
            / "builtin"
            / "package_index.json"
        )
        data = json.loads(catalog.read_text(encoding="utf-8"))
        plugin_ids = {
            str(plugin_id)
            for pkg in data.get("packages", [])
            if isinstance(pkg, dict) and str(pkg.get("status", "")).lower() != "planned"
            for plugin_id in pkg.get("plugins", [])
        }
        self.assertLessEqual(plugin_ids, _discover_plugin_class_names())

    def test_project_layout_has_no_flat_legacy_dirs(self):
        from tools.check_release_consistency import _check_project_layout

        errors: list[str] = []
        _check_project_layout(errors)
        self.assertEqual(errors, [])
        self.assertFalse(
            list((ROOT / "workspace" / "projects" / "samples").glob("*/dist")),
            "sample projects must not contain generated Player export dist directories",
        )

    def test_sr2d_native_release_contract(self):
        from tools.check_release_consistency import (
            _check_sr2d_native_release_contract,
        )

        errors: list[str] = []
        _check_sr2d_native_release_contract(errors)
        self.assertEqual(errors, [])
    def test_ci_compileall_matches_release_surface(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "python -m compileall -q FrameCore workspace tools main.py player.py",
            workflow,
        )

    def test_ci_covers_minimum_and_current_python_versions(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn('python-version: ["3.11", "3.12"]', workflow)


if __name__ == "__main__":
    unittest.main()
