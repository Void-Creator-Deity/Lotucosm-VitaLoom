# -*- coding: utf-8 -*-
"""E45 GameViewport shell, exact event lease, and teardown red lines."""
from __future__ import annotations

import json
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

EVENT_NAMES = [
    "simulation_play",
    "simulation_pause",
    "simulation_stop",
    "language_changed",
]


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


class _GameViewport:
    instances: list["_GameViewport"] = []

    def __init__(self) -> None:
        self.deleted = 0
        self.retranslate_calls = 0
        self.register_calls = 0
        self.release_calls = 0
        self.capabilities_active = False
        self.editor_context = None
        self._publication = None
        self.instances.append(self)

    def register_as_sr_host(self) -> None:
        from core.VitaLoom.core.capability_publication import publish_capabilities
        from core.VitaLoom.core.service_keys import (
            SIMULATION_SR_HOST,
            SR_SELECTED_IDENTITY_HOST,
        )

        self.register_calls += 1
        self._publication = publish_capabilities(
            self.editor_context.services,
            owner="test.game-viewport",
            capabilities={
                SIMULATION_SR_HOST: self,
                SR_SELECTED_IDENTITY_HOST: self,
            },
        )
        self.capabilities_active = True

    def dispose_runtime_capabilities(self) -> None:
        self.release_calls += 1
        if self._publication is not None:
            self._publication.release()
            self._publication = None
        self.capabilities_active = False

    def deleteLater(self) -> None:
        assert not self.capabilities_active, (
            "runtime capabilities must be released before surface destruction"
        )
        self.deleted += 1

    def retranslate_ui(self) -> None:
        self.retranslate_calls += 1

    def start_simulation(self) -> None:
        pass

    def pause_simulation(self) -> None:
        pass

    def stop_simulation(self) -> None:
        pass


class _ForbiddenTabs:
    @property
    def viewport_tabs(self):
        raise AssertionError("plugin must not access Host viewport_tabs")


def _load_plugin(
    monkeypatch,
    *,
    bus: _EventBus | None = None,
    translations: dict[str, str] | None = None,
):
    import builtin.editor_extensions.game_viewport_plugin as module
    import core.VitaLoom.viewports.game_viewport as viewport_module

    bus = bus or _EventBus()
    translations = translations or {}
    kernel = SimpleNamespace(layout_manager=_ForbiddenTabs())
    from core.VitaLoom.core.editor_context import ServiceRegistry

    context = SimpleNamespace(
        event_bus=bus,
        kernel=kernel,
        services=ServiceRegistry(),
        i18n_tr=lambda key, default: translations.get(key, default),
    )
    monkeypatch.setattr(viewport_module, "GameViewport", _GameViewport)
    plugin = module.GameViewportPlugin()
    plugin.on_load(context)
    return module, plugin, context, bus, translations


def test_game_viewport_declares_one_json_safe_qt_free_shell() -> None:
    from builtin.editor_extensions.game_viewport_plugin import GameViewportPlugin

    info = GameViewportPlugin().get_plugin_info()
    assert info["provides"] == ["viewport", "editor_contribution"]
    assert info["editor_contributions"] == [
        {
            "id": "game.surface",
            "kind": "viewport_surface",
            "viewport_id": "game",
            "name_key": "game_viewport.name",
            "default_name": "游戏",
            "order": 20,
            "refresh_events": ["language_changed"],
        }
    ]
    json.dumps(info["editor_contributions"], ensure_ascii=False)


def test_create_is_idempotent_and_owns_exact_events_once(monkeypatch) -> None:
    _module, plugin, _context, bus, _translations = _load_plugin(monkeypatch)

    assert bus.subscribe_calls == []
    viewport = plugin.create_viewport_widget()

    assert plugin.create_viewport_widget() is viewport
    assert viewport.register_calls == 1
    assert [name for name, _callback in bus.subscribe_calls] == EVENT_NAMES
    assert [name for name, _callback in plugin._event_subscriptions] == EVENT_NAMES

    plugin.prepare_host_teardown()

    assert [name for name, _callback in bus.unsubscribe_calls] == list(
        reversed(EVENT_NAMES)
    )
    assert plugin._event_subscriptions == []
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert viewport.release_calls == 1
    assert viewport.deleted == 0

    plugin.on_unload()
    plugin.on_unload()

    assert plugin.viewport is None
    assert viewport.release_calls == 1
    assert len(bus.unsubscribe_calls) == len(EVENT_NAMES)
    assert viewport.deleted == 0


