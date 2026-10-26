# -*- coding: utf-8 -*-
"""E39 PackageManager dock shell, in-place localization, and exact lifecycle."""
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
    def __init__(
        self,
        *,
        fail_subscribe_on: str | None = None,
        fail_unsubscribe_once_on: str | None = None,
    ) -> None:
        self.fail_subscribe_on = fail_subscribe_on
        self.fail_unsubscribe_once_on = fail_unsubscribe_once_on
        self.callbacks: dict[str, list] = {}
        self.subscribe_calls: list[tuple[str, object]] = []
        self.unsubscribe_calls: list[tuple[str, object]] = []

    def subscribe(self, event_name: str, callback) -> None:
        if event_name == self.fail_subscribe_on:
            raise RuntimeError(f"subscribe failed: {event_name}")
        self.subscribe_calls.append((event_name, callback))
        self.callbacks.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name: str, callback) -> None:
        self.unsubscribe_calls.append((event_name, callback))
        if event_name == self.fail_unsubscribe_once_on:
            self.fail_unsubscribe_once_on = None
            raise RuntimeError(f"unsubscribe failed: {event_name}")
        callbacks = self.callbacks.get(event_name, [])
        if callback in callbacks:
            callbacks.remove(callback)

    def publish(self, event_name: str, data=None) -> None:
        for callback in tuple(self.callbacks.get(event_name, ())):
            callback(data)


class _Signal:
    def __init__(
        self,
        name: str,
        *,
        fail_connect: bool = False,
        fail_disconnect_once: bool = False,
    ) -> None:
        self.name = name
        self.fail_connect = fail_connect
        self.fail_disconnect_once = fail_disconnect_once
        self.callbacks: list = []
        self.connect_calls: list[object] = []
        self.disconnect_calls: list[object] = []

    def connect(self, callback) -> None:
        if self.fail_connect:
            raise RuntimeError(f"connect failed: {self.name}")
        self.connect_calls.append(callback)
        self.callbacks.append(callback)

    def disconnect(self, callback) -> None:
        self.disconnect_calls.append(callback)
        if self.fail_disconnect_once:
            self.fail_disconnect_once = False
            raise RuntimeError(f"disconnect failed: {self.name}")
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def emit(self, value: str) -> None:
        for callback in tuple(self.callbacks):
            callback(value)


class _Registry:
    def __init__(
        self,
        *,
        fail_register_on: str | None = None,
        fail_unregister_once_on: str | None = None,
    ) -> None:
        self.values: dict[str, object] = {}
        self.fail_register_on = fail_register_on
        self.fail_unregister_once_on = fail_unregister_once_on
        self.register_calls: list[tuple[str, object]] = []
        self.unregister_calls: list[str] = []

    def register(self, key: str, value: object) -> None:
        self.register_calls.append((key, value))
        if key == self.fail_register_on:
            raise RuntimeError(f"register failed: {key}")
        self.values[key] = value

    def unregister(self, key: str) -> None:
        self.unregister_calls.append(key)
        if key == self.fail_unregister_once_on:
            self.fail_unregister_once_on = None
            raise RuntimeError(f"unregister failed: {key}")
        self.values.pop(key, None)

    def get(self, key: str, default=None):
        return self.values.get(key, default)

    def has(self, key: str) -> bool:
        return key in self.values


class _TextTarget:
    def __init__(self, text: str = "") -> None:
        self.text = text
        self.placeholder = ""
        self.tooltip = ""

    def setText(self, value: str) -> None:
        self.text = value

    def setPlaceholderText(self, value: str) -> None:
        self.placeholder = value

    def setToolTip(self, value: str) -> None:
        self.tooltip = value


class _ComboTarget:
    def __init__(self, count: int, current_index: int) -> None:
        self.labels = [f"old-{index}" for index in range(count)]
        self.current_index = current_index

    def setItemText(self, index: int, value: str) -> None:
        self.labels[index] = value

    def currentIndex(self) -> int:
        return self.current_index


class _TabsTarget(_ComboTarget):
    def setTabText(self, index: int, value: str) -> None:
        self.setItemText(index, value)


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


