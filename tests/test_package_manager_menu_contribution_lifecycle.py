# -*- coding: utf-8 -*-
"""E48 PackageManager portable reveal menu command and Dock visibility lifecycle."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

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
PACKAGE_MANAGER_SOURCE = (
    RUNTIME / "builtin" / "editor_extensions" / "package_manager_plugin.py"
)


def _normalized_info() -> dict[str, Any]:
    from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin
    from core.VitaLoom.core.editor_contribution_contract import (
        parse_editor_contributions,
    )

    info = PackageManagerPlugin().get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "PackageManagerPlugin",
                info["editor_contributions"],
            )
        ],
    }


def _contains_live_value(value: object) -> bool:
    if callable(value):
        return True
    if isinstance(value, dict):
        return any(_contains_live_value(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_live_value(item) for item in value)
    return False


class _Signal:
    def __init__(self) -> None:
        self.values: list[str] = []
        self.callbacks: list[Any] = []

    def connect(self, callback: Any) -> None:
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def disconnect(self, callback: Any) -> None:
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def emit(self, value: str) -> None:
        self.values.append(value)
        for callback in tuple(self.callbacks):
            callback(value)


class _Dock:
    def __init__(self) -> None:
        self.object_name = ""
        self.title = ""

    def setObjectName(self, value: str) -> None:
        self.object_name = value

    def setWindowTitle(self, value: str) -> None:
        self.title = value


class _Layout:
    def __init__(self) -> None:
        self.docks: dict[str, object] = {}
        self.menu_batches: list[tuple[str, list[dict[str, Any]]]] = []
        self.removed_ui: list[str] = []
        self.removed_docks: list[str] = []

    def add_dock(self, dock: object, config: dict[str, Any]) -> None:
        self.docks[str(config["title"])] = dock

    def remove_dock(self, dock_id: str) -> None:
        self.removed_docks.append(dock_id)
        self.docks.pop(dock_id, None)

    def add_menu_items(self, items, plugin_id: str) -> None:
        self.menu_batches.append((plugin_id, list(items)))

    def add_toolbar_items(self, items, plugin_id: str) -> None:
        raise AssertionError(f"unexpected toolbar projection for {plugin_id}: {list(items)!r}")

    def remove_plugin_ui(self, plugin_id: str) -> None:
        self.removed_ui.append(plugin_id)

    def process_pending_dock_tabify(self) -> None:
        return None


class _RevealLayout:
    def __init__(self) -> None:
        self.calls: list[tuple[str, bool]] = []

    def show_dock_with_mode(self, dock_id: str, floating: bool) -> None:
        self.calls.append((dock_id, floating))


class _Toggle:
    def __init__(self) -> None:
        self.checked: list[bool] = []

    def setChecked(self, value: bool) -> None:
        self.checked.append(bool(value))


def test_package_manager_declares_one_immutable_json_safe_reveal_menu_command() -> None:
    from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin
    from core.VitaLoom.core.editor_contribution_contract import (
        EditorDockSurfaceContribution,
        EditorMenuCommandContribution,
        parse_editor_contributions,
    )

    info = PackageManagerPlugin().get_plugin_info()
    assert info["provides"] == ["dock", "command", "editor_contribution"]
    parsed = parse_editor_contributions(
        "PackageManagerPlugin", info["editor_contributions"]
    )
    assert len(parsed) == 2
    dock = next(item for item in parsed if isinstance(item, EditorDockSurfaceContribution))
    menu = next(item for item in parsed if isinstance(item, EditorMenuCommandContribution))

    assert dock.id == "package_manager.surface"
    assert menu.id == "package_manager.reveal"
    assert menu.owner_plugin_id == "PackageManagerPlugin"
    assert [segment.id for segment in menu.menu_path] == ["tools"]
    assert menu.label_key == "plugin_manager.title"
    assert menu.default_label == "项目插件"
    assert menu.command_id == "plugin.package_manager.reveal"
    assert dict(menu.command_payload) == {}
    assert menu.shortcut is None
    assert menu.order == 70
    with pytest.raises(dataclasses.FrozenInstanceError):
        menu.order = 99

    copied = json.loads(json.dumps(info["editor_contributions"], ensure_ascii=False))
    assert copied == info["editor_contributions"]
    assert not _contains_live_value(copied)


def test_runtime_host_copies_package_manager_menu_and_canonical_owner() -> None:
    from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    declaration = PackageManagerPlugin().get_plugin_info()

    class Plugin(PackageManagerPlugin):
        def get_plugin_info(self):
            return declaration

    host = RuntimePluginHost()
    plugin_id = host.register_plugin(Plugin())
    declaration["editor_contributions"][1]["order"] = 999

    observed = host.plugin_metadata[plugin_id]["editor_contributions"]
    menu = next(item for item in observed if item["id"] == "package_manager.reveal")
    assert menu["owner_plugin_id"] == "PackageManagerPlugin"
    assert menu["order"] == 70
    json.dumps(observed, ensure_ascii=False)

def test_package_manager_source_removes_legacy_live_menu_provider() -> None:
    source = PACKAGE_MANAGER_SOURCE.read_text(encoding="utf-8-sig")

    assert "IMenuProvider" not in source
    assert "def get_menu_items(" not in source
    assert "def get_toolbar_items(" not in source


def test_package_manager_exposes_exact_canonical_gui_reveal_command() -> None:
    from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin

    specs = PackageManagerPlugin().get_command_specs()

    assert len(specs) == 1
    spec = specs[0]
    assert spec.id == "plugin.package_manager.reveal"
    assert spec.owner == "PackageManagerPlugin"
    assert spec.mutates is True
    assert spec.undoable is False
    assert spec.requires_gui is True
    assert spec.input_schema == {"type": "object", "properties": {}}
    assert spec.output_schema == {"type": "object"}


def test_reveal_command_returns_portable_dock_or_dialog_result_and_failure() -> None:
    from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin

    plugin = PackageManagerPlugin()
    plugin.show = lambda: "dock"
    dock_result = plugin._reveal_command({}, {})
    assert dock_result["ok"] is True
    assert dock_result["result"] == {
        "status": "revealed",
        "surface": "dock",
        "dock_id": "Package Manager",
    }

    plugin.show = lambda: "dialog"
    dialog_result = plugin._reveal_command({}, {})
    assert dialog_result["ok"] is True
    assert dialog_result["result"]["surface"] == "dialog"

    plugin.show = lambda: None
    unavailable = plugin._reveal_command({}, {})
    assert unavailable["ok"] is False
    assert unavailable["error"]["code"] == "package_manager_reveal_unavailable"

    def _boom():
        raise RuntimeError("reveal exploded")

    plugin.show = _boom
    failed = plugin._reveal_command({}, {})
    assert failed["ok"] is False
    assert failed["error"]["code"] == "package_manager_reveal_failed"
    assert failed["error"]["details"] == {"error": "reveal exploded"}


def test_existing_show_path_preserves_layout_mode_geometry_and_retained_content() -> None:
    from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin

    plugin = PackageManagerPlugin()
    layout = _RevealLayout()
    plugin.kernel = SimpleNamespace(layout_manager=layout)
    plugin.dock = object()
    plugin.window = None
    plugin._ensure_ui_refs = lambda: True
    plugin._get_package_manager_open_mode = lambda: "floating"
    events: list[str] = []
    plugin._sync_hex_from_dock_for_fallback = lambda: events.append("sync_geometry")
    plugin._ensure_floating_dock_size = lambda: events.append("ensure_size")
    plugin._refresh = lambda: events.append("refresh")
    plugin._on_selection_changed = lambda: events.append("selection")
    plugin._update_float_toggle_btn_text = lambda: events.append("toggle_text")
    plugin.open_mode_toggle_cb = _Toggle()

    result = plugin.show()

    assert result == "dock"
    assert layout.calls == [("Package Manager", True)]
    assert events == [
        "sync_geometry",
        "ensure_size",
        "refresh",
        "selection",
        "toggle_text",
    ]
    assert plugin.open_mode_toggle_cb.checked == [True]


def test_adapter_projects_copied_menu_without_legacy_enumeration_and_canonicalizes_owner() -> None:
    from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin
    from core.VitaLoom.commands.registry import get_command_registry, reset_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    reset_command_registry()
    layout = _Layout()
    context = SimpleNamespace(i18n_tr=lambda _key, default="": default)
    kernel = SimpleNamespace(
        layout_manager=layout,
        get_context=lambda: context,
        plugin_loaded=_Signal(),
        plugin_unloaded=_Signal(),
    )
    context.kernel = kernel
    adapter = LegacyEditorPluginAdapter(kernel)
    plugin = PackageManagerPlugin()
    plugin.create_dock_widget = lambda: _Dock()
    plugin.show = lambda: "dock"
    declared_specs = plugin.get_command_specs
    plugin.get_command_specs = lambda: [
        dataclasses.replace(spec, owner="declared-owner")
        for spec in declared_specs()
    ]
    host = RuntimePluginHost(
        activation_context_resolver=lambda _info: context,
        adapter=adapter,
    )
    host.register_plugin(plugin)

    plugin_id = host.load_plugin(plugin)
    host.loaded_plugins[plugin_id] = plugin
    assert len(layout.menu_batches) == 1
    owner, items = layout.menu_batches[0]
    assert owner == "PackageManagerPlugin"
    assert len(items) == 1
    declared_menu = next(
        contribution
        for contribution in _normalized_info()["editor_contributions"]
        if contribution["id"] == "package_manager.reveal"
    )
    expected_path = "/".join(
        [
            *(segment["default_label"] for segment in declared_menu["menu_path"]),
            declared_menu["default_label"],
        ]
    )
    assert items[0]["path"] == expected_path
    assert items[0]["shortcut"] is None
    result = items[0]["action"]()
    assert result["ok"] is True
    assert result["result"]["surface"] == "dock"
    registry = get_command_registry()
    assert registry.describe("plugin.package_manager.reveal")["owner"] == (
        "PackageManagerPlugin"
    )

def test_unload_reload_cleans_reveal_command_action_and_existing_dock_authority() -> None:
    from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin
    from core.VitaLoom.commands.registry import get_command_registry, reset_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    reset_command_registry()
    layout = _Layout()
    context = SimpleNamespace(i18n_tr=lambda _key, default="": default)
    kernel = SimpleNamespace(
        layout_manager=layout,
        get_context=lambda: context,
        plugin_loaded=_Signal(),
        plugin_unloaded=_Signal(),
    )
    context.kernel = kernel
    adapter = LegacyEditorPluginAdapter(kernel)
    host = RuntimePluginHost(
        activation_context_resolver=lambda _info: context,
        adapter=adapter,
    )

    first = PackageManagerPlugin()
    first.create_dock_widget = lambda: _Dock()
    first.show = lambda: "dock"
    host.register_plugin(first, protected=False)
    first_plugin_id = host.load_plugin(first)
    host.loaded_plugins[first_plugin_id] = first
    old_action = layout.menu_batches[-1][1][0]["action"]
    assert host.unload_plugin("PackageManagerPlugin") is True

    registry = get_command_registry()
    with pytest.raises(KeyError):
        registry.describe("plugin.package_manager.reveal")
    assert old_action()["error"]["code"] == "unknown_command"
    assert layout.removed_docks == ["Package Manager"]
    assert layout.removed_ui == ["PackageManagerPlugin"]

    second = PackageManagerPlugin()
    second.create_dock_widget = lambda: _Dock()
    second.show = lambda: "dock"
    host.register_plugin(second, protected=False)
    second_plugin_id = host.load_plugin(second)
    host.loaded_plugins[second_plugin_id] = second
    assert registry.describe("plugin.package_manager.reveal")["owner"] == (
        "PackageManagerPlugin"
    )

