# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.project.asset_index import build_project_asset_index


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


class AssetIndexCommandIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="asset_index_cmd_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        (self.project / "assets" / "sprites").mkdir(parents=True)
        (self.project / "scripts").mkdir()
        (self.project / "scenes").mkdir()
        (self.project / "project.json").write_text(
            json.dumps(
                {
                    "name": "asset-index-command",
                    "active_scene": "main.pond",
                    "suite_id": "lotucosm.vitaloom.suite",
                    "product_id": "lotucosm-vitaloom",
                }
            ),
            encoding="utf-8",
        )
        (self.project / "project.lock.json").write_text("{}", encoding="utf-8")
        (self.project / "assets" / "sprites" / "hero.png").write_bytes(b"hero")
        (self.project / "scripts" / "brain.py").write_text("class Brain: pass\n", encoding="utf-8")
        (self.project / "scenes" / "main.pond").write_text(
            json.dumps(
                {
                    "entities": [
                        {
                            "scripts": [{"name": "brain"}],
                            "sprite_path": "assets/sprites/hero.png",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        self.registry = reset_command_registry()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_scan_dependencies_validate_and_export_use_index_interface(self) -> None:
        real_builder = build_project_asset_index
        with patch(
            "core.VitaLoom.project.asset_index.build_project_asset_index",
            wraps=real_builder,
        ) as builder:
            results = {
                command_id: self.registry.run(command_id, {"project_path": str(self.project)})
                for command_id in (
                    "asset.scan",
                    "asset.dependencies",
                    "asset.validate",
                    "asset.export_closure",
                    "export.player.prepare",
                )
            }
        self.assertEqual(builder.call_count, 5)
        for command_id, result in results.items():
            self.assertTrue(result["ok"], (command_id, result))
            json.dumps(result, allow_nan=False)

        scan = results["asset.scan"]["result"]
        deps = results["asset.dependencies"]["result"]
        validation = results["asset.validate"]["result"]
        closure = results["asset.export_closure"]["result"]
        prepared = results["export.player.prepare"]["result"]
        self.assertIn("project_path", scan)
        self.assertIn("assets", scan)
        self.assertIn("asset_count", scan)
        self.assertIn("index_revision", scan)
        for result in (deps, validation):
            for field in (
                "project_path",
                "total_edges",
                "edges",
                "missing_scripts",
                "missing_assets",
                "missing_total",
                "missing_by_kind",
            ):
                self.assertIn(field, result)
        for field in (
            "files",
            "file_count",
            "file_metadata",
            "dependency_edges",
            "missing_scripts",
            "missing_assets",
            "missing_total",
            "missing_by_kind",
            "enabled_plugins",
            "warnings",
            "ready",
        ):
            self.assertIn(field, closure)
        self.assertTrue(prepared["ready"])
        self.assertEqual(scan["index_revision"], closure["index_revision"])
        asset = next(row for row in scan["assets"] if row["path"] == "assets/sprites/hero.png")
        metadata = next(row for row in closure["file_metadata"] if row["path"] == asset["path"])
        self.assertEqual(asset["sha256"], metadata["sha256"])

    def test_existing_external_dependency_blocks_closure_and_player_prepare(self) -> None:
        external = self.tmp / "external.png"
        external.write_bytes(b"exists-but-not-exportable")
        (self.project / "scenes" / "main.pond").write_text(
            json.dumps({"sprite_path": str(external)}),
            encoding="utf-8",
        )

        deps = self.registry.run("asset.dependencies", {"project_path": str(self.project)})["result"]
        closure = self.registry.run("asset.export_closure", {"project_path": str(self.project)})["result"]
        prepared = self.registry.run("export.player.prepare", {"project_path": str(self.project)})["result"]
        self.assertEqual(deps["missing_total"], 0)
        self.assertEqual(deps["outside_project_total"], 1)
        self.assertFalse(closure["ready"])
        self.assertFalse(prepared["ready"])
        self.assertIn("export_closure_has_outside_project_dependencies", closure["warnings"])

    def test_export_tool_rejects_existing_external_dependency_before_copy(self) -> None:
        from tools.export_player import export_project

        external = self.tmp / "external-export.png"
        external.write_bytes(b"outside")
        (self.project / "scenes" / "main.pond").write_text(
            json.dumps({"sprite_path": str(external)}), encoding="utf-8"
        )
        with self.assertRaisesRegex(RuntimeError, "asset index is not export-ready"):
            export_project(self.project, repo_root=ROOT)
    def test_malformed_scene_is_explicit_and_blocks_export(self) -> None:
        (self.project / "scenes" / "broken.pond").write_text("{broken", encoding="utf-8")
        deps = self.registry.run("asset.dependencies", {"project_path": str(self.project)})["result"]
        closure = self.registry.run("asset.export_closure", {"project_path": str(self.project)})["result"]
        self.assertEqual(deps["malformed_scenes"][0]["scene"], "scenes/broken.pond")
        self.assertFalse(closure["ready"])
        self.assertIn("export_closure_has_malformed_scenes", closure["warnings"])


if __name__ == "__main__":
    unittest.main()

