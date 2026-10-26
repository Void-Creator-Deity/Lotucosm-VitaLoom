# -*- coding: utf-8 -*-
"""E53 proofs for declarative Dock authority and activation rollback."""
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
BUILTIN_DOCKS = (
    "console_plugin.py",
    "ecology_dashboard_plugin.py",
    "hierarchy_plugin.py",
    "inspector_plugin.py",
    "package_manager_plugin.py",
    "project_browser_plugin.py",
    "ps_experiment_plugin.py",
    "simulation_control_plugin.py",
)


class _Signal:
    def __init__(self, events: list[object], name: str) -> None:
        self.events = events
        self.name = name

    def emit(self, plugin_id: str) -> None:
        self.events.append((self.name, plugin_id))


class _EventBus:
    def __init__(self) -> None:
        self.callbacks: dict[str, list[object]] = {}
        self.subscribe_calls: list[tuple[str, object]] = []
        self.unsubscribe_calls: list[tuple[str, object]] = []

    def subscribe(self, event_name: str, callback) -> None:
        self.subscribe_calls.append((event_name, callback))
        self.callbacks.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name: str, callback) -> None:
        self.unsubscribe_calls.append((event_name, callback))
        callbacks = self.callbacks.get(event_name, [])
        if callback in callbacks:
            callbacks.remove(callback)


class _Dock:
    def __init__(self) -> None:
        self.object_name = ""
        self.window_title = ""

    def setObjectName(self, value: str) -> None:
        self.object_name = value

    def setWindowTitle(self, value: str) -> None:
        self.window_title = value


class _Layout:
    def __init__(self, events: list[object]) -> None:
        self.events = events
        self.docks: dict[str, _Dock] = {}

    def add_dock(self, dock: _Dock, config: dict) -> None:
        self.docks[config["title"]] = dock
        self.events.append(("add_dock", dict(config)))

    def remove_dock(self, dock_id: str) -> None:
        self.docks.pop(dock_id, None)
        self.events.append(("remove_dock", dock_id))

    def add_menu_items(self, _items, _plugin_id: str) -> None:
        return None

    def add_toolbar_items(self, _items, _plugin_id: str) -> None:
        return None

    def remove_plugin_ui(self, plugin_id: str) -> None:
        self.events.append(("remove_ui", plugin_id))


@pytest.fixture(autouse=True)
def _fresh_command_registry():
    from core.VitaLoom.commands.registry import reset_command_registry

    reset_command_registry()
    yield
    reset_command_registry()


def _plugin(factory_mode: str, events: list[object]):
    from core.VitaLoom.commands.registry import CommandSpec, command_ok
    from core.VitaLoom.core.runtime_plugin_contract import (
        ICommandProvider,
        IRuntimePlugin,
    )

    class DeclarativeDockPlugin(IRuntimePlugin, ICommandProvider):
        def __init__(self) -> None:
            self.factory_calls = 0
            self.unloaded = False
            if factory_mode == "none":
                self.create_dock_widget = None
            elif factory_mode == "raises":
                self.create_dock_widget = self._raise_factory
            elif factory_mode == "works":
                self.create_dock_widget = self._create_dock
            elif factory_mode != "missing":
                raise AssertionError(f"unexpected factory mode: {factory_mode}")

        def get_plugin_info(self):
            return {
                "name": "DeclarativeDockPlugin",
                "version": "1.0.0",
                "dependencies": [],
                "provides": ["dock", "command", "editor_contribution"],
                "activation_context": "runtime",
                "editor_contributions": [
                    {
                        "id": "declarative.dock.surface",
                        "kind": "dock_surface",
                        "dock_id": "DeclarativeDock",
                        "title_key": "declarative.dock.title",
                        "default_title": "Declarative Dock",
                        "area": "right",
                        "default_visible": True,
                        "can_close": True,
                        "can_float": True,
                        "can_move": True,
                        "tabbed_with": None,
                        "order": 1,
                        "refresh_events": ["declarative.dock.refresh"],
                    }
                ],
            }

        def get_command_specs(self):
            return [
                CommandSpec(
                    id="declarative.dock.command",
                    title="Declarative Dock Command",
                    owner="incorrect-declared-owner",
                    handler=lambda _payload, _context: command_ok(),
                )
            ]

        def on_load(self, _context) -> None:
            events.append("on_load")

        def on_unload(self) -> None:
            self.unloaded = True
            events.append("on_unload")

        def _create_dock(self):
            self.factory_calls += 1
            return _Dock()

        def _raise_factory(self):
            self.factory_calls += 1
            raise RuntimeError("dock factory failed")

    return DeclarativeDockPlugin()