class _PackageManagerBridge:
    def __init__(self, info: dict) -> None:
        self.info = info
        self.created = 0
        self.panel = object()
        self.dock: _Dock | None = None

    def get_plugin_info(self):
        return self.info

    def create_dock_widget(self):
        self.created += 1
        self.dock = _Dock(self.panel)
        return self.dock

    def get_dock_config(self):
        raise AssertionError("declarative dock config must be authoritative")

    def get_menu_items(self):
        return []

    def get_toolbar_items(self):
        return []


def _normalized_info() -> dict:
    from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin
    from core.VitaLoom.core.editor_contribution_contract import (
        parse_editor_contributions,
    )

    info = PackageManagerPlugin().get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "PackageManagerPlugin", info["editor_contributions"]
            )
        ],
    }


def _load_plugin(
    monkeypatch,
    *,
    bus: _EventBus | None = None,
    registry: _Registry | None = None,
    loaded_signal: _Signal | None = None,
    unloaded_signal: _Signal | None = None,
):
    import builtin.editor_extensions.package_manager_plugin as module

    bus = bus or _EventBus()
    registry = registry or _Registry()
    loaded_signal = loaded_signal or _Signal("plugin_loaded")
    unloaded_signal = unloaded_signal or _Signal("plugin_unloaded")
    catalog = object()
    operations = object()

    monkeypatch.setattr(module, "PackageCatalogService", lambda _root: catalog)
    monkeypatch.setattr(
        module,
        "PackageOperationService",
        lambda _read_model, _configuration_host: operations,
    )
    monkeypatch.setattr(module, "get_project_world_read_model", lambda _context: object())
    monkeypatch.setattr(
        module,
        "get_project_world_configuration_host",
        lambda _context: object(),
    )
    monkeypatch.setattr(module.PackageManagerPlugin, "_get_repo_root", lambda _self: "repo")
    monkeypatch.setattr(module.PackageManagerPlugin, "_warm_package_cache", lambda _self: None)

    kernel = SimpleNamespace(
        plugin_loaded=loaded_signal,
        plugin_unloaded=unloaded_signal,
    )
    context = SimpleNamespace(event_bus=bus, services=registry, kernel=kernel)
    plugin = module.PackageManagerPlugin()
    plugin.on_load(context)
    return module, plugin, bus, registry, loaded_signal, unloaded_signal, catalog, operations


def test_package_manager_declares_one_qt_free_dock_shell() -> None:
    from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin

    info = PackageManagerPlugin().get_plugin_info()

    assert info["provides"] == ["dock", "command", "editor_contribution"]
    assert info["editor_contributions"][0] == {
            "id": "package_manager.surface",
            "kind": "dock_surface",
            "dock_id": "Package Manager",
            "title_key": "plugin_manager.title",
            "default_title": "项目插件",
            "area": "right",
            "default_visible": False,
            "can_close": True,
            "can_float": True,
            "can_move": True,
            "tabbed_with": None,
            "order": 70,
            "refresh_events": ["language_changed"],
        }


def test_package_manager_adapter_projects_and_refreshes_title_in_place() -> None:
    from PyQt6.QtCore import Qt
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    bus = _EventBus()
    translations = {"plugin_manager.title": "项目插件"}
    context = SimpleNamespace(
        event_bus=bus,
        i18n_tr=lambda key, default: translations.get(key, default),
    )
    layout = _Layout()
    kernel = SimpleNamespace(
        layout_manager=layout,
        get_context=lambda: context,
        plugin_loaded=_Signal("plugin_loaded"),
        plugin_unloaded=_Signal("plugin_unloaded"),
    )
    adapter = LegacyEditorPluginAdapter(kernel)
    info = _normalized_info()
    plugin = _PackageManagerBridge(info)
    adapter.bind_active_plugin_metadata_resolver(
        lambda: (("PackageManagerPlugin", info),)
    )
    adapter.bind_active_plugin_items_resolver(
        lambda: (("PackageManagerPlugin", plugin),)
    )

    adapter.after_plugin_load(plugin, "PackageManagerPlugin", info)
    dock = layout.docks["Package Manager"]
    panel = plugin.panel

    translations["plugin_manager.title"] = "Project Packages"
    bus.publish("language_changed")

    assert plugin.created == 1
    assert len(layout.add_calls) == 1
    assert layout.remove_calls == []
    assert layout.docks["Package Manager"] is dock
    assert dock.panel is panel
    assert dock.window_title == "Project Packages"
    assert layout.add_calls[0][1] == {
        "title": "Package Manager",
        "area": Qt.DockWidgetArea.RightDockWidgetArea,
        "default_visible": False,
        "can_close": True,
        "can_float": True,
        "can_move": True,
        "tabbed_with": None,
    }


