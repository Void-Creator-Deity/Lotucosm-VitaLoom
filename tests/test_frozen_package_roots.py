# -*- coding: utf-8
"""打包态 physical_roots 与包索引可用性。"""
from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch


class FrozenPackageRootsTests(unittest.TestCase):
    def test_required_core_package_exists_when_frozen(self):
        from core.VitaLoom.core import bundle_paths as bp
        from core.VitaLoom.project.project_manifest import _package_roots_exist

        fake_meipass = Path("/bundled/internal")
        pkg = {
            "id": "vitalloom.core.platform",
            "physical_roots": ["core/Lotucosm", "core/VitaLoom"],
        }
        with patch.object(bp, "is_frozen_bundle", return_value=True), patch.object(
            bp, "resource_root", return_value=fake_meipass
        ):
            self.assertTrue(_package_roots_exist(fake_meipass, pkg))

    def test_builtin_root_exists_in_dev(self):
        from core.VitaLoom.core import bundle_paths as bp
        from core.VitaLoom.project.project_manifest import _package_roots_exist

        root = bp._dev_repo_root()
        pkg = {"id": "vitalloom.editor_essentials", "physical_roots": ["builtin/editor_extensions"]}
        with patch.object(bp, "is_frozen_bundle", return_value=False):
            self.assertTrue(_package_roots_exist(root, pkg))


if __name__ == "__main__":
    unittest.main()
