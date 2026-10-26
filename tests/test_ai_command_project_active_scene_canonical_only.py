# -*- coding: utf-8 -*-
"""E194 active-scene authority and terminal-rejection contracts."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from core.VitaLoom.commands import runtime_commands
from core.VitaLoom.commands.registry import canonical_command_audit_path, reset_command_registry


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


class _NoFallback:
    def __init__(self) -> None:
        self.calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def __getattr__(self, name: str):
        def called(*args, **kwargs):
            self.calls.append(((name, *args), kwargs))
            raise AssertionError(f"Unexpected fallback invocation: {name}")

        return called


class _RegistryStub:
    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict[str, object]]] = []

    def run(self, command_id: str, payload: dict[str, object]) -> dict[str, object]:
        self.calls.append((command_id, dict(payload)))
        return self.responses.pop(0)


class ProjectActiveSceneCanonicalOnlyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = reset_command_registry()
        self.tmp = Path(tempfile.mkdtemp(prefix="e194_active_scene_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        self.scenes = self.project / "scenes"
        self.scenes.mkdir(parents=True)
        self.main = self.scenes / "main.pond"
        self.alt = self.scenes / "nested" / "alt.pond"
        self.alt.parent.mkdir()
        self.main.write_text('{"name": "Main", "entities": []}', encoding="utf-8")
        self.alt.write_text('{"name": "Alt", "entities": []}', encoding="utf-8")
        self.manifest = self.project / "project.json"
        self.manifest.write_text(
            json.dumps({"name": "E194", "active_scene": "main.pond", "kept": {"value": 1}}, indent=2),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_canonical_success_ignores_legacy_load_context_and_never_touches_host(self) -> None:
        manager = MagicMock()
        manager.load_scene.return_value = True
        scene_manager = types.ModuleType("core.VitaLoom.scene.scene_manager")
        scene_manager.get_scene_manager = MagicMock(return_value=manager)
        editor_context = SimpleNamespace(current_scene={"before": True}, current_project_path="unrelated")
        event_bus = _NoFallback()
        command_stack = _NoFallback()

        with patch.dict(sys.modules, {"core.VitaLoom.scene.scene_manager": scene_manager}):
            result = self.registry.run(
                "project.set_active_scene",
                {"project_path": str(self.project), "scene_path": str(self.alt)},
                context={
                    "load_scene": True,
                    "editor_context": editor_context,
                    "event_bus": event_bus,
                    "command_stack": command_stack,
                },
            )

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["events"], ["active_scene_changed"])
        self.assertEqual(result["result"]["active_scene"], "nested/alt.pond")
        self.assertFalse(result["result"]["scene_loaded"])
        self.assertEqual(json.loads(self.manifest.read_text(encoding="utf-8"))["active_scene"], "nested/alt.pond")
        self.assertEqual(editor_context.current_scene, {"before": True})
        self.assertEqual(editor_context.current_project_path, "unrelated")
        scene_manager.get_scene_manager.assert_not_called()
        manager.load_scene.assert_not_called()
        self.assertEqual(event_bus.calls, [])
        self.assertEqual(command_stack.calls, [])

    def test_rejected_scene_is_terminal_with_no_write_audit_or_host_rehydration(self) -> None:
        outside = self.tmp / "outside.pond"
        outside.write_text("{}", encoding="utf-8")
        before_manifest = self.manifest.read_text(encoding="utf-8")
        manager = MagicMock()
        scene_manager = types.ModuleType("core.VitaLoom.scene.scene_manager")
        scene_manager.get_scene_manager = MagicMock(return_value=manager)
        editor_context = SimpleNamespace(current_scene={"before": True}, current_project_path="unrelated")
        event_bus = _NoFallback()
        command_stack = _NoFallback()
        audit_path = canonical_command_audit_path(self.project)

        with (
            patch.object(runtime_commands, "_write_json", wraps=runtime_commands._write_json) as write_json,
            patch.dict(sys.modules, {"core.VitaLoom.scene.scene_manager": scene_manager}),
        ):
            result = self.registry.run(
                "project.set_active_scene",
                {"project_path": str(self.project), "scene_path": str(outside)},
                context={
                    "load_scene": True,
                    "editor_context": editor_context,
                    "event_bus": event_bus,
                    "command_stack": command_stack,
                },
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "scene_outside_project")
        self.assertEqual(result["events"], [])
        self.assertEqual(write_json.call_count, 0)
        self.assertEqual(self.manifest.read_text(encoding="utf-8"), before_manifest)
        self.assertFalse(audit_path.exists())
        self.assertEqual(editor_context.current_scene, {"before": True})
        self.assertEqual(editor_context.current_project_path, "unrelated")
        scene_manager.get_scene_manager.assert_not_called()
        manager.load_scene.assert_not_called()
        self.assertEqual(event_bus.calls, [])
        self.assertEqual(command_stack.calls, [])

    def test_library_browser_opens_only_after_canonical_success_and_reports_open_failure(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from core.VitaLoom.docks import library_browser

        host = SimpleNamespace(current_project_path=str(self.project))
        registry = _RegistryStub(
            [
                {"ok": True, "result": {"active_scene": "nested/alt.pond"}},
                {
                    "ok": False,
                    "result": {},
                    "error": {"code": "scene_open_failed", "message": "host refused"},
                },
            ]
        )
        with (
            patch("core.VitaLoom.commands.registry.get_command_registry", return_value=registry),
            patch.object(library_browser.logger, "warning") as warning,
        ):
            library_browser.ProjectPanel._set_active_scene(host, str(self.alt))

        self.assertEqual(
            registry.calls,
            [
                (
                    "project.set_active_scene",
                    {"project_path": str(self.project), "scene_path": str(self.alt)},
                ),
                ("scene.open", {"scene_path": str(self.alt)}),
            ],
        )
        self.assertTrue(warning.called)
        self.assertIn("scene.open failed", str(warning.call_args))

    def test_library_browser_rejection_does_not_attempt_scene_open(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from core.VitaLoom.docks import library_browser

        host = SimpleNamespace(current_project_path=str(self.project))
        registry = _RegistryStub(
            [
                {
                    "ok": False,
                    "result": {},
                    "error": {"code": "scene_outside_project", "message": "outside"},
                }
            ]
        )
        with patch("core.VitaLoom.commands.registry.get_command_registry", return_value=registry):
            library_browser.ProjectPanel._set_active_scene(host, str(self.alt))

        self.assertEqual(
            registry.calls,
            [
                (
                    "project.set_active_scene",
                    {"project_path": str(self.project), "scene_path": str(self.alt)},
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
