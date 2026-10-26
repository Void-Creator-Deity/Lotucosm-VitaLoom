# -*- coding: utf-8
"""插件 id 与 package_index 一致性。"""
from __future__ import annotations

import json
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


class PluginIdConsistencyTests(unittest.TestCase):
    def test_index_plugins_use_plugin_suffix(self):
        data = json.loads(
            CATALOG.read_text(encoding="utf-8")
        )
        for pkg in data.get("packages", []):
            for pid in pkg.get("plugins", []) or []:
                self.assertTrue(
                    str(pid).endswith("Plugin"),
                    f"package {pkg.get('id')} plugin id {pid} should end with Plugin",
                )

    def test_canonical_id_preserves_plugin_suffix(self):
        from core.VitaLoom.kernel.plugin_ids import canonical_plugin_id

        self.assertEqual(canonical_plugin_id("PsExperimentPlugin"), "PsExperimentPlugin")
        self.assertEqual(canonical_plugin_id("PackageManagerPlugin"), "PackageManagerPlugin")

    def test_canonical_id_appends_plugin_suffix(self):
        from core.VitaLoom.kernel.plugin_ids import canonical_plugin_id

        self.assertEqual(canonical_plugin_id("PsExperiment"), "PsExperimentPlugin")
        self.assertEqual(canonical_plugin_id("", "PackageManagerPlugin"), "PackageManagerPlugin")


if __name__ == "__main__":
    unittest.main()
