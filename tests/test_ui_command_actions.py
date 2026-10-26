# -*- coding: utf-8 -*-
"""Editor undo/redo UI actions should call the shared command registry path."""
from __future__ import annotations

import unittest
import os

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget


class _ShortcutManager:
    def __init__(self) -> None:
        self.registered: dict[str, dict] = {}

    def register_shortcut(self, shortcut_id, callback, description="", context=None, key_sequence=None):
        self.registered[shortcut_id] = {
            "callback": callback,
            "description": description,
            "context": context,
            "key_sequence": key_sequence,
        }


class _Registry:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def run(self, command_id, payload):
        self.calls.append((command_id, payload))
        return {"ok": True, "result": {}, "events": [], "warnings": [], "error": None}


class UiCommandActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def test_registers_editor_undo_redo_actions_against_command_registry(self) -> None:
        from core.VitaLoom.ui.command_actions import register_editor_command_actions

        shortcuts = _ShortcutManager()
        registry = _Registry()

        actions = register_editor_command_actions(
            shortcut_manager=shortcuts,
            registry=registry,
            context="main-window",
        )

        self.assertEqual(actions, {"undo": "edit.undo", "redo": "edit.redo"})
        self.assertIn("edit.undo", shortcuts.registered)
        self.assertIn("edit.redo", shortcuts.registered)
        self.assertEqual(shortcuts.registered["edit.undo"]["context"], "main-window")

        shortcuts.registered["edit.undo"]["callback"]()
        shortcuts.registered["edit.redo"]["callback"]()

        self.assertEqual(
            registry.calls,
            [("command.undo", {}), ("command.redo", {})],
        )

    def test_history_actions_reopen_the_affected_scene_after_registry_undo_redo(self) -> None:
        from core.VitaLoom.ui.command_actions import register_editor_command_actions

        class _HistoryRegistry(_Registry):
            def run(self, command_id, payload):
                self.calls.append((command_id, payload))
                if command_id in {"command.undo", "command.redo"}:
                    return {
                        "ok": True,
                        "result": {"scene_path": "workspace/projects/demo/scenes/main.pond"},
                        "events": [],
                        "warnings": [],
                        "error": None,
                    }
                return {"ok": True, "result": {}, "events": [], "warnings": [], "error": None}

        shortcuts = _ShortcutManager()
        registry = _HistoryRegistry()
        register_editor_command_actions(shortcut_manager=shortcuts, registry=registry, context="main-window")

        shortcuts.registered["edit.undo"]["callback"]()
        shortcuts.registered["edit.redo"]["callback"]()

        self.assertEqual(
            registry.calls,
            [
                ("command.undo", {}),
                ("scene.open", {"scene_path": "workspace/projects/demo/scenes/main.pond"}),
                ("command.redo", {}),
                ("scene.open", {"scene_path": "workspace/projects/demo/scenes/main.pond"}),
            ],
        )

    def test_history_actions_do_not_reopen_scene_when_history_result_opt_out_is_explicit(self) -> None:
        from core.VitaLoom.ui.command_actions import register_editor_command_actions

        class _ManifestOnlyHistoryRegistry(_Registry):
            def run(self, command_id, payload):
                self.calls.append((command_id, payload))
                return {
                    "ok": True,
                    "result": {
                        "scene_path": "workspace/projects/demo/scenes/main.pond",
                        "history_rehydrate_scene": False,
                    },
                    "events": [],
                    "warnings": [],
                    "error": None,
                }

        shortcuts = _ShortcutManager()
        registry = _ManifestOnlyHistoryRegistry()
        register_editor_command_actions(shortcut_manager=shortcuts, registry=registry, context="main-window")

        shortcuts.registered["edit.undo"]["callback"]()
        shortcuts.registered["edit.redo"]["callback"]()

        self.assertEqual(registry.calls, [("command.undo", {}), ("command.redo", {})])

    def test_history_actions_mirror_opted_out_scene_save_snapshot_without_scene_open(self) -> None:
        from core.VitaLoom.ui.command_actions import register_editor_command_actions
        from unittest.mock import Mock, patch

        scene_path = "workspace/projects/demo/scenes/main.pond"
        snapshot = {"name": "main", "nested": {"value": 1}}

        class _SceneSaveHistoryRegistry(_Registry):
            def run(self, command_id, payload):
                self.calls.append((command_id, payload))
                return {
                    "ok": True,
                    "result": {
                        "scene_path": scene_path,
                        "scene_data": snapshot,
                        "history_rehydrate_scene": False,
                        "history_sync_host_scene": True,
                    },
                    "events": [],
                    "warnings": [],
                    "error": None,
                }

        shortcuts = _ShortcutManager()
        registry = _SceneSaveHistoryRegistry()
        manager = Mock()
        with patch("core.VitaLoom.scene.scene_manager.get_scene_manager", return_value=manager):
            register_editor_command_actions(shortcut_manager=shortcuts, registry=registry, context="main-window")
            shortcuts.registered["edit.undo"]["callback"]()
            shortcuts.registered["edit.redo"]["callback"]()

        self.assertEqual(registry.calls, [("command.undo", {}), ("command.redo", {})])
        self.assertEqual(manager.commit_persisted_scene.call_count, 2)
        for call in manager.commit_persisted_scene.call_args_list:
            self.assertEqual(call.args[0], scene_path)
            self.assertEqual(call.args[1], snapshot)
            self.assertIsNot(call.args[1], snapshot)

    def test_host_mirror_failure_does_not_reopen_or_raise(self) -> None:
        from core.VitaLoom.ui.command_actions import register_editor_command_actions
        from unittest.mock import Mock, patch

        class _SceneSaveHistoryRegistry(_Registry):
            def run(self, command_id, payload):
                self.calls.append((command_id, payload))
                return {
                    "ok": True,
                    "result": {
                        "scene_path": "workspace/projects/demo/scenes/main.pond",
                        "scene_data": {"name": "main"},
                        "history_rehydrate_scene": False,
                        "history_sync_host_scene": True,
                    },
                    "events": [],
                    "warnings": [],
                    "error": None,
                }

        shortcuts = _ShortcutManager()
        registry = _SceneSaveHistoryRegistry()
        manager = Mock()
        manager.commit_persisted_scene.side_effect = RuntimeError("host unavailable")
        with patch("core.VitaLoom.scene.scene_manager.get_scene_manager", return_value=manager):
            register_editor_command_actions(shortcut_manager=shortcuts, registry=registry, context="main-window")
            shortcuts.registered["edit.undo"]["callback"]()

        self.assertEqual(registry.calls, [("command.undo", {})])
        manager.commit_persisted_scene.assert_called_once()

    def test_rejected_history_never_mirrors_or_reopens_scene(self) -> None:
        from core.VitaLoom.ui.command_actions import register_editor_command_actions
        from unittest.mock import Mock, patch

        class _RejectedHistoryRegistry(_Registry):
            def run(self, command_id, payload):
                self.calls.append((command_id, payload))
                return {
                    "ok": False,
                    "result": {
                        "scene_path": "workspace/projects/demo/scenes/main.pond",
                        "scene_data": {"name": "stale"},
                        "history_rehydrate_scene": False,
                        "history_sync_host_scene": True,
                    },
                    "events": [],
                    "warnings": [],
                    "error": {"code": "stale_scene_snapshot"},
                }

        shortcuts = _ShortcutManager()
        registry = _RejectedHistoryRegistry()
        manager = Mock()
        with patch("core.VitaLoom.scene.scene_manager.get_scene_manager", return_value=manager):
            register_editor_command_actions(shortcut_manager=shortcuts, registry=registry, context="main-window")
            shortcuts.registered["edit.undo"]["callback"]()

        self.assertEqual(registry.calls, [("command.undo", {})])
        manager.commit_persisted_scene.assert_not_called()

    def test_editor_kernel_core_action_hook_registers_with_self_context(self) -> None:
        from core.VitaLoom.kernel.editor_kernel import EditorKernel
        import core.VitaLoom.ui.command_actions as command_actions

        calls = []
        original = command_actions.register_editor_command_actions

        def fake_register(*, context=None, **kwargs):
            calls.append({"context": context, "kwargs": kwargs})
            return {"undo": "edit.undo", "redo": "edit.redo"}

        try:
            command_actions.register_editor_command_actions = fake_register
            kernel = type("KernelStub", (), {})()
            EditorKernel._register_core_command_actions(kernel)
        finally:
            command_actions.register_editor_command_actions = original

        self.assertEqual(calls, [{"context": kernel, "kwargs": {"layout_manager": None}}])

    def test_live_menu_and_toolbar_actions_trigger_command_registry(self) -> None:
        from core.VitaLoom.kernel.layout_manager import LayoutManager
        from core.VitaLoom.ui.command_actions import register_editor_command_actions

        window = QMainWindow()
        window.central_stack = QStackedWidget()
        window.setCentralWidget(window.central_stack)
        layout = LayoutManager(window)
        shortcuts = _ShortcutManager()
        registry = _Registry()

        actions = register_editor_command_actions(
            shortcut_manager=shortcuts,
            registry=registry,
            context=window,
            layout_manager=layout,
        )

        self.assertEqual(actions["undo"], "edit.undo")
        self.assertEqual(actions["redo"], "edit.redo")
        self.assertIn("edit.undo", shortcuts.registered)
        self.assertIn("edit.redo", shortcuts.registered)

        edit_menu = self._menu(layout, "Edit")
        self.assertIsNotNone(edit_menu)
        menu_undo = self._action(edit_menu.actions(), "Undo")
        menu_redo = self._action(edit_menu.actions(), "Redo")
        toolbar_undo = self._action(layout.toolbar.actions(), "Undo")
        toolbar_redo = self._action(layout.toolbar.actions(), "Redo")

        for action in (menu_undo, menu_redo, toolbar_undo, toolbar_redo):
            self.assertIsNotNone(action)
            action.trigger()

        self.assertEqual(
            registry.calls,
            [
                ("command.undo", {}),
                ("command.redo", {}),
                ("command.undo", {}),
                ("command.redo", {}),
            ],
        )

    def _menu(self, layout, text):
        for action in layout.menubar.actions():
            if action.text() == text and action.menu():
                return action.menu()
        return None

    def _action(self, actions, text):
        for action in actions:
            if action.text() == text:
                return action
        return None


if __name__ == "__main__":
    unittest.main()