def test_package_manager_retranslates_retained_content_without_rebuild() -> None:
    from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin

    values = {
        "package_manager.scope_hint": "scope-new",
        "package_manager.search_placeholder": "search-new",
        "package_manager.search_clear": "clear-new",
        "package_manager.filter.status.all": "all-new",
        "package_manager.filter.status.enabled": "enabled-new",
        "package_manager.filter.status.disabled": "disabled-new",
        "package_manager.filter.status.issues": "issues-new",
        "package_manager.filter.source.all": "source-all-new",
        "package_manager.filter.source.builtin": "builtin-new",
        "package_manager.filter.source.file": "file-new",
        "package_manager.filter.source.url": "url-new",
        "package_manager.tab.installed": "installed-new",
        "package_manager.tab.plugins": "plugins-new",
        "package_manager.tab.core": "core-new",
        "package_manager.tab.official": "official-new",
        "package_manager.tab.resources": "resources-new",
        "package_manager.tab.community": "community-new",
        "package_manager.tab.updates": "updates-new",
        "package_manager.refresh": "refresh-new",
        "package_manager.placeholder": "detail-new",
        "package_manager.result.placeholder": "result-new",
    }
    plugin = PackageManagerPlugin.__new__(PackageManagerPlugin)
    plugin.context = SimpleNamespace(
        i18n_tr=lambda key, default: values.get(key, default)
    )
    plugin.dock = object()
    plugin.window = None
    plugin._scope_hint = _TextTarget()
    plugin.search_input = _TextTarget("keep-query")
    plugin._clear_search_btn = _TextTarget()
    plugin.status_filter = _ComboTarget(4, 2)
    plugin.source_filter = _ComboTarget(4, 3)
    plugin.tab_bar = _TabsTarget(7, 5)
    plugin.queue_select_all_btn = None
    plugin.queue_invert_btn = None
    plugin.queue_clear_btn = None
    plugin.queue_only_checked_cb = None
    plugin._refresh_btn = _TextTarget()
    plugin._enable_btn = None
    plugin._disable_btn = None
    plugin._more_btn = None
    plugin._more_actions = {}
    plugin._float_open_action = None
    plugin._reload_btn = None
    plugin._unload_btn = None
    plugin._project_disable_btn = None
    plugin._project_enable_btn = None
    plugin.detail_text = _TextTarget()
    plugin.result_text = _TextTarget()
    plugin.package_list = object()
    plugin._ui_building = False
    plugin._pending_language_rebuild = False
    plugin._refresh = lambda: None
    plugin._on_selection_changed = lambda: None
    plugin._update_queue_stats_label = lambda: None
    plugin._update_float_toggle_btn_text = lambda: None

    dock_before = plugin.dock
    list_before = plugin.package_list
    plugin._on_language_changed(None)

    assert plugin.dock is dock_before
    assert plugin.package_list is list_before
    assert plugin.search_input.text == "keep-query"
    assert plugin.status_filter.currentIndex() == 2
    assert plugin.source_filter.currentIndex() == 3
    assert plugin.tab_bar.currentIndex() == 5
    assert plugin._scope_hint.text == "scope-new"
    assert plugin.search_input.placeholder == "search-new"
    assert plugin._clear_search_btn.text == "clear-new"
    assert plugin.status_filter.labels == [
        "all-new",
        "enabled-new",
        "disabled-new",
        "issues-new",
    ]
    assert plugin.source_filter.labels == [
        "source-all-new",
        "builtin-new",
        "file-new",
        "url-new",
    ]
    assert plugin.tab_bar.labels == [
        "installed-new",
        "plugins-new",
        "core-new",
        "official-new",
        "resources-new",
        "community-new",
        "updates-new",
    ]
    assert plugin._refresh_btn.text == "refresh-new"
    assert plugin.detail_text.placeholder == "detail-new"
    assert plugin.result_text.placeholder == "result-new"

    source = (
        RUNTIME / "builtin" / "editor_extensions" / "package_manager_plugin.py"
    ).read_text(encoding="utf-8-sig")
    language_body = source.split("def _on_language_changed", 1)[1].split("\n    def ", 1)[0]
    assert "_rebuild_dock_for_language" not in language_body
    assert ".remove_dock(" not in language_body
    assert ".add_dock(" not in language_body


