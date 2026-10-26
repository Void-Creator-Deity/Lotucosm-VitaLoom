# -*- coding: utf-8 -*-
"""bundle_paths contract tests for repo and frozen product-version layouts."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class BundlePathsTests(unittest.TestCase):
    def test_dev_repo_root_is_application_root(self) -> None:
        from core.VitaLoom.core import bundle_paths as bp

        root = bp._dev_repo_root()
        self.assertTrue((root / "FrameCore").is_dir())
        self.assertTrue((root / "main.py").is_file())

    def test_frozen_resource_root_prefers_product_runtime(self) -> None:
        from core.VitaLoom.core import bundle_paths as bp

        fake_meipass = Path("C:/bundled/internal")
        fake_exe = Path("C:/apps/FrameCore/FrameCore.exe")
        fake_version = (
            fake_meipass
            / "FrameCore"
            / "plugins"
            / "lotucosm-vitaloom"
            / "versions"
            / "1.0.0"
        )
        with patch.object(bp.sys, "frozen", True, create=True), patch.object(
            bp.sys, "_MEIPASS", str(fake_meipass), create=True
        ), patch.object(bp.sys, "executable", str(fake_exe)), patch.dict(
            bp.os.environ,
            {
                "VITALOOM_APP_ROOT": str(fake_exe.parent),
                "VITALOOM_PRODUCT_VERSION_ROOT": str(fake_version),
            },
            clear=False,
        ), patch.object(Path, "exists", lambda self: str(self).endswith("runtime")):
            self.assertEqual(bp.application_root(), fake_exe.parent)
            self.assertEqual(bp.resource_root(), fake_version / "runtime")

    def test_workspace_extensions_are_sources_unless_dev_scan_enabled(self) -> None:
        from core.VitaLoom.core import bundle_paths as bp

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace" / "extensions" / "user").mkdir(parents=True)
            (root / "workspace" / "extensions" / "community").mkdir()
            (root / "workspace" / "extensions" / "legacy_flat_plugin").mkdir()

            with patch.dict(bp.os.environ, {}, clear=True):
                self.assertEqual(bp._collect_user_plugin_dirs(root, include_legacy_flat=False), [])

            with patch.dict(bp.os.environ, {"VITALOOM_ENABLE_WORKSPACE_EXTENSIONS": "1"}, clear=True):
                default_dirs = bp._collect_user_plugin_dirs(root, include_legacy_flat=False)
                self.assertIn(str(root / "workspace" / "extensions" / "user"), default_dirs)
                self.assertIn(str(root / "workspace" / "extensions" / "community"), default_dirs)
                self.assertNotIn(str(root / "workspace" / "extensions" / "legacy_flat_plugin"), default_dirs)

                legacy_dirs = bp._collect_user_plugin_dirs(root, include_legacy_flat=True)
                self.assertIn(str(root / "workspace" / "extensions" / "legacy_flat_plugin"), legacy_dirs)

    def test_editor_launcher_uses_authoritative_plugin_layers(self) -> None:
        from core.VitaLoom.core import bundle_paths as bp
        from core.VitaLoom.editor_launcher import default_plugin_layers

        self.assertEqual(default_plugin_layers("ignored"), bp.default_plugin_layer_dirs())


if __name__ == "__main__":
    unittest.main()
