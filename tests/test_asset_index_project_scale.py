# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from core.VitaLoom.project.asset_index import build_project_asset_index


class AssetIndexProjectScaleTests(unittest.TestCase):
    def test_thousand_asset_snapshot_is_deterministic_with_explicit_full_rebuild_cost(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "scale"
            (project / "assets").mkdir(parents=True)
            (project / "scenes").mkdir()
            (project / "scripts").mkdir()
            (project / "project.json").write_text(json.dumps({"name": "scale"}), encoding="utf-8")
            for index in range(1000):
                (project / "assets" / f"asset_{index:04d}.dat").write_bytes(f"asset-{index}".encode())
            for scene_index in range(20):
                refs = [
                    {"asset_path": f"assets/asset_{scene_index * 20 + offset:04d}.dat"}
                    for offset in range(20)
                ]
                (project / "scenes" / f"scene_{scene_index:02d}.pond").write_text(
                    json.dumps({"entities": refs}), encoding="utf-8"
                )

            started = time.perf_counter()
            first = build_project_asset_index(project)
            cold_seconds = time.perf_counter() - started
            started = time.perf_counter()
            second = build_project_asset_index(project)
            rebuild_seconds = time.perf_counter() - started
            started = time.perf_counter()
            projection = [
                {"path": row["path"], "sha256": row["sha256"]}
                for row in first["assets"]
            ]
            projection_seconds = time.perf_counter() - started

            self.assertEqual(first["asset_count"], 1000)
            self.assertEqual(first["dependencies"]["total_edges"], 400)
            self.assertEqual(first["index_revision"], second["index_revision"])
            self.assertEqual(len(projection), 1000)
            self.assertLess(cold_seconds, 10.0)
            self.assertLess(rebuild_seconds, 10.0)
            self.assertLess(projection_seconds, 1.0)


if __name__ == "__main__":
    unittest.main()

