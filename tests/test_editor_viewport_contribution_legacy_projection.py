# -*- coding: utf-8 -*-
"""Current PyQt Host projection for Qt-free viewport surface facts."""
from __future__ import annotations

from types import SimpleNamespace

import pytest


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


class _Viewport:
    def __init__(self) -> None:
        self.deleted = 0

    def deleteLater(self) -> None:
        self.deleted += 1


class _Layout:
    def __init__(self, events: list[object]) -> None:
        self.events = events
        self.viewports: dict[str, _Viewport] = {}
        self.viewport_providers: dict[str, object] = {}
        self.display_names: dict[str, str] = {}
        self.add_calls: list[tuple[str, _Viewport, object, str | None]] = []
        self.remove_calls: list[str] = []
        self.rename_calls: list[tuple[str, str]] = []

    def add_viewport(
        self,
        viewport_id: str,
        widget: _Viewport,
        provider=None,
        display_name: str | None = None,
    ) -> None:
        self.add_calls.append((viewport_id, widget, provider, display_name))
        self.viewports[viewport_id] = widget
        if provider is not None:
            self.viewport_providers[viewport_id] = provider
        self.display_names[viewport_id] = display_name or viewport_id
        self.events.append(("add_viewport", viewport_id, display_name))

    def set_viewport_display_name(self, viewport_id: str, display_name: str) -> None:
        assert viewport_id in self.viewports
        self.rename_calls.append((viewport_id, display_name))
        self.display_names[viewport_id] = display_name

    def remove_viewport(self, viewport_id: str) -> None:
        self.remove_calls.append(viewport_id)
        widget = self.viewports.pop(viewport_id, None)
        self.viewport_providers.pop(viewport_id, None)
        self.display_names.pop(viewport_id, None)
        if widget is not None:
            widget.deleteLater()
        self.events.append(("remove_viewport", viewport_id))

    def add_menu_items(self, _items, _plugin_id: str) -> None:
        pass

    def add_toolbar_items(self, _items, _plugin_id: str) -> None:
        pass

    def remove_plugin_ui(self, plugin_id: str) -> None:
        self.events.append(("remove_ui", plugin_id))

    def process_pending_dock_tabify(self) -> None:
        self.events.append(("settle",))


class _CellEditorBridge:
    def __init__(self, info: dict) -> None:
        self.info = info
        self.created = 0
        self.viewport: _Viewport | None = None

    def get_plugin_info(self):
        return self.info

    def create_viewport_widget(self):
        self.created += 1
        if self.viewport is None:
            self.viewport = _Viewport()
        return self.viewport

    def get_viewport_id(self):
        raise AssertionError("declarative viewport_id must be authoritative")

    def get_viewport_name(self):
        raise AssertionError("declarative viewport name must be authoritative")


class _LegacyViewportBridge:
    def get_plugin_info(self):
        return {
            "name": "CommunityViewportPlugin",
            "version": "1.0.0",
            "provides": ["viewport"],
        }

    def create_viewport_widget(self):
        return _Viewport()

    def get_viewport_id(self):
        return "community"

    def get_viewport_name(self):
        return "Community"

    def on_load(self, _context):
        pass

    def on_unload(self):
        pass

    def on_viewport_activated(self):
        pass

    def on_viewport_deactivated(self):
        pass


def _normalized_cell_editor_info() -> dict:
    from builtin.editor_extensions.cell_editor_plugin import CellEditorPlugin
    from core.VitaLoom.core.editor_contribution_contract import parse_editor_contributions

    info = CellEditorPlugin().get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "CellEditorPlugin", info["editor_contributions"]
            )
        ],
    }


def _normalized_scene_viewport_info() -> dict:
    from builtin.editor_extensions.scene_viewport_plugin import SceneViewportPlugin
    from core.VitaLoom.core.editor_contribution_contract import parse_editor_contributions

    info = SceneViewportPlugin().get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "SceneViewportPlugin", info["editor_contributions"]
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


def test_adapter_projects_cell_editor_shell_from_qt_free_facts() -> None:
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import LegacyEditorPluginAdapter

    events: list[object] = []
    bus = _EventBus()
    context = SimpleNamespace(
        event_bus=bus,
        i18n_tr=lambda key, default: "Cell Editor translated"
        if key == "cell_editor.name"
        else default,
    )
    kernel = _kernel(events, context)
    adapter = LegacyEditorPluginAdapter(kernel)
    info = _normalized_cell_editor_info()
    plugin = _CellEditorBridge(info)

    adapter.after_plugin_load(plugin, "CellEditorPlugin", info)

    assert plugin.created == 1
    assert len(kernel.layout_manager.add_calls) == 1
    viewport_id, widget, provider, display_name = kernel.layout_manager.add_calls[0]
    assert viewport_id == "cell_editor"
    assert widget is plugin.viewport
    assert provider is plugin
    assert display_name == "Cell Editor translated"
    assert kernel.layout_manager.viewports == {"cell_editor": widget}
    assert [name for name, _callback in bus.subscribe_calls] == ["language_changed"]
    assert events[-1] == ("loaded", "CellEditorPlugin")