def test_partial_subscription_failure_reverses_rollback_and_discards_widget(
    monkeypatch,
) -> None:
    bus = _EventBus(fail_subscribe_on="simulation_stop")
    _module, plugin, _context, bus, _translations = _load_plugin(
        monkeypatch, bus=bus
    )

    with pytest.raises(RuntimeError, match="subscribe failed: simulation_stop"):
        plugin.create_viewport_widget()

    viewport = _GameViewport.instances[-1]
    assert [name for name, _callback in bus.subscribe_calls] == [
        "simulation_play",
        "simulation_pause",
    ]
    assert [name for name, _callback in bus.unsubscribe_calls] == [
        "simulation_pause",
        "simulation_play",
    ]
    assert viewport.release_calls == 1
    assert viewport.deleted == 1
    assert plugin.viewport is None
    assert plugin._event_subscriptions == []


def test_failed_unsubscribe_retains_only_exact_event_for_retry(monkeypatch) -> None:
    bus = _EventBus(fail_unsubscribe_once_on="simulation_pause")
    _module, plugin, _context, bus, _translations = _load_plugin(
        monkeypatch, bus=bus
    )
    viewport = plugin.create_viewport_widget()

    with pytest.raises(RuntimeError, match="unsubscribe failed: simulation_pause"):
        plugin.prepare_host_teardown()

    assert [name for name, _callback in plugin._event_subscriptions] == [
        "simulation_pause"
    ]
    assert viewport.release_calls == 1
    assert viewport.deleted == 0

    plugin.prepare_host_teardown()
    plugin.on_unload()

    assert plugin._event_subscriptions == []
    assert viewport.release_calls == 1
    assert plugin.viewport is None


def test_language_change_refreshes_content_without_host_tab_access(monkeypatch) -> None:
    _module, plugin, _context, bus, _translations = _load_plugin(monkeypatch)
    viewport = plugin.create_viewport_widget()

    bus.publish("language_changed")

    assert plugin.viewport is viewport
    assert viewport.retranslate_calls == 1


def test_legacy_viewport_getters_remain_available(monkeypatch) -> None:
    translations = {"game_viewport.name": "Game"}
    _module, plugin, _context, _bus, _translations = _load_plugin(
        monkeypatch, translations=translations
    )

    assert plugin.get_viewport_id() == "game"
    assert plugin.get_viewport_name() == "Game"


def test_game_language_refresh_source_does_not_penetrate_host_tabs() -> None:
    source = (
        RUNTIME / "builtin" / "editor_extensions" / "game_viewport_plugin.py"
    ).read_text(encoding="utf-8-sig")

    assert "viewport_tabs" not in source
    assert "setTabText" not in source
    assert ".deleteLater()" not in source.split("def on_unload", 1)[1].split(
        "def create_viewport_widget", 1
    )[0]



def test_capability_replacements_survive_exact_plugin_teardown(monkeypatch) -> None:
    from core.VitaLoom.core.service_keys import (
        SIMULATION_SR_HOST,
        SR_SELECTED_IDENTITY_HOST,
    )

    _module, plugin, context, _bus, _translations = _load_plugin(monkeypatch)
    viewport = plugin.create_viewport_widget()
    assert context.services.get(SIMULATION_SR_HOST) is viewport
    assert context.services.get(SR_SELECTED_IDENTITY_HOST) is viewport

    sr_replacement = object()
    selection_replacement = object()
    context.services.register(SIMULATION_SR_HOST, sr_replacement)
    context.services.register(SR_SELECTED_IDENTITY_HOST, selection_replacement)

    plugin.prepare_host_teardown()
    plugin.on_unload()

    assert context.services.get(SIMULATION_SR_HOST) is sr_replacement
    assert context.services.get(SR_SELECTED_IDENTITY_HOST) is selection_replacement
    assert viewport.release_calls == 1


