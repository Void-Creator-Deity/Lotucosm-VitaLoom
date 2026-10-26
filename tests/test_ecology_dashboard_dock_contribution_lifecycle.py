# -*- coding: utf-8 -*-
"""E42 EcologyDashboard declarative shell and exact refresh-resource lifecycle."""
from __future__ import annotations

import os
import sys
from types import ModuleType, SimpleNamespace

import pytest


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


class _Dock:
    def __init__(self, title: str = "", panel: object | None = None) -> None:
        self.object_name = ""
        self.window_title = title
        self.panel = panel
        self.deleted = 0

    def setObjectName(self, value: str) -> None:
        self.object_name = value

    def setWindowTitle(self, value: str) -> None:
        self.window_title = value

    def setWidget(self, panel: object) -> None:
        self.panel = panel

    def widget(self):
        return self.panel

    def deleteLater(self) -> None:
        self.deleted += 1


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


class _Signal:
    def connect(self, _callback) -> None:
        pass

    def disconnect(self, _callback) -> None:
        pass

    def emit(self, *_args) -> None:
        pass


class _Bridge:
    def __init__(self, info: dict) -> None:
        self.info = info
        self.created = 0
        self.panel = object()
        self.dock: _Dock | None = None

    def get_plugin_info(self):
        return self.info

    def create_dock_widget(self):
        self.created += 1
        self.dock = _Dock(panel=self.panel)
        return self.dock

    def get_dock_config(self):
        raise AssertionError("declarative dock config must be authoritative")

    def get_menu_items(self):
        return []

    def get_toolbar_items(self):
        return []


class _FakePanel:
    def __init__(self, _context, *, fail_stop_once: bool = False) -> None:
        self.refresh_count = 0
        self.retranslated = 0
        self.timer_active = True
        self.stop_calls = 0
        self.fail_stop_once = fail_stop_once

    def refresh(self) -> None:
        self.refresh_count += 1

    def retranslate_ui(self) -> None:
        self.retranslated += 1

    def stop_refresh_timer(self) -> None:
        self.stop_calls += 1
        if self.fail_stop_once:
            self.fail_stop_once = False
            raise RuntimeError("timer stop failed")
        self.timer_active = False


def _normalized_info() -> dict:
    from builtin.editor_extensions.ecology_dashboard_plugin import EcologyDashboardPlugin
    from core.VitaLoom.core.editor_contribution_contract import parse_editor_contributions

    info = EcologyDashboardPlugin().get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "EcologyDashboardPlugin", info["editor_contributions"]
            )
        ],
    }


def _load_plugin(
    monkeypatch,
    *,
    bus: _EventBus | None = None,
    fail_stop_once: bool = False,
):
    import builtin.editor_extensions.ecology_dashboard_plugin as module

    bus = bus or _EventBus()
    context = SimpleNamespace(
        event_bus=bus,
        i18n_tr=lambda _key, default: default,
    )
    panel = _FakePanel(context, fail_stop_once=fail_stop_once)
    panel_module = ModuleType("core.VitaLoom.docks.ecology_dashboard")
    panel_module.EcologyDashboardPanel = lambda _context: panel
    monkeypatch.setitem(sys.modules, panel_module.__name__, panel_module)
    monkeypatch.setattr(module, "QDockWidget", _Dock)
    plugin = module.EcologyDashboardPlugin()
    plugin.on_load(context)
    return module, plugin, panel, context, bus


def test_ecology_dashboard_declares_one_qt_free_dock_shell() -> None:
    from builtin.editor_extensions.ecology_dashboard_plugin import EcologyDashboardPlugin

    info = EcologyDashboardPlugin().get_plugin_info()
    assert info["provides"] == ["dock", "editor_contribution"]
    assert info["editor_contributions"] == [
        {
            "id": "ecology_dashboard.surface",
            "kind": "dock_surface",
            "dock_id": "EcologyDashboard",
            "title_key": "ecology_dashboard.dock_title",
            "default_title": "生态统计",
            "area": "right",
            "default_visible": False,
            "can_close": True,
            "can_float": True,
            "can_move": True,
            "tabbed_with": None,
            "order": 90,
            "refresh_events": ["language_changed"],
        }
    ]


def test_adapter_projects_and_refreshes_ecology_title_in_place() -> None:
    from PyQt6.QtCore import Qt
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import LegacyEditorPluginAdapter

    bus = _EventBus()
    translations = {"ecology_dashboard.dock_title": "生态统计"}
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
    info = _normalized_info()
    plugin = _Bridge(info)
    adapter.bind_active_plugin_metadata_resolver(
        lambda: (("EcologyDashboardPlugin", info),)
    )
    adapter.bind_active_plugin_items_resolver(
        lambda: (("EcologyDashboardPlugin", plugin),)
    )

    adapter.after_plugin_load(plugin, "EcologyDashboardPlugin", info)
    dock = layout.docks["EcologyDashboard"]
    panel = plugin.panel
    translations["ecology_dashboard.dock_title"] = "Ecology"
    bus.publish("language_changed")

    assert plugin.created == 1
    assert len(layout.add_calls) == 1
    assert layout.remove_calls == []
    assert layout.docks["EcologyDashboard"] is dock
    assert dock.panel is panel
    assert dock.window_title == "Ecology"
    assert layout.add_calls[0][1] == {
        "title": "EcologyDashboard",
        "area": Qt.DockWidgetArea.RightDockWidgetArea,
        "default_visible": False,
        "can_close": True,
        "can_float": True,
        "can_move": True,
        "tabbed_with": None,
    }


