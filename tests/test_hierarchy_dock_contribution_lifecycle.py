# -*- coding: utf-8 -*-
"""E36 Hierarchy dock shell and exact event subscription ownership."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


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
        self.updates: list[tuple[object, object]] = []
        self.headers: list[str] = []

    def update_tree(self, nodes, connections) -> None:
        self.updates.append((nodes, connections))

    def setHeaderLabel(self, value: str) -> None:
        self.headers.append(value)


class _Signal:
    def emit(self, _plugin_id: str) -> None:
        pass


class _Dock:
    def __init__(self) -> None:
        self.object_name = ""
        self.window_title = "legacy"

    def setObjectName(self, value: str) -> None:
        self.object_name = value

    def setWindowTitle(self, value: str) -> None:
        self.window_title = value


class _Layout:
    def __init__(self) -> None:
        self.docks: dict[str, _Dock] = {}
        self.add_calls: list[tuple[_Dock, dict]] = []
        self.remove_calls: list[str] = []

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

    def remove_plugin_ui(self, _plugin_id: str) -> None:
        pass

    def process_pending_dock_tabify(self) -> None:
        pass


class _HierarchyBridge:
    def __init__(self, info: dict) -> None:
        self.info = info
        self.created = 0

    def get_plugin_info(self):
        return self.info

    def create_dock_widget(self):
        self.created += 1
        return _Dock()

    def get_dock_config(self):
        raise AssertionError("declarative dock config must be authoritative")


def _normalized_hierarchy_info() -> dict:
    from builtin.editor_extensions.hierarchy_plugin import HierarchyPlugin
    from core.VitaLoom.core.editor_contribution_contract import (
        parse_editor_contributions,
    )

    info = HierarchyPlugin().get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "HierarchyPlugin", info["editor_contributions"]
            )
        ],
    }


def test_hierarchy_declares_one_qt_free_dock_shell() -> None:
    from builtin.editor_extensions.hierarchy_plugin import HierarchyPlugin

    info = HierarchyPlugin().get_plugin_info()

    assert info["provides"] == ["dock", "editor_contribution"]
    assert info["editor_contributions"] == [
        {
            "id": "hierarchy.surface",
            "kind": "dock_surface",
            "dock_id": "Hierarchy",
            "title_key": "hierarchy.title",
            "default_title": "层级",
            "area": "left",
            "default_visible": True,
            "can_close": True,
            "can_float": True,
            "can_move": True,
            "tabbed_with": None,
            "order": 30,
            "refresh_events": ["language_changed"],
        }
    ]

    source = (
        RUNTIME / "builtin" / "editor_extensions" / "hierarchy_plugin.py"
    ).read_text(encoding="utf-8-sig")
    assert "layout_manager" not in source
    assert "self.dock.setWindowTitle" not in source


def test_hierarchy_adapter_projects_once_and_uses_declarative_shell() -> None:
    from PyQt6.QtCore import Qt
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    bus = _EventBus()
    context = SimpleNamespace(
        event_bus=bus,
        i18n_tr=lambda key, default: "Hierarchy translated"
        if key == "hierarchy.title"
        else default,
    )
    layout = _Layout()
    kernel = SimpleNamespace(
        layout_manager=layout,
        get_context=lambda: context,
        plugin_loaded=_Signal(),
        plugin_unloaded=_Signal(),
    )
    adapter = LegacyEditorPluginAdapter(kernel)
    info = _normalized_hierarchy_info()
    plugin = _HierarchyBridge(info)

    adapter.after_plugin_load(plugin, "HierarchyPlugin", info)
    adapter.after_plugin_load(plugin, "HierarchyPlugin", info)

    assert plugin.created == 1
    assert len(layout.add_calls) == 1
    dock, config = layout.add_calls[0]
    assert dock.object_name == "Hierarchy"
    assert dock.window_title == "Hierarchy translated"
    assert config == {
        "title": "Hierarchy",
        "area": Qt.DockWidgetArea.LeftDockWidgetArea,
        "default_visible": True,
        "can_close": True,
        "can_float": True,
        "can_move": True,
        "tabbed_with": None,
    }

    adapter.before_plugin_unload(plugin, "HierarchyPlugin", info)
    assert layout.remove_calls == ["Hierarchy"]


def test_hierarchy_unload_releases_every_owned_subscription_exactly_once() -> None:
    from builtin.editor_extensions.hierarchy_plugin import HierarchyPlugin

    bus = _EventBus()
    plugin = HierarchyPlugin()
    plugin.on_load(SimpleNamespace(event_bus=bus, kernel=None))
    panel = _Panel()
    plugin.hierarchy_panel = panel

    bus.publish(
        "scene_hierarchy_updated",
        {"nodes": ["cell"], "connections": [("a", "b")]},
    )
    assert panel.updates == [(["cell"], [("a", "b")])]

    plugin.on_unload()

    expected = [
        "scene_loaded",
        "entity_created_in_scene",
        "entity_created",
        "entity_deleted",
        "language_changed",
        "scene_hierarchy_updated",
    ]
    assert [name for name, _callback in bus.subscribe_calls] == expected
    assert [name for name, _callback in bus.unsubscribe_calls] == expected
    assert all(not callbacks for callbacks in bus.callbacks.values())

    bus.publish(
        "scene_hierarchy_updated",
        {"nodes": ["stale"], "connections": []},
    )
    assert panel.updates == [(["cell"], [("a", "b")])]

    plugin.on_unload()
    assert [name for name, _callback in bus.unsubscribe_calls] == expected


def test_hierarchy_load_rolls_back_partial_subscriptions_on_failure() -> None:
    from builtin.editor_extensions.hierarchy_plugin import HierarchyPlugin

    bus = _EventBus(fail_on="entity_deleted")
    plugin = HierarchyPlugin()

    with pytest.raises(RuntimeError, match="entity_deleted"):
        plugin.on_load(SimpleNamespace(event_bus=bus, kernel=None))

    subscribed = [name for name, _callback in bus.subscribe_calls]
    assert subscribed == [
        "scene_loaded",
        "entity_created_in_scene",
        "entity_created",
    ]
    assert [name for name, _callback in bus.unsubscribe_calls] == subscribed
    assert all(not callbacks for callbacks in bus.callbacks.values())


def test_hierarchy_language_refresh_keeps_content_refresh_without_shell_mutation() -> None:
    from builtin.editor_extensions.hierarchy_plugin import HierarchyPlugin

    bus = _EventBus()
    context = SimpleNamespace(
        event_bus=bus,
        kernel=None,
        i18n_tr=lambda key, default: "Scene translated"
        if key == "hierarchy.header.scene"
        else default,
    )
    plugin = HierarchyPlugin()
    plugin.on_load(context)
    panel = _Panel()
    plugin.hierarchy_panel = panel

    bus.publish("language_changed")

    assert panel.headers == ["Scene translated"]
    plugin.on_unload()
