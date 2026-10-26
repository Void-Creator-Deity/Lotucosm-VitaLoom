# -*- coding: utf-8 -*-
"""E56 proofs for capability-based legacy Editor-ready delivery."""
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
EDITOR_READY_BUILTINS = (
    ("builtin.editor_extensions.editor_workflow_plugin", "EditorWorkflowPlugin"),
    ("builtin.editor_extensions.localization_plugin", "LocalizationPlugin"),
    ("builtin.editor_extensions.hot_reload_plugin", "HotReloadPlugin"),
    ("builtin.editor_extensions.standard_ui_plugin", "StandardUIPlugin"),
)


class _Signal:
    def __init__(self, events: list[object], name: str) -> None:
        self.events = events
        self.name = name

    def emit(self, plugin_id: str) -> None:
        self.events.append((self.name, plugin_id))


class _Layout:
    def __init__(self, events: list[object]) -> None:
        self.events = events
        self.menu_items: list[tuple[str, list[dict[str, object]]]] = []

    def add_menu_items(self, items, plugin_id: str) -> None:
        copied = [dict(item) for item in items]
        self.menu_items.append((plugin_id, copied))
        self.events.append(("menu_projection", plugin_id))

    def add_toolbar_items(self, _items, _plugin_id: str) -> None:
        return None

    def remove_plugin_ui(self, plugin_id: str) -> None:
        self.events.append(("remove_ui", plugin_id))


class _EventBus:
    def subscribe(self, _event_name: str, _callback) -> None:
        return None

    def unsubscribe(self, _event_name: str, _callback) -> None:
        return None


def _host(events: list[object]):
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    kernel = SimpleNamespace(
        layout_manager=_Layout(events),
        get_context=lambda: SimpleNamespace(event_bus=_EventBus()),
        plugin_loaded=_Signal(events, "loaded"),
        plugin_unloaded=_Signal(events, "unloaded"),
    )
    adapter = LegacyEditorPluginAdapter(kernel)
    host = RuntimePluginHost(
        adapter=adapter,
        activation_context_resolver=lambda _plugin_info: object(),
    )
    return host, kernel


def _plugin(callback_mode: str, events: list[object]):
    from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin

    class DirectRuntimeEditorPlugin(IRuntimePlugin):
        def __init__(self) -> None:
            if callback_mode == "works":
                self.on_editor_ready = self._ready
            elif callback_mode == "non_callable":
                self.on_editor_ready = None
            elif callback_mode == "raises":
                self.on_editor_ready = self._raise_ready
            elif callback_mode != "missing":
                raise AssertionError(f"unexpected callback mode: {callback_mode}")

        def get_plugin_info(self):
            return {
                "name": "DirectRuntimeEditorPlugin",
                "version": "1.0.0",
                "dependencies": [],
                "provides": ["editor_contribution"],
                "editor_contributions": [
                    {
                        "id": "direct.ready.separator",
                        "kind": "menu_separator",
                        "menu_path": [
                            {
                                "id": "tools",
                                "label_key": "menu.tools",
                                "default_label": "Tools",
                            }
                        ],
                        "order": 1,
                    }
                ],
            }

        def on_load(self, _context) -> None:
            events.append("on_load")

        def on_unload(self) -> None:
            events.append("on_unload")

        def _ready(self) -> None:
            events.append("editor_ready")

        def _raise_ready(self) -> None:
            events.append("editor_ready_raises")
            raise RuntimeError("ready callback failed")

    return DirectRuntimeEditorPlugin()


def test_direct_runtime_plugin_receives_editor_ready_after_projection_without_ieditorplugin() -> None:
    from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
    from core.VitaLoom.kernel.plugin_interfaces import IEditorPlugin

    events: list[object] = []
    plugin = _plugin("works", events)
    host, kernel = _host(events)
    assert isinstance(plugin, IRuntimePlugin)
    assert not isinstance(plugin, IEditorPlugin)

    host.register_plugin(plugin)
    report = host.execute_lifecycle_target(
        {"DirectRuntimeEditorPlugin"}, source="test", allow_deactivate=True
    )

    assert report["status"] == "settled"
    assert host.loaded_plugins == {"DirectRuntimeEditorPlugin": plugin}
    assert kernel.layout_manager.menu_items
    assert events == [
        "on_load",
        ("menu_projection", "DirectRuntimeEditorPlugin"),
        "editor_ready",
        ("loaded", "DirectRuntimeEditorPlugin"),
    ]

    assert host.unload_plugin("DirectRuntimeEditorPlugin") is True
    assert events[-3:] == [
        ("remove_ui", "DirectRuntimeEditorPlugin"),
        "on_unload",
        ("unloaded", "DirectRuntimeEditorPlugin"),
    ]


@pytest.mark.parametrize("callback_mode", ("missing", "non_callable", "raises"))
def test_editor_ready_capability_is_optional_and_best_effort(callback_mode: str) -> None:
    events: list[object] = []
    plugin = _plugin(callback_mode, events)
    host, kernel = _host(events)
    host.register_plugin(plugin)

    report = host.execute_lifecycle_target(
        {"DirectRuntimeEditorPlugin"}, source="test", allow_deactivate=True
    )

    assert report["status"] == "settled"
    assert host.loaded_plugins == {"DirectRuntimeEditorPlugin": plugin}
    assert kernel.layout_manager.menu_items
    assert ("loaded", "DirectRuntimeEditorPlugin") in events
    if callback_mode == "raises":
        assert "editor_ready_raises" in events
    else:
        assert "editor_ready" not in events

    assert host.unload_plugin("DirectRuntimeEditorPlugin") is True
    assert host.loaded_plugins == {}


def test_adapter_and_builtins_have_no_ieditorplugin_runtime_authority() -> None:
    from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin

    adapter_source = (
        RUNTIME / "core" / "VitaLoom" / "kernel" / "legacy_editor_plugin_adapter.py"
    ).read_text(encoding="utf-8-sig")
    assert "IEditorPlugin" not in adapter_source

    for module_name, class_name in EDITOR_READY_BUILTINS:
        module = __import__(module_name, fromlist=[class_name])
        plugin_class = getattr(module, class_name)
        source_path = RUNTIME.joinpath(*module_name.split(".")).with_suffix(".py")
        source = source_path.read_text(encoding="utf-8-sig")
        assert "IEditorPlugin" not in source
        assert issubclass(plugin_class, IRuntimePlugin)

