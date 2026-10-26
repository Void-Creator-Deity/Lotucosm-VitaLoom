# -*- coding: utf-8 -*-
"""E38 Console dock shell and exact logging/capability lifecycle."""
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
        fail_subscribe: bool = False,
        fail_unsubscribe_once: bool = False,
    ) -> None:
        self.fail_subscribe = fail_subscribe
        self.fail_unsubscribe_once = fail_unsubscribe_once
        self.callbacks: dict[str, list] = {}
        self.subscribe_calls: list[tuple[str, object]] = []
        self.unsubscribe_calls: list[tuple[str, object]] = []

    def subscribe(self, event_name: str, callback) -> None:
        if self.fail_subscribe:
            raise RuntimeError("subscribe failed")
        self.subscribe_calls.append((event_name, callback))
        self.callbacks.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name: str, callback) -> None:
        self.unsubscribe_calls.append((event_name, callback))
        if self.fail_unsubscribe_once:
            self.fail_unsubscribe_once = False
            raise RuntimeError("unsubscribe failed")
        callbacks = self.callbacks.get(event_name, [])
        if callback in callbacks:
            callbacks.remove(callback)

    def publish(self, event_name: str, data=None) -> None:
        for callback in tuple(self.callbacks.get(event_name, ())):
            callback(data)


class _Registry:
    _MISSING = object()

    def __init__(self) -> None:
        self.values: dict[str, object] = {}

    def register(self, key: str, value: object) -> None:
        self.values[key] = value

    def get(self, key: str, default=None):
        return self.values.get(key, default)

    def unregister(self, key: str) -> None:
        self.values.pop(key, None)

    def has(self, key: str) -> bool:
        return key in self.values


class _Panel:
    def __init__(self) -> None:
        self.retranslate_calls = 0

    def retranslate_ui(self) -> None:
        self.retranslate_calls += 1


class _Dock:
    def __init__(self, *_args, **_kwargs) -> None:
        self.object_name = ""
        self.window_title = "legacy"
        self.panel = None
        self.deleted = 0

    def setObjectName(self, value: str) -> None:
        self.object_name = value

    def setWindowTitle(self, value: str) -> None:
        self.window_title = value

    def setWidget(self, panel: object) -> None:
        self.panel = panel

    def deleteLater(self) -> None:
        self.deleted += 1


class _Signal:
    def emit(self, _plugin_id: str) -> None:
        pass


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


class _ConsoleBridge:
    def __init__(self, info: dict) -> None:
        self.info = info
        self.created = 0
        self.console_panel = _Panel()
        self.dock: _Dock | None = None

    def get_plugin_info(self):
        return self.info

    def create_dock_widget(self):
        self.created += 1
        self.dock = _Dock()
        self.dock.setWidget(self.console_panel)
        return self.dock

    def get_dock_config(self):
        raise AssertionError("declarative dock config must be authoritative")


def _normalized_console_info() -> dict:
    from builtin.editor_extensions.console_plugin import ConsolePlugin
    from core.VitaLoom.core.editor_contribution_contract import (
        parse_editor_contributions,
    )

    info = ConsolePlugin().get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "ConsolePlugin", info["editor_contributions"]
            )
        ],
    }


def _loaded_plugin(monkeypatch):
    import builtin.editor_extensions.console_plugin as module
    import core.VitaLoom.ui.console as console_module

    monkeypatch.setattr(module, "QDockWidget", _Dock)
    monkeypatch.setattr(console_module, "ConsolePanel", _Panel)
    bus = _EventBus()
    registry = _Registry()
    plugin = module.ConsolePlugin()
    plugin.on_load(
        SimpleNamespace(
            event_bus=bus,
            services=registry,
            kernel=None,
            i18n_tr=lambda _key, default: default,
        )
    )
    return module, plugin, bus, registry


def test_console_declares_one_qt_free_dock_shell() -> None:
    from builtin.editor_extensions.console_plugin import ConsolePlugin

    info = ConsolePlugin().get_plugin_info()

    assert info["provides"] == ["dock", "editor_contribution"]
    assert info["editor_contributions"] == [
        {
            "id": "console.surface",
            "kind": "dock_surface",
            "dock_id": "Console",
            "title_key": "console.title",
            "default_title": "控制台",
            "area": "bottom",
            "default_visible": True,
            "can_close": True,
            "can_float": True,
            "can_move": True,
            "tabbed_with": "Project",
            "order": 60,
            "refresh_events": ["language_changed"],
        }
    ]

    source = (
        RUNTIME / "builtin" / "editor_extensions" / "console_plugin.py"
    ).read_text(encoding="utf-8-sig")
    assert ".setWindowTitle(" not in source


