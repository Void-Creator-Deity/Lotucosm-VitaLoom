# -*- coding: utf-8 -*-
"""SceneViewport placement helpers must route through the shared command layer."""
from __future__ import annotations

import unittest

from core.VitaLoom.viewports.scene_viewport import SceneViewport


class _Registry:
    def __init__(self, result=None):
        self.calls = []
        self.result = result or {"ok": True, "result": {}, "events": [], "warnings": [], "error": None}

    def run(self, command_id, payload):
        self.calls.append((command_id, payload))
        return self.result


class SceneViewportCommandBridgeTests(unittest.TestCase):
    def test_entity_creation_routes_through_entity_command(self):
        registry = _Registry()

        ok = SceneViewport._run_scene_entity_create_command(
            {
                "scene_path": "workspace/projects/demo/scenes/main.pond",
                "entity": {
                    "id": "organism_01",
                    "name": "Organism",
                    "type": "organism",
                    "position": [3.0, 4.0],
                    "scripts": [],
                },
            },
            registry=registry,
        )

        self.assertTrue(ok)
        self.assertEqual(registry.calls[0][0], "entity.create")
        self.assertEqual(registry.calls[0][1]["entity"]["type"], "organism")
        self.assertEqual(registry.calls[0][1]["entity"]["position"], [3.0, 4.0])

    def test_asset_placement_routes_through_asset_command(self):
        registry = _Registry()

        ok = SceneViewport._run_scene_placement_command(
            "asset.apply_to_scene",
            {
                "scene_path": "workspace/projects/demo/scenes/main.pond",
                "asset_path": "workspace/projects/demo/assets/hero.png",
                "entity_id": "hero_png",
                "name": "hero.png",
                "entity_type": "sprite",
                "position": [12.0, 34.0],
            },
            registry=registry,
        )

        self.assertTrue(ok)
        self.assertEqual(len(registry.calls), 1)
        command_id, payload = registry.calls[0]
        self.assertEqual(command_id, "asset.apply_to_scene")
        self.assertEqual(payload["entity_type"], "sprite")
        self.assertEqual(payload["position"], [12.0, 34.0])

    def test_external_asset_import_routes_through_asset_import_command(self):
        registry = _Registry({"ok": True, "result": {"path": "workspace/projects/demo/assets/hero.png"}})

        result = SceneViewport._run_asset_import_command(
            {
                "project_path": "workspace/projects/demo",
                "source_path": "C:/outside/hero.png",
                "target_folder": "assets",
                "name": "hero.png",
            },
            registry=registry,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(registry.calls[0][0], "asset.import")
        self.assertEqual(registry.calls[0][1]["target_folder"], "assets")

    def test_prefab_placement_routes_through_prefab_command(self):
        registry = _Registry()

        ok = SceneViewport._run_scene_placement_command(
            "prefab.place",
            {
                "scene_path": "workspace/projects/demo/scenes/main.pond",
                "prefab_path": "workspace/projects/demo/assets/prefabs/crate.json",
                "entity_id": "crate_json",
                "position": [1.0, 2.0],
            },
            registry=registry,
        )

        self.assertTrue(ok)
        self.assertEqual(registry.calls[0][0], "prefab.place")
        self.assertEqual(registry.calls[0][1]["entity_id"], "crate_json")

    def test_command_failure_returns_false_for_legacy_fallback(self):
        registry = _Registry({"ok": False, "error": {"code": "asset_not_found"}})

        ok = SceneViewport._run_scene_placement_command(
            "asset.apply_to_scene",
            {
                "scene_path": "workspace/projects/demo/scenes/main.pond",
                "asset_path": "workspace/projects/demo/assets/missing.png",
                "entity_id": "missing_png",
            },
            registry=registry,
        )

        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
