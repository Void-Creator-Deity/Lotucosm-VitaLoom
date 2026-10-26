"""LayoutManager layout persistence, viewport lifecycle, and UI behavior tests."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDockWidget, QMainWindow, QStackedWidget, QWidget

from core.VitaLoom.kernel.editor_layout_state import EditorLayoutState
from core.VitaLoom.kernel.layout_manager import LayoutManager


class _DummyViewportProvider:
    def __init__(self, name: str):
        self._name = name
        self.activated = 0
        self.deactivated = 0

    def get_viewport_name(self):
        return self._name

    def on_viewport_activated(self):
        self.activated += 1

    def on_viewport_deactivated(self):
        self.deactivated += 1


class LayoutManagerBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.main_window = QMainWindow()
        self.main_window.central_stack = QStackedWidget()
        self.main_window.setCentralWidget(self.main_window.central_stack)
        self.layout = LayoutManager(self.main_window)
        if self.layout.viewport_tabs is not None:
            self.main_window.setCentralWidget(self.layout.viewport_tabs)

    def test_restore_layout_tolerates_partial_geometry_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = os.path.join(tmp, "layout.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "geometry": {"width": 100, "height": 100},
                        "window_state": "",
                        "dock_states": {},
                        "viewport_state": {},
                    },
                    f,
                )
            self.layout.layout_config_path = config_path
            result = self.layout.restore_layout()
            self.assertTrue(result)

    def test_state_home_can_be_overridden_for_smoke_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"VITALOOM_STATE_HOME": tmp}):
                layout = LayoutManager(self.main_window)
        self.assertEqual(
            layout.layout_config_path,
            os.path.join(tmp, "layout_config.json"),
        )
        self.assertEqual(
            layout._dock_geometry_cache_path(),
            os.path.join(tmp, "dock_geometry_cache.json"),
        )

    def test_remove_plugin_ui_cleans_menu_and_toolbar_actions(self):
        self.layout.add_menu_items(
            [{"path": "Tools/TestAction", "action": lambda: None}],
            plugin_name="plugin_test",
        )
        self.layout.add_toolbar_items(
            [{"text": "ToolAction", "action": lambda: None}],
            plugin_name="plugin_test",
        )
        tools_menu = None
        for action in self.layout.menubar.actions():
            if action.text() == "Tools" and action.menu():
                tools_menu = action.menu()
                break
        self.assertIsNotNone(tools_menu)
        self.assertTrue(any(action.text() == "TestAction" for action in tools_menu.actions()))
        self.layout.remove_plugin_ui("plugin_test")
        after_toolbar = len(self.layout.toolbar.actions())
        self.assertEqual(after_toolbar, 0)
        self.assertFalse(any(action.text() == "TestAction" for action in tools_menu.actions()))

    def test_main_toolbar_has_stable_state_object_name(self):
        self.assertEqual(self.layout.toolbar.objectName(), "MainToolbar")

    def test_remove_plugin_ui_cleans_separators_and_empty_menu_shell(self):
        self.layout.add_menu_items(
            [
                {"path": "Tools/TestAction", "action": lambda: None},
                {"path": "Tools/", "separator": True},
                {"path": "Tools/OtherAction", "action": None},
            ],
            plugin_name="plugin_sep",
        )
        self.layout.add_toolbar_items(
            [
                {"text": "ToolAction", "action": lambda: None},
                {"separator": True},
            ],
            plugin_name="plugin_sep",
        )

        before_toolbar = len(self.layout.toolbar.actions())
        self.assertGreater(before_toolbar, 0)
        self.layout.remove_plugin_ui("plugin_sep")

        self.assertEqual(len(self.layout.toolbar.actions()), 0)
        self.assertFalse(any(action.text() == "Tools" for action in self.layout.menubar.actions()))

    def test_viewport_replacement_fails_closed_when_old_runtime_cleanup_fails(self):
        class _FailingViewport(QWidget):
            def dispose_runtime_capabilities(self):
                raise RuntimeError("cleanup failed")

        old_viewport = _FailingViewport()
        replacement = QWidget()
        self.layout.add_viewport("vp", old_viewport, _DummyViewportProvider("Old"))

        self.assertFalse(self.layout.remove_viewport("vp"))

        with self.assertRaisesRegex(RuntimeError, "cannot replace viewport"):
            self.layout.add_viewport("vp", replacement, _DummyViewportProvider("New"))

        self.assertIs(self.layout.viewports["vp"], old_viewport)
        self.assertEqual(self.layout.viewport_tabs.count(), 1)
        self.assertIs(self.layout.viewport_tabs.widget(0), old_viewport)


    def test_viewport_switch_updates_current_consistently(self):
        first_provider = _DummyViewportProvider("First")
        second_provider = _DummyViewportProvider("Second")

        self.layout.add_viewport("vp1", QWidget(), first_provider)
        self.layout.add_viewport("vp2", QWidget(), second_provider)
        self.layout.switch_viewport("vp2")

        self.assertEqual(self.layout.current_viewport, "vp2")
        self.assertGreaterEqual(first_provider.deactivated, 1)
        self.assertGreaterEqual(second_provider.activated, 1)


    def test_menu_and_toolbar_accept_icon_field_without_error(self):
        from PyQt6.QtGui import QIcon

        icon = QIcon()
        self.layout.add_menu_items(
            [{"path": "Edit/IconProbe", "action": lambda: None, "icon": icon}],
            plugin_name="icon_probe",
        )
        self.layout.add_toolbar_items(
            [{"text": "IcoProbe", "action": lambda: None, "icon": icon}],
            plugin_name="icon_probe",
        )
        self.layout.remove_plugin_ui("icon_probe")


    def test_viewport_tab_projection_switch_remove_and_saved_order(self):
        self.assertIs(self.main_window.centralWidget(), self.layout.viewport_tabs)
        first = QWidget()
        second = QWidget()
        self.layout.add_viewport("vp1", first, _DummyViewportProvider("First"))
        self.layout.add_viewport("vp2", second, _DummyViewportProvider("Second"))

        tabs = self.layout.viewport_tabs
        self.assertIsNotNone(tabs)
        self.assertEqual(tabs.count(), 2)
        self.layout.switch_viewport("vp2")
        self.assertEqual(tabs.currentWidget(), second)

        tabs.tabBar().moveTab(1, 0)
        with tempfile.TemporaryDirectory() as tmp:
            self.layout.layout_config_path = os.path.join(tmp, "layout.json")
            self.assertTrue(self.layout.save_layout())
            with open(self.layout.layout_config_path, encoding="utf-8") as saved_file:
                persisted = json.load(saved_file)
            self.assertEqual(persisted["viewport_state"]["tabs_order"], ["vp2", "vp1"])
            tabs.tabBar().moveTab(0, 1)
            self.assertEqual([tabs.tabText(index) for index in range(tabs.count())], ["First", "Second"])
            with open(self.layout.layout_config_path, "w", encoding="utf-8") as saved_file:
                json.dump(persisted, saved_file)
            self.assertTrue(self.layout.restore_layout())
            self.assertEqual([tabs.tabText(index) for index in range(tabs.count())], ["Second", "First"])
            self.assertEqual(self.layout.current_viewport, "vp2")

        self.layout.remove_viewport("vp1")
        self.assertEqual(tabs.count(), 1)
        self.assertEqual(self.layout.current_viewport, "vp2")


    def test_deferred_dock_tabify_resolves_and_removal_cleans_relationship(self):
        child = QDockWidget("Timeline", self.main_window)
        self.layout.add_dock(
            child,
            {
                "title": "Timeline",
                "area": Qt.DockWidgetArea.BottomDockWidgetArea,
                "tabbed_with": "Inspector",
            },
        )
        self.assertEqual(self.layout._pending_tabify, [("Timeline", "Inspector")])

        host = QDockWidget("Inspector", self.main_window)
        self.layout.add_dock(
            host,
            {"title": "Inspector", "area": Qt.DockWidgetArea.RightDockWidgetArea},
        )
        QApplication.processEvents()
        self.assertIn(child, self.main_window.tabifiedDockWidgets(host))
        self.assertEqual(self.layout._pending_tabify, [])

        self.layout.remove_dock("Inspector")
        self.assertNotIn("Inspector", self.layout.docks)
        self.assertNotIn("Inspector", [title for pair in self.layout._pending_tabify for title in pair])

    def test_partial_layout_restores_docked_area_and_visibility_without_window_state(self):
        self.main_window.resize(900, 600)
        self.main_window.show()
        QApplication.processEvents()
        dock = QDockWidget("Inspector", self.main_window)
        self.layout.add_dock(
            dock,
            {"title": "Inspector", "area": Qt.DockWidgetArea.RightDockWidgetArea},
        )
        QApplication.processEvents()

        with tempfile.TemporaryDirectory() as tmp:
            self.layout.layout_config_path = os.path.join(tmp, "layout.json")
            self.assertTrue(self.layout.save_layout())
            with open(self.layout.layout_config_path, encoding="utf-8") as saved_file:
                persisted = json.load(saved_file)
            saved_dock_state = persisted["dock_states"]["Inspector"]
            self.assertFalse(saved_dock_state["floating"])
            self.assertEqual(saved_dock_state["area"], int(Qt.DockWidgetArea.RightDockWidgetArea.value))
            persisted["window_state"] = ""

            dock.setFloating(True)
            dock.setGeometry(120, 120, 320, 240)
            dock.hide()
            QApplication.processEvents()
            self.assertTrue(dock.isFloating())
            self.assertFalse(dock.isVisible())

            with open(self.layout.layout_config_path, "w", encoding="utf-8") as saved_file:
                json.dump(persisted, saved_file)
            self.assertTrue(self.layout.restore_layout())
            QApplication.processEvents()

        self.assertFalse(dock.isFloating())
        self.assertEqual(
            self.main_window.dockWidgetArea(dock),
            Qt.DockWidgetArea.RightDockWidgetArea,
        )
        self.assertTrue(dock.isVisible())


    def test_save_layout_uses_portable_layout_state_contract(self):
        first_provider = _DummyViewportProvider("First")
        second_provider = _DummyViewportProvider("Second")
        self.layout.add_viewport("vp1", QWidget(), first_provider)
        self.layout.add_viewport("vp2", QWidget(), second_provider)
        self.layout.switch_viewport("vp2")
        self.layout.add_dock(
            QDockWidget("Inspector", self.main_window),
            {"title": "Inspector", "default_visible": True},
        )

        with tempfile.TemporaryDirectory() as tmp:
            config_path = os.path.join(tmp, "layout.json")
            self.layout.layout_config_path = config_path
            self.assertTrue(self.layout.save_layout())
            with open(config_path, "r", encoding="utf-8") as saved_file:
                persisted = json.load(saved_file)

        state = EditorLayoutState.from_mapping(persisted)
        self.assertEqual(
            set(persisted),
            {"window_state", "geometry", "dock_states", "viewport_state"},
        )
        self.assertEqual(state.viewport_state["current"], "vp2")
        self.assertIsInstance(state.viewport_state["tabs_order"], list)
        self.assertIn("Inspector", state.dock_states)
        self.assertIn("visible", state.dock_states["Inspector"])


    def test_runtime_host_retains_declarative_viewport_until_cleanup_retry_succeeds(self):
        from types import SimpleNamespace

        from core.VitaLoom.commands.registry import (
            CommandSpec,
            command_ok,
            get_command_registry,
            reset_command_registry,
        )
        from core.VitaLoom.core.runtime_plugin_contract import (
            ICommandProvider,
            IRuntimePlugin,
        )
        from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
        from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
            LegacyEditorPluginAdapter,
        )

        class _Signal:
            def emit(self, _plugin_id):
                return None

        class RetryableViewport(QWidget):
            def __init__(self):
                super().__init__()
                self.fail_cleanup = True
                self.cleanup_attempts = 0

            def dispose_runtime_capabilities(self):
                self.cleanup_attempts += 1
                if self.fail_cleanup:
                    raise RuntimeError("simulated viewport cleanup failure")

        class RetryableViewportPlugin(IRuntimePlugin, ICommandProvider):
            def __init__(self):
                self.viewport = None
                self.unload_calls = 0

            def get_plugin_info(self):
                return {
                    "name": "RetryableViewportPlugin",
                    "version": "1.0.0",
                    "dependencies": [],
                    "provides": ["viewport", "command", "editor_contribution"],
                    "activation_context": "runtime",
                    "editor_contributions": [{
                        "id": "retryable.viewport.surface",
                        "kind": "viewport_surface",
                        "viewport_id": "RetryableViewport",
                        "name_key": "viewport.retryable.name",
                        "default_name": "Retryable Viewport",
                    }],
                }

            def get_command_specs(self):
                return [
                    CommandSpec(
                        id="retryable.viewport.command",
                        title="Retryable Viewport Command",
                        owner="declared-owner-is-normalized-by-host",
                        handler=lambda _payload, _context: command_ok(),
                    )
                ]

            def on_load(self, _runtime_context):
                return None

            def on_unload(self):
                self.unload_calls += 1

            def create_viewport_widget(self):
                self.viewport = RetryableViewport()
                return self.viewport

        reset_command_registry()
        try:
            kernel = SimpleNamespace(
                layout_manager=self.layout,
                get_context=lambda: SimpleNamespace(),
                plugin_loaded=_Signal(),
                plugin_unloaded=_Signal(),
            )
            adapter = LegacyEditorPluginAdapter(kernel)
            host = RuntimePluginHost(
                adapter=adapter,
                activation_context_resolver=lambda _info: object(),
            )
            plugin = RetryableViewportPlugin()
            host.register_plugin(plugin)

            report = host.execute_lifecycle_target(
                {"RetryableViewportPlugin"}, source="e68-test", allow_deactivate=True
            )
            self.assertEqual(report["status"], "settled")
            self.assertIs(self.layout.viewports["RetryableViewport"], plugin.viewport)
            self.assertEqual(self.layout.viewport_tabs.count(), 1)
            self.assertEqual(
                adapter._declarative_viewport_owner_by_id,
                {"RetryableViewport": "RetryableViewportPlugin"},
            )
            self.assertEqual(
                get_command_registry().describe("retryable.viewport.command")["owner"],
                "RetryableViewportPlugin",
            )

            self.assertFalse(host.unload_plugin("RetryableViewportPlugin"))
            self.assertEqual(host.loaded_plugins, {"RetryableViewportPlugin": plugin})
            self.assertEqual(plugin.unload_calls, 0)
            self.assertEqual(plugin.viewport.cleanup_attempts, 1)
            self.assertIs(self.layout.viewports["RetryableViewport"], plugin.viewport)
            self.assertEqual(self.layout.viewport_tabs.count(), 1)
            self.assertEqual(
                adapter._declarative_viewport_owner_by_id,
                {"RetryableViewport": "RetryableViewportPlugin"},
            )
            self.assertEqual(
                get_command_registry().describe("retryable.viewport.command")["owner"],
                "RetryableViewportPlugin",
            )

            plugin.viewport.fail_cleanup = False
            self.assertTrue(host.unload_plugin("RetryableViewportPlugin"))
            self.assertEqual(host.loaded_plugins, {})
            self.assertEqual(plugin.unload_calls, 1)
            self.assertEqual(plugin.viewport.cleanup_attempts, 2)
            self.assertNotIn("RetryableViewport", self.layout.viewports)
            self.assertEqual(self.layout.viewport_tabs.count(), 0)
            self.assertEqual(adapter._declarative_viewport_owner_by_id, {})
            self.assertIsNone(get_command_registry().get("retryable.viewport.command"))
        finally:
            reset_command_registry()


    def test_runtime_host_preserves_dock_until_viewport_cleanup_retry_succeeds(self):
        from types import SimpleNamespace

        from core.VitaLoom.commands.registry import (
            CommandSpec,
            command_ok,
            get_command_registry,
            reset_command_registry,
        )
        from core.VitaLoom.core.runtime_plugin_contract import (
            ICommandProvider,
            IRuntimePlugin,
        )
        from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
        from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
            LegacyEditorPluginAdapter,
        )

        class _Signal:
            def emit(self, *_args, **_kwargs) -> None:
                return None

        class RetryableViewport(QWidget):
            def __init__(self) -> None:
                super().__init__()
                self.fail_cleanup = True
                self.cleanup_attempts = 0

            def dispose_runtime_capabilities(self) -> None:
                self.cleanup_attempts += 1
                if self.fail_cleanup:
                    raise RuntimeError("simulated multi-surface viewport cleanup failure")

        class DockAndViewportPlugin(IRuntimePlugin, ICommandProvider):
            def __init__(self) -> None:
                self.dock: QDockWidget | None = None
                self.viewport: RetryableViewport | None = None
                self.unload_calls = 0

            def get_plugin_info(self):
                return {
                    "name": "DockAndViewportPlugin",
                    "version": "1.0.0",
                    "dependencies": [],
                    "provides": ["dock", "viewport", "command", "editor_contribution"],
                    "activation_context": "runtime",
                    "editor_contributions": [
                        {
                            "id": "retryable.dock.surface",
                            "kind": "dock_surface",
                            "dock_id": "RetryableDock",
                            "title_key": "dock.retryable.title",
                            "default_title": "Retryable Dock",
                            "area": "left",
                        },
                        {
                            "id": "retryable.viewport.surface",
                            "kind": "viewport_surface",
                            "viewport_id": "RetryableViewport",
                            "name_key": "viewport.retryable.name",
                            "default_name": "Retryable Viewport",
                        },
                    ],
                }

            def get_command_specs(self):
                return [
                    CommandSpec(
                        id="retryable.multi_surface.command",
                        title="Retryable Multi-Surface Command",
                        owner="declared-owner-is-normalized-by-host",
                        handler=lambda _payload, _context: command_ok(),
                    )
                ]

            def on_load(self, _runtime_context):
                return None

            def on_unload(self):
                self.unload_calls += 1

            def create_dock_widget(self):
                self.dock = QDockWidget("Retryable Dock")
                self.dock.setWidget(QWidget())
                return self.dock

            def create_viewport_widget(self):
                self.viewport = RetryableViewport()
                return self.viewport

        reset_command_registry()
        try:
            kernel = SimpleNamespace(
                layout_manager=self.layout,
                get_context=lambda: SimpleNamespace(),
                plugin_loaded=_Signal(),
                plugin_unloaded=_Signal(),
            )
            adapter = LegacyEditorPluginAdapter(kernel)
            host = RuntimePluginHost(
                adapter=adapter,
                activation_context_resolver=lambda _info: object(),
            )
            plugin = DockAndViewportPlugin()
            host.register_plugin(plugin)

            report = host.execute_lifecycle_target(
                {"DockAndViewportPlugin"}, source="e69-test", allow_deactivate=True
            )
            self.assertEqual(report["status"], "settled")
            self.assertIs(self.layout.docks["RetryableDock"], plugin.dock)
            self.assertIs(
                self.layout.viewports["RetryableViewport"], plugin.viewport
            )
            self.assertEqual(self.layout.viewport_tabs.count(), 1)
            self.assertEqual(
                adapter._declarative_dock_owner_by_id,
                {"RetryableDock": "DockAndViewportPlugin"},
            )
            self.assertEqual(
                adapter._declarative_viewport_owner_by_id,
                {"RetryableViewport": "DockAndViewportPlugin"},
            )

            self.assertFalse(host.unload_plugin("DockAndViewportPlugin"))
            self.assertEqual(host.loaded_plugins, {"DockAndViewportPlugin": plugin})
            self.assertEqual(plugin.unload_calls, 0)
            self.assertEqual(plugin.viewport.cleanup_attempts, 1)
            self.assertIs(self.layout.docks["RetryableDock"], plugin.dock)
            self.assertIs(
                self.layout.viewports["RetryableViewport"], plugin.viewport
            )
            self.assertEqual(self.layout.viewport_tabs.count(), 1)
            self.assertEqual(
                adapter._declarative_dock_owner_by_id,
                {"RetryableDock": "DockAndViewportPlugin"},
            )
            self.assertEqual(
                adapter._declarative_viewport_owner_by_id,
                {"RetryableViewport": "DockAndViewportPlugin"},
            )
            self.assertEqual(
                get_command_registry().describe(
                    "retryable.multi_surface.command"
                )["owner"],
                "DockAndViewportPlugin",
            )

            plugin.viewport.fail_cleanup = False
            self.assertTrue(host.unload_plugin("DockAndViewportPlugin"))
            self.assertEqual(host.loaded_plugins, {})
            self.assertEqual(plugin.unload_calls, 1)
            self.assertEqual(plugin.viewport.cleanup_attempts, 2)
            self.assertNotIn("RetryableDock", self.layout.docks)
            self.assertNotIn("RetryableViewport", self.layout.viewports)
            self.assertEqual(self.layout.viewport_tabs.count(), 0)
            self.assertEqual(adapter._declarative_dock_owner_by_id, {})
            self.assertEqual(adapter._declarative_viewport_owner_by_id, {})
            self.assertIsNone(
                get_command_registry().get("retryable.multi_surface.command")
            )
        finally:
            reset_command_registry()



    def test_runtime_host_retries_after_post_cleanup_on_unload_failure(self):
        from types import SimpleNamespace

        from core.VitaLoom.commands.registry import (
            CommandSpec,
            command_ok,
            get_command_registry,
            reset_command_registry,
        )
        from core.VitaLoom.core.runtime_plugin_contract import (
            ICommandProvider,
            IRuntimePlugin,
        )
        from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
        from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
            LegacyEditorPluginAdapter,
        )

        class _Signal:
            def emit(self, *_args, **_kwargs) -> None:
                return None

        class PostCleanupFailurePlugin(IRuntimePlugin, ICommandProvider):
            def __init__(self) -> None:
                self.dock: QDockWidget | None = None
                self.viewport: QWidget | None = None
                self.fail_on_unload = True
                self.unload_calls = 0

            def get_plugin_info(self):
                return {
                    "name": "PostCleanupFailurePlugin",
                    "version": "1.0.0",
                    "dependencies": [],
                    "provides": ["dock", "viewport", "command", "editor_contribution"],
                    "activation_context": "runtime",
                    "editor_contributions": [
                        {
                            "id": "post.cleanup.dock.surface",
                            "kind": "dock_surface",
                            "dock_id": "PostCleanupDock",
                            "title_key": "dock.post.cleanup.title",
                            "default_title": "Post-Cleanup Dock",
                            "area": "left",
                        },
                        {
                            "id": "post.cleanup.viewport.surface",
                            "kind": "viewport_surface",
                            "viewport_id": "PostCleanupViewport",
                            "name_key": "viewport.post.cleanup.name",
                            "default_name": "Post-Cleanup Viewport",
                        },
                    ],
                }

            def get_command_specs(self):
                return [
                    CommandSpec(
                        id="post.cleanup.failure.command",
                        title="Post-Cleanup Failure Command",
                        owner="declared-owner-is-normalized-by-host",
                        handler=lambda _payload, _context: command_ok(),
                    )
                ]

            def on_load(self, _runtime_context):
                return None

            def on_unload(self):
                self.unload_calls += 1
                if self.fail_on_unload:
                    raise RuntimeError("simulated post-cleanup on_unload failure")

            def create_dock_widget(self):
                self.dock = QDockWidget("Post-Cleanup Dock")
                self.dock.setWidget(QWidget())
                return self.dock

            def create_viewport_widget(self):
                self.viewport = QWidget()
                return self.viewport

        reset_command_registry()
        try:
            kernel = SimpleNamespace(
                layout_manager=self.layout,
                get_context=lambda: SimpleNamespace(),
                plugin_loaded=_Signal(),
                plugin_unloaded=_Signal(),
            )
            adapter = LegacyEditorPluginAdapter(kernel)
            host = RuntimePluginHost(
                adapter=adapter,
                activation_context_resolver=lambda _info: object(),
            )
            plugin = PostCleanupFailurePlugin()
            host.register_plugin(plugin)
            report = host.execute_lifecycle_target(
                {"PostCleanupFailurePlugin"}, source="e70-test", allow_deactivate=True
            )
            self.assertEqual(report["status"], "settled")

            self.assertFalse(host.unload_plugin("PostCleanupFailurePlugin"))
            self.assertEqual(
                host.loaded_plugins,
                {"PostCleanupFailurePlugin": plugin},
            )
            self.assertEqual(plugin.unload_calls, 1)
            self.assertNotIn("PostCleanupDock", self.layout.docks)
            self.assertNotIn("PostCleanupViewport", self.layout.viewports)
            self.assertEqual(self.layout.viewport_tabs.count(), 0)
            self.assertEqual(adapter._declarative_dock_owner_by_id, {})
            self.assertEqual(adapter._declarative_viewport_owner_by_id, {})
            self.assertEqual(
                get_command_registry().describe(
                    "post.cleanup.failure.command"
                )["owner"],
                "PostCleanupFailurePlugin",
            )

            plugin.fail_on_unload = False
            self.assertTrue(host.unload_plugin("PostCleanupFailurePlugin"))
            self.assertEqual(host.loaded_plugins, {})
            self.assertEqual(plugin.unload_calls, 2)
            self.assertIsNone(
                get_command_registry().get("post.cleanup.failure.command")
            )
        finally:
            reset_command_registry()

if __name__ == "__main__":
    unittest.main()
