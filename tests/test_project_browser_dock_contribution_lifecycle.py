# -*- coding: utf-8 -*-
"""E37 ProjectBrowser dock shell, panel identity, and event ownership."""
from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest


_QT_APP = None


RUNTIME = (
    Path(__file__).resolve().parents[1]
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
)


class _EventBus:
    def __init__(self, *, fail_on: str | None = None) -> None:
        self.fail_on = fail_on
        self.callbacks: dict[str, list] = {}
        self.subscribe_calls: list[tuple[str, object]] = []
        self.unsubscribe_calls: list[tuple[str, object]] = []

    def subscribe(self, event_name: str, callback) -> None:
        if event_name == self.fail_on:
            raise RuntimeError(f"subscribe failed: {event_name}")
        self.subscribe_calls.append((event_name, callback))
        callbacks = self.callbacks.setdefault(event_name, [])
        if callback not in callbacks:
            callbacks.append(callback)

    def unsubscribe(self, event_name: str, callback) -> None:
        self.unsubscribe_calls.append((event_name, callback))
        callbacks = self.callbacks.get(event_name, [])
        if callback in callbacks:
            callbacks.remove(callback)

    def publish(self, event_name: str, data=None) -> None:
        for callback in tuple(self.callbacks.get(event_name, ())):
            callback(data)


class _Panel:
    def __init__(self) -> None:
        self.retranslate_calls = 0
        self.opened: list[str] = []
        self.refresh_calls = 0

    def retranslate_ui(self) -> None:
        self.retranslate_calls += 1

    def on_project_opened(self, path: str) -> None:
        self.opened.append(path)

    def _refresh_folder(self) -> None:
        self.refresh_calls += 1


class _Signal:
    def emit(self, _plugin_id: str) -> None:
        pass


class _Dock:
    def __init__(self, panel: object | None = None) -> None:
        self.object_name = ""
        self.window_title = "legacy"
        self.panel = panel

    def setObjectName(self, value: str) -> None:
        self.object_name = value

    def setWindowTitle(self, value: str) -> None:
        self.window_title = value


class _Layout:
    def __init__(self) -> None:
        self.docks: dict[str, _Dock] = {}
        self.add_calls: list[tuple[_Dock, dict]] = []
        self.remove_calls: list[str] = []
        self.remove_ui_calls: list[str] = []

    def add_dock(self, dock, config) -> None:
        copied = dict(config)
        self.add_calls.append((dock, copied))
        self.docks[copied["title"]] = dock

    def remove_dock(self, dock_id: str) -> None:
        self.remove_calls.append(dock_id)
        self.docks.pop(dock_id, None)

    def add_menu_items(self, _items, _plugin_id: str) -> None:
        pass

    def add_toolbar_items(self, _items, _plugin_id: str) -> None:
        pass

    def remove_plugin_ui(self, plugin_id: str) -> None:
        self.remove_ui_calls.append(plugin_id)

    def process_pending_dock_tabify(self) -> None:
        pass


class _ProjectBrowserBridge:
    def __init__(self, info: dict) -> None:
        self.info = info
        self.created = 0
        self.project_panel = _Panel()
        self.dock: _Dock | None = None

    def get_plugin_info(self):
        return self.info

    def create_dock_widget(self):
        self.created += 1
        self.dock = _Dock(self.project_panel)
        return self.dock

    def get_dock_config(self):
        raise AssertionError("declarative dock config must be authoritative")


def _normalized_project_browser_info() -> dict:
    from builtin.editor_extensions.project_browser_plugin import ProjectBrowserPlugin
    from core.VitaLoom.core.editor_contribution_contract import (
        parse_editor_contributions,
    )

    info = ProjectBrowserPlugin().get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "ProjectBrowserPlugin", info["editor_contributions"]
            )
        ],
    }


def test_project_browser_declares_one_qt_free_dock_shell() -> None:
    from builtin.editor_extensions.project_browser_plugin import ProjectBrowserPlugin

    info = ProjectBrowserPlugin().get_plugin_info()

    assert info["provides"] == ["dock", "editor_contribution"]
    assert info["editor_contributions"] == [
        {
            "id": "project_browser.surface",
            "kind": "dock_surface",
            "dock_id": "Project",
            "title_key": "project_browser.title",
            "default_title": "项目",
            "area": "bottom",
            "default_visible": True,
            "can_close": True,
            "can_float": True,
            "can_move": True,
            "tabbed_with": None,
            "order": 50,
            "refresh_events": ["language_changed"],
        }
    ]

    source = (
        RUNTIME / "builtin" / "editor_extensions" / "project_browser_plugin.py"
    ).read_text(encoding="utf-8-sig")
    assert "layout_manager" not in source
    assert ".remove_dock(" not in source
    assert ".add_dock(" not in source


