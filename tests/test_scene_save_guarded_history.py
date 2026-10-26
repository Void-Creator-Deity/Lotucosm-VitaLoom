# -*- coding: utf-8 -*-
"""Guarded scene.save history remains exact, durable, and host-isolated."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from datetime import datetime as RealDatetime
from pathlib import Path
from unittest.mock import Mock, patch

from core.VitaLoom.commands import runtime_commands
from core.VitaLoom.commands.registry import reset_command_registry


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


class _SequencedClock:
    calls = 0

    @classmethod
    def now(cls) -> RealDatetime:
        cls.calls += 1
        return RealDatetime(2026, 8, 1, 12, 0, cls.calls)


class SceneSaveGuardedHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="scene_save_history_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        self.scene = self.project / "scenes" / "main.pond"
        self.scene.parent.mkdir(parents=True)
        self.project.joinpath("project.json").write_text(json.dumps({"name": "Scene Save History"}), encoding="utf-8")
        self.original = {
            "name": "main",
            "entities": [{"id": "root", "meta": {"stable": True}}],
            "nested": {"items": [1, {"value": "before"}]},
            "modified_at": "2020-01-01 00:00:00",
        }
        self._write_scene(self.original)
        self.registry = reset_command_registry()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_memory_undo_redo_restores_exact_snapshot_and_preserves_modified_at(self) -> None:
        source = {
            "name": "main",
            "entities": [{"id": "root", "meta": {"stable": False}}],
            "nested": {"items": [2, {"value": "after"}]},
            "modified_at": "caller value must be replaced on direct save",
        }
        _SequencedClock.calls = 0
        with patch.object(runtime_commands, "datetime", _SequencedClock):
            applied = self.registry.run("scene.save", {"scene_path": str(self.scene), "data": source})
            self.assertTrue(applied["ok"], applied)
            executed = applied["result"]["scene_data"]
            source["nested"]["items"][1]["value"] = "caller-mutated"
            self.assertEqual(self._scene_data(), executed)
            self.assertEqual(executed["modified_at"], "2026-08-01 12:00:01")
            self.assertFalse(applied["result"]["history_rehydrate_scene"])
            self.assertTrue(applied["result"]["history_sync_host_scene"])

            undone = self.registry.undo_last()
            self.assertTrue(undone["ok"], undone)
            self.assertFalse(undone["result"]["history_rehydrate_scene"])
            self.assertTrue(undone["result"]["history_sync_host_scene"])
            self.assertEqual(self._scene_data(), self.original)

            redone = self.registry.redo_last()
            self.assertTrue(redone["ok"], redone)
            self.assertFalse(redone["result"]["history_rehydrate_scene"])
            self.assertTrue(redone["result"]["history_sync_host_scene"])

        self.assertEqual(_SequencedClock.calls, 1, "history redo must not create a new modified_at timestamp")
        self.assertEqual(self._scene_data(), executed)
        self.assertEqual(
            [entry["action"] for entry in self._audit_entries()],
            ["execute", "undo", "redo"],
        )

    def test_fresh_registry_durable_undo_redo_replays_exact_snapshot(self) -> None:
        source = {"name": "main", "entities": [{"id": "durable"}], "nested": {"v": [1, 2]}}
        _SequencedClock.calls = 0
        with patch.object(runtime_commands, "datetime", _SequencedClock):
            applied = self.registry.run("scene.save", {"scene_path": str(self.scene), "data": source})
            self.assertTrue(applied["ok"], applied)
            executed = applied["result"]["scene_data"]
            source_audit_id = applied["result"]["audit_id"]

            undone = reset_command_registry().run("command.undo_project", {"project_path": str(self.project)})
            self.assertTrue(undone["ok"], undone)
            self.assertEqual(undone["result"]["source_audit_id"], source_audit_id)
            self.assertFalse(undone["result"]["history_rehydrate_scene"])
            self.assertEqual(self._scene_data(), self.original)

            redone = reset_command_registry().run("command.redo_project", {"project_path": str(self.project)})
            self.assertTrue(redone["ok"], redone)
            self.assertFalse(redone["result"]["history_rehydrate_scene"])

        self.assertEqual(_SequencedClock.calls, 1)
        self.assertEqual(self._scene_data(), executed)
        self.assertEqual(
            [entry["action"] for entry in self._audit_entries()],
            ["execute", "durable_undo", "durable_redo"],
        )

    def test_stale_undo_rejects_before_replace_audit_or_host_effect(self) -> None:
        applied = self.registry.run("scene.save", {"scene_path": str(self.scene), "data": {"name": "saved"}})
        self.assertTrue(applied["ok"], applied)
        self._write_scene({"name": "external", "nested": {"changed": True}})
        before = self.scene.read_text(encoding="utf-8")
        manager = Mock()
        event_bus = Mock()
        command_stack = Mock()
        context = {"scene_manager": manager, "event_bus": event_bus, "command_stack": command_stack, "load_scene": Mock()}

        with patch("core.VitaLoom.scene.scene_persistence.os.replace", wraps=__import__("os").replace) as replace:
            rejected = reset_command_registry().run(
                "command.undo_project", {"project_path": str(self.project)}, context=context
            )

        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["code"], "stale_scene_snapshot")
        self.assertEqual(replace.call_count, 0)
        self.assertEqual(self.scene.read_text(encoding="utf-8"), before)
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute"])
        manager.assert_not_called()
        event_bus.assert_not_called()
        command_stack.assert_not_called()
        context["load_scene"].assert_not_called()

    def test_stale_redo_rejects_then_canonical_retry_replays_the_captured_snapshot(self) -> None:
        applied = self.registry.run("scene.save", {"scene_path": str(self.scene), "data": {"name": "saved", "v": 1}})
        self.assertTrue(applied["ok"], applied)
        executed = applied["result"]["scene_data"]
        undone = self.registry.undo_last()
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(self._scene_data(), self.original)

        self._write_scene({"name": "external"})
        before = self.scene.read_text(encoding="utf-8")
        with patch("core.VitaLoom.scene.scene_persistence.os.replace", wraps=__import__("os").replace) as replace:
            rejected = self.registry.redo_last()
        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["code"], "stale_scene_snapshot")
        self.assertEqual(replace.call_count, 0)
        self.assertEqual(self.scene.read_text(encoding="utf-8"), before)
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute", "undo"])

        self._write_scene(self.original)
        retried = self.registry.redo_last()
        self.assertTrue(retried["ok"], retried)
        self.assertEqual(self._scene_data(), executed)
        self.assertEqual([entry["action"] for entry in self._audit_entries()], ["execute", "undo", "redo"])

    def test_project_history_selection_is_isolated_to_the_scene_project(self) -> None:
        applied = self.registry.run("scene.save", {"scene_path": str(self.scene), "data": {"name": "saved"}})
        self.assertTrue(applied["ok"], applied)
        other_project = self.tmp / "other"
        other_scene = other_project / "scenes" / "other.pond"
        other_scene.parent.mkdir(parents=True)
        other_project.joinpath("project.json").write_text(json.dumps({"name": "Other"}), encoding="utf-8")
        other_scene.write_text(json.dumps({"name": "other"}), encoding="utf-8")

        other_result = reset_command_registry().run("command.undo_project", {"project_path": str(other_project)})
        self.assertFalse(other_result["ok"])
        self.assertEqual(other_result["error"]["code"], "audit_history_missing")
        self.assertEqual(self._scene_data()["name"], "saved")
        self.assertEqual(len(self._audit_entries()), 1)

    def _write_scene(self, data: dict) -> None:
        self.scene.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _scene_data(self) -> dict:
        return json.loads(self.scene.read_text(encoding="utf-8"))

    def _audit_entries(self) -> list[dict]:
        audit = self.project / ".vitaloom" / "command_audit.jsonl"
        return [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines() if line.strip()]


if __name__ == "__main__":
    unittest.main()