def test_console_adapter_refreshes_title_in_place_and_preserves_panel() -> None:
    from PyQt6.QtCore import Qt
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    bus = _EventBus()
    translations = {"console.title": "控制台"}
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
    info = _normalized_console_info()
    plugin = _ConsoleBridge(info)
    adapter.bind_active_plugin_metadata_resolver(lambda: (("ConsolePlugin", info),))
    adapter.bind_active_plugin_items_resolver(lambda: (("ConsolePlugin", plugin),))

    adapter.after_plugin_load(plugin, "ConsolePlugin", info)
    dock = layout.docks["Console"]
    panel = plugin.console_panel

    translations["console.title"] = "Console"
    bus.publish("language_changed")

    assert plugin.created == 1
    assert len(layout.add_calls) == 1
    assert layout.remove_calls == []
    assert layout.docks["Console"] is dock
    assert plugin.console_panel is panel
    assert dock.panel is panel
    assert dock.window_title == "Console"
    assert layout.add_calls[0][1] == {
        "title": "Console",
        "area": Qt.DockWidgetArea.BottomDockWidgetArea,
        "default_visible": True,
        "can_close": True,
        "can_float": True,
        "can_move": True,
        "tabbed_with": "Project",
    }


def test_console_panel_exposes_retranslation_without_self_subscription() -> None:
    from core.VitaLoom.ui.console import ConsolePanel

    source = (
        RUNTIME / "core" / "VitaLoom" / "ui" / "console.py"
    ).read_text(encoding="utf-8-sig")
    assert 'event_bus.subscribe("language_changed"' not in source

    class _TextTarget:
        def __init__(self) -> None:
            self.value = ""

        def setText(self, value: str) -> None:
            self.value = value

    panel = ConsolePanel.__new__(ConsolePanel)
    panel.editor_context = SimpleNamespace(
        i18n_tr=lambda key, default: {
            "console.title": "Console",
            "console.action.clear": "Clear",
        }.get(key, default)
    )
    panel.title_label = _TextTarget()
    panel.clear_button = _TextTarget()

    panel.retranslate_ui()

    assert panel.title_label.value == "Console"
    assert panel.clear_button.value == "Clear"


def test_console_plugin_owns_one_language_binding_and_releases_it() -> None:
    from builtin.editor_extensions.console_plugin import ConsolePlugin

    bus = _EventBus()
    plugin = ConsolePlugin()
    plugin.on_load(SimpleNamespace(event_bus=bus, kernel=None))
    panel = _Panel()
    plugin.console_panel = panel

    bus.publish("language_changed")
    assert panel.retranslate_calls == 1

    plugin.on_unload()
    assert [name for name, _ in bus.subscribe_calls] == ["language_changed"]
    assert [name for name, _ in bus.unsubscribe_calls] == ["language_changed"]
    assert bus.callbacks["language_changed"] == []

    bus.publish("language_changed")
    assert panel.retranslate_calls == 1

    plugin.on_unload()
    assert len(bus.unsubscribe_calls) == 1


def test_console_load_failure_leaves_no_subscription_or_state() -> None:
    from builtin.editor_extensions.console_plugin import ConsolePlugin

    bus = _EventBus(fail_subscribe=True)
    plugin = ConsolePlugin()

    with pytest.raises(RuntimeError, match="subscribe failed"):
        plugin.on_load(SimpleNamespace(event_bus=bus, kernel=None))

    assert plugin._event_subscriptions == []
    assert bus.callbacks == {}
    assert plugin.dock is None
    assert plugin.console_panel is None


