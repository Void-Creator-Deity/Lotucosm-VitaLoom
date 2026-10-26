# -*- coding: utf-8 -*-
"""runtime_packages 解析。"""
from __future__ import annotations

import unittest
from pathlib import Path


class RuntimePackagesTests(unittest.TestCase):
    def test_excludes_editor_only_packages(self) -> None:
        from core.VitaLoom.project.project_manifest import load_package_catalog
        from core.VitaLoom.project.runtime_packages import collect_runtime_package_ids

        repo = Path(__file__).resolve().parents[1]
        catalog = load_package_catalog(repo)
        ids = collect_runtime_package_ids(
            {
                "required_packages": [
                    "vitalloom.editor_essentials",
                    "vitalloom.engine.sr2d",
                ],
                "capabilities": [],
            },
            catalog,
            repo_root=str(repo),
        )
        self.assertIn("vitalloom.engine.sr2d", ids)
        self.assertNotIn("vitalloom.editor_essentials", ids)


if __name__ == "__main__":
    unittest.main()
