# -*- coding: utf-8 -*-
"""E54 proofs for declarative theme authority and activation rollback."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

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


class _Signal:
    def __init__(self, events: list[object], name: str) -> None:
        self.events = events
        self.name = name

    def emit(self, plugin_id: str) -> None:
        self.events.append((self.name, plugin_id))


class _ThemeLayout:
    def __init__(self, events: list[object]) -> None:
        self.events = events
        self.theme_state = {
            "application": "APP-BASELINE",
            "main_window": "WINDOW-BASELINE",
        }
        self.apply_calls: list[tuple[str, str]] = []
        self.restore_calls: list[dict[str, str]] = []

    def capture_theme_style_state(self):
        return dict(self.theme_state)

    def register_theme(self, theme_name: str, stylesheet: str) -> None:
        self.apply_calls.append((theme_name, stylesheet))
        self.theme_state = {
            "application": stylesheet,
            "main_window": stylesheet,
        }
        self.events.append(("apply_theme", theme_name, stylesheet))

    def restore_theme_style_state(self, state) -> None:
        copied = {
            "application": state["application"],
            "main_window": state["main_window"],
        }
        self.restore_calls.append(copied)
        self.theme_state = copied
        self.events.append(("restore_theme", copied))

    def add_menu_items(self, _items, _plugin_id: str) -> None:
        return None

    def add_toolbar_items(self, _items, _plugin_id: str) -> None:
        return None

    def remove_plugin_ui(self, plugin_id: str) -> None:
        self.events.append(("remove_ui", plugin_id))

    def process_pending_dock_tabify(self) -> None:
        return None


@pytest.fixture(autouse=True)
def _fresh_command_registry():
    from core.VitaLoom.commands.registry import reset_command_registry

    reset_command_registry()
    yield
    reset_command_registry()

def _style_dependencies():
    return (
        patch(
            "core.VitaLoom.ui.theme_manager.get_theme_manager",
            return_value=SimpleNamespace(DARK_THEME="DARK", LIGHT_THEME="LIGHT"),
        ),
        patch(
            "core.VitaLoom.ui.design_tokens.modern_editor_overlay",
            return_value="OVERLAY",
        ),
    )

def _plugin(payload_mode: str, events: list[object]):
    from core.VitaLoom.commands.registry import CommandSpec, command_ok
    from core.VitaLoom.core.runtime_plugin_contract import (
        ICommandProvider,
        IRuntimePlugin,
    )

    class DeclarativeThemePlugin(IRuntimePlugin, ICommandProvider):
        def __init__(self) -> None:
            self.payload_calls = 0
            self.unloaded = False
            if payload_mode == "none":
                self.get_stylesheet = lambda: None
            elif payload_mode == "raises":
                self.get_stylesheet = self._raise_payload
            elif payload_mode == "works":
                self.get_stylesheet = self._theme_payload
            elif payload_mode != "missing":
                raise AssertionError(f"unexpected payload mode: {payload_mode}")

        def get_plugin_info(self):
            return {
                "name": "DeclarativeThemePlugin",
                "version": "1.0.0",
                "dependencies": [],
                "provides": ["theme", "command", "editor_contribution"],
                "activation_context": "runtime",
                "editor_contributions": [
                    {
                        "id": "declarative.theme.profile",
                        "kind": "theme_profile",
                        "theme_id": "declarative.theme",
                        "name_key": "theme.declarative.name",
                        "default_name": "Declarative Theme",
                        "appearance": "dark",
                        "palette": {"background": "#101010", "text": "#efefef"},
                        "order": 10,
                    }
                ],
            }

        def get_command_specs(self):
            return [
                CommandSpec(
                    id="declarative.theme.command",
                    title="Declarative Theme Command",
                    owner="incorrect-declared-owner",
                    handler=lambda _payload, _context: command_ok(),
                )
            ]

        def on_load(self, _context) -> None:
            events.append("on_load")

        def on_unload(self) -> None:
            self.unloaded = True
            events.append("on_unload")

        def _theme_payload(self) -> str:
            self.payload_calls += 1
            return "THEME-PAYLOAD"

        def _raise_payload(self) -> str:
            self.payload_calls += 1
            raise RuntimeError("theme payload failed")

    return DeclarativeThemePlugin()


def _host(events: list[object]):
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    kernel = SimpleNamespace(
        layout_manager=_ThemeLayout(events),
        get_context=lambda: SimpleNamespace(),
        plugin_loaded=_Signal(events, "loaded"),
        plugin_unloaded=_Signal(events, "unloaded"),
    )
    adapter = LegacyEditorPluginAdapter(kernel)
    host = RuntimePluginHost(
        adapter=adapter,
        activation_context_resolver=lambda _plugin_info: object(),
    )
    return host, adapter, kernel


def test_qt_free_runtime_plugin_projects_declarative_theme_without_itheme_provider() -> None:
    from core.VitaLoom.commands.registry import get_command_registry

    events: list[object] = []
    plugin = _plugin("works", events)
    host, adapter, kernel = _host(events)
    host.register_plugin(plugin)

    dark_patch, overlay_patch = _style_dependencies()
    with dark_patch, overlay_patch:
        report = host.execute_lifecycle_target(
            {"DeclarativeThemePlugin"}, source="test", allow_deactivate=True
        )

    assert report["status"] == "settled"
    assert host.loaded_plugins == {"DeclarativeThemePlugin": plugin}
    assert plugin.payload_calls == 1
    assert kernel.layout_manager.apply_calls == [
        ("Declarative Theme", "DARK\nOVERLAY\nTHEME-PAYLOAD")
    ]
    assert get_command_registry().describe("declarative.theme.command")["owner"] == (
        "DeclarativeThemePlugin"
    )
    assert adapter._theme_owner_by_id == {
        "declarative.theme": "DeclarativeThemePlugin"
    }

    assert host.unload_plugin("DeclarativeThemePlugin") is True
    assert host.loaded_plugins == {}
    assert kernel.layout_manager.theme_state == {
        "application": "APP-BASELINE",
        "main_window": "WINDOW-BASELINE",
    }
    assert adapter._theme_owner_by_id == {}
    assert adapter._theme_projection_by_owner == {}
    assert adapter._theme_baseline_state is None
    assert plugin.unloaded is True


@pytest.mark.parametrize("payload_mode", ["missing", "none", "raises"])
def test_declarative_theme_payload_failure_rolls_back_host_publication(payload_mode: str) -> None:
    from core.VitaLoom.commands.registry import get_command_registry

    events: list[object] = []
    plugin = _plugin(payload_mode, events)
    host, adapter, kernel = _host(events)
    host.register_plugin(plugin)

    report = host.execute_lifecycle_target(
        {"DeclarativeThemePlugin"}, source="test", allow_deactivate=True
    )

    assert report["status"] == "failed"
    assert report["failed_action"]["action"] == "activate"
    assert host.loaded_plugins == {}
    assert get_command_registry().get("declarative.theme.command") is None
    assert kernel.layout_manager.apply_calls == []
    assert kernel.layout_manager.theme_state == {
        "application": "APP-BASELINE",
        "main_window": "WINDOW-BASELINE",
    }
    assert adapter._theme_owner_by_id == {}
    assert adapter._theme_projection_by_owner == {}
    assert adapter._theme_baseline_state is None
    assert plugin.unloaded is True
    assert ("loaded", "DeclarativeThemePlugin") not in events


def test_e54_source_guards_retire_legacy_theme_provider_from_builtin_authority() -> None:
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
    unity_theme_source = (
        RUNTIME
        / "builtin"
        / "editor_extensions"
        / "unity_dark_theme_plugin.py"
    ).read_text(encoding="utf-8-sig")

    assert "IThemeProvider" not in adapter_source
    assert "isinstance(plugin, IThemeProvider)" not in loader_source
    assert "IThemeProvider" not in unity_theme_source
    assert "class UnityDarkThemePlugin(IRuntimePlugin)" in unity_theme_source