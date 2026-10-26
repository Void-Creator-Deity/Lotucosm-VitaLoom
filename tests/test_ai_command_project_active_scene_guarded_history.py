# -*- coding: utf-8 -*-
"""Project active-scene history stays manifest-only and guarded."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from core.VitaLoom.commands import runtime_commands
from core.VitaLoom.commands.registry import reset_command_registry


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


class ProjectActiveSceneGuardedHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="project_active_scene_history_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        self.project.mkdir(parents=True)
        self.scenes = self.project / "scenes"
        self.scenes.mkdir()
        self.main_scene = self.scenes / "main.pond"
        self.alt_scene = self.scenes / "alt.pond"
        self.main_scene.write_text("{}", encoding="utf-8")
        self.alt_scene.write_text("{}", encoding="utf-8")
        self._write_project({"name": "Active Scene History", "active_scene": "main.pond", "unrelated": {"keep": True}})
        self.registry = reset_command_registry()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_memory_undo_redo_restores_active_scene_without_host_rehydrate(self) -> None:
        applied = self._set_active(self.alt_scene)
        self.assertTrue(applied["ok"], applied)
        self.assertTrue(applied["result"]["history_previous_active_scene_present"])
        self.assertEqual(applied["result"]["history_previous_active_scene_value"], "main.pond")
        self.assertFalse(applied["result"]["history_rehydrate_scene"])
        self.assertEqual(self._project_data()["active_scene"], "alt.pond")

        undone = self.registry.undo_last()
        self.assertTrue(undone["ok"], undone)
        self.assertFalse(undone["result"]["history_rehydrate_scene"])
        self.assertEqual(self._project_data()["active_scene"], "main.pond")

        redone = self.registry.redo_last()
        self.assertTrue(redone["ok"], redone)
        self.assertFalse(redone["result"]["history_rehydrate_scene"])
        self.assertEqual(self._project_data()["active_scene"], "alt.pond")
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute", "undo", "redo"])

    def test_durable_undo_redo_from_fresh_registries(self) -> None:
        applied = self._set_active(self.alt_scene)
        self.assertTrue(applied["ok"], applied)
        source_audit_id = applied["result"]["audit_id"]

        undone = reset_command_registry().run("command.undo_project", {"project_path": str(self.project)})
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(undone["result"]["source_audit_id"], source_audit_id)
        self.assertFalse(undone["result"]["history_rehydrate_scene"])
        self.assertEqual(self._project_data()["active_scene"], "main.pond")

        redone = reset_command_registry().run("command.redo_project", {"project_path": str(self.project)})
        self.assertTrue(redone["ok"], redone)
        self.assertFalse(redone["result"]["history_rehydrate_scene"])
        self.assertEqual(self._project_data()["active_scene"], "alt.pond")
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute", "durable_undo", "durable_redo"])

    def test_stale_undo_rejects_before_write_audit_or_host_side_effect(self) -> None:
        manager = Mock()
        event_bus = Mock()
        stack = Mock()
        context = {"scene_manager": manager, "event_bus": event_bus, "command_stack": stack, "load_scene": Mock()}
        applied = self.registry.run(
            "project.set_active_scene",
            {"project_path": str(self.project), "scene_path": str(self.alt_scene)},
            context=context,
        )
        self.assertTrue(applied["ok"], applied)
        divergent = self._project_data()
        divergent["unrelated"] = {"keep": False, "external": "change"}
        self._write_project(divergent)
        stale_text = self._project_path().read_text(encoding="utf-8")

        with patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
            rejected = reset_command_registry().run(
                "command.undo_project", {"project_path": str(self.project)}, context=context
            )

        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["code"], "stale_project_active_scene")
        self.assertEqual(write_json.call_count, 0)
        self.assertEqual(self._project_path().read_text(encoding="utf-8"), stale_text)
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute"])
        manager.assert_not_called()
        event_bus.assert_not_called()
        stack.assert_not_called()
        context["load_scene"].assert_not_called()

    def test_stale_redo_rejects_then_retries_after_canonical_restore(self) -> None:
        applied = self._set_active(self.alt_scene)
        self.assertTrue(applied["ok"], applied)
        undone = reset_command_registry().run("command.undo_project", {"project_path": str(self.project)})
        self.assertTrue(undone["ok"], undone)
        canonical_post_undo = self._project_data()

        divergent = json.loads(json.dumps(canonical_post_undo))
        divergent["unrelated"] = {"keep": True, "external": "change"}
        self._write_project(divergent)
        stale_text = self._project_path().read_text(encoding="utf-8")
        with patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json:
            rejected = reset_command_registry().run("command.redo_project", {"project_path": str(self.project)})

        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["code"], "stale_project_active_scene")
        self.assertEqual(write_json.call_count, 0)
        self.assertEqual(self._project_path().read_text(encoding="utf-8"), stale_text)
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute", "durable_undo"])

        self._write_project(canonical_post_undo)
        retried = reset_command_registry().run("command.redo_project", {"project_path": str(self.project)})
        self.assertTrue(retried["ok"], retried)
        self.assertEqual(self._project_data()["active_scene"], "alt.pond")

    def test_undo_deletes_absent_key_and_restores_legacy_value_exactly(self) -> None:
        absent = self._project_data()
        absent.pop("active_scene")
        self._write_project(absent)
        self.assertTrue(self._set_active(self.alt_scene)["ok"])
        self.assertTrue(self.registry.undo_last()["ok"])
        self.assertNotIn("active_scene", self._project_data())

        legacy = self._project_data()
        legacy["active_scene"] = ["legacy", {"scene": "old"}]
        self._write_project(legacy)
        self.assertTrue(self._set_active(self.alt_scene)["ok"])
        self.assertTrue(self.registry.undo_last()["ok"])
        self.assertEqual(self._project_data()["active_scene"], ["legacy", {"scene": "old"}])

    def test_cross_project_history_does_not_touch_other_manifest(self) -> None:
        other = self.tmp / "other"
        other_scenes = other / "scenes"
        other_scenes.mkdir(parents=True)
        other_main = other_scenes / "other.pond"
        other_main.write_text("{}", encoding="utf-8")
        (other / "project.json").write_text(json.dumps({"name": "Other", "active_scene": "other.pond"}), encoding="utf-8")
        other_before = (other / "project.json").read_text(encoding="utf-8")

        self.assertTrue(self._set_active(self.alt_scene)["ok"])
        self.assertTrue(self.registry.undo_last()["ok"])
        self.assertEqual((other / "project.json").read_text(encoding="utf-8"), other_before)

    def test_direct_compatibility_keeps_scene_result_and_ignores_load_scene(self) -> None:
        load_scene = Mock()
        result = self.registry.run(
            "project.set_active_scene",
            {"project_path": str(self.project), "scene_path": str(self.alt_scene)},
            context={"load_scene": load_scene},
        )
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["result"]["scene_path"], str(self.alt_scene))
        self.assertEqual(result["result"]["scene_loaded"], False)
        self.assertEqual(result["events"], ["active_scene_changed"])
        load_scene.assert_not_called()

    def _set_active(self, scene: Path) -> dict:
        return self.registry.run(
            "project.set_active_scene", {"project_path": str(self.project), "scene_path": str(scene)}
        )

    def _project_path(self) -> Path:
        return self.project / "project.json"

    def _project_data(self) -> dict:
        return json.loads(self._project_path().read_text(encoding="utf-8"))

    def _write_project(self, data: dict) -> None:
        self._project_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _audit_entries(self) -> list[dict]:
        audit_path = self.project / ".vitaloom" / "command_audit.jsonl"
        return [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]


if __name__ == "__main__":
    unittest.main()
