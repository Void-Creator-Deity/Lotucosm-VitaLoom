# -*- coding: utf-8 -*-
"""Project evolution-defaults history must preserve nested JSON and stale guards."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.VitaLoom.commands import runtime_commands
from core.VitaLoom.commands.registry import reset_command_registry


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


class ProjectEvolutionDefaultsGuardedHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="project_evolution_defaults_history_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        self.project.mkdir(parents=True)
        self._write_project(
            {
                "name": "Evolution Defaults History",
                "active_scene": "main.pond",
                "unrelated": {"keep": True},
            }
        )
        self.registry = reset_command_registry()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_memory_undo_redo_preserves_detached_nested_defaults_and_absent_field(self) -> None:
        defaults = self._nested_defaults()
        applied = self._set_defaults(defaults)
        self.assertTrue(applied["ok"], applied)
        self.assertFalse(applied["result"]["history_previous_defaults_present"])
        self.assertIsNone(applied["result"]["history_previous_defaults_value"])
        expected = json.loads(json.dumps(defaults))
        self.assertEqual(self._project_data()["evolution_defaults"], expected)

        # History must keep a serialized snapshot rather than references to the
        # mutable caller mapping or its nested collections.
        defaults["genetics"]["mutation"]["rate"] = 9.9
        defaults["limits"].append(999)
        undone = self.registry.undo_last()
        self.assertTrue(undone["ok"], undone)
        self.assertNotIn("evolution_defaults", self._project_data())

        redone = self.registry.redo_last()
        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._project_data()["evolution_defaults"], expected)
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute", "undo", "redo"])

    def test_durable_undo_redo_preserves_nested_defaults(self) -> None:
        defaults = self._nested_defaults()
        applied = self._set_defaults(defaults)
        self.assertTrue(applied["ok"], applied)
        source_audit_id = applied["result"]["audit_id"]

        undone = reset_command_registry().run(
            "command.undo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(undone["result"]["source_audit_id"], source_audit_id)
        self.assertNotIn("evolution_defaults", self._project_data())

        redone = reset_command_registry().run(
            "command.redo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._project_data()["evolution_defaults"], defaults)
        self.assertEqual(
            [entry["action"] for entry in self._audit_entries()],
            ["execute", "durable_undo", "durable_redo"],
        )

    def test_durable_undo_rejects_unrelated_manifest_change_before_write_or_audit(self) -> None:
        applied = self._set_defaults(self._nested_defaults())
        self.assertTrue(applied["ok"], applied)
        divergent = self._project_data()
        divergent["unrelated"] = {"keep": False, "external": "change"}
        self._write_project(divergent)
        stale_text = self._project_path().read_text(encoding="utf-8")

        with patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
            rejected = reset_command_registry().run(
                "command.undo_project", {"project_path": str(self.project)}
            )

        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["code"], "stale_project_evolution_defaults")
        self.assertEqual(write_json.call_count, 0)
        self.assertEqual(self._project_path().read_text(encoding="utf-8"), stale_text)
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute"])

    def test_durable_redo_rejects_unrelated_post_undo_change_and_retries_after_restore(self) -> None:
        defaults = self._nested_defaults()
        applied = self._set_defaults(defaults)
        self.assertTrue(applied["ok"], applied)
        undone = reset_command_registry().run(
            "command.undo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(undone["ok"], undone)
        canonical_post_undo = self._project_data()

        divergent = json.loads(json.dumps(canonical_post_undo))
        divergent["unrelated"] = {"keep": True, "external": "change"}
        self._write_project(divergent)
        stale_text = self._project_path().read_text(encoding="utf-8")
        with patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
            rejected = reset_command_registry().run(
                "command.redo_project", {"project_path": str(self.project)}
            )

        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["code"], "stale_project_evolution_defaults")
        self.assertEqual(write_json.call_count, 0)
        self.assertEqual(self._project_path().read_text(encoding="utf-8"), stale_text)
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute", "durable_undo"])

        self._write_project(canonical_post_undo)
        retried = reset_command_registry().run(
            "command.redo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(retried["ok"], retried)
        self.assertEqual(self._project_data()["evolution_defaults"], defaults)
        self.assertEqual(
            [entry["action"] for entry in self._audit_entries()],
            ["execute", "durable_undo", "durable_redo"],
        )

    def test_undo_restores_prior_legacy_non_mapping_value_exactly(self) -> None:
        original = self._project_data()
        original["evolution_defaults"] = ["legacy", {"value": 1}]
        self._write_project(original)

        applied = self._set_defaults(self._nested_defaults())
        self.assertTrue(applied["ok"], applied)
        undone = self.registry.undo_last()
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(self._project_data()["evolution_defaults"], ["legacy", {"value": 1}])

    def test_direct_command_remains_compatible_without_expected_project(self) -> None:
        result = self._set_defaults({})
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["events"], ["evolution_defaults_changed"])
        self.assertEqual(self._project_data()["evolution_defaults"], {})

    def _nested_defaults(self) -> dict:
        return {
            "genetics": {
                "mutation": {"rate": 0.08, "modes": ["small", "structural"]},
                "selection_pressure": 0.5,
            },
            "limits": [12, 24, {"population": 42}],
            "enabled": True,
        }

    def _set_defaults(self, defaults: dict) -> dict:
        return self.registry.run(
            "project.set_evolution_defaults",
            {"project_path": str(self.project), "defaults": defaults},
        )

    def _project_path(self) -> Path:
        return self.project / "project.json"

    def _project_data(self) -> dict:
        return json.loads(self._project_path().read_text(encoding="utf-8"))

    def _write_project(self, data: dict) -> None:
        self._project_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _audit_entries(self) -> list[dict]:
        audit_path = self.project / ".vitaloom" / "command_audit.jsonl"
        return [
            json.loads(line)
            for line in audit_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


if __name__ == "__main__":
    unittest.main()