def test_package_manager_acquires_and_releases_exact_resources(monkeypatch) -> None:
    from core.VitaLoom.core.service_keys import PACKAGE_CATALOG, PACKAGE_OPERATIONS

    (
        _module,
        plugin,
        bus,
        registry,
        loaded_signal,
        unloaded_signal,
        catalog,
        operations,
    ) = _load_plugin(monkeypatch)

    assert [name for name, _callback in bus.subscribe_calls] == [
        "language_changed",
        "project_opened",
        "project_plugins_synced",
        "project_manifest_issues",
    ]
    assert len(loaded_signal.callbacks) == 1
    assert len(unloaded_signal.callbacks) == 1
    assert registry.get(PACKAGE_CATALOG) is catalog
    assert registry.get(PACKAGE_OPERATIONS) is operations

    plugin.on_unload()

    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert loaded_signal.callbacks == []
    assert unloaded_signal.callbacks == []
    assert registry.has(PACKAGE_CATALOG) is False
    assert registry.has(PACKAGE_OPERATIONS) is False
    assert plugin._event_subscriptions == []
    assert plugin._kernel_signal_connections == []
    assert plugin._service_publication is None
    assert plugin.catalog_service is None
    assert plugin.operation_service is None

    plugin.on_unload()
    assert len(bus.unsubscribe_calls) == 4
    assert len(loaded_signal.disconnect_calls) == 1
    assert len(unloaded_signal.disconnect_calls) == 1


def test_package_manager_partial_event_failure_rolls_back(monkeypatch) -> None:
    import builtin.editor_extensions.package_manager_plugin as module

    bus = _EventBus(fail_subscribe_on="project_plugins_synced")
    registry = _Registry()
    plugin = module.PackageManagerPlugin()
    context = SimpleNamespace(event_bus=bus, services=registry, kernel=None)

    monkeypatch.setattr(module, "PackageCatalogService", lambda _root: object())
    monkeypatch.setattr(module.PackageManagerPlugin, "_get_repo_root", lambda _self: "repo")

    with pytest.raises(RuntimeError, match="project_plugins_synced"):
        plugin.on_load(context)

    assert [name for name, _callback in bus.subscribe_calls] == [
        "language_changed",
        "project_opened",
    ]
    assert [name for name, _callback in bus.unsubscribe_calls] == [
        "project_opened",
        "language_changed",
    ]
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert plugin._event_subscriptions == []
    assert plugin._service_publication is None


def test_package_manager_publication_failure_rolls_back_events(monkeypatch) -> None:
    from core.VitaLoom.core.service_keys import PACKAGE_OPERATIONS

    bus = _EventBus()
    registry = _Registry(fail_register_on=PACKAGE_OPERATIONS)

    with pytest.raises(RuntimeError, match="register failed"):
        _load_plugin(monkeypatch, bus=bus, registry=registry)

    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert registry.values == {}