def test_console_adapter_acquires_once_and_releases_in_reverse_order(
    monkeypatch,
) -> None:
    from core.VitaLoom.core.service_keys import UI_CONSOLE_PANEL

    module, plugin, _bus, registry = _loaded_plugin(monkeypatch)
    calls: list[tuple[str, object]] = []
    original_publish = module.publish_capabilities

    def publish(*args, **kwargs):
        lease = original_publish(*args, **kwargs)
        original_release = lease.release

        def release():
            calls.append(("release", registry.get(UI_CONSOLE_PANEL)))
            return original_release()

        lease.release = release
        calls.append(("publish", kwargs["capabilities"][UI_CONSOLE_PANEL]))
        return lease

    handler = object()

    def attach(panel):
        calls.append(("attach", panel))
        return handler

    def detach(exact_handler):
        calls.append(("detach", exact_handler))
        return True

    monkeypatch.setattr(module, "publish_capabilities", publish)
    monkeypatch.setattr(module, "attach_console_logging", attach)
    monkeypatch.setattr(module, "detach_console_logging", detach)

    dock = plugin.create_dock_widget()
    panel = dock.panel

    assert registry.get(UI_CONSOLE_PANEL) is panel
    assert plugin.console_panel is panel
    assert plugin._logging_handler is handler
    assert [name for name, _ in calls] == ["publish", "attach"]

    plugin.on_unload()

    assert [name for name, _ in calls] == [
        "publish",
        "attach",
        "detach",
        "release",
    ]
    assert registry.has(UI_CONSOLE_PANEL) is False
    assert plugin._logging_handler is None
    assert plugin._console_publication is None
    assert plugin.console_panel is None
    assert plugin.dock is None


def test_console_attach_failure_rolls_back_publication_and_construction(
    monkeypatch,
) -> None:
    from core.VitaLoom.core.service_keys import UI_CONSOLE_PANEL

    module, plugin, _bus, registry = _loaded_plugin(monkeypatch)

    def fail_attach(_panel):
        raise RuntimeError("attach failed")

    monkeypatch.setattr(module, "attach_console_logging", fail_attach)

    with pytest.raises(RuntimeError, match="attach failed"):
        plugin.create_dock_widget()

    assert registry.has(UI_CONSOLE_PANEL) is False
    assert plugin._console_publication is None
    assert plugin._logging_handler is None
    assert plugin.console_panel is None
    assert plugin.dock is None


def test_console_publication_failure_does_not_attach_or_keep_construction(
    monkeypatch,
) -> None:
    module, plugin, _bus, _registry = _loaded_plugin(monkeypatch)
    attach_calls = 0

    def fail_publish(*_args, **_kwargs):
        raise RuntimeError("publish failed")

    def attach(_panel):
        nonlocal attach_calls
        attach_calls += 1
        return object()

    monkeypatch.setattr(module, "publish_capabilities", fail_publish)
    monkeypatch.setattr(module, "attach_console_logging", attach)

    with pytest.raises(RuntimeError, match="publish failed"):
        plugin.create_dock_widget()

    assert attach_calls == 0
    assert plugin._console_publication is None
    assert plugin._logging_handler is None
    assert plugin.console_panel is None
    assert plugin.dock is None


def test_console_detach_failure_still_releases_capability_and_is_retryable(
    monkeypatch,
) -> None:
    from core.VitaLoom.core.service_keys import UI_CONSOLE_PANEL

    module, plugin, _bus, registry = _loaded_plugin(monkeypatch)
    handler = object()
    detach_calls = 0

    monkeypatch.setattr(module, "attach_console_logging", lambda _panel: handler)

    def detach(exact_handler):
        nonlocal detach_calls
        assert exact_handler is handler
        detach_calls += 1
        if detach_calls == 1:
            raise RuntimeError("detach failed")
        return True

    monkeypatch.setattr(module, "detach_console_logging", detach)
    plugin.create_dock_widget()
    dock = plugin.dock
    panel = plugin.console_panel

    with pytest.raises(RuntimeError, match="detach failed"):
        plugin.on_unload()

    assert registry.has(UI_CONSOLE_PANEL) is False
    assert plugin._console_publication is None
    assert plugin._logging_handler is handler
    assert plugin.dock is dock
    assert plugin.console_panel is panel

    plugin.on_unload()
    assert detach_calls == 2
    assert plugin._logging_handler is None
    assert plugin.dock is None
    assert plugin.console_panel is None