def _host(events: list[object]):
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    bus = _EventBus()
    kernel = SimpleNamespace(
        layout_manager=_Layout(events),
        get_context=lambda: SimpleNamespace(event_bus=bus),
        plugin_loaded=_Signal(events, "loaded"),
        plugin_unloaded=_Signal(events, "unloaded"),
    )
    adapter = LegacyEditorPluginAdapter(kernel)
    host = RuntimePluginHost(
        adapter=adapter,
        activation_context_resolver=lambda _plugin_info: object(),
    )
    return host, adapter, kernel, bus


def test_qt_free_runtime_plugin_projects_declarative_dock_without_idock_provider() -> None:
    from core.VitaLoom.commands.registry import get_command_registry

    events: list[object] = []
    plugin = _plugin("works", events)
    host, adapter, kernel, bus = _host(events)
    host.register_plugin(plugin)

    report = host.execute_lifecycle_target(
        {"DeclarativeDockPlugin"}, source="test", allow_deactivate=True
    )

    assert report["status"] == "settled"
    assert host.loaded_plugins == {"DeclarativeDockPlugin": plugin}
    assert plugin.factory_calls == 1
    dock = kernel.layout_manager.docks["DeclarativeDock"]
    assert dock.object_name == "DeclarativeDock"
    assert dock.window_title == "Declarative Dock"
    assert get_command_registry().describe("declarative.dock.command")["owner"] == (
        "DeclarativeDockPlugin"
    )
    assert adapter._declarative_dock_owner_by_id == {
        "DeclarativeDock": "DeclarativeDockPlugin"
    }
    assert bus.subscribe_calls

    assert host.unload_plugin("DeclarativeDockPlugin") is True
    assert host.loaded_plugins == {}
    assert kernel.layout_manager.docks == {}
    assert adapter._declarative_dock_owner_by_id == {}
    assert adapter._contribution_refresh_events_by_owner == {}
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert plugin.unloaded is True


@pytest.mark.parametrize("factory_mode", ["missing", "none", "raises"])
def test_declarative_dock_factory_failure_rolls_back_host_publication(factory_mode: str) -> None:
    from core.VitaLoom.commands.registry import get_command_registry

    events: list[object] = []
    plugin = _plugin(factory_mode, events)
    host, adapter, kernel, bus = _host(events)
    host.register_plugin(plugin)

    report = host.execute_lifecycle_target(
        {"DeclarativeDockPlugin"}, source="test", allow_deactivate=True
    )

    assert report["status"] == "failed"
    assert report["failed_action"]["action"] == "activate"
    assert host.loaded_plugins == {}
    assert get_command_registry().get("declarative.dock.command") is None
    assert kernel.layout_manager.docks == {}
    assert adapter._declarative_dock_owner_by_id == {}
    assert adapter._contribution_refresh_events_by_owner == {}
    assert adapter._contribution_refresh_callbacks == {}
    assert bus.subscribe_calls == []
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert plugin.unloaded is True
    assert ("loaded", "DeclarativeDockPlugin") not in events


def test_e53_source_guards_retire_legacy_dock_provider_from_builtin_authority() -> None:
    adapter_source = (
        RUNTIME
        / "core"
        / "VitaLoom"
        / "kernel"
        / "legacy_editor_plugin_adapter.py"
    ).read_text(encoding="utf-8-sig")
    loader_source = (
        RUNTIME / "core" / "VitaLoom" / "kernel" / "plugin_loader.py"
    ).read_text(encoding="utf-8-sig")

    assert "IDockProvider" not in adapter_source
    assert "isinstance(plugin, IDockProvider)" not in loader_source
    for filename in BUILTIN_DOCKS:
        source = (
            RUNTIME / "builtin" / "editor_extensions" / filename
        ).read_text(encoding="utf-8-sig")
        assert "IDockProvider" not in source
        assert "def get_dock_config" not in source
