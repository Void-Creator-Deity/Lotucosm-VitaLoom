# -*- coding: utf-8 -*-
"""E41 SimulationControl Dock shell, retained localization, and exact events."""
from __future__ import annotations

import os
from types import SimpleNamespace

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
    def __init__(self, *args, **kwargs) -> None:
        self.retranslated = 0
        self.play_btn = SimpleNamespace(setEnabled=lambda value: setattr(self, "play_enabled", value))
        self.pause_btn = SimpleNamespace(setEnabled=lambda value: setattr(self, "pause_enabled", value))
        self.stop_btn = SimpleNamespace(setEnabled=lambda value: setattr(self, "stop_enabled", value))
        self.status = ""

    def _set_status(self, text: str) -> None:
        self.status = text

    def _t(self, _key: str, default: str = "") -> str:
        return default

    def retranslate_ui(self) -> None:
        self.retranslated += 1


def _normalized_info() -> dict:
    from builtin.editor_extensions.simulation_control_plugin import SimulationControlPlugin
    from core.VitaLoom.core.editor_contribution_contract import parse_editor_contributions

    info = SimulationControlPlugin().get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "SimulationControlPlugin", info["editor_contributions"]
            )
        ],
    }


def _load_plugin(monkeypatch, *, bus: _EventBus | None = None):
    import builtin.editor_extensions.simulation_control_plugin as module

    bus = bus or _EventBus()
    context = SimpleNamespace(
        event_bus=bus,
        i18n_tr=lambda _key, default: default,
    )
    monkeypatch.setattr(module, "QDockWidget", _Dock)
    monkeypatch.setattr(module, "SimulationControlPanel", _FakePanel)
    plugin = module.SimulationControlPlugin()
    plugin.on_load(context)
    return module, plugin, context, bus


def test_simulation_control_declares_one_qt_free_dock_shell() -> None:
    from builtin.editor_extensions.simulation_control_plugin import SimulationControlPlugin

    info = SimulationControlPlugin().get_plugin_info()
    assert info["provides"] == ["dock", "editor_contribution"]
    assert info["editor_contributions"] == [
        {
            "id": "simulation_control.surface",
            "kind": "dock_surface",
            "dock_id": "SimulationControl",
            "title_key": "sim_control.dock_title",
            "default_title": "模拟",
            "area": "left",
            "default_visible": False,
            "can_close": True,
            "can_float": True,
            "can_move": True,
            "tabbed_with": "Hierarchy",
            "order": 70,
            "refresh_events": ["language_changed"],
        }
    ]


def test_adapter_projects_and_refreshes_simulation_title_in_place() -> None:
    from PyQt6.QtCore import Qt
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import LegacyEditorPluginAdapter

    bus = _EventBus()
    translations = {"sim_control.dock_title": "模拟"}
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
        lambda: (("SimulationControlPlugin", info),)
    )
    adapter.bind_active_plugin_items_resolver(
        lambda: (("SimulationControlPlugin", plugin),)
    )

    adapter.after_plugin_load(plugin, "SimulationControlPlugin", info)
    dock = layout.docks["SimulationControl"]
    panel = plugin.panel
    translations["sim_control.dock_title"] = "Simulation"
    bus.publish("language_changed")

    assert plugin.created == 1
    assert len(layout.add_calls) == 1
    assert layout.remove_calls == []
    assert layout.docks["SimulationControl"] is dock
    assert dock.panel is panel
    assert dock.window_title == "Simulation"
    assert layout.add_calls[0][1] == {
        "title": "SimulationControl",
        "area": Qt.DockWidgetArea.LeftDockWidgetArea,
        "default_visible": False,
        "can_close": True,
        "can_float": True,
        "can_move": True,
        "tabbed_with": "Hierarchy",
    }


