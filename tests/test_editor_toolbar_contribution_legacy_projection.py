# -*- coding: utf-8 -*-
"""Legacy Qt Host projection for command-backed toolbar facts."""
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
        self._events = events
        self._name = name

    def emit(self, plugin_id: str) -> None:
        self._events.append((self._name, plugin_id))


class _EventBus:
    def __init__(self) -> None:
        self.callbacks: dict[str, list] = {}
        self.subscribe_calls: list[tuple[str, object]] = []
        self.unsubscribe_calls: list[tuple[str, object]] = []

    def subscribe(self, event_name: str, callback):
        self.subscribe_calls.append((event_name, callback))
        self.callbacks.setdefault(event_name, []).append(callback)
        return callback

    def unsubscribe(self, event_name: str, callback) -> None:
        self.unsubscribe_calls.append((event_name, callback))
        callbacks = self.callbacks.setdefault(event_name, [])
        if callback in callbacks:
            callbacks.remove(callback)

    def publish(self, event_name: str, data=None) -> None:
        for callback in tuple(self.callbacks.get(event_name, ())):
            callback(data)


class _Layout:
    def __init__(self, events: list[object]) -> None:
        self.events = events
        self.menu_batches: list[tuple[str, list[dict[str, object]]]] = []
        self.toolbar_batches: list[tuple[str, list[dict[str, object]]]] = []

    def add_menu_items(self, items, plugin_id: str) -> None:
        copied = list(items)
        self.menu_batches.append((plugin_id, copied))
        self.events.append(("menu", plugin_id, len(copied)))

    def add_toolbar_items(self, items, plugin_id: str) -> None:
        copied = list(items)
        self.toolbar_batches.append((plugin_id, copied))
        self.events.append(("toolbar", plugin_id, len(copied)))

    def remove_plugin_ui(self, plugin_id: str) -> None:
        self.events.append(("remove", plugin_id))


class _PassivePlugin:
    def get_plugin_info(self):
        return {"name": "PassivePlugin", "version": "1.0.0"}

    def on_load(self, _context) -> None:
        return None

    def on_unload(self) -> None:
        return None


def _kernel(events: list[object], context: object):
    return SimpleNamespace(
        layout_manager=_Layout(events),
        get_context=lambda: context,
        plugin_loaded=_Signal(events, "loaded"),
        plugin_unloaded=_Signal(events, "unloaded"),
    )


def _normalized_standard_ui_info() -> dict[str, object]:
    from builtin.editor_extensions.standard_ui_plugin import StandardUIPlugin
    from core.VitaLoom.core.editor_contribution_contract import (
        parse_editor_contributions,
    )

    info = StandardUIPlugin().get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "StandardUIPlugin", info["editor_contributions"]
            )
        ],
    }


def _toolbar_items(layout: _Layout, plugin_id: str) -> list[dict[str, object]]:
    return next(items for owner, items in reversed(layout.toolbar_batches) if owner == plugin_id)


def _fake_transport(*, playing=False, paused=False, speed=1.0, calls=None):
    calls = calls if calls is not None else []

    class Transport:
        def __init__(self) -> None:
            self.state = SimpleNamespace(
                is_playing=playing,
                is_paused=paused,
                speed=speed,
            )

        def request_toggle(self) -> None:
            calls.append("toggle")

        def request_stop(self) -> None:
            calls.append("stop")

    return Transport(), calls


def test_simulation_transport_status_command_returns_json_safe_phase(monkeypatch) -> None:
    from core.VitaLoom.commands.registry import reset_command_registry
    from core.VitaLoom.simulation import simulation_transport

    transport, _calls = _fake_transport(playing=True, paused=False, speed=1.5)
    monkeypatch.setattr(simulation_transport, "_transport", transport)
    result = reset_command_registry().run("simulation.transport.status", {})

    assert result["ok"] is True
    assert result["events"] == []
    assert result["result"] == {
        "phase": "playing",
        "is_playing": True,
        "is_paused": False,
        "speed": 1.5,
    }


