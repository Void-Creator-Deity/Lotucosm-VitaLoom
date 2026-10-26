# -*- coding: utf-8 -*-
"""E197 canonical scene-save authority and terminal rejection contracts."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.scene.scene_manager import SceneManager
from core.VitaLoom.scene.scene_persistence import ScenePersistenceError


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


class SceneSaveCanonicalPersistenceAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="scene_save_canonical_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        self.scene = self.project / "scenes" / "main.pond"
        self.scene.parent.mkdir(parents=True)
        (self.project / "project.json").write_text(json.dumps({"name": "Save Contract"}), encoding="utf-8")
        self.original = {"name": "main", "entities": [], "nested": {"value": 1}}
        self.scene.write_text(json.dumps(self.original, ensure_ascii=False, indent=2), encoding="utf-8")
        self.registry = reset_command_registry()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_registry_persists_explicit_snapshot_and_writes_project_audit(self) -> None:
        next_scene = {"name": "main", "entities": [{"id": "a"}], "nested": {"value": 2}}
        result = self.registry.run(
            "scene.save", {"scene_path": str(self.scene), "data": next_scene, "expected_scene": self.original}
        )

        self.assertTrue(result["ok"], result)
        persisted_scene = self._scene_data()
        self.assertEqual({key: value for key, value in persisted_scene.items() if key != "modified_at"}, next_scene)
        self.assertIsInstance(persisted_scene.get("modified_at"), str)
        self.assertEqual(result["result"]["previous_scene"], self.original)
        self.assertEqual(result["result"]["scene_data"], persisted_scene)
        self.assertFalse(result["result"]["history_rehydrate_scene"])
        self.assertEqual(result["events"], ["scene_saved"])
        entries = self._audit_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["command_id"], "scene.save")
        self.assertEqual(entries[0]["payload"]["scene_path"], str(self.scene))

    def test_stale_or_invalid_input_rejects_before_target_write_or_audit(self) -> None:
        externally_changed = {"name": "main", "entities": [{"id": "external"}]}
        self.scene.write_text(json.dumps(externally_changed), encoding="utf-8")
        before = self.scene.read_text(encoding="utf-8")
        with patch("core.VitaLoom.scene.scene_persistence.os.replace", wraps=__import__("os").replace) as replace:
            stale = self.registry.run(
                "scene.save",
                {"scene_path": str(self.scene), "data": {"name": "attempt"}, "expected_scene": self.original},
            )

        self.assertFalse(stale["ok"])
        self.assertEqual(stale["error"]["code"], "stale_scene_snapshot")
        self.assertEqual(replace.call_count, 0)
        self.assertEqual(self.scene.read_text(encoding="utf-8"), before)
        self.assertFalse((self.project / ".vitaloom" / "command_audit.jsonl").exists())

        with patch("core.VitaLoom.scene.scene_persistence.os.replace", wraps=__import__("os").replace) as replace:
            invalid = self.registry.run(
                "scene.save", {"scene_path": str(self.scene), "data": {"not_json": {1, 2}}}
            )
        self.assertFalse(invalid["ok"])
        self.assertEqual(invalid["error"]["code"], "scene_data_not_json")
        self.assertEqual(replace.call_count, 0)
        self.assertEqual(self.scene.read_text(encoding="utf-8"), before)
        self.assertFalse((self.project / ".vitaloom" / "command_audit.jsonl").exists())

    def test_rejection_never_imports_or_calls_scene_manager(self) -> None:
        with patch("core.VitaLoom.scene.scene_manager.get_scene_manager") as manager:
            rejected = self.registry.run(
                "scene.save", {"scene_path": str(self.tmp / "outside.pond"), "data": {"name": "bad"}}
            )
        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["code"], "scene_not_found")
        manager.assert_not_called()
        self.assertFalse((self.project / ".vitaloom" / "command_audit.jsonl").exists())

    def test_legacy_scene_manager_commits_host_state_only_after_persistence_success(self) -> None:
        old_data = {"name": "old"}
        new_data = {"name": "new"}
        host = SimpleNamespace(
            _current_scene_path=str(self.scene),
            _current_scene_data=old_data,
            _scene_modified=True,
            editor_context=SimpleNamespace(current_scene=old_data),
            scene_saved=Mock(),
            scene_modified=Mock(),
            signal_bus=SimpleNamespace(emit_scene_saved=Mock()),
        )
        host.commit_persisted_scene = SceneManager.commit_persisted_scene.__get__(host, type(host))

        with patch(
            "core.VitaLoom.scene.scene_persistence.persist_scene_snapshot",
            side_effect=ScenePersistenceError("scene_write_failed", "no write"),
        ):
            ok = SceneManager.save_scene(host, data=new_data)

        self.assertFalse(ok)
        self.assertEqual(host._current_scene_data, old_data)
        self.assertEqual(host.editor_context.current_scene, old_data)
        self.assertTrue(host._scene_modified)
        host.scene_saved.emit.assert_not_called()
        host.scene_modified.emit.assert_not_called()
        host.signal_bus.emit_scene_saved.assert_not_called()

    def test_standard_ui_commits_host_only_after_registry_success(self) -> None:
        from builtin.editor_extensions.standard_ui_plugin import StandardUIPlugin

        scene_data = {"name": "main", "entities": []}
        manager = SimpleNamespace(
            get_current_scene_path=lambda: str(self.scene),
            get_scene_data=lambda: scene_data,
            commit_persisted_scene=Mock(),
        )
        registry = Mock()
        persisted_scene = {**scene_data, "modified_at": "2026-08-01 00:00:00"}
        registry.run.return_value = {"ok": True, "result": {"scene_data": persisted_scene}, "events": ["scene_saved"], "warnings": []}
        plugin = StandardUIPlugin()
        plugin.kernel = SimpleNamespace(layout_manager=SimpleNamespace(viewport_providers={}))
        with (
            patch("core.VitaLoom.scene.scene_manager.get_scene_manager", return_value=manager),
            patch("core.VitaLoom.commands.registry.get_command_registry", return_value=registry),
        ):
            result = plugin.save_scene()

        self.assertTrue(result["ok"], result)
        self.assertEqual(registry.run.call_args.args, ("scene.save", {"scene_path": str(self.scene), "data": scene_data}))
        committed_path, committed_data = manager.commit_persisted_scene.call_args.args
        self.assertEqual(committed_path, str(self.scene))
        self.assertEqual({key: value for key, value in committed_data.items() if key != "modified_at"}, scene_data)
        self.assertIsInstance(committed_data.get("modified_at"), str)

    def _scene_data(self) -> dict:
        return json.loads(self.scene.read_text(encoding="utf-8"))

    def _audit_entries(self) -> list[dict]:
        audit = self.project / ".vitaloom" / "command_audit.jsonl"
        return [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines() if line.strip()]


if __name__ == "__main__":
    unittest.main()