def test_panel_retranslates_in_place_without_losing_runtime_state(monkeypatch) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication
    import core.VitaLoom.simulation.simulation_control as panel_module

    app = QApplication.instance() or QApplication([])
    translations: dict[str, str] = {}
    context = SimpleNamespace(i18n_tr=lambda key, default: translations.get(key, default))
    panel = panel_module.SimulationControlPanel(editor_context=context)
    panel.speed_slider.setValue(275)
    panel.fps_limit_spin.setValue(144)
    panel.time_step_spin.setValue(0.025)
    panel.auto_save_check.setChecked(True)
    panel.play_btn.setEnabled(False)
    panel.pause_btn.setEnabled(True)
    panel.stop_btn.setEnabled(True)
    panel.status_label.setText("dynamic-playing-status")
    identities = {
        "panel": id(panel),
        "slider": id(panel.speed_slider),
        "fps": id(panel.fps_limit_spin),
    }
    translations.update(
        {
            "sim_control.group.playback": "Playback",
            "sim_control.play": "Play",
            "sim_control.pause": "Pause",
            "sim_control.stop": "Stop",
            "sim_control.group.speed": "Speed",
            "sim_control.speed": "Multiplier",
            "sim_control.group.params": "Simulation Parameters",
            "sim_control.fps_limit": "FPS Limit",
            "sim_control.time_step": "Time Step",
            "sim_control.auto_save": "Auto Save",
            "sim_control.hint.pvaec": "SR simulation uses the canonical transport.",
        }
    )

    panel.retranslate_ui()
    app.processEvents()

    assert identities == {
        "panel": id(panel),
        "slider": id(panel.speed_slider),
        "fps": id(panel.fps_limit_spin),
    }
    assert panel.speed_slider.value() == 275
    assert panel.fps_limit_spin.value() == 144
    assert panel.time_step_spin.value() == pytest.approx(0.025)
    assert panel.auto_save_check.isChecked() is True
    assert panel.play_btn.isEnabled() is False
    assert panel.pause_btn.isEnabled() is True
    assert panel.stop_btn.isEnabled() is True
    assert panel.status_label.text() == "dynamic-playing-status"
    assert panel._play_group.title() == "Playback"
    assert panel.play_btn.text() == "Play"
    assert panel.pause_btn.text() == "Pause"
    assert panel.stop_btn.text() == "Stop"
    assert panel._speed_group.title() == "Speed"
    assert panel._speed_static_label.text() == "Multiplier"
    assert panel._params_group.title() == "Simulation Parameters"
    assert panel._params_layout.labelForField(panel.fps_limit_spin).text() == "FPS Limit"
    assert panel._params_layout.labelForField(panel.time_step_spin).text() == "Time Step"
    assert panel._params_layout.labelForField(panel.auto_save_check).text() == "Auto Save"
    assert panel._hint_label.text() == "SR simulation uses the canonical transport."


def test_plugin_owns_events_once_and_releases_in_reverse(monkeypatch) -> None:
    _module, plugin, _context, bus = _load_plugin(monkeypatch)

    dock = plugin.create_dock_widget()
    panel = dock.panel
    assert plugin.create_dock_widget() is dock
    assert [name for name, _callback in bus.subscribe_calls] == [
        "simulation_transport_state",
        "language_changed",
    ]

    bus.publish("language_changed", {})
    assert panel.retranslated == 1
    state = SimpleNamespace(is_playing=True, is_paused=False)
    bus.publish("simulation_transport_state", state)
    assert (panel.play_enabled, panel.pause_enabled, panel.stop_enabled) == (
        False,
        True,
        True,
    )

    plugin.on_unload()
    assert [name for name, _callback in bus.unsubscribe_calls] == [
        "language_changed",
        "simulation_transport_state",
    ]
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert dock.deleted == 1
    assert plugin.dock is None
    assert plugin.panel is None

    plugin.on_unload()
    assert len(bus.unsubscribe_calls) == 2
    assert dock.deleted == 1


def test_partial_subscription_failure_rolls_back_without_stale_panel(monkeypatch) -> None:
    bus = _EventBus(fail_subscribe_on="language_changed")
    _module, plugin, _context, _bus = _load_plugin(monkeypatch, bus=bus)

    with pytest.raises(RuntimeError, match="subscribe failed: language_changed"):
        plugin.create_dock_widget()

    assert [name for name, _callback in bus.subscribe_calls] == [
        "simulation_transport_state"
    ]
    assert [name for name, _callback in bus.unsubscribe_calls] == [
        "simulation_transport_state"
    ]
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert plugin._event_subscriptions == []
    assert plugin.dock is None
    assert plugin.panel is None


def test_failed_unsubscribe_retains_exact_state_for_retry(monkeypatch) -> None:
    bus = _EventBus(fail_unsubscribe_once_on="language_changed")
    _module, plugin, _context, _bus = _load_plugin(monkeypatch, bus=bus)
    dock = plugin.create_dock_widget()

    with pytest.raises(RuntimeError, match="unsubscribe failed: language_changed"):
        plugin.on_unload()

    assert [name for name, _callback in plugin._event_subscriptions] == [
        "language_changed"
    ]
    assert plugin.dock is dock
    assert plugin.panel is dock.panel
    assert dock.deleted == 0
    assert bus.callbacks["simulation_transport_state"] == []
    assert len(bus.callbacks["language_changed"]) == 1

    plugin.on_unload()
    assert plugin._event_subscriptions == []
    assert plugin.dock is None
    assert plugin.panel is None
    assert dock.deleted == 1
    assert all(not callbacks for callbacks in bus.callbacks.values())
