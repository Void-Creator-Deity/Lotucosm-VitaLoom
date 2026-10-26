# -*- coding: utf-8 -*-
"""Undo/redo must be reachable through command-facing agent paths."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.VitaLoom.commands import mcp_adapter, runtime_commands
from core.VitaLoom.commands.registry import reset_command_registry


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


class AiCommandUndoRedoCommandPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = reset_command_registry()
        self.tmp = Path(tempfile.mkdtemp(prefix="ai_command_path_undo_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        self.scene = self.project / "scenes" / "main.pond"
        self.scene.parent.mkdir(parents=True)
        (self.project / "project.json").write_text(
            json.dumps({"name": "Command Path Undo", "active_scene": "main.pond"}, indent=2),
            encoding="utf-8",
        )
        self.scene.write_text(
            json.dumps(
                {
                    "name": "Main",
                    "entities": [
                        {
                            "id": "hero",
                            "position": [1.0, 2.0],
                            "rotation": 0.0,
                            "scale": [1.0, 1.0],
                            "scripts": [],
                        }
                    ],
                    "components": [],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_command_registry_exposes_command_undo_redo_path(self) -> None:
        ids = {row["id"] for row in self.registry.list()}
        self.assertIn("command.undo", ids)
        self.assertIn("command.redo", ids)

        moved = self.registry.run(
            "transform.set",
            {
                "scene_path": str(self.scene),
                "entity_id": "hero",
                "position": [9.0, 10.0],
            },
        )
        self.assertTrue(moved["ok"], moved)
        self.assertEqual(self._hero()["position"], [9.0, 10.0])

        undone = self.registry.run("command.undo", {})
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(self._hero()["position"], [1.0, 2.0])

        redone = self.registry.run("command.redo", {})
        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._hero()["position"], [9.0, 10.0])

        actions = self._audit_actions()
        self.assertEqual(actions, ["execute", "undo", "redo"])

    def test_stale_transform_position_undo_is_rejected_without_overwriting_later_state(self) -> None:
        moved = self.registry.run("transform.set", {"scene_path": str(self.scene), "entity_id": "hero", "position": [9.0, 10.0]})
        self.assertTrue(moved["ok"], moved)
        later_write = runtime_commands._transform_set({"scene_path": str(self.scene), "entity_id": "hero", "position": [11.0, 12.0]}, {})
        self.assertTrue(later_write["ok"], later_write)

        failed_undo = self.registry.run("command.undo", {})

        self.assertFalse(failed_undo["ok"])
        self.assertEqual(failed_undo["error"]["code"], "stale_transform_position")
        self.assertEqual(self._hero()["position"], [11.0, 12.0])
        retry = self.registry.run("command.undo", {})
        self.assertFalse(retry["ok"])
        self.assertEqual(retry["error"]["code"], "stale_transform_position")

    def test_stale_transform_position_redo_is_rejected_without_overwriting_later_state(self) -> None:
        moved = self.registry.run("transform.set", {"scene_path": str(self.scene), "entity_id": "hero", "position": [9.0, 10.0]})
        self.assertTrue(moved["ok"], moved)
        undone = self.registry.run("command.undo", {})
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(self._hero()["position"], [1.0, 2.0])
        later_write = runtime_commands._transform_set({"scene_path": str(self.scene), "entity_id": "hero", "position": [4.0, 5.0]}, {})
        self.assertTrue(later_write["ok"], later_write)

        failed_redo = self.registry.run("command.redo", {})

        self.assertFalse(failed_redo["ok"])
        self.assertEqual(failed_redo["error"]["code"], "stale_transform_position")
        self.assertEqual(self._hero()["position"], [4.0, 5.0])
        retry = self.registry.run("command.redo", {})
        self.assertFalse(retry["ok"])
        self.assertEqual(retry["error"]["code"], "stale_transform_position")

    def test_transform_position_contract_rejects_invalid_or_unguarded_inputs_without_writing(self) -> None:
        original = self.scene.read_text(encoding="utf-8")
        cases = [
            ("invalid_position", {"position": [1.0]}),
            ("invalid_position", {"position": [1.0, True]}),
            ("invalid_position", {"position": [float("nan"), 2.0]}),
            ("invalid_position", {"position": [float("inf"), 2.0]}),
            ("invalid_expected_position", {"position": [3.0, 4.0], "expected_position": [1.0]}),
            ("expected_position_requires_position", {"expected_position": [1.0, 2.0]}),
        ]
        for expected_code, update in cases:
            with self.subTest(update=update), patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
                result = self.registry.run("transform.set", {"scene_path": str(self.scene), "entity_id": "hero", **update})
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], expected_code)
            self.assertEqual(write_json.call_count, 0)
            self.assertEqual(self.scene.read_text(encoding="utf-8"), original)

    def test_mcp_helpers_delegate_to_command_undo_redo(self) -> None:
        created = mcp_adapter.run_command(
            "entity.create",
            {"scene_path": str(self.scene), "entity": {"id": "crate", "position": [3.0, 4.0]}},
        )
        self.assertTrue(created["ok"], created)
        self.assertIn("crate", self._entity_ids())

        undone = mcp_adapter.undo_last()
        self.assertTrue(undone["ok"], undone)
        self.assertNotIn("crate", self._entity_ids())

        redone = mcp_adapter.redo_last()
        self.assertTrue(redone["ok"], redone)
        self.assertIn("crate", self._entity_ids())

    def _scene_data(self) -> dict:
        return json.loads(self.scene.read_text(encoding="utf-8"))

    def _hero(self) -> dict:
        return next(ent for ent in self._scene_data()["entities"] if ent.get("id") == "hero")

    def _entity_ids(self) -> list[str]:
        return [str(ent.get("id")) for ent in self._scene_data()["entities"]]

    def _audit_actions(self) -> list[str]:
        audit_path = self.project / ".vitaloom" / "command_audit.jsonl"
        return [
            json.loads(line).get("action", "execute")
            for line in audit_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


if __name__ == "__main__":
    unittest.main()