def test_language_refresh_updates_existing_viewport_without_recreation() -> None:
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import LegacyEditorPluginAdapter

    events: list[object] = []
    bus = _EventBus()
    translations = {"cell_editor.name": "细胞编辑"}
    context = SimpleNamespace(
        event_bus=bus,
        i18n_tr=lambda key, default: translations.get(key, default),
    )
    kernel = _kernel(events, context)
    adapter = LegacyEditorPluginAdapter(kernel)
    info = _normalized_cell_editor_info()
    plugin = _CellEditorBridge(info)
    adapter.bind_active_plugin_metadata_resolver(
        lambda: (("CellEditorPlugin", info),)
    )
    adapter.bind_active_plugin_items_resolver(
        lambda: (("CellEditorPlugin", plugin),)
    )
    adapter.after_plugin_load(plugin, "CellEditorPlugin", info)
    widget = kernel.layout_manager.viewports["cell_editor"]

    translations["cell_editor.name"] = "Cell Editor"
    bus.publish("language_changed")

    assert plugin.created == 1
    assert len(kernel.layout_manager.add_calls) == 1
    assert kernel.layout_manager.remove_calls == []
    assert kernel.layout_manager.viewports["cell_editor"] is widget
    assert kernel.layout_manager.display_names["cell_editor"] == "Cell Editor"
    assert kernel.layout_manager.rename_calls == [("cell_editor", "Cell Editor")]


def test_cleanup_uses_declarative_viewport_id_and_deletes_once() -> None:
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import LegacyEditorPluginAdapter

    events: list[object] = []
    bus = _EventBus()
    context = SimpleNamespace(event_bus=bus, i18n_tr=lambda _key, default: default)
    kernel = _kernel(events, context)
    adapter = LegacyEditorPluginAdapter(kernel)
    info = _normalized_cell_editor_info()
    plugin = _CellEditorBridge(info)
    adapter.after_plugin_load(plugin, "CellEditorPlugin", info)
    widget = plugin.viewport

    adapter.before_plugin_unload(plugin, "CellEditorPlugin", info)

    assert kernel.layout_manager.remove_calls == ["cell_editor"]
    assert widget is not None and widget.deleted == 1
    assert [name for name, _callback in bus.unsubscribe_calls] == [
        "language_changed"
    ]
    assert bus.callbacks["language_changed"] == []


def test_adapter_projects_and_refreshes_scene_shell_without_recreation() -> None:
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import LegacyEditorPluginAdapter

    events: list[object] = []
    bus = _EventBus()
    translations = {"scene_viewport.name": "场景"}
    context = SimpleNamespace(
        event_bus=bus,
        i18n_tr=lambda key, default: translations.get(key, default),
    )
    kernel = _kernel(events, context)
    adapter = LegacyEditorPluginAdapter(kernel)
    info = _normalized_scene_viewport_info()
    plugin = _CellEditorBridge(info)
    adapter.bind_active_plugin_metadata_resolver(
        lambda: (("SceneViewportPlugin", info),)
    )
    adapter.bind_active_plugin_items_resolver(
        lambda: (("SceneViewportPlugin", plugin),)
    )

    adapter.after_plugin_load(plugin, "SceneViewportPlugin", info)
    widget = kernel.layout_manager.viewports["scene"]

    assert plugin.created == 1
    assert kernel.layout_manager.add_calls == [("scene", widget, plugin, "场景")]
    assert [name for name, _callback in bus.subscribe_calls] == ["language_changed"]

    translations["scene_viewport.name"] = "Scene"
    bus.publish("language_changed")

    assert plugin.created == 1
    assert kernel.layout_manager.viewports["scene"] is widget
    assert kernel.layout_manager.rename_calls == [("scene", "Scene")]

    adapter.before_plugin_unload(plugin, "SceneViewportPlugin", info)

    assert kernel.layout_manager.remove_calls == ["scene"]
    assert widget.deleted == 1
    assert [name for name, _callback in bus.unsubscribe_calls] == [
        "language_changed"
    ]


