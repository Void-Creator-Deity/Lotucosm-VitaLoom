# -*- coding: utf-8 -*-
"""Current PyQt Host projection for Qt-free dock surface facts."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace


RUNTIME = (
    Path(__file__).resolve().parents[1]
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
)


class _Signal:
    def __init__(self, events: list[object], name: str) -> None:
        self.events = events
        self.name = name

    def emit(self, plugin_id: str) -> None:
        self.events.append((self.name, plugin_id))


class _EventBus:
    def __init__(self) -> None:
        self.callbacks: dict[str, list] = {}
        self.subscribe_calls: list[tuple[str, object]] = []
        self.unsubscribe_calls: list[tuple[str, object]] = []

    def subscribe(self, event_name: str, callback) -> None:
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


class _Dock:
    def __init__(self) -> None:
        self.object_name = ""
        self.window_title = "legacy-title"

    def setObjectName(self, value: str) -> None:
        self.object_name = value

    def setWindowTitle(self, value: str) -> None:
        self.window_title = value


class _Layout:
    def __init__(self, events: list[object]) -> None:
        self.events = events
        self.docks: dict[str, _Dock] = {}
        self.add_calls: list[tuple[_Dock, dict]] = []

    def add_dock(self, dock, config) -> None:
        copied = dict(config)
        self.add_calls.append((dock, copied))
        self.docks[copied["title"]] = dock
        self.events.append(("add_dock", copied))

    def remove_dock(self, dock_id: str) -> None:
        self.docks.pop(dock_id, None)
        self.events.append(("remove_dock", dock_id))

    def add_menu_items(self, _items, _plugin_id: str) -> None:
        pass

    def add_toolbar_items(self, _items, _plugin_id: str) -> None:
        pass

    def remove_plugin_ui(self, plugin_id: str) -> None:
        self.events.append(("remove_ui", plugin_id))

    def process_pending_dock_tabify(self) -> None:
        self.events.append(("settle",))


class _InspectorBridge:
    def __init__(self) -> None:
        self.created = 0
        self.dock = None

    def get_plugin_info(self):
        return _normalized_inspector_info()

    def on_load(self, _context):
        pass

    def on_unload(self):
        pass

    def on_editor_ready(self):
        pass

    def create_dock_widget(self):
        self.created += 1
        self.dock = _Dock()
        return self.dock

    def get_dock_config(self):
        raise AssertionError("declarative dock config must be authoritative")


def _normalized_inspector_info():
    from builtin.editor_extensions.inspector_plugin import InspectorPlugin
    from core.VitaLoom.core.editor_contribution_contract import (
        parse_editor_contributions,
    )

    info = InspectorPlugin().get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "InspectorPlugin", info["editor_contributions"]
            )
        ],
    }


def _kernel(events: list[object], context: object):
    return SimpleNamespace(
        layout_manager=_Layout(events),
        get_context=lambda: context,
        plugin_loaded=_Signal(events, "loaded"),
        plugin_unloaded=_Signal(events, "unloaded"),
    )


def test_adapter_projects_inspector_shell_from_qt_free_facts() -> None:
    from PyQt6.QtCore import Qt
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    events: list[object] = []
    bus = _EventBus()
    context = SimpleNamespace(
        event_bus=bus,
        i18n_tr=lambda key, default: "Inspector translated"
        if key == "inspector.title"
        else default,
    )
    kernel = _kernel(events, context)
    adapter = LegacyEditorPluginAdapter(kernel)
    plugin = _InspectorBridge()
    info = _normalized_inspector_info()

    adapter.after_plugin_load(plugin, "InspectorPlugin", info)

    assert plugin.created == 1
    assert len(kernel.layout_manager.add_calls) == 1
    dock, config = kernel.layout_manager.add_calls[0]
    assert dock.object_name == "Inspector"
    assert dock.window_title == "Inspector translated"
    assert config == {
        "title": "Inspector",
        "area": Qt.DockWidgetArea.RightDockWidgetArea,
        "default_visible": True,
        "can_close": True,
        "can_float": True,
        "can_move": True,
        "tabbed_with": None,
    }
    assert [name for name, _callback in bus.subscribe_calls] == [
        "language_changed"
    ]
    assert events[-1] == ("loaded", "InspectorPlugin")


def test_language_refresh_updates_existing_dock_without_recreation() -> None:
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    events: list[object] = []
    bus = _EventBus()
    translations = {"inspector.title": "检视器"}
    context = SimpleNamespace(
        event_bus=bus,
        i18n_tr=lambda key, default: translations.get(key, default),
    )
    kernel = _kernel(events, context)
    adapter = LegacyEditorPluginAdapter(kernel)
    plugin = _InspectorBridge()
    info = _normalized_inspector_info()
    adapter.bind_active_plugin_metadata_resolver(
        lambda: (("InspectorPlugin", info),)
    )
    adapter.bind_active_plugin_items_resolver(
        lambda: (("InspectorPlugin", plugin),)
    )
    adapter.after_plugin_load(plugin, "InspectorPlugin", info)
    dock = kernel.layout_manager.docks["Inspector"]

    translations["inspector.title"] = "Inspector"
    bus.publish("language_changed")

    assert plugin.created == 1
    assert len(kernel.layout_manager.add_calls) == 1
    assert kernel.layout_manager.docks["Inspector"] is dock
    assert dock.window_title == "Inspector"


def test_cleanup_uses_declarative_dock_id_and_unsubscribes_exact_owner() -> None:
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    events: list[object] = []
    bus = _EventBus()
    context = SimpleNamespace(event_bus=bus, i18n_tr=lambda _key, default: default)
    kernel = _kernel(events, context)
    adapter = LegacyEditorPluginAdapter(kernel)
    plugin = _InspectorBridge()
    info = _normalized_inspector_info()
    adapter.after_plugin_load(plugin, "InspectorPlugin", info)

    adapter.before_plugin_unload(plugin, "InspectorPlugin", info)

    assert ("remove_dock", "Inspector") in events
    assert [name for name, _callback in bus.unsubscribe_calls] == [
        "language_changed"
    ]
    assert bus.callbacks["language_changed"] == []


def test_inspector_plugin_declares_shell_without_direct_layout_or_title_refresh() -> None:
    from builtin.editor_extensions.inspector_plugin import InspectorPlugin

    info = InspectorPlugin().get_plugin_info()
    assert info["provides"] == ["dock", "editor_contribution"]
    assert info["editor_contributions"] == [
        {
            "id": "inspector.surface",
            "kind": "dock_surface",
            "dock_id": "Inspector",
            "title_key": "inspector.title",
            "default_title": "检视器",
            "area": "right",
            "default_visible": True,
            "can_close": True,
            "can_float": True,
            "can_move": True,
            "tabbed_with": None,
            "order": 40,
            "refresh_events": ["language_changed"],
        }
    ]
    source = (
        RUNTIME / "builtin" / "editor_extensions" / "inspector_plugin.py"
    ).read_text(encoding="utf-8-sig")
    assert 'subscribe("language_changed"' not in source
    assert 'unsubscribe("language_changed"' not in source
    assert "layout_manager" not in source
    assert "def _on_language_changed" not in source