def test_console_repeated_create_replaces_owned_adapter_without_leak(
    monkeypatch,
) -> None:
    from core.VitaLoom.core.service_keys import UI_CONSOLE_PANEL

    module, plugin, _bus, registry = _loaded_plugin(monkeypatch)
    handlers: list[object] = []
    detached: list[object] = []

    def attach(_panel):
        handler = object()
        handlers.append(handler)
        return handler

    monkeypatch.setattr(module, "attach_console_logging", attach)
    monkeypatch.setattr(
        module,
        "detach_console_logging",
        lambda handler: detached.append(handler) is None or True,
    )

    first_dock = plugin.create_dock_widget()
    first_panel = plugin.console_panel
    second_dock = plugin.create_dock_widget()
    second_panel = plugin.console_panel

    assert first_dock is not second_dock
    assert first_panel is not second_panel
    assert first_dock.deleted == 1
    assert detached == [handlers[0]]
    assert registry.get(UI_CONSOLE_PANEL) is second_panel

    plugin.on_unload()
    assert detached == handlers
    assert registry.has(UI_CONSOLE_PANEL) is False


def test_console_event_unsubscribe_failure_is_retained_for_retry() -> None:
    from builtin.editor_extensions.console_plugin import ConsolePlugin

    bus = _EventBus(fail_unsubscribe_once=True)
    plugin = ConsolePlugin()
    plugin.on_load(SimpleNamespace(event_bus=bus, kernel=None))

    plugin.on_unload()
    assert len(plugin._event_subscriptions) == 1
    assert len(bus.callbacks["language_changed"]) == 1

    plugin.on_unload()
    assert plugin._event_subscriptions == []
    assert bus.callbacks["language_changed"] == []
    assert len(bus.unsubscribe_calls) == 2


def test_console_capability_release_failure_keeps_retry_state(
    monkeypatch,
) -> None:
    from core.VitaLoom.core.service_keys import UI_CONSOLE_PANEL

    module, plugin, _bus, registry = _loaded_plugin(monkeypatch)
    original_publish = module.publish_capabilities
    handler = object()

    class _FailOnceLease:
        def __init__(self, lease) -> None:
            self.lease = lease
            self.calls = 0

        def release(self):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("release failed")
            return self.lease.release()

    monkeypatch.setattr(
        module,
        "publish_capabilities",
        lambda *args, **kwargs: _FailOnceLease(
            original_publish(*args, **kwargs)
        ),
    )
    monkeypatch.setattr(module, "attach_console_logging", lambda _panel: handler)
    monkeypatch.setattr(module, "detach_console_logging", lambda _handler: True)

    plugin.create_dock_widget()
    dock = plugin.dock
    panel = plugin.console_panel

    with pytest.raises(RuntimeError, match="release failed"):
        plugin.on_unload()

    assert plugin._logging_handler is None
    assert plugin._console_publication is not None
    assert registry.get(UI_CONSOLE_PANEL) is panel
    assert plugin.dock is dock
    assert plugin.console_panel is panel

    plugin.on_unload()
    assert registry.has(UI_CONSOLE_PANEL) is False
    assert plugin._console_publication is None
    assert plugin.dock is None
    assert plugin.console_panel is None


def test_console_attach_primary_error_survives_rollback_failure_and_retries(
    monkeypatch,
) -> None:
    from core.VitaLoom.core.service_keys import UI_CONSOLE_PANEL

    module, plugin, _bus, registry = _loaded_plugin(monkeypatch)
    original_publish = module.publish_capabilities

    class _FailOnceLease:
        def __init__(self, lease) -> None:
            self.lease = lease
            self.calls = 0

        def release(self):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("rollback failed")
            return self.lease.release()

    monkeypatch.setattr(
        module,
        "publish_capabilities",
        lambda *args, **kwargs: _FailOnceLease(
            original_publish(*args, **kwargs)
        ),
    )
    monkeypatch.setattr(
        module,
        "attach_console_logging",
        lambda _panel: (_ for _ in ()).throw(RuntimeError("attach failed")),
    )

    with pytest.raises(RuntimeError, match="attach failed"):
        plugin.create_dock_widget()

    panel = plugin.console_panel
    assert panel is not None
    assert plugin.dock is not None
    assert plugin._console_publication is not None
    assert registry.get(UI_CONSOLE_PANEL) is panel

    plugin.on_unload()
    assert registry.has(UI_CONSOLE_PANEL) is False
    assert plugin._console_publication is None
    assert plugin.dock is None
    assert plugin.console_panel is None