def test_adapter_projects_dynamic_label_and_runs_canonical_command(monkeypatch) -> None:
    from core.VitaLoom.commands.registry import reset_command_registry
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )
    from core.VitaLoom.simulation import simulation_transport

    transport, calls = _fake_transport()
    monkeypatch.setattr(simulation_transport, "_transport", transport)
    reset_command_registry()
    events: list[object] = []
    context = SimpleNamespace(event_bus=None, i18n_tr=lambda _key, default: default)
    kernel = _kernel(events, context)
    adapter = LegacyEditorPluginAdapter(kernel)
    info = _normalized_standard_ui_info()

    adapter.register_editor_contributions("StandardUIPlugin", info)
    items = _toolbar_items(kernel.layout_manager, "StandardUIPlugin")
    command_items = [item for item in items if not item.get("separator")]
    expected_labels = [
        item["default_label"]
        for item in info["editor_contributions"]
        if item["kind"] == "toolbar_command"
    ]

    assert [item["text"] for item in command_items] == expected_labels
    assert command_items[1]["action"]()["ok"] is True
    assert command_items[2]["action"]()["ok"] is True
    assert calls == ["toggle", "stop"]


def test_transport_event_refreshes_label_once_without_duplicate_subscription(
    monkeypatch,
) -> None:
    from core.VitaLoom.commands.registry import reset_command_registry
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )
    from core.VitaLoom.simulation import simulation_transport

    transport, _calls = _fake_transport()
    monkeypatch.setattr(simulation_transport, "_transport", transport)
    reset_command_registry()
    events: list[object] = []
    bus = _EventBus()
    context = SimpleNamespace(event_bus=bus, i18n_tr=lambda _key, default: default)
    kernel = _kernel(events, context)
    adapter = LegacyEditorPluginAdapter(kernel)
    info = _normalized_standard_ui_info()
    adapter.bind_active_plugin_metadata_resolver(
        lambda: (("StandardUIPlugin", info),)
    )
    adapter.bind_active_plugin_items_resolver(lambda: ())

    adapter.register_editor_contributions("StandardUIPlugin", info)
    adapter.register_editor_contributions(
        "StandardUIPlugin", info, replace_existing=True
    )
    assert [name for name, _callback in bus.subscribe_calls] == [
        "simulation_transport_state"
    ]

    transport.state = SimpleNamespace(is_playing=True, is_paused=True, speed=1.0)
    removes_before = sum(event == ("remove", "StandardUIPlugin") for event in events)
    bus.publish("simulation_transport_state", transport.state)
    removes_after = sum(event == ("remove", "StandardUIPlugin") for event in events)

    assert removes_after == removes_before + 1
    assert len(bus.callbacks["simulation_transport_state"]) == 1
    items = _toolbar_items(kernel.layout_manager, "StandardUIPlugin")
    simulation_toggle = next(
        item
        for item in info["editor_contributions"]
        if item["id"] == "simulation.toggle"
    )
    assert items[-2]["text"] == simulation_toggle["state"]["label_variants"][
        "paused"
    ]["default_label"]


def test_cleanup_unsubscribes_last_owner_and_removes_toolbar() -> None:
    from core.VitaLoom.commands.registry import reset_command_registry
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    reset_command_registry()
    events: list[object] = []
    bus = _EventBus()
    context = SimpleNamespace(event_bus=bus, i18n_tr=lambda _key, default: default)
    kernel = _kernel(events, context)
    adapter = LegacyEditorPluginAdapter(kernel)
    plugin = _PassivePlugin()
    info = _normalized_standard_ui_info()

    adapter.register_editor_contributions("StandardUIPlugin", info)
    adapter.before_plugin_unload(plugin, "StandardUIPlugin", info)

    assert events[-1] == ("remove", "StandardUIPlugin")
    assert bus.callbacks["simulation_transport_state"] == []
    assert [name for name, _callback in bus.unsubscribe_calls] == [
        "simulation_transport_state"
    ]


