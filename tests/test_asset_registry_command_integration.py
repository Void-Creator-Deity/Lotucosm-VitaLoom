# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.VitaLoom.commands.registry import reset_command_registry


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


class AssetRegistryCommandIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="asset_registry_cmd_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        (self.project / "assets").mkdir(parents=True)
        (self.project / "scripts").mkdir()
        (self.project / "scenes").mkdir()
        (self.project / "project.json").write_text(
            json.dumps(
                {
                    "name": "asset-registry-command",
                    "active_scene": "main.pond",
                    "suite_id": "lotucosm.vitaloom.suite",
                    "product_id": "lotucosm-vitaloom",
                }
            ),
            encoding="utf-8",
        )
        (self.project / "project.lock.json").write_text("{}", encoding="utf-8")
        (self.project / "assets" / "hero.png").write_bytes(b"hero")
        (self.project / "scenes" / "main.pond").write_text(
            json.dumps({"sprite_path": "assets/hero.png"}), encoding="utf-8"
        )
        self.registry = reset_command_registry()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_read_only_asset_scan_never_creates_registry(self) -> None:
        registry_path = self.project / ".vitaloom" / "asset_registry.json"
        result = self.registry.run("asset.scan", {"project_path": str(self.project)})
        self.assertTrue(result["ok"], result)
        self.assertFalse(registry_path.exists())

    def test_refresh_create_import_rename_and_delete_share_persistent_identity_authority(self) -> None:
        refreshed = self.registry.run("asset.refresh", {"project_path": str(self.project)})
        self.assertTrue(refreshed["ok"], refreshed)
        initial = refreshed["result"]
        hero_id = next(row["asset_id"] for row in initial["asset_projection"] if row["path"] == "assets/hero.png")
        self.assertTrue((self.project / ".vitaloom" / "asset_registry.json").is_file())

        created = self.registry.run(
            "asset.create",
            {
                "project_path": str(self.project),
                "asset_type": "component",
                "name": "brain_extra",
                "folder": "scripts",
            },
        )
        self.assertTrue(created["ok"], created)
        self.assertTrue(created["result"]["asset_id"].startswith("asset_"))
        self.assertIn("asset_registry_revision", created["result"])

        external = self.tmp / "external-image.png"
        external.write_bytes(b"imported")
        imported = self.registry.run(
            "asset.import",
            {
                "project_path": str(self.project),
                "source_path": str(external),
                "target_folder": "assets",
                "name": "imported.png",
            },
        )
        self.assertTrue(imported["ok"], imported)
        imported_id = imported["result"]["asset_id"]

        renamed = self.registry.run(
            "asset.rename",
            {
                "project_path": str(self.project),
                "source_path": "assets/imported.png",
                "target_path": "assets/renamed-imported.png",
            },
        )
        self.assertTrue(renamed["ok"], renamed)
        self.assertEqual(renamed["result"]["asset_id"], imported_id)
        self.assertTrue((self.project / "assets" / "renamed-imported.png").is_file())

        deleted = self.registry.run(
            "asset.delete",
            {
                "project_path": str(self.project),
                "asset_path": "assets/renamed-imported.png",
            },
        )
        self.assertTrue(deleted["ok"], deleted)
        self.assertEqual(deleted["result"]["asset_id"], imported_id)
        self.assertFalse((self.project / "assets" / "renamed-imported.png").exists())

        renamed_hero = self.registry.run(
            "asset.rename",
            {
                "project_path": str(self.project),
                "source_path": "assets/hero.png",
                "target_path": "assets/hero-renamed.png",
            },
        )
        self.assertTrue(renamed_hero["ok"], renamed_hero)
        self.assertEqual(renamed_hero["result"]["asset_id"], hero_id)

        final = self.registry.run("asset.refresh", {"project_path": str(self.project)})
        self.assertTrue(final["ok"], final)
        rows = final["result"]["asset_projection"]
        self.assertEqual(
            next(row["asset_id"] for row in rows if row["path"] == "assets/hero-renamed.png"),
            hero_id,
        )
        self.assertTrue(any(row["asset_id"] == imported_id for row in final["result"]["tombstones"]))

    def test_rename_and_delete_reject_non_project_or_directory_inputs(self) -> None:
        source = self.registry.run(
            "asset.rename",
            {
                "project_path": str(self.project),
                "source_path": "assets/hero.png",
                "target_path": "../outside.png",
            },
        )
        self.assertFalse(source["ok"])
        self.assertEqual(source["error"]["code"], "asset_path_outside_project")

        deleted = self.registry.run(
            "asset.delete",
            {"project_path": str(self.project), "asset_path": "assets"},
        )
        self.assertFalse(deleted["ok"])
        self.assertEqual(deleted["error"]["code"], "asset_delete_requires_file")


if __name__ == "__main__":
    unittest.main()
