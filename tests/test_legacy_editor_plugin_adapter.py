# -*- coding: utf-8 -*-
"""E24 coverage for the concrete legacy Editor plugin Host Adapter."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _stub_theme_stylesheet_composition(monkeypatch):
    """Keep adapter projection tests headless when PyQt6 is unavailable."""
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    def compose(_self, appearance, payload, *, include_modern_overlay):
        base = "LIGHT" if appearance == "light" else "BASE"
        return f"{base}\n{payload}"

    monkeypatch.setattr(
        LegacyEditorPluginAdapter,
        "_compose_theme_stylesheet",
        compose,
    )


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
    def __init__(self, label: str, events: list[str]) -> None:
        self.label = label
        self.events = events

    def emit(self, plugin_id: str) -> None:
        self.events.append(f"signal:{self.label}:{plugin_id}")


class _Layout:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.menu_items: dict[str, list[dict[str, object]]] = {}
        self.toolbar_items: dict[str, list[dict[str, object]]] = {}

    def add_dock(self, widget, config) -> None:
        self.events.append(f"layout:add_dock:{config['title']}:{widget}")

    def add_viewport(self, viewport_id, widget, plugin, **_kwargs) -> None:
        self.events.append(f"layout:add_viewport:{viewport_id}:{widget}")

    def add_menu_items(self, items, plugin_id: str) -> None:
        self.menu_items[plugin_id] = list(items)
        self.events.append(f"layout:add_menu:{plugin_id}:{len(items)}")

    def add_toolbar_items(self, items, plugin_id: str) -> None:
        self.toolbar_items[plugin_id] = list(items)
        self.events.append(f"layout:add_toolbar:{plugin_id}:{len(items)}")

    def register_theme(self, theme_name: str, stylesheet: str) -> None:
        self.events.append(f"layout:add_theme:{theme_name}:{stylesheet}")

    def remove_dock(self, title: str) -> None:
        self.events.append(f"layout:remove_dock:{title}")

    def remove_viewport(self, viewport_id: str) -> None:
        self.events.append(f"layout:remove_viewport:{viewport_id}")

    def remove_plugin_ui(self, plugin_id: str) -> None:
        self.events.append(f"layout:remove_all:{plugin_id}")

    def process_pending_dock_tabify(self) -> None:
        self.events.append("layout:settle")


def _kernel(events: list[str]):
    context = SimpleNamespace()
    kernel = SimpleNamespace(
        get_context=lambda: context,
        plugin_loaded=_Signal("loaded", events),
        plugin_unloaded=_Signal("unloaded", events),
        layout_manager=_Layout(events),
    )
    context.kernel = kernel
    return kernel


def _adapter(kernel):
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    return LegacyEditorPluginAdapter(kernel)


def _full_plugin(events: list[str], *, fail_dock=False, fail_ready=False):
    from core.VitaLoom.commands.registry import CommandSpec, command_ok
    from core.VitaLoom.kernel.plugin_interfaces import (
        ICommandProvider,
        IDockProvider,
        IThemeProvider,
        IViewportProvider,
    )

    class FullPlugin(
        IDockProvider,
        IViewportProvider,
        IThemeProvider,
        ICommandProvider,
    ):
        def get_plugin_info(self):
            return {
                "name": "FullPlugin",
                "version": "1.0.0",
                "dependencies": [],
                "provides": [
                    "dock",
                    "viewport",
                    "theme",
                    "command",
                    "editor_contribution",
                ],
                "editor_contributions": [
                    {
                        "id": "full.menu",
                        "kind": "menu_command",
                        "menu_path": [
                            {
                                "id": "tools",
                                "label_key": "menu.tools",
                                "default_label": "Tools",
                            }
                        ],
                        "label_key": "menu.full",
                        "default_label": "Full",
                        "command_id": "full.command",
                        "command_payload": {},
                        "order": 10,
                    },
                    {
                        "id": "full.toolbar",
                        "kind": "toolbar_command",
                        "label_key": "toolbar.full",
                        "default_label": "Full",
                        "command_id": "full.command",
                        "command_payload": {},
                        "icon": "full",
                        "group": "main",
                        "order": 10,
                    },
                ],
            }

        def on_load(self, _context) -> None:
            events.append("plugin:on_load")

        def on_unload(self) -> None:
            events.append("plugin:on_unload")

        def on_editor_ready(self) -> None:
            events.append("plugin:editor_ready")
            if fail_ready:
                raise RuntimeError("ready failed")

        def create_dock_widget(self):
            events.append("plugin:create_dock")
            if fail_dock:
                raise RuntimeError("dock failed")
            return "dock-widget"

        def get_dock_config(self):
            return {"title": "Full Dock"}

        def create_viewport_widget(self):
            events.append("plugin:create_viewport")
            return "viewport-widget"

        def get_viewport_id(self):
            return "full.viewport"

        def get_viewport_name(self):
            return "Full Viewport"

        def get_theme_name(self):
            return "Full Theme"

        def get_stylesheet(self):
            return "QWidget { color: white; }"

        def get_color_scheme(self):
            return {"foreground": "white"}

        def get_command_specs(self):
            events.append("plugin:get_commands")
            return [
                CommandSpec(
                    id="full.command",
                    title="Full command",
                    description="Full command",
                    input_schema={"type": "object", "properties": {}},
                    handler=lambda _payload, _context: command_ok({"value": "full"}),
                    owner="wrong-owner",
                )
            ]

    return FullPlugin()


def _normalized_info(plugin) -> dict[str, object]:
    from core.VitaLoom.core.editor_contribution_contract import (
        parse_editor_contributions,
    )

    info = plugin.get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "FullPlugin", info["editor_contributions"]
            )
        ],
    }


def test_adapter_module_is_concrete_and_qt_free_hosts_do_not_import_it() -> None:
    adapter_path = (
        RUNTIME / "core" / "VitaLoom" / "kernel" / "legacy_editor_plugin_adapter.py"
    )
    source = adapter_path.read_text(encoding="utf-8-sig")
    assert "class LegacyEditorPluginAdapter" in source
    assert "RuntimePluginHostAdapter" in source
    assert "kernel.plugin_interfaces" not in source
    assert "core.runtime_plugin_contract" in source

    for relative in (
        "core/VitaLoom/core/runtime_plugin_host.py",
        "core/VitaLoom/project/project_scoped_plugin_host.py",
        "core/VitaLoom/core/manual_plugin_reload_host.py",
        "core/VitaLoom/core/nested_plugin_host.py",
    ):
        host_source = (RUNTIME / relative).read_text(encoding="utf-8-sig")
        assert "legacy_editor_plugin_adapter" not in host_source
        assert "PyQt6" not in host_source


def test_adapter_projects_and_caches_runtime_context_without_inference() -> None:
    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
    )
    from core.VitaLoom.core.runtime_event_bus import InMemoryRuntimeEventBus

    services = InMemoryRuntimeCapabilityRegistry()
    event_bus = InMemoryRuntimeEventBus()
    legacy_context = SimpleNamespace(services=services, event_bus=event_bus, kernel=object())
    kernel = SimpleNamespace(get_context=lambda: legacy_context)
    adapter = _adapter(kernel)

    first = adapter.activation_context_for(
        {"name": "RuntimeA", "activation_context": "runtime"}
    )
    second = adapter.activation_context_for(
        {"name": "RuntimeB", "activation_context": "runtime"}
    )
    legacy_result = adapter.activation_context_for(
        {"name": "Legacy", "activation_context": "legacy_ui", "provides": []}
    )

    assert first is second is adapter.runtime_activation_context
    assert first.services is services
    assert first.event_bus is event_bus
    assert legacy_result is legacy_context
    with pytest.raises(ValueError, match="unsupported activation_context"):
        adapter.activation_context_for(
            {"name": "Invalid", "activation_context": "mystery"}
        )


def test_adapter_projects_editor_contributions_without_owning_commands() -> None:
    from core.VitaLoom.commands.registry import (
        get_command_registry,
        reset_command_registry,
    )

    reset_command_registry()
    events: list[str] = []
    adapter = _adapter(_kernel(events))
    plugin = _full_plugin(events)
    info = _normalized_info(plugin)
    theme = SimpleNamespace(DARK_THEME="BASE", LIGHT_THEME="LIGHT")

    adapter.after_plugin_load(plugin, "FullPlugin", info)

    assert events[-2:] == ["plugin:editor_ready", "signal:loaded:FullPlugin"]
    assert events.index("plugin:create_dock") < events.index(
        "layout:add_dock:Full Dock:dock-widget"
    )
    assert events.index("plugin:create_viewport") < events.index(
        "layout:add_viewport:full.viewport:viewport-widget"
    )
    assert "layout:add_menu:FullPlugin:1" in events
    assert "layout:add_toolbar:FullPlugin:1" in events
    assert "layout:add_theme:Full Theme:BASE\nQWidget { color: white; }" in events
    with pytest.raises(KeyError):
        get_command_registry().describe("full.command")


def test_adapter_command_actions_thaw_a_fresh_payload_for_each_trigger() -> None:
    from core.VitaLoom.commands.registry import (
        CommandSpec,
        command_ok,
        get_command_registry,
        reset_command_registry,
    )

    reset_command_registry()
    events: list[str] = []
    kernel = _kernel(events)
    adapter = _adapter(kernel)
    plugin = _full_plugin(events)
    info = _normalized_info(plugin)
    info["editor_contributions"][0]["command_payload"] = {"nested": {"count": 0}}
    observed_counts: list[int] = []
    registry = get_command_registry()
    registry.register(
        CommandSpec(
            id="full.command",
            title="Mutable payload probe",
            description="Mutates only its supplied payload.",
            input_schema={"type": "object"},
            handler=lambda payload, _context: (
                observed_counts.append(payload["nested"]["count"]),
                payload["nested"].__setitem__("count", 99),
                command_ok({"ok": True}),
            )[-1],
            owner="runtime-host",
        )
    )

    adapter.after_plugin_load(plugin, "FullPlugin", info)
    action = kernel.layout_manager.menu_items["FullPlugin"][0]["action"]
    action()
    action()

    assert observed_counts == [0, 0]
    assert registry.describe("full.command")["owner"] == "runtime-host"
    reset_command_registry()


def test_adapter_preserves_cleanup_and_signal_order_without_command_authority() -> None:
    from core.VitaLoom.commands.registry import (
        get_command_registry,
        reset_command_registry,
    )

    reset_command_registry()
    events: list[str] = []
    adapter = _adapter(_kernel(events))
    plugin = _full_plugin(events)
    info = _normalized_info(plugin)
    theme = SimpleNamespace(DARK_THEME="BASE", LIGHT_THEME="LIGHT")

    adapter.after_plugin_load(plugin, "FullPlugin", info)
    adapter.before_plugin_unload(plugin, "FullPlugin", info)
    plugin.on_unload()
    with pytest.raises(KeyError):
        get_command_registry().describe("full.command")
    adapter.after_plugin_deactivated(plugin, "FullPlugin", info)

    assert events.index("layout:remove_dock:Full Dock") < events.index("plugin:on_unload")
    assert events.index("layout:remove_viewport:full.viewport") < events.index(
        "plugin:on_unload"
    )
    assert events.index("plugin:on_unload") < events.index(
        "signal:unloaded:FullPlugin"
    )


def test_adapter_isolates_contribution_and_editor_ready_failures() -> None:
    from core.VitaLoom.commands.registry import reset_command_registry

    reset_command_registry()
    events: list[str] = []
    adapter = _adapter(_kernel(events))
    plugin = _full_plugin(events, fail_dock=True, fail_ready=True)
    info = _normalized_info(plugin)
    theme = SimpleNamespace(DARK_THEME="BASE", LIGHT_THEME="LIGHT")

    adapter.after_plugin_load(plugin, "FullPlugin", info)

    assert "plugin:editor_ready" in events
    assert events[-1] == "signal:loaded:FullPlugin"
    assert "layout:add_viewport:full.viewport:viewport-widget" in events
    assert "layout:add_menu:FullPlugin:1" in events
    assert "layout:add_toolbar:FullPlugin:1" in events


def test_adapter_settles_layout_only_when_supported() -> None:
    events: list[str] = []
    adapter = _adapter(_kernel(events))
    adapter.after_lifecycle_transition({"status": "settled"})
    assert events == ["layout:settle"]

    adapter_without_layout = _adapter(SimpleNamespace(get_context=lambda: object()))
    adapter_without_layout.after_lifecycle_transition({"status": "settled"})


def test_loader_wires_exact_adapter_without_command_ownership_delegates() -> None:
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    events: list[str] = []
    loader = PluginLoader(_kernel(events))
    loader_source = (
        RUNTIME / "core" / "VitaLoom" / "kernel" / "plugin_loader.py"
    ).read_text(encoding="utf-8-sig")

    assert isinstance(loader.legacy_editor_plugin_adapter, LegacyEditorPluginAdapter)
    assert loader.runtime_plugin_host.adapter is loader.legacy_editor_plugin_adapter
    assert loader._activation_context_for.__self__ is loader
    assert loader._runtime_activation_context is None
    assert "runtime_adapter=self.legacy_editor_plugin_adapter" in loader_source
    assert "runtime_adapter=self," not in loader_source
    for concrete_marker in (
        "create_dock_widget",
        "create_viewport_widget",
        "add_menu_items",
        "add_toolbar_items",
        "get_theme_manager",
        "registry.register(owned_spec)",
    ):
        assert concrete_marker not in loader_source
    assert "def _register_menu(" not in loader_source
    assert ".register_menu(" not in loader_source
    assert "after_plugin_unload_callback" not in loader_source
    assert "after_plugin_shutdown_callback" not in loader_source



def test_adapter_projects_structural_legacy_payloads_without_provider_subclasses() -> None:
    from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
    from core.VitaLoom.kernel.plugin_interfaces import (
        IDockProvider,
        IThemeProvider,
        IViewportProvider,
    )

    events: list[str] = []

    class StructuralLegacyPayload(IRuntimePlugin):
        def get_plugin_info(self):
            return {
                "name": "StructuralLegacyPayload",
                "version": "1.0.0",
                "dependencies": [],
                "provides": ["dock", "viewport", "theme"],
            }

        def on_load(self, _context) -> None:
            events.append("plugin:on_load")

        def on_unload(self) -> None:
            events.append("plugin:on_unload")

        def create_dock_widget(self):
            events.append("plugin:create_dock")
            return "structural-dock"

        def get_dock_config(self):
            return {"title": "Structural Dock"}

        def create_viewport_widget(self):
            events.append("plugin:create_viewport")
            return "structural-viewport"

        def get_viewport_id(self):
            return "structural.viewport"

        def get_theme_name(self):
            return "Structural Theme"

        def get_stylesheet(self):
            return "QWidget { color: cyan; }"

    plugin = StructuralLegacyPayload()
    assert not isinstance(plugin, (IDockProvider, IViewportProvider, IThemeProvider))

    adapter = _adapter(_kernel(events))
    with patch.object(
        adapter,
        "_compose_theme_stylesheet",
        return_value="BASE\nQWidget { color: cyan; }",
    ):
        adapter.after_plugin_load(
            plugin,
            "StructuralLegacyPayload",
            plugin.get_plugin_info(),
        )

    assert "layout:add_dock:Structural Dock:structural-dock" in events
    assert "layout:add_viewport:structural.viewport:structural-viewport" in events
    assert "layout:add_theme:Structural Theme:BASE\nQWidget { color: cyan; }" in events
    assert events[-1] == "signal:loaded:StructuralLegacyPayload"

def test_adapter_blocks_dynamic_unload_when_declarative_viewport_cleanup_fails() -> None:
    events: list[str] = []

    class FailingViewportCleanupLayout(_Layout):
        def remove_viewport(self, viewport_id: str) -> bool:
            self.events.append(f"layout:remove_viewport:{viewport_id}")
            return False

    class ViewportPlugin:
        def get_plugin_info(self):
            return {
                "name": "ViewportPlugin",
                "version": "1.0.0",
                "dependencies": [],
                "provides": ["viewport", "editor_contribution"],
                "editor_contributions": [{
                    "id": "viewport.plugin.surface",
                    "kind": "viewport_surface",
                    "owner_plugin_id": "ViewportPlugin",
                    "viewport_id": "viewport.plugin",
                    "name_key": "viewport.plugin",
                    "default_name": "Viewport Plugin",
                }],
            }

    kernel = _kernel(events)
    kernel.layout_manager = FailingViewportCleanupLayout(events)
    adapter = _adapter(kernel)
    plugin = ViewportPlugin()
    info = plugin.get_plugin_info()
    adapter._declarative_viewport_owner_by_id["viewport.plugin"] = "ViewportPlugin"

    with pytest.raises(RuntimeError, match="viewport contribution cleanup failed"):
        adapter.before_plugin_unload(plugin, "ViewportPlugin", info)

    assert adapter._declarative_viewport_owner_by_id["viewport.plugin"] == "ViewportPlugin"
    assert events == ["layout:remove_viewport:viewport.plugin"]
