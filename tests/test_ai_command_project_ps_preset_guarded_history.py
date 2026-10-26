# -*- coding: utf-8 -*-
"""Project PS preset history must restore exact manifests with stale-state guards."""
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


class ProjectPsExperimentPresetGuardedHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="project_ps_preset_history_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        self.project.mkdir(parents=True)
        self._write_project(
            {
                "name": "Preset History",
                "active_scene": "main.pond",
                "unrelated": {"keep": True},
            }
        )
        self.registry = reset_command_registry()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_memory_undo_redo_normalizes_and_restores_absent_field(self) -> None:
        applied = self._set_preset(r"experiments\quick.json")
        self.assertTrue(applied["ok"], applied)
        self.assertEqual(applied["result"]["ps_experiment_preset"], "experiments/quick.json")
        self.assertFalse(applied["result"]["history_previous_preset_present"])
        self.assertIsNone(applied["result"]["history_previous_preset_value"])
        self.assertEqual(self._project_data()["ps_experiment_preset"], "experiments/quick.json")

        undone = self.registry.undo_last()
        self.assertTrue(undone["ok"], undone)
        self.assertNotIn("ps_experiment_preset", self._project_data())

        redone = self.registry.redo_last()
        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._project_data()["ps_experiment_preset"], "experiments/quick.json")
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute", "undo", "redo"])

    def test_durable_undo_redo_replays_without_preset_source(self) -> None:
        applied = self._set_preset("experiments/nonexistent.json")
        self.assertTrue(applied["ok"], applied)
        source_audit_id = applied["result"]["audit_id"]

        undone = reset_command_registry().run(
            "command.undo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(undone["result"]["source_audit_id"], source_audit_id)
        self.assertNotIn("ps_experiment_preset", self._project_data())

        redone = reset_command_registry().run(
            "command.redo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self._project_data()["ps_experiment_preset"], "experiments/nonexistent.json")
        self.assertEqual(
            [entry["action"] for entry in self._audit_entries()],
            ["execute", "durable_undo", "durable_redo"],
        )

    def test_durable_undo_rejects_unrelated_manifest_change_before_write_or_audit(self) -> None:
        applied = self._set_preset("experiments/quick.json")
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
        self.assertEqual(rejected["error"]["code"], "stale_project_ps_experiment_preset")
        self.assertEqual(write_json.call_count, 0)
        self.assertEqual(self._project_path().read_text(encoding="utf-8"), stale_text)
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute"])

    def test_durable_redo_rejects_unrelated_post_undo_change_and_retries_after_restore(self) -> None:
        applied = self._set_preset("experiments/quick.json")
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
        self.assertEqual(rejected["error"]["code"], "stale_project_ps_experiment_preset")
        self.assertEqual(write_json.call_count, 0)
        self.assertEqual(self._project_path().read_text(encoding="utf-8"), stale_text)
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute", "durable_undo"])

        self._write_project(canonical_post_undo)
        retried = reset_command_registry().run(
            "command.redo_project", {"project_path": str(self.project)}
        )
        self.assertTrue(retried["ok"], retried)
        self.assertEqual(self._project_data()["ps_experiment_preset"], "experiments/quick.json")
        self.assertEqual(
            [entry["action"] for entry in self._audit_entries()],
            ["execute", "durable_undo", "durable_redo"],
        )

    def test_undo_restores_prior_non_string_value_exactly(self) -> None:
        original = self._project_data()
        original["ps_experiment_preset"] = {"legacy": True, "version": 1}
        self._write_project(original)

        applied = self._set_preset("experiments/quick.json")
        self.assertTrue(applied["ok"], applied)
        undone = self.registry.undo_last()
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(self._project_data()["ps_experiment_preset"], {"legacy": True, "version": 1})

    def test_direct_command_remains_compatible_without_expected_project(self) -> None:
        result = self._set_preset("experiments/quick.json")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["events"], ["ps_experiment_preset_changed"])

    def _set_preset(self, preset_path: str) -> dict:
        return self.registry.run(
            "project.set_ps_experiment_preset",
            {"project_path": str(self.project), "preset_path": preset_path},
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