def test_unmigrated_community_viewport_provider_keeps_legacy_fallback() -> None:
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import LegacyEditorPluginAdapter
    class CommunityViewportPlugin(_LegacyViewportBridge):
        pass

    events: list[object] = []
    context = SimpleNamespace(event_bus=_EventBus())
    kernel = _kernel(events, context)
    adapter = LegacyEditorPluginAdapter(kernel)
    plugin = CommunityViewportPlugin()
    info = plugin.get_plugin_info()

    adapter.after_plugin_load(plugin, "CommunityViewportPlugin", info)

    assert len(kernel.layout_manager.add_calls) == 1
    viewport_id, _widget, provider, display_name = kernel.layout_manager.add_calls[0]
    assert viewport_id == "community"
    assert provider is plugin
    assert display_name is None


def test_cleanup_releases_owner_so_same_surface_can_reload() -> None:
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import LegacyEditorPluginAdapter

    events: list[object] = []
    bus = _EventBus()
    context = SimpleNamespace(event_bus=bus, i18n_tr=lambda _key, default: default)
    kernel = _kernel(events, context)
    adapter = LegacyEditorPluginAdapter(kernel)
    info = _normalized_cell_editor_info()
    first = _CellEditorBridge(info)
    second = _CellEditorBridge(info)

    adapter.after_plugin_load(first, "CellEditorPlugin", info)
    first_widget = first.viewport
    adapter.before_plugin_unload(first, "CellEditorPlugin", info)
    adapter.after_plugin_load(second, "CellEditorPlugin", info)

    assert first_widget is not None and first_widget.deleted == 1
    assert second.viewport is not first_widget
    assert kernel.layout_manager.viewports == {"cell_editor": second.viewport}
    assert [call[0] for call in kernel.layout_manager.add_calls] == [
        "cell_editor",
        "cell_editor",
    ]
    assert kernel.layout_manager.remove_calls == ["cell_editor"]
    assert adapter._declarative_viewport_owner_by_id == {
        "cell_editor": "CellEditorPlugin"
    }


def test_declarative_surface_rejects_existing_legacy_viewport_collision() -> None:
    from core.VitaLoom.core.editor_contribution_contract import (
        parse_editor_contributions,
    )
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import LegacyEditorPluginAdapter

    events: list[object] = []
    context = SimpleNamespace(
        event_bus=_EventBus(), i18n_tr=lambda _key, default: default
    )
    kernel = _kernel(events, context)
    existing = _Viewport()
    kernel.layout_manager.viewports["cell_editor"] = existing
    adapter = LegacyEditorPluginAdapter(kernel)
    from builtin.editor_extensions.cell_editor_plugin import CellEditorPlugin

    info = _normalized_cell_editor_info()
    raw_info = CellEditorPlugin().get_plugin_info()
    contribution = parse_editor_contributions(
        "CellEditorPlugin", raw_info["editor_contributions"]
    )[0]
    plugin = _CellEditorBridge(info)

    with pytest.raises(
        RuntimeError, match="collides with an existing legacy viewport"
    ):
        adapter._project_viewport_surface(contribution, plugin)

    assert plugin.created == 0
    assert kernel.layout_manager.viewports["cell_editor"] is existing
    assert adapter._declarative_viewport_owner_by_id == {}


def test_declarative_surface_rejects_cross_owner_collision() -> None:
    from core.VitaLoom.core.editor_contribution_contract import (
        parse_editor_contributions,
    )
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import LegacyEditorPluginAdapter

    events: list[object] = []
    context = SimpleNamespace(
        event_bus=_EventBus(), i18n_tr=lambda _key, default: default
    )
    kernel = _kernel(events, context)
    adapter = LegacyEditorPluginAdapter(kernel)
    from builtin.editor_extensions.cell_editor_plugin import CellEditorPlugin

    info = _normalized_cell_editor_info()
    plugin = _CellEditorBridge(info)
    adapter.after_plugin_load(plugin, "CellEditorPlugin", info)
    raw_info = CellEditorPlugin().get_plugin_info()
    other = parse_editor_contributions(
        "OtherViewportPlugin", raw_info["editor_contributions"]
    )[0]

    with pytest.raises(
        RuntimeError, match="already owned by another plugin"
    ):
        adapter._project_viewport_surface(other, _CellEditorBridge(info))

    assert plugin.created == 1
    assert kernel.layout_manager.viewports["cell_editor"] is plugin.viewport
    assert adapter._declarative_viewport_owner_by_id == {
        "cell_editor": "CellEditorPlugin"
    }

