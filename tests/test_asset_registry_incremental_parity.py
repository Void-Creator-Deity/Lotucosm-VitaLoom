# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.VitaLoom.project.asset_index import build_project_asset_index
from core.VitaLoom.project.asset_registry import refresh_project_asset_registry


class AssetRegistryIncrementalParityTests(unittest.TestCase):
    def _project(self, root: Path, *, assets: int = 24) -> Path:
        project = root / "project"
        (project / "assets" / "tiles").mkdir(parents=True)
        (project / "scenes").mkdir()
        (project / "scripts").mkdir()
        (project / "project.json").write_text(
            json.dumps({"name": "incremental-parity", "active_scene": "main.pond"}),
            encoding="utf-8",
        )
        (project / "project.lock.json").write_text("{}", encoding="utf-8")
        for index in range(assets):
            (project / "assets" / "tiles" / f"tile-{index:03d}.bin").write_bytes(f"tile-{index}".encode())
        (project / "scenes" / "main.pond").write_text(
            json.dumps({"sprite_path": "assets/tiles/tile-000.bin"}), encoding="utf-8"
        )
        return project

    @staticmethod
    def _facts(index: dict[str, object]) -> dict[str, object]:
        return {
            "index_revision": index["index_revision"],
            "inventory": index["inventory"],
            "assets": index["assets"],
            "dependencies": index["dependencies"],
            "provenance": index["provenance"],
            "export": index["export"],
            "coverage": index["coverage"],
        }

    def test_unchanged_and_one_file_refresh_match_full_rebuild_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            cold = refresh_project_asset_registry(project)
            full_cold = build_project_asset_index(project)
            self.assertEqual(self._facts(cold["asset_index"]), self._facts(full_cold))

            unchanged = refresh_project_asset_registry(project)
            full_unchanged = build_project_asset_index(project)
            self.assertEqual(self._facts(unchanged["asset_index"]), self._facts(full_unchanged))
            self.assertEqual(unchanged["refresh"]["cache_misses"], 0)
            self.assertEqual(unchanged["refresh"]["changed_files"], 0)
            self.assertTrue(unchanged["refresh"]["parity"])

            target = project / "assets" / "tiles" / "tile-009.bin"
            target.write_bytes(b"tile-009-mutated")
            incremental = refresh_project_asset_registry(project)
            full_mutated = build_project_asset_index(project)
            self.assertEqual(self._facts(incremental["asset_index"]), self._facts(full_mutated))
            self.assertEqual(incremental["refresh"]["cache_misses"], 1)
            self.assertEqual(incremental["refresh"]["changed_files"], 1)
            self.assertTrue(incremental["refresh"]["parity"])

    def test_atomic_write_does_not_leave_temporary_registry_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp), assets=2)
            refresh_project_asset_registry(project)
            registry_dir = project / ".vitaloom"
            self.assertEqual(
                sorted(path.name for path in registry_dir.iterdir()),
                ["asset_registry.json"],
            )


if __name__ == "__main__":
    unittest.main()
