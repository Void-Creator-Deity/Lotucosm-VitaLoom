# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.VitaLoom.project.asset_index import build_project_asset_index


class ProjectAssetIndexTests(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        project = root / "project"
        (project / "assets" / "sprites").mkdir(parents=True)
        (project / "scripts").mkdir()
        (project / "scenes").mkdir()
        (project / "project.json").write_text(
            json.dumps({"name": "index-test", "active_scene": "main.pond"}),
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
                            "id": "hero",
                            "scripts": [{"name": "brain"}],
                            "visual": {"sprite_path": "assets/sprites/hero.png"},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        return project

    def test_build_is_deterministic_json_only_and_copy_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            first = build_project_asset_index(project)
            second = build_project_asset_index(project)

            self.assertEqual(first, second)
            self.assertEqual(first["schema_version"], 1)
            self.assertEqual(first["index_revision"], second["index_revision"])
            json.dumps(first, allow_nan=False)
            self.assertEqual(
                [row["id"] for row in first["assets"]],
                sorted(row["id"] for row in first["assets"]),
            )
            first["assets"][0]["id"] = "mutated"
            self.assertNotEqual(first["assets"], second["assets"])

    def test_content_change_updates_digest_and_revision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            before = build_project_asset_index(project)
            target = project / "assets" / "sprites" / "hero.png"
            before_asset = next(row for row in before["assets"] if row["id"] == "assets/sprites/hero.png")
            target.write_bytes(b"hero-v2")
            after = build_project_asset_index(project)
            after_asset = next(row for row in after["assets"] if row["id"] == "assets/sprites/hero.png")

            self.assertNotEqual(before_asset["sha256"], after_asset["sha256"])
            self.assertNotEqual(before["index_revision"], after["index_revision"])

    def test_dependency_edges_preserve_pointer_and_canonical_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            index = build_project_asset_index(project)
            deps = index["dependencies"]

            script = next(edge for edge in deps["edges"] if edge["kind"] == "script")
            asset = next(edge for edge in deps["edges"] if edge["kind"] == "asset")
            self.assertEqual(script["target"], "scripts/brain.py")
            self.assertEqual(script["status"], "ok")
            self.assertEqual(script["json_pointer"], "$.entities[0].scripts[0]")
            self.assertEqual(asset["target"], "assets/sprites/hero.png")
            self.assertEqual(asset["json_pointer"], "$.entities[0].visual.sprite_path")
            self.assertEqual(deps["missing_total"], 0)
            self.assertEqual(deps["outside_project_total"], 0)
            self.assertTrue(deps["ready"])

    def test_existing_absolute_and_traversal_targets_outside_project_are_not_exportable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self._project(root)
            external = root / "external.png"
            external.write_bytes(b"exists")
            scene = project / "scenes" / "main.pond"
            scene.write_text(
                json.dumps(
                    {
                        "entities": [
                            {
                                "sprite_path": str(external),
                                "audio_path": "../../external.png",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            index = build_project_asset_index(project)
            deps = index["dependencies"]
            self.assertEqual(deps["outside_project_total"], 2)
            self.assertEqual(deps["missing_total"], 0)
            self.assertFalse(deps["ready"])
            self.assertFalse(index["export"]["ready"])
            self.assertTrue(all(edge["status"] == "outside_project" for edge in deps["edges"] if edge["kind"] == "asset"))

    def test_missing_outside_and_malformed_are_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            scene = project / "scenes" / "main.pond"
            scene.write_text(json.dumps({"sprite_path": "assets/missing.png"}), encoding="utf-8")
            (project / "scenes" / "broken.pond").write_text("{not-json", encoding="utf-8")

            index = build_project_asset_index(project)
            deps = index["dependencies"]
            self.assertEqual(deps["missing_total"], 1)
            self.assertEqual(deps["outside_project_total"], 0)
            self.assertEqual(len(deps["malformed_scenes"]), 1)
            self.assertEqual(deps["malformed_scenes"][0]["scene"], "scenes/broken.pond")
            self.assertFalse(deps["ready"])
            self.assertIn("export_closure_has_malformed_scenes", index["export"]["warnings"])

    def test_duplicate_references_have_deterministic_distinct_pointers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            (project / "scenes" / "main.pond").write_text(
                json.dumps(
                    {
                        "entities": [
                            {"sprite_path": "assets/sprites/hero.png"},
                            {"sprite_path": "assets/sprites/hero.png"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            first = build_project_asset_index(project)["dependencies"]["edges"]
            second = build_project_asset_index(project)["dependencies"]["edges"]
            hero_edges = [edge for edge in first if edge.get("target") == "assets/sprites/hero.png"]
            self.assertEqual(first, second)
            self.assertEqual(len(hero_edges), 2)
            self.assertNotEqual(hero_edges[0]["json_pointer"], hero_edges[1]["json_pointer"])

    def test_provenance_is_correlated_without_fabricated_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            (project / "assets" / "manifest.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "sources": {
                            "sprites/hero.png": {
                                "origin": "project_generated",
                                "generator": "tools/gen.py",
                                "license": "generated-project-owned",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            index = build_project_asset_index(project)
            hero = next(row for row in index["assets"] if row["id"] == "assets/sprites/hero.png")
            self.assertEqual(hero["provenance"]["status"], "proven")
            self.assertEqual(hero["provenance"]["origin"], "project_generated")
            self.assertNotIn("author", hero["provenance"])
            self.assertEqual(index["provenance"]["proven_assets"], 1)

    def test_module_is_qt_and_editor_global_free(self) -> None:
        import core.VitaLoom.project.asset_index as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in ("PyQt", "ProjectManager", "get_project_manager", "editor_context", "CommandRegistry"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