def test_package_manager_signal_failure_rolls_back_publication_and_events(
    monkeypatch,
) -> None:
    from core.VitaLoom.core.service_keys import PACKAGE_CATALOG, PACKAGE_OPERATIONS

    bus = _EventBus()
    registry = _Registry()
    loaded_signal = _Signal("plugin_loaded")
    unloaded_signal = _Signal("plugin_unloaded", fail_connect=True)

    with pytest.raises(RuntimeError, match="connect failed: plugin_unloaded"):
        _load_plugin(
            monkeypatch,
            bus=bus,
            registry=registry,
            loaded_signal=loaded_signal,
            unloaded_signal=unloaded_signal,
        )

    assert loaded_signal.callbacks == []
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert registry.has(PACKAGE_CATALOG) is False
    assert registry.has(PACKAGE_OPERATIONS) is False


def test_package_manager_release_failures_are_retained_and_retryable(
    monkeypatch,
) -> None:
    from core.VitaLoom.core.service_keys import PACKAGE_CATALOG, PACKAGE_OPERATIONS

    bus = _EventBus(fail_unsubscribe_once_on="project_opened")
    registry = _Registry(fail_unregister_once_on=PACKAGE_OPERATIONS)
    loaded_signal = _Signal("plugin_loaded", fail_disconnect_once=True)
    unloaded_signal = _Signal("plugin_unloaded")
    (
        _module,
        plugin,
        _bus,
        _registry,
        _loaded,
        _unloaded,
        catalog,
        operations,
    ) = _load_plugin(
        monkeypatch,
        bus=bus,
        registry=registry,
        loaded_signal=loaded_signal,
        unloaded_signal=unloaded_signal,
    )

    with pytest.raises(RuntimeError):
        plugin.on_unload()

    assert len(plugin._event_subscriptions) == 1
    assert len(plugin._kernel_signal_connections) == 1
    assert plugin._service_publication is not None
    assert plugin.catalog_service is catalog
    assert plugin.operation_service is operations
    assert registry.has(PACKAGE_CATALOG) is False
    assert registry.get(PACKAGE_OPERATIONS) is operations

    plugin.on_unload()

    assert plugin._event_subscriptions == []
    assert plugin._kernel_signal_connections == []
    assert plugin._service_publication is None
    assert plugin.catalog_service is None
    assert plugin.operation_service is None
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert loaded_signal.callbacks == []
    assert unloaded_signal.callbacks == []
    assert registry.has(PACKAGE_CATALOG) is False
    assert registry.has(PACKAGE_OPERATIONS) is False


def test_package_manager_primary_load_error_survives_rollback_failure(
    monkeypatch,
) -> None:
    import builtin.editor_extensions.package_manager_plugin as module
    from core.VitaLoom.core.service_keys import PACKAGE_OPERATIONS

    bus = _EventBus()
    registry = _Registry(fail_unregister_once_on=PACKAGE_OPERATIONS)
    loaded_signal = _Signal("plugin_loaded")
    unloaded_signal = _Signal("plugin_unloaded", fail_connect=True)
    catalog = object()
    operations = object()

    monkeypatch.setattr(module, "PackageCatalogService", lambda _root: catalog)
    monkeypatch.setattr(
        module,
        "PackageOperationService",
        lambda _read_model, _configuration_host: operations,
    )
    monkeypatch.setattr(module, "get_project_world_read_model", lambda _context: object())
    monkeypatch.setattr(
        module,
        "get_project_world_configuration_host",
        lambda _context: object(),
    )
    monkeypatch.setattr(module.PackageManagerPlugin, "_get_repo_root", lambda _self: "repo")
    monkeypatch.setattr(module.PackageManagerPlugin, "_warm_package_cache", lambda _self: None)

    plugin = module.PackageManagerPlugin()
    context = SimpleNamespace(
        event_bus=bus,
        services=registry,
        kernel=SimpleNamespace(
            plugin_loaded=loaded_signal,
            plugin_unloaded=unloaded_signal,
        ),
    )

    with pytest.raises(RuntimeError, match="connect failed: plugin_unloaded"):
        plugin.on_load(context)

    assert plugin._service_publication is not None
    assert registry.get(PACKAGE_OPERATIONS) is operations
    assert plugin._kernel_signal_connections == []
    assert loaded_signal.callbacks == []
    assert plugin._event_subscriptions == []

    plugin.on_unload()
    assert plugin._service_publication is None
    assert registry.has(PACKAGE_OPERATIONS) is False