def test_project_browser_adapter_refreshes_title_in_place_and_preserves_panel() -> None:
    from PyQt6.QtCore import Qt
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    bus = _EventBus()
    translations = {"project_browser.title": "项目"}
    context = SimpleNamespace(
        event_bus=bus,
        i18n_tr=lambda key, default: translations.get(key, default),
    )
    layout = _Layout()
    kernel = SimpleNamespace(
        layout_manager=layout,
        get_context=lambda: context,
        plugin_loaded=_Signal(),
        plugin_unloaded=_Signal(),
    )
    adapter = LegacyEditorPluginAdapter(kernel)
    info = _normalized_project_browser_info()
    plugin = _ProjectBrowserBridge(info)
    adapter.bind_active_plugin_metadata_resolver(
        lambda: (("ProjectBrowserPlugin", info),)
    )
    adapter.bind_active_plugin_items_resolver(
        lambda: (("ProjectBrowserPlugin", plugin),)
    )

    adapter.after_plugin_load(plugin, "ProjectBrowserPlugin", info)
    dock = layout.docks["Project"]
    panel = plugin.project_panel

    translations["project_browser.title"] = "Project"
    bus.publish("language_changed")

    assert plugin.created == 1
    assert len(layout.add_calls) == 1
    assert layout.remove_calls == []
    assert layout.docks["Project"] is dock
    assert plugin.project_panel is panel
    assert dock.panel is panel
    assert dock.window_title == "Project"
    assert layout.add_calls[0][1] == {
        "title": "Project",
        "area": Qt.DockWidgetArea.BottomDockWidgetArea,
        "default_visible": True,
        "can_close": True,
        "can_float": True,
        "can_move": True,
        "tabbed_with": None,
    }


def test_project_browser_unload_releases_owned_events_and_stops_stale_updates() -> None:
    from builtin.editor_extensions.project_browser_plugin import ProjectBrowserPlugin

    bus = _EventBus()
    plugin = ProjectBrowserPlugin()
    plugin.on_load(SimpleNamespace(event_bus=bus, kernel=None))
    panel = _Panel()
    plugin.project_panel = panel

    bus.publish("project_opened", {"path": "world-a"})
    bus.publish("refresh_project_browser")
    bus.publish("language_changed")
    assert panel.opened == ["world-a"]
    assert panel.refresh_calls == 1
    assert panel.retranslate_calls == 1

    plugin.on_unload()

    expected = [
        "project_opened",
        "create_asset",
        "refresh_project_browser",
        "language_changed",
    ]
    assert [name for name, _callback in bus.subscribe_calls] == expected
    assert [name for name, _callback in bus.unsubscribe_calls] == expected
    assert all(not callbacks for callbacks in bus.callbacks.values())

    bus.publish("project_opened", {"path": "stale"})
    bus.publish("refresh_project_browser")
    bus.publish("language_changed")
    assert panel.opened == ["world-a"]
    assert panel.refresh_calls == 1
    assert panel.retranslate_calls == 1

    plugin.on_unload()
    assert [name for name, _callback in bus.unsubscribe_calls] == expected


def test_project_browser_load_rolls_back_partial_subscriptions() -> None:
    from builtin.editor_extensions.project_browser_plugin import ProjectBrowserPlugin

    bus = _EventBus(fail_on="refresh_project_browser")
    plugin = ProjectBrowserPlugin()

    with pytest.raises(RuntimeError, match="refresh_project_browser"):
        plugin.on_load(SimpleNamespace(event_bus=bus, kernel=None))

    subscribed = [name for name, _callback in bus.subscribe_calls]
    assert subscribed == ["project_opened", "create_asset"]
    assert [name for name, _callback in bus.unsubscribe_calls] == subscribed
    assert all(not callbacks for callbacks in bus.callbacks.values())


def test_project_panel_exposes_in_place_retranslation_without_self_subscription() -> None:
    from core.VitaLoom.docks.library_browser import ProjectPanel

    source = (
        RUNTIME / "core" / "VitaLoom" / "docks" / "library_browser.py"
    ).read_text(encoding="utf-8-sig")
    assert 'event_bus.subscribe("project_opened"' not in source

    class _TextTarget:
        def __init__(self) -> None:
            self.value = ""

        def setText(self, value: str) -> None:
            self.value = value

        def setPlaceholderText(self, value: str) -> None:
            self.value = value

        def setHeaderLabel(self, value: str) -> None:
            self.value = value

    values = {
        "project_panel.search_placeholder": "Search assets...",
        "project_panel.view.list": "List",
        "project_panel.view.grid": "Grid",
        "project_panel.header.project_tree": "Project",
        "project_panel.icon_size": "Icons",
    }
    panel = ProjectPanel.__new__(ProjectPanel)
    panel.editor_context = SimpleNamespace(
        i18n_tr=lambda key, default: values.get(key, default)
    )
    panel.search_box = _TextTarget()
    panel.list_view_btn = _TextTarget()
    panel.grid_view_btn = _TextTarget()
    panel.folder_tree = _TextTarget()
    panel._icon_size_label = _TextTarget()
    panel.asset_list = _TextTarget()

    panel.retranslate_ui()

    assert panel.search_box.value == "Search assets..."
    assert panel.list_view_btn.value == "List"
    assert panel.grid_view_btn.value == "Grid"
    assert panel.folder_tree.value == "Project"
    assert panel._icon_size_label.value == "Icons"


def test_project_panel_real_widget_retranslation_keeps_initialized_icon_label() -> None:
    from PyQt6.QtWidgets import QApplication
    from core.VitaLoom.docks.library_browser import ProjectPanel

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    global _QT_APP
    _QT_APP = QApplication.instance() or QApplication([])
    app = _QT_APP
    panel = ProjectPanel()

    icon_size_label = panel._icon_size_label
    panel.retranslate_ui()

    assert panel._icon_size_label is icon_size_label
    assert panel._icon_size_label.text()
    panel.deleteLater()
    app.processEvents()