def test_shared_refresh_event_unsubscribes_only_after_last_owner() -> None:
    from core.VitaLoom.commands.registry import reset_command_registry
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    reset_command_registry()
    events: list[object] = []
    bus = _EventBus()
    context = SimpleNamespace(event_bus=bus, i18n_tr=lambda _key, default: default)
    kernel = _kernel(events, context)
    adapter = LegacyEditorPluginAdapter(kernel)
    first = _normalized_standard_ui_info()
    second = {
        "name": "SecondPlugin",
        "version": "1.0.0",
        "provides": ["editor_contribution"],
        "editor_contributions": [
            {
                **next(
                    item
                    for item in first["editor_contributions"]
                    if item["id"] == "simulation.toggle"
                ),
                "owner_plugin_id": "SecondPlugin",
                "id": "second.simulation.toggle",
            }
        ],
    }
    plugin = _PassivePlugin()

    adapter.register_editor_contributions("StandardUIPlugin", first)
    adapter.register_editor_contributions("SecondPlugin", second)
    assert len(bus.subscribe_calls) == 1

    adapter.before_plugin_unload(plugin, "StandardUIPlugin", first)
    assert len(bus.callbacks["simulation_transport_state"]) == 1
    assert bus.unsubscribe_calls == []

    adapter.before_plugin_unload(plugin, "SecondPlugin", second)
    assert bus.callbacks["simulation_transport_state"] == []
    assert [name for name, _callback in bus.unsubscribe_calls] == [
        "simulation_transport_state"
    ]


def test_standard_ui_refresh_projects_one_declarative_toolbar_slice(
    monkeypatch,
) -> None:
    from builtin.editor_extensions.standard_ui_plugin import StandardUIPlugin
    from core.VitaLoom.commands.registry import reset_command_registry
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )
    from core.VitaLoom.simulation import simulation_transport

    transport, _calls = _fake_transport()
    monkeypatch.setattr(simulation_transport, "_transport", transport)
    reset_command_registry()
    events: list[object] = []
    bus = _EventBus()
    context = SimpleNamespace(event_bus=bus, i18n_tr=lambda _key, default: default)
    kernel = _kernel(events, context)
    context.kernel = kernel
    plugin = StandardUIPlugin()
    adapter = LegacyEditorPluginAdapter(kernel)
    info = _normalized_standard_ui_info()
    adapter.bind_active_plugin_metadata_resolver(
        lambda: (("StandardUIPlugin", info),)
    )
    adapter.bind_active_plugin_items_resolver(
        lambda: (("StandardUIPlugin", plugin),)
    )

    adapter.refresh_editor_contributions()

    batches = kernel.layout_manager.toolbar_batches
    assert events.count(("remove", "StandardUIPlugin")) == 1
    expected_slice = [
        "|" if item["kind"] == "toolbar_separator" else item["default_label"]
        for item in info["editor_contributions"]
        if item["kind"].startswith("toolbar_")
    ]
    assert [
        "|" if item.get("separator") else item["text"]
        for _owner, items in batches
        for item in items
    ] == expected_slice


def test_standard_ui_toolbar_slice_is_fully_declarative_without_live_refresh() -> None:
    from builtin.editor_extensions.standard_ui_plugin import StandardUIPlugin

    info = StandardUIPlugin().get_plugin_info()
    toolbar_contributions = [
        item
        for item in info["editor_contributions"]
        if item["kind"].startswith("toolbar_")
    ]
    assert [
        "|" if item["kind"] == "toolbar_separator" else item["command_id"]
        for item in toolbar_contributions
    ] == [
        "plugin.standard_ui.save_project",
        "|",
        "simulation.toggle",
        "simulation.stop",
    ]

    source = (
        RUNTIME / "builtin" / "editor_extensions" / "standard_ui_plugin.py"
    ).read_text(encoding="utf-8-sig")
    for forbidden in (
        'subscribe("simulation_transport_state"',
        'unsubscribe("simulation_transport_state"',
        "def _on_transport_state",
        "def play_simulation",
        "def stop_simulation",
        "def _run_command_or_transport",
        "def get_toolbar_items(",
        "refresh_legacy_menu_contributions",
        "refresh_menu_providers",
    ):
        assert forbidden not in source
