# -*- coding: utf-8 -*-
"""Mutating AI scene commands should write durable project audit history."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.VitaLoom.commands.registry import reset_command_registry


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


class AiCommandAuditHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = reset_command_registry()
        self.tmp = Path(tempfile.mkdtemp(prefix="ai_command_audit_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        self.scene = self.project / "scenes" / "main.pond"
        self.scene.parent.mkdir(parents=True)
        (self.project / "project.json").write_text(
            json.dumps(
                {
                    "name": "Audit Test",
                    "active_scene": "main.pond",
                    "suite_id": "lotucosm.vitaloom.suite",
                    "product_id": "lotucosm-vitaloom",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
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
                            "rotation": 0.0,
                            "scale": [1.0, 1.0],
                            "scripts": [
                                {
                                    "name": "brain",
                                    "type": "Brain",
                                    "properties": {"mind": {"level": 1}},
                                }
                            ],
                        }
                    ],
                    "components": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_scene_edit_commands_append_project_audit_history(self) -> None:
        create = self.registry.run(
            "entity.create",
            {
                "scene_path": str(self.scene),
                "entity": {"id": "crate", "type": "game_prop", "position": [3.0, 4.0]},
            },
        )
        transform = self.registry.run(
            "transform.set",
            {
                "scene_path": str(self.scene),
                "entity_id": "hero",
                "position": [7.0, 8.0],
            },
        )
        scripted = self.registry.run(
            "script.set_property",
            {
                "scene_path": str(self.scene),
                "entity_id": "hero",
                "script": "brain",
                "property_path": "mind.level",
                "value": 5,
            },
        )

        results = [create, transform, scripted]
        for result in results:
            self.assertTrue(result["ok"], result)
            self.assertIn("audit_id", result["result"])
            self.assertIn("audit_path", result["result"])

        audit_path = self.project / ".vitaloom" / "command_audit.jsonl"
        self.assertTrue(audit_path.is_file())
        entries = [
            json.loads(line)
            for line in audit_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(
            [entry["command_id"] for entry in entries],
            ["entity.create", "transform.set", "script.set_property"],
        )
        self.assertEqual([entry["audit_id"] for entry in entries], [r["result"]["audit_id"] for r in results])
        for entry in entries:
            self.assertEqual(entry["project_path"], str(self.project))
            self.assertIn("payload", entry)
            self.assertIn("result", entry)
            self.assertIsInstance(entry["events"], list)
            self.assertTrue(entry["undoable"])


if __name__ == "__main__":
    unittest.main()