def test_real_host_shutdown_releases_capabilities_before_layout_deletion_and_reloads(
    monkeypatch,
) -> None:
    from core.VitaLoom.core.editor_context import ServiceRegistry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
    from core.VitaLoom.core.service_keys import (
        SIMULATION_SR_HOST,
        SR_SELECTED_IDENTITY_HOST,
    )
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    class Signal:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def emit(self, plugin_id: str) -> None:
            self.calls.append(plugin_id)

    class Layout:
        def __init__(self) -> None:
            self.viewports: dict[str, _GameViewport] = {}
            self.remove_calls: list[str] = []
            self.add_calls: list[str] = []

        def add_viewport(self, viewport_id, widget, provider=None, display_name=None):
            self.add_calls.append(viewport_id)
            self.viewports[viewport_id] = widget

        def set_viewport_display_name(self, viewport_id, display_name):
            assert viewport_id in self.viewports

        def remove_viewport(self, viewport_id):
            self.remove_calls.append(viewport_id)
            widget = self.viewports.pop(viewport_id, None)
            if widget is not None:
                widget.deleteLater()

        def remove_plugin_ui(self, _plugin_id):
            pass

        def process_pending_dock_tabify(self):
            pass

    services = ServiceRegistry()
    bus = _EventBus()
    context = SimpleNamespace(
        event_bus=bus,
        services=services,
        i18n_tr=lambda _key, default: default,
    )
    kernel = SimpleNamespace(
        layout_manager=Layout(),
        get_context=lambda: context,
        plugin_loaded=Signal(),
        plugin_unloaded=Signal(),
    )
    context.kernel = kernel
    adapter = LegacyEditorPluginAdapter(kernel)

    def activate_one():
        import builtin.editor_extensions.game_viewport_plugin as module
        import core.VitaLoom.viewports.game_viewport as viewport_module

        monkeypatch.setattr(viewport_module, "GameViewport", _GameViewport)
        plugin = module.GameViewportPlugin()
        plugin.on_load(context)
        info = plugin.get_plugin_info()
        host = RuntimePluginHost(adapter=adapter)
        host.register_plugin(
            plugin,
            scope=host.SCOPE_OFFICIAL,
            source="game_viewport_plugin.py",
        )
        host.loaded_plugins["GameViewportPlugin"] = plugin
        host.resolve_dependencies()
        copied_info = host.plugin_metadata["GameViewportPlugin"]
        adapter.after_plugin_load(
            plugin, "GameViewportPlugin", copied_info
        )
        return host, plugin, plugin.viewport

    first_host, first_plugin, first_viewport = activate_one()
    assert first_viewport is not None
    assert services.get(SIMULATION_SR_HOST) is first_viewport
    assert services.get(SR_SELECTED_IDENTITY_HOST) is first_viewport

    first_report = first_host.shutdown_plugins()

    assert first_report["status"] == "settled"
    assert first_plugin.viewport is None
    assert first_viewport.release_calls == 1
    assert first_viewport.deleted == 1
    assert kernel.layout_manager.remove_calls == ["game"]
    assert services.has(SIMULATION_SR_HOST) is False
    assert services.has(SR_SELECTED_IDENTITY_HOST) is False

    second_host, second_plugin, second_viewport = activate_one()
    assert second_viewport is not first_viewport
    assert kernel.layout_manager.viewports == {"game": second_viewport}
    assert services.get(SIMULATION_SR_HOST) is second_viewport

    second_report = second_host.shutdown_plugins()

    assert second_report["status"] == "settled"
    assert second_plugin.viewport is None
    assert second_viewport.deleted == 1
    assert kernel.layout_manager.add_calls == ["game", "game"]
    assert kernel.layout_manager.remove_calls == ["game", "game"]
