# -*- coding: utf-8 -*-
"""AI commands should mirror editor scene/entity/resource operations."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.VitaLoom.commands.registry import reset_command_registry


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


class AiIsomorphicSceneCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = reset_command_registry()
        self.tmp = Path(tempfile.mkdtemp(prefix="ai_command_scene_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        self.scene = self.project / "scenes" / "main.pond"
        (self.project / "scenes").mkdir(parents=True)
        (self.project / "scripts").mkdir()
        (self.project / "assets" / "sprites").mkdir(parents=True)
        (self.project / "project.json").write_text(
            json.dumps(
                {
                    "name": "AI Command Test",
                    "active_scene": "main.pond",
                    "suite_id": "lotucosm.vitaloom.suite",
                    "product_id": "lotucosm-vitaloom",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (self.project / "scripts" / "brain.py").write_text(
            "from core.Lotucosm.scripts import ScriptBase\nclass Brain(ScriptBase):\n    pass\n",
            encoding="utf-8",
        )
        self.alt_scene = self.project / "scenes" / "alt.pond"
        (self.project / "assets" / "sprites" / "hero.png").write_bytes(b"png")
        self.scene.write_text(
            json.dumps(
                {
                    "name": "Main",
                    "entities": [
                        {
                            "id": "hero",
                            "name": "Hero",
                            "type": "game_actor",
                            "position": [1.0, 2.0],
                            "radius": 10.0,
                            "scripts": [{"name": "brain", "type": "Brain", "properties": {}}],
                            "sr_visual": {"sprite_path": "assets/sprites/hero.png"},
                        }
                    ],
                    "components": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self.alt_scene.write_text(
            json.dumps({"name": "Alt", "entities": [], "components": []}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_scene_entity_and_asset_commands_are_registered_with_mutation_metadata(self) -> None:
        commands = {row["id"]: row for row in self.registry.list()}
        for command_id in (
            "entity.create",
            "entity.set_property",
            "entity.delete",
            "transform.set",
            "script.set_property",
            "prefab.place",
            "scene.validate",
            "project.set_active_scene",
            "project.set_ps_experiment_preset",
            "project.set_evolution_defaults",
            "asset.create",
            "asset.import",
            "asset.validate",
            "asset.scan",
            "asset.dependencies",
            "asset.export_closure",
            "asset.apply_to_scene",
        ):
            self.assertIn(command_id, commands)
        self.assertTrue(commands["entity.create"]["mutates"])
        self.assertTrue(commands["entity.set_property"]["mutates"])
        self.assertTrue(commands["entity.delete"]["mutates"])
        self.assertTrue(commands["project.set_active_scene"]["mutates"])
        self.assertTrue(commands["project.set_active_scene"]["undoable"])
        self.assertTrue(commands["project.set_ps_experiment_preset"]["mutates"])
        self.assertTrue(commands["project.set_evolution_defaults"]["mutates"])
        self.assertTrue(commands["project.set_evolution_defaults"]["undoable"])
        self.assertTrue(commands["asset.create"]["mutates"])
        self.assertTrue(commands["asset.import"]["mutates"])
        self.assertTrue(commands["asset.apply_to_scene"]["mutates"])
        self.assertTrue(commands["prefab.place"]["mutates"])
        self.assertTrue(commands["script.set_property"]["mutates"])
        self.assertTrue(commands["transform.set"]["mutates"])
        self.assertFalse(commands["scene.validate"]["mutates"])
        self.assertFalse(commands["asset.scan"]["mutates"])
        self.assertFalse(commands["asset.validate"]["mutates"])
        self.assertFalse(commands["asset.export_closure"]["mutates"])

    def test_project_set_active_scene_updates_project_contract(self) -> None:
        result = self.registry.run(
            "project.set_active_scene",
            {
                "project_path": str(self.project),
                "scene_path": str(self.alt_scene),
            },
        )
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["events"], ["active_scene_changed"])
        self.assertEqual(result["result"]["active_scene"], "alt.pond")
        self.assertFalse(result["result"]["scene_loaded"])

        meta = json.loads((self.project / "project.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["active_scene"], "alt.pond")

    def test_project_ps_experiment_preset_updates_project_contract(self) -> None:
        result = self.registry.run(
            "project.set_ps_experiment_preset",
            {
                "project_path": str(self.project),
                "preset_path": "workspace/experiments/quick_evolution_only.json",
            },
        )
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["events"], ["ps_experiment_preset_changed"])

        meta = json.loads((self.project / "project.json").read_text(encoding="utf-8"))
        self.assertEqual(
            meta["ps_experiment_preset"],
            "workspace/experiments/quick_evolution_only.json",
        )

    def test_project_evolution_defaults_updates_project_contract(self) -> None:
        defaults = {
            "mutation_rate": 0.08,
            "selection_pressure": 0.5,
            "max_population": 42,
        }
        result = self.registry.run(
            "project.set_evolution_defaults",
            {"project_path": str(self.project), "defaults": defaults},
        )
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["events"], ["evolution_defaults_changed"])

        meta = json.loads((self.project / "project.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["evolution_defaults"], defaults)

    def test_asset_create_uses_project_asset_contract(self) -> None:
        result = self.registry.run(
            "asset.create",
            {
                "project_path": str(self.project),
                "asset_type": "component",
                "name": "sensor patrol",
                "folder": "scripts",
            },
        )
        self.assertTrue(result["ok"], result)
        created = Path(result["result"]["path"])
        self.assertTrue(created.is_file())
        self.assertEqual(created.name, "sensor patrol.py")
        self.assertIn("class SensorPatrol", created.read_text(encoding="utf-8"))

        outside = self.registry.run(
            "asset.create",
            {
                "project_path": str(self.project),
                "asset_type": "entity",
                "name": "bad",
                "folder": "../escape",
            },
        )
        self.assertFalse(outside["ok"])
        self.assertEqual(outside["error"]["code"], "asset_folder_outside_project")

    def test_project_set_active_scene_rejects_scene_outside_project(self) -> None:
        outside = self.tmp / "outside.pond"
        outside.write_text("{}", encoding="utf-8")

        result = self.registry.run(
            "project.set_active_scene",
            {
                "project_path": str(self.project),
                "scene_path": str(outside),
            },
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "scene_outside_project")

    def test_entity_create_set_property_and_delete_modify_scene_through_command(self) -> None:
        create = self.registry.run(
            "entity.create",
            {
                "scene_path": str(self.scene),
                "entity": {
                    "id": "crate",
                    "name": "Crate",
                    "type": "game_prop",
                    "position": [4.0, 5.0],
                    "radius": 8.0,
                    "scripts": [],
                    "sr_visual": {"sprite": "box"},
                },
            },
        )
        self.assertTrue(create["ok"], create)
        self.assertEqual(create["events"], ["entity_created"])

        set_prop = self.registry.run(
            "entity.set_property",
            {
                "scene_path": str(self.scene),
                "entity_id": "crate",
                "property_path": "sr_visual.sprite",
                "value": "hero",
            },
        )
        self.assertTrue(set_prop["ok"], set_prop)

        data = json.loads(self.scene.read_text(encoding="utf-8"))
        crate = next(ent for ent in data["entities"] if ent["id"] == "crate")
        self.assertEqual(crate["sr_visual"]["sprite"], "hero")

        delete = self.registry.run(
            "entity.delete",
            {"scene_path": str(self.scene), "entity_id": "crate"},
        )
        self.assertTrue(delete["ok"], delete)
        data = json.loads(self.scene.read_text(encoding="utf-8"))
        self.assertEqual([ent["id"] for ent in data["entities"]], ["hero"])

    def test_transform_and_script_commands_update_scene_contract(self) -> None:
        moved = self.registry.run(
            "transform.set",
            {
                "scene_path": str(self.scene),
                "entity_id": "hero",
                "position": [7.0, 8.0],
                "rotation": 15,
                "scale": [2.0, 2.0],
            },
        )
        self.assertTrue(moved["ok"], moved)
        self.assertEqual(moved["events"], ["transform_changed"])

        scripted = self.registry.run(
            "script.set_property",
            {
                "scene_path": str(self.scene),
                "entity_id": "hero",
                "script": "brain",
                "property_path": "awareness.level",
                "value": 3,
            },
        )
        self.assertTrue(scripted["ok"], scripted)
        self.assertEqual(scripted["events"], ["script_property_changed"])

        data = json.loads(self.scene.read_text(encoding="utf-8"))
        hero = next(ent for ent in data["entities"] if ent["id"] == "hero")
        self.assertEqual(hero["position"], [7.0, 8.0])
        self.assertEqual(hero["rotation"], 15)
        self.assertEqual(hero["scale"], [2.0, 2.0])
        self.assertEqual(hero["scripts"][0]["properties"]["awareness"]["level"], 3)

    def test_prefab_and_asset_apply_create_scene_entities(self) -> None:
        prefab = self.project / "assets" / "prefabs" / "crate.json"
        prefab.parent.mkdir(parents=True)
        prefab.write_text(
            json.dumps(
                {
                    "id": "crate_template",
                    "name": "Crate Template",
                    "type": "prefab",
                    "position": [0.0, 0.0],
                    "scripts": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        placed = self.registry.run(
            "prefab.place",
            {
                "scene_path": str(self.scene),
                "prefab_path": str(prefab),
                "entity_id": "crate_01",
                "position": [9.0, 10.0],
            },
        )
        self.assertTrue(placed["ok"], placed)
        self.assertEqual(placed["events"], ["prefab_placed"])

        applied = self.registry.run(
            "asset.apply_to_scene",
            {
                "scene_path": str(self.scene),
                "asset_path": str(self.project / "assets" / "sprites" / "hero.png"),
                "entity_id": "hero_sprite_ref",
                "position": [1.5, 2.5],
            },
        )
        self.assertTrue(applied["ok"], applied)
        self.assertEqual(applied["events"], ["asset_applied_to_scene"])

        data = json.loads(self.scene.read_text(encoding="utf-8"))
        ids = {ent["id"] for ent in data["entities"]}
        self.assertIn("crate_01", ids)
        self.assertIn("hero_sprite_ref", ids)

    def test_asset_import_validate_and_export_closure(self) -> None:
        source = self.tmp / "external_sprite.png"
        source.write_bytes(b"external")
        imported = self.registry.run(
            "asset.import",
            {
                "project_path": str(self.project),
                "source_path": str(source),
                "target_folder": "assets/sprites",
            },
        )
        self.assertTrue(imported["ok"], imported)
        imported_path = Path(imported["result"]["path"])
        self.assertTrue(imported_path.is_file())
        self.assertEqual(imported_path.read_bytes(), b"external")

        validation = self.registry.run("asset.validate", {"project_path": str(self.project)})
        self.assertTrue(validation["ok"], validation)
        self.assertEqual(validation["result"]["missing_total"], 0)

        closure = self.registry.run("asset.export_closure", {"project_path": str(self.project)})
        self.assertTrue(closure["ok"], closure)
        result = closure["result"]
        self.assertIn("scenes/main.pond", result["files"])
        self.assertIn("scripts/brain.py", result["files"])
        self.assertIn("assets/sprites/hero.png", result["files"])
        self.assertEqual(result["missing_total"], 0)
        self.assertIn("enabled_plugins", result)

    def test_scene_validate_and_asset_dependencies_report_missing_files(self) -> None:
        data = json.loads(self.scene.read_text(encoding="utf-8"))
        data["entities"][0]["scripts"].append({"name": "missing_ai", "type": "MissingAI"})
        data["entities"][0]["sr_visual"]["texture_path"] = "assets/sprites/missing.png"
        self.scene.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        validation = self.registry.run("scene.validate", {"scene_path": str(self.scene)})
        self.assertTrue(validation["ok"], validation)
        self.assertEqual(validation["result"]["missing_scripts"], ["scripts/missing_ai.py"])
        self.assertEqual(validation["result"]["missing_assets"], ["assets/sprites/missing.png"])

        deps = self.registry.run("asset.dependencies", {"project_path": str(self.project)})
        self.assertTrue(deps["ok"], deps)
        self.assertEqual(deps["result"]["missing_total"], 2)
        self.assertGreaterEqual(deps["result"]["total_edges"], 4)

    def test_entity_command_rejects_duplicate_ids(self) -> None:
        result = self.registry.run(
            "entity.create",
            {
                "scene_path": str(self.scene),
                "entity": {
                    "id": "hero",
                    "type": "game_actor",
                    "position": [0.0, 0.0],
                },
            },
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "entity_id_exists")


if __name__ == "__main__":
    unittest.main()
