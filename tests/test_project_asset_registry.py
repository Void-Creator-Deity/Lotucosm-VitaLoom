# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.VitaLoom.project.asset_index import build_project_asset_index
from core.VitaLoom.project.asset_registry import (
    load_project_asset_registry,
    refresh_project_asset_registry,
)


class ProjectAssetRegistryTests(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        project = root / "project"
        (project / "assets" / "sprites").mkdir(parents=True)
        (project / "scripts").mkdir()
        (project / "scenes").mkdir()
        (project / "project.json").write_text(
            json.dumps({"name": "registry-test", "active_scene": "main.pond"}),
            encoding="utf-8",
        )
        (project / "project.lock.json").write_text("{}", encoding="utf-8")
        (project / "assets" / "sprites" / "hero.png").write_bytes(b"hero-v1")
        (project / "scripts" / "brain.py").write_text("class Brain: pass\n", encoding="utf-8")
        (project / "scenes" / "main.pond").write_text(
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
        return project

    @staticmethod
    def _id_for(snapshot: dict[str, object], path: str) -> str:
        return next(row["asset_id"] for row in snapshot["asset_projection"] if row["path"] == path)  # type: ignore[index]

    def test_initial_refresh_is_persistent_json_only_and_metadata_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            refreshed = refresh_project_asset_registry(project)
            registry_path = project / ".vitaloom" / "asset_registry.json"

            self.assertTrue(registry_path.is_file())
            self.assertEqual(refreshed["schema_version"], 1)
            self.assertEqual(refreshed["asset_count"], build_project_asset_index(project)["file_count"])
            self.assertTrue(all(str(row["asset_id"]).startswith("asset_") for row in refreshed["asset_projection"]))
            self.assertNotIn(".vitaloom/asset_registry.json", refreshed["asset_index"]["export"]["files"])
            self.assertNotIn(".vitaloom/asset_registry.json", [row["path"] for row in refreshed["asset_index"]["inventory"]])
            json.dumps(refreshed, allow_nan=False)

            loaded = load_project_asset_registry(project)
            self.assertEqual(loaded["registry_revision"], refreshed["registry_revision"])
            self.assertEqual(loaded["asset_count"], refreshed["asset_count"])

    def test_unchanged_refresh_reuses_digests_and_revision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            first = refresh_project_asset_registry(project)
            with patch("core.VitaLoom.project.asset_index._digest", wraps=__import__("core.VitaLoom.project.asset_index", fromlist=["_digest"])._digest) as digest:
                second = refresh_project_asset_registry(project)

            self.assertEqual(first["registry_revision"], second["registry_revision"])
            self.assertEqual(first["asset_projection"], second["asset_projection"])
            self.assertEqual(second["refresh"]["cache_misses"], 0)
            self.assertEqual(second["refresh"]["cache_hits"], second["asset_count"])
            self.assertEqual(digest.call_count, 0)

    def test_content_change_delete_and_recreate_have_truthful_identity_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            original = refresh_project_asset_registry(project)
            hero = project / "assets" / "sprites" / "hero.png"
            original_id = self._id_for(original, "assets/sprites/hero.png")

            hero.write_bytes(b"hero-v2")
            changed = refresh_project_asset_registry(project)
            self.assertEqual(original_id, self._id_for(changed, "assets/sprites/hero.png"))
            self.assertEqual(changed["refresh"]["changed_files"], 1)

            hero.unlink()
            deleted = refresh_project_asset_registry(project)
            self.assertNotIn("assets/sprites/hero.png", [row["path"] for row in deleted["asset_projection"]])
            self.assertTrue(any(row["asset_id"] == original_id for row in deleted["tombstones"]))

            hero.write_bytes(b"hero-v3-new")
            recreated = refresh_project_asset_registry(project)
            self.assertNotEqual(original_id, self._id_for(recreated, "assets/sprites/hero.png"))
            self.assertTrue(any(row["asset_id"] == original_id for row in recreated["tombstones"]))

    def test_unique_external_rename_preserves_identity_but_ambiguous_content_never_guesses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            first = refresh_project_asset_registry(project)
            before_id = self._id_for(first, "assets/sprites/hero.png")
            old = project / "assets" / "sprites" / "hero.png"
            new = project / "assets" / "sprites" / "renamed-hero.png"
            old.rename(new)
            renamed = refresh_project_asset_registry(project)
            self.assertEqual(before_id, self._id_for(renamed, "assets/sprites/renamed-hero.png"))
            self.assertEqual(renamed["refresh"]["renamed_files"], 1)

            left = project / "assets" / "duplicate-left.bin"
            right = project / "assets" / "duplicate-right.bin"
            left.write_bytes(b"same")
            right.write_bytes(b"same")
            duplicates = refresh_project_asset_registry(project)
            old_ids = {
                self._id_for(duplicates, "assets/duplicate-left.bin"),
                self._id_for(duplicates, "assets/duplicate-right.bin"),
            }
            left.unlink()
            right.unlink()
            (project / "assets" / "duplicate-new.bin").write_bytes(b"same")
            ambiguous = refresh_project_asset_registry(project)
            new_id = self._id_for(ambiguous, "assets/duplicate-new.bin")
            self.assertNotIn(new_id, old_ids)
            self.assertTrue(ambiguous["refresh"]["ambiguous_renames"])

    def test_malformed_registry_never_claims_existing_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            first = refresh_project_asset_registry(project)
            hero_id = self._id_for(first, "assets/sprites/hero.png")
            registry_path = project / ".vitaloom" / "asset_registry.json"
            registry_path.write_text("{broken", encoding="utf-8")

            loaded = load_project_asset_registry(project)
            self.assertEqual(loaded["status"], "malformed")
            recovered = refresh_project_asset_registry(project)
            self.assertEqual(recovered["recovery"]["status"], "reinitialized_from_malformed")
            self.assertNotEqual(hero_id, self._id_for(recovered, "assets/sprites/hero.png"))

    def test_registry_supported_index_has_full_rebuild_parity_and_no_qt_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            refreshed = refresh_project_asset_registry(project)
            full = build_project_asset_index(project)
            self.assertEqual(refreshed["asset_index"], full)
            self.assertEqual(
                [(row["path"], row["sha256"]) for row in refreshed["asset_projection"]],
                [(row["path"], row["sha256"]) for row in full["inventory"]],
            )

        source = Path(__file__).resolve().parents[1] / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/project/asset_registry.py"
        text = source.read_text(encoding="utf-8")
        for forbidden in ("PyQt", "project_manager", "editor_context", "commands.registry"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
