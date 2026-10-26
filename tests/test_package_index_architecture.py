# -*- coding: utf-8 -*-
"""官方 package_index 架构契约：核心包 + 扩展包依赖链。"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = (
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


class TestPackageIndexArchitecture(unittest.TestCase):
    def setUp(self) -> None:
        with open(CATALOG, "r", encoding="utf-8") as f:
            self.index = json.load(f)

    def test_schema_and_required_core(self) -> None:
        self.assertGreaterEqual(int(self.index.get("schema_version", 0)), 2)
        pkgs = {p["id"]: p for p in self.index.get("packages", [])}
        core = pkgs.get("vitalloom.core.platform")
        self.assertIsNotNone(core)
        assert core is not None
        self.assertEqual(core.get("status"), "required")
        self.assertIn("core/Lotucosm", core.get("physical_roots", []))

    def test_sr_demo_dependency_chain(self) -> None:
        pkgs = {p["id"]: p for p in self.index.get("packages", [])}
        chain = [
            "vitalloom.core.platform",
            "vitalloom.editor_essentials",
            "vitalloom.lotuspond.runtime",
            "vitalloom.pvaec.simulation",
            "vitalloom.engine.sr2d",
        ]
        for pid in chain:
            self.assertIn(pid, pkgs, f"missing package {pid}")
        sr2d = pkgs["vitalloom.engine.sr2d"]
        deps = " ".join(sr2d.get("dependencies", []))
        self.assertIn("vitalloom.lotuspond.runtime", deps)
        provides = " ".join(sr2d.get("provides", []))
        self.assertIn("sr.physics2d", provides)

    def test_engine_3d_is_planned_only(self) -> None:
        pkgs = {p["id"]: p for p in self.index.get("packages", [])}
        p3d = pkgs.get("vitalloom.engine.3d")
        self.assertIsNotNone(p3d)
        assert p3d is not None
        self.assertEqual(p3d.get("status"), "planned")
        self.assertEqual(p3d.get("plugins"), [])

    def test_packages_declare_project_plugin_contributions(self) -> None:
        for pkg in self.index.get("packages", []):
            with self.subTest(pkg=pkg.get("id")):
                self.assertIn("commands", pkg)
                self.assertIsInstance(pkg["commands"], list)
                self.assertIn("resources", pkg)
                self.assertIsInstance(pkg["resources"], list)
                self.assertIn("export_entries", pkg)
                self.assertIsInstance(pkg["export_entries"], list)
                if pkg.get("plugins") and not pkg["commands"]:
                    self.assertIsInstance(pkg.get("ui_only_reason"), str)
                    self.assertTrue(pkg["ui_only_reason"].strip())
