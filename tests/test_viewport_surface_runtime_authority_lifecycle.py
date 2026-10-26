# -*- coding: utf-8 -*-
"""E55 proofs for declarative viewport authority and activation rollback."""
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
BUILTIN_VIEWPORTS = (
    "cell_editor_plugin.py",
    "game_viewport_plugin.py",
    "scene_viewport_plugin.py",
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


class _Viewport:
    def __init__(self) -> None:
        self.deleted = 0

    def deleteLater(self) -> None:
        self.deleted += 1


class _Layout:
    def __init__(self, events: list[object]) -> None:
        self.events = events
        self.viewports: dict[str, tuple[_Viewport, object, str]] = {}

    def add_viewport(
        self,
        viewport_id: str,
        viewport: _Viewport,
        plugin: object,
        *,
        display_name: str,
    ) -> None:
        self.viewports[viewport_id] = (viewport, plugin, display_name)
        self.events.append(("add_viewport", viewport_id, display_name))

    def remove_viewport(self, viewport_id: str) -> None:
        self.viewports.pop(viewport_id, None)
        self.events.append(("remove_viewport", viewport_id))

    def set_viewport_display_name(self, viewport_id: str, display_name: str) -> None:
        viewport, plugin, _old_name = self.viewports[viewport_id]
        self.viewports[viewport_id] = (viewport, plugin, display_name)

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

    class DeclarativeViewportPlugin(IRuntimePlugin, ICommandProvider):
        def __init__(self) -> None:
            self.factory_calls = 0
            self.unloaded = False
            if factory_mode == "none":
                self.create_viewport_widget = None
            elif factory_mode == "raises":
                self.create_viewport_widget = self._raise_factory
            elif factory_mode == "works":
                self.create_viewport_widget = self._create_viewport
            elif factory_mode != "missing":
                raise AssertionError(f"unexpected factory mode: {factory_mode}")

        def get_plugin_info(self):
            return {
                "name": "DeclarativeViewportPlugin",
                "version": "1.0.0",
                "dependencies": [],
                "provides": ["viewport", "command", "editor_contribution"],
                "activation_context": "runtime",
                "editor_contributions": [
                    {
                        "id": "declarative.viewport.surface",
                        "kind": "viewport_surface",
                        "viewport_id": "DeclarativeViewport",
                        "name_key": "viewport.declarative.name",
                        "default_name": "Declarative Viewport",
                        "order": 10,
                        "refresh_events": ["declarative.viewport.refresh"],
                    }
                ],
            }

        def get_command_specs(self):
            return [
                CommandSpec(
                    id="declarative.viewport.command",
                    title="Declarative Viewport Command",
                    owner="incorrect-declared-owner",
                    handler=lambda _payload, _context: command_ok(),
                )
            ]

        def on_load(self, _context) -> None:
            events.append("on_load")

        def on_unload(self) -> None:
            self.unloaded = True
            events.append("on_unload")

        def _create_viewport(self):
            self.factory_calls += 1
            return _Viewport()

        def _raise_factory(self):
            self.factory_calls += 1
            raise RuntimeError("viewport factory failed")

    return DeclarativeViewportPlugin()


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


def test_qt_free_runtime_plugin_projects_declarative_viewport_without_iviewport_provider() -> None:
    from core.VitaLoom.commands.registry import get_command_registry

    events: list[object] = []
    plugin = _plugin("works", events)
    host, adapter, kernel, bus = _host(events)
    host.register_plugin(plugin)

    report = host.execute_lifecycle_target(
        {"DeclarativeViewportPlugin"}, source="test", allow_deactivate=True
    )

    assert report["status"] == "settled"
    assert host.loaded_plugins == {"DeclarativeViewportPlugin": plugin}
    assert plugin.factory_calls == 1
    viewport, owner, display_name = kernel.layout_manager.viewports["DeclarativeViewport"]
    assert isinstance(viewport, _Viewport)
    assert owner is plugin
    assert display_name == "Declarative Viewport"
    assert get_command_registry().describe("declarative.viewport.command")["owner"] == (
        "DeclarativeViewportPlugin"
    )
    assert adapter._declarative_viewport_owner_by_id == {
        "DeclarativeViewport": "DeclarativeViewportPlugin"
    }
    assert bus.subscribe_calls

    assert host.unload_plugin("DeclarativeViewportPlugin") is True
    assert host.loaded_plugins == {}
    assert kernel.layout_manager.viewports == {}
    assert adapter._declarative_viewport_owner_by_id == {}
    assert adapter._contribution_refresh_events_by_owner == {}
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert plugin.unloaded is True


@pytest.mark.parametrize("factory_mode", ["missing", "none", "raises"])
def test_declarative_viewport_factory_failure_rolls_back_host_publication(
    factory_mode: str,
) -> None:
    from core.VitaLoom.commands.registry import get_command_registry

    events: list[object] = []
    plugin = _plugin(factory_mode, events)
    host, adapter, kernel, bus = _host(events)
    host.register_plugin(plugin)

    report = host.execute_lifecycle_target(
        {"DeclarativeViewportPlugin"}, source="test", allow_deactivate=True
    )

    assert report["status"] == "failed"
    assert report["failed_action"]["action"] == "activate"
    assert host.loaded_plugins == {}
    assert get_command_registry().get("declarative.viewport.command") is None
    assert kernel.layout_manager.viewports == {}
    assert adapter._declarative_viewport_owner_by_id == {}
    assert adapter._contribution_refresh_events_by_owner == {}
    assert adapter._contribution_refresh_callbacks == {}
    assert bus.subscribe_calls == []
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert plugin.unloaded is True


@pytest.mark.parametrize(
    ("module_name", "class_name"),
    [
        ("builtin.editor_extensions.cell_editor_plugin", "CellEditorPlugin"),
        ("builtin.editor_extensions.game_viewport_plugin", "GameViewportPlugin"),
        ("builtin.editor_extensions.scene_viewport_plugin", "SceneViewportPlugin"),
    ],
)
def test_builtin_viewport_plugins_remain_runtime_plugin_discovery_candidates(
    module_name: str, class_name: str,
) -> None:
    import importlib

    from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin

    module = importlib.import_module(module_name)
    plugin_class = getattr(module, class_name)
    assert issubclass(plugin_class, IRuntimePlugin)

def test_e55_source_guards_retire_legacy_viewport_provider_from_builtin_authority() -> None:
    adapter_source = (
        RUNTIME
        / "core"
        / "VitaLoom"
        / "kernel"
        / "legacy_editor_plugin_adapter.py"
    ).read_text(encoding="utf-8-sig")

    assert "IViewportProvider" not in adapter_source
    for filename in BUILTIN_VIEWPORTS:
        source = (
            RUNTIME / "builtin" / "editor_extensions" / filename
        ).read_text(encoding="utf-8-sig")
        assert "IViewportProvider" not in source