def test_panel_retranslates_static_content_without_resetting_output_or_timer(monkeypatch) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication
    import core.VitaLoom.docks.ecology_dashboard as panel_module

    app = QApplication.instance() or QApplication([])
    translations: dict[str, str] = {}

    class NoSubscriptions:
        def subscribe(self, *_args) -> None:
            raise AssertionError("Panel must not own event subscriptions")

    context = SimpleNamespace(
        event_bus=NoSubscriptions(),
        i18n_tr=lambda key, default: translations.get(key, default),
    )
    monkeypatch.setattr(panel_module, "collect_ecology_snapshots", lambda _ctx: [])
    panel = panel_module.EcologyDashboardPanel(context)
    panel._labels[0].setText("runtime ecology line")
    identities = {
        "panel": id(panel),
        "title": id(panel._title_label),
        "hint": id(panel._hint_label),
        "timer": id(panel._timer),
    }
    translations.update(
        {
            "ecology_dashboard.title": "Lotus Ecology (SR + PS)",
            "ecology_dashboard.hint": "SR and PS remain separate observation lanes.",
        }
    )

    panel.retranslate_ui()
    app.processEvents()

    assert identities == {
        "panel": id(panel),
        "title": id(panel._title_label),
        "hint": id(panel._hint_label),
        "timer": id(panel._timer),
    }
    assert panel._title_label.text() == "Lotus Ecology (SR + PS)"
    assert panel._hint_label.text() == "SR and PS remain separate observation lanes."
    assert panel._labels[0].text() == "runtime ecology line"
    assert panel._timer.isActive() is True
    panel.stop_refresh_timer()
    assert panel._timer.isActive() is False


def test_plugin_owns_refresh_events_once_and_releases_resources_in_reverse(monkeypatch) -> None:
    _module, plugin, panel, _context, bus = _load_plugin(monkeypatch)

    dock = plugin.create_dock_widget()
    assert plugin.create_dock_widget() is dock
    assert [name for name, _callback in bus.subscribe_calls] == [
        "ps_experiment_state",
        "ps_experiment_finished",
        "simulation_transport_state",
        "language_changed",
    ]

    for event_name in (
        "ps_experiment_state",
        "ps_experiment_finished",
        "simulation_transport_state",
    ):
        bus.publish(event_name, {})
    bus.publish("language_changed", {})
    assert panel.refresh_count == 3
    assert panel.retranslated == 1

    plugin.on_unload()
    assert [name for name, _callback in bus.unsubscribe_calls] == [
        "language_changed",
        "simulation_transport_state",
        "ps_experiment_finished",
        "ps_experiment_state",
    ]
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert panel.stop_calls == 1
    assert panel.timer_active is False
    assert dock.deleted == 1
    assert plugin.dock is None
    assert plugin.panel is None

    plugin.on_unload()
    assert len(bus.unsubscribe_calls) == 4
    assert panel.stop_calls == 1
    assert dock.deleted == 1


def test_partial_subscription_failure_rolls_back_events_and_timer(monkeypatch) -> None:
    bus = _EventBus(fail_subscribe_on="simulation_transport_state")
    _module, plugin, panel, _context, _bus = _load_plugin(monkeypatch, bus=bus)

    with pytest.raises(RuntimeError, match="subscribe failed: simulation_transport_state"):
        plugin.create_dock_widget()

    assert [name for name, _callback in bus.subscribe_calls] == [
        "ps_experiment_state",
        "ps_experiment_finished",
    ]
    assert [name for name, _callback in bus.unsubscribe_calls] == [
        "ps_experiment_finished",
        "ps_experiment_state",
    ]
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert panel.stop_calls == 1
    assert panel.timer_active is False
    assert plugin._event_subscriptions == []
    assert plugin._panel_timer_owned is False
    assert plugin.dock is None
    assert plugin.panel is None


def test_failed_unsubscribe_retains_only_exact_event_for_retry(monkeypatch) -> None:
    bus = _EventBus(fail_unsubscribe_once_on="simulation_transport_state")
    _module, plugin, panel, _context, _bus = _load_plugin(monkeypatch, bus=bus)
    dock = plugin.create_dock_widget()

    with pytest.raises(RuntimeError, match="unsubscribe failed: simulation_transport_state"):
        plugin.on_unload()

    assert [name for name, _callback in plugin._event_subscriptions] == [
        "simulation_transport_state"
    ]
    assert plugin._panel_timer_owned is False
    assert panel.stop_calls == 1
    assert panel.timer_active is False
    assert plugin.dock is dock
    assert plugin.panel is panel
    assert dock.deleted == 0
    assert len(bus.callbacks["simulation_transport_state"]) == 1
    assert all(
        not callbacks
        for name, callbacks in bus.callbacks.items()
        if name != "simulation_transport_state"
    )

    plugin.on_unload()
    assert plugin._event_subscriptions == []
    assert plugin.dock is None
    assert plugin.panel is None
    assert panel.stop_calls == 1
    assert dock.deleted == 1
    assert all(not callbacks for callbacks in bus.callbacks.values())


def test_failed_timer_stop_retains_exact_timer_state_for_retry(monkeypatch) -> None:
    _module, plugin, panel, _context, bus = _load_plugin(
        monkeypatch,
        fail_stop_once=True,
    )
    dock = plugin.create_dock_widget()

    with pytest.raises(RuntimeError, match="timer stop failed"):
        plugin.on_unload()

    assert plugin._event_subscriptions == []
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert plugin._panel_timer_owned is True
    assert plugin.dock is dock
    assert plugin.panel is panel
    assert dock.deleted == 0

    plugin.on_unload()
    assert plugin._panel_timer_owned is False
    assert panel.stop_calls == 2
    assert panel.timer_active is False
    assert plugin.dock is None
    assert plugin.panel is None
    assert dock.deleted == 1
