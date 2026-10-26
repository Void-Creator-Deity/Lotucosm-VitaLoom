# -*- coding: utf-8 -*-
"""E44 SceneViewport shell projection and exact event lifecycle red lines."""
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
    "project_opened",
    "scene_loaded",
    "create_entity",
    "delete_entity",
    "add_script_to_entity",
    "add_component_to_entity",
    "set_entity_sprite_path",
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


class _SceneViewport:
    instances: list['_SceneViewport'] = []

    def __init__(self) -> None:
        self.deleted = 0
        self.retranslate_calls = 0
        self.instances.append(self)

    def deleteLater(self) -> None:
        self.deleted += 1

    def retranslate_ui(self) -> None:
        self.retranslate_calls += 1


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
    import builtin.editor_extensions.scene_viewport_plugin as module
    import core.VitaLoom.viewports.scene_viewport as viewport_module

    bus = bus or _EventBus()
    translations = translations or {}
    kernel = SimpleNamespace(layout_manager=_ForbiddenTabs())
    context = SimpleNamespace(
        event_bus=bus,
        kernel=kernel,
        i18n_tr=lambda key, default: translations.get(key, default),
    )
    monkeypatch.setattr(viewport_module, "SceneViewport", _SceneViewport)
    plugin = module.SceneViewportPlugin()
    plugin.on_load(context)
    return module, plugin, context, bus, translations


def test_scene_viewport_declares_one_json_safe_qt_free_shell() -> None:
    from builtin.editor_extensions.scene_viewport_plugin import SceneViewportPlugin

    info = SceneViewportPlugin().get_plugin_info()
    assert info["provides"] == ["viewport", "editor_contribution"]
    assert info["editor_contributions"] == [
        {
            "id": "scene.surface",
            "kind": "viewport_surface",
            "viewport_id": "scene",
            "name_key": "scene_viewport.name",
            "default_name": "场景",
            "order": 10,
            "refresh_events": ["language_changed"],
        }
    ]
    json.dumps(info["editor_contributions"], ensure_ascii=False)


def test_create_is_idempotent_and_owns_exact_events_once(monkeypatch) -> None:
    _module, plugin, _context, bus, _translations = _load_plugin(monkeypatch)

    viewport = plugin.create_viewport_widget()

    assert plugin.create_viewport_widget() is viewport
    assert [name for name, _callback in bus.subscribe_calls] == EVENT_NAMES
    assert [name for name, _callback in plugin._event_subscriptions] == EVENT_NAMES

    plugin.on_unload()

    assert [name for name, _callback in bus.unsubscribe_calls] == list(
        reversed(EVENT_NAMES)
    )
    assert plugin._event_subscriptions == []
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert viewport.deleted == 0
    assert plugin.viewport is None

    plugin.on_unload()
    assert len(bus.unsubscribe_calls) == len(EVENT_NAMES)
    assert viewport.deleted == 0


def test_partial_subscription_failure_reverses_rollback_and_discards_widget(
    monkeypatch,
) -> None:
    bus = _EventBus(fail_subscribe_on="add_component_to_entity")
    _module, plugin, _context, _bus, _translations = _load_plugin(
        monkeypatch, bus=bus
    )

    with pytest.raises(RuntimeError, match="subscribe failed: add_component_to_entity"):
        plugin.create_viewport_widget()

    successful = EVENT_NAMES[:5]
    assert [name for name, _callback in bus.subscribe_calls] == successful
    assert [name for name, _callback in bus.unsubscribe_calls] == list(
        reversed(successful)
    )
    assert plugin._event_subscriptions == []
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert plugin.viewport is None
    assert _SceneViewport.instances[-1].deleted == 1


def test_failed_unsubscribe_retains_only_exact_event_for_retry(monkeypatch) -> None:
    bus = _EventBus(fail_unsubscribe_once_on="add_component_to_entity")
    _module, plugin, _context, _bus, _translations = _load_plugin(
        monkeypatch, bus=bus
    )
    viewport = plugin.create_viewport_widget()

    with pytest.raises(RuntimeError, match="unsubscribe failed: add_component_to_entity"):
        plugin.on_unload()

    assert [name for name, _callback in plugin._event_subscriptions] == [
        "add_component_to_entity"
    ]
    assert plugin.viewport is viewport
    assert viewport.deleted == 0
    assert len(bus.callbacks["add_component_to_entity"]) == 1
    assert all(
        not callbacks
        for name, callbacks in bus.callbacks.items()
        if name != "add_component_to_entity"
    )

    plugin.on_unload()

    assert plugin._event_subscriptions == []
    assert plugin.viewport is None
    assert viewport.deleted == 0
    assert all(not callbacks for callbacks in bus.callbacks.values())


def test_language_change_refreshes_retained_content_without_host_tab_access(
    monkeypatch,
) -> None:
    _module, plugin, _context, bus, _translations = _load_plugin(monkeypatch)
    viewport = plugin.create_viewport_widget()

    bus.publish("language_changed")

    assert plugin.viewport is viewport
    assert viewport.retranslate_calls == 1


def test_legacy_viewport_getters_remain_available(monkeypatch) -> None:
    translations = {"scene_viewport.name": "Scene"}
    _module, plugin, _context, _bus, _translations = _load_plugin(
        monkeypatch, translations=translations
    )

    assert plugin.get_viewport_id() == "scene"
    assert plugin.get_viewport_name() == "Scene"


def test_scene_language_refresh_source_does_not_penetrate_host_tabs() -> None:
    source = (
        RUNTIME / "builtin" / "editor_extensions" / "scene_viewport_plugin.py"
    ).read_text(encoding="utf-8-sig")

    assert "viewport_tabs" not in source
    assert "setTabText" not in source
