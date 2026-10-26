# -*- coding: utf-8 -*-
"""E50 StandardUI portable menu/save-toolbar and exact Host bridge lifecycle."""
from __future__ import annotations

import builtins
import dataclasses
import importlib
import json
import sys
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
STANDARD_SOURCE = RUNTIME / "builtin" / "editor_extensions" / "standard_ui_plugin.py"

COMMAND_IDS = [
    "plugin.standard_ui.save_project",
    "plugin.standard_ui.save_scene",
    "plugin.standard_ui.exit",
    "plugin.standard_ui.undo",
    "plugin.standard_ui.redo",
    "plugin.standard_ui.view.scene",
    "plugin.standard_ui.view.game",
    "plugin.standard_ui.layout.save",
    "plugin.standard_ui.layout.restore",
    "plugin.standard_ui.layout.reset",
    "plugin.standard_ui.dock.simulation.reveal",
    "plugin.standard_ui.dock.ecology.reveal",
    "plugin.standard_ui.dock.ps_experiment.reveal",
    "plugin.standard_ui.dock.inspector.toggle_floating",
    "plugin.standard_ui.dock.console.toggle_floating",
    "plugin.standard_ui.about",
]


class _EventBus:
    def __init__(self) -> None:
        self.callbacks: dict[str, list[Any]] = {}
        self.unsubscribe_calls: list[tuple[str, Any]] = []

    def subscribe(self, event: str, callback) -> None:
        self.callbacks.setdefault(event, []).append(callback)

    def unsubscribe(self, event: str, callback) -> None:
        self.unsubscribe_calls.append((event, callback))
        callbacks = self.callbacks.get(event, [])
        if callback in callbacks:
            callbacks.remove(callback)


class _Layout:
    def __init__(self) -> None:
        self.menu_batches: list[tuple[str, list[dict[str, Any]]]] = []
        self.toolbar_batches: list[tuple[str, list[dict[str, Any]]]] = []
        self.removed_ui: list[str] = []

    def add_menu_items(self, items, plugin_id: str) -> None:
        self.menu_batches.append((plugin_id, list(items)))

    def add_toolbar_items(self, items, plugin_id: str) -> None:
        self.toolbar_batches.append((plugin_id, list(items)))

    def remove_plugin_ui(self, plugin_id: str) -> None:
        self.removed_ui.append(plugin_id)

    def process_pending_dock_tabify(self) -> None:
        return None


def _context(**values: Any) -> SimpleNamespace:
    defaults = {
        "kernel": None,
        "current_project_path": "",
        "i18n_tr": lambda _key, default="": default,
        "services": {},
        "event_bus": _EventBus(),
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


def _normalized_info() -> dict[str, Any]:
    from builtin.editor_extensions.standard_ui_plugin import StandardUIPlugin
    from core.VitaLoom.core.editor_contribution_contract import parse_editor_contributions

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


def test_declares_exact_command_and_separator_inventory() -> None:
    from builtin.editor_extensions.standard_ui_plugin import StandardUIPlugin
    from core.VitaLoom.core.editor_contribution_contract import (
        EditorMenuCommandContribution,
        EditorMenuSeparatorContribution,
        EditorToolbarCommandContribution,
        EditorToolbarSeparatorContribution,
        parse_editor_contributions,
    )

    info = StandardUIPlugin().get_plugin_info()
    assert info["provides"] == ["command", "editor_contribution"]
    parsed = parse_editor_contributions("StandardUIPlugin", info["editor_contributions"])
    menu_commands = [item for item in parsed if isinstance(item, EditorMenuCommandContribution)]
    menu_separators = [item for item in parsed if isinstance(item, EditorMenuSeparatorContribution)]
    toolbar_commands = [item for item in parsed if isinstance(item, EditorToolbarCommandContribution)]
    toolbar_separators = [item for item in parsed if isinstance(item, EditorToolbarSeparatorContribution)]

    assert len(parsed) == 22
    assert len(menu_commands) == 16
    assert len(menu_separators) == 2
    assert len(toolbar_commands) == 3
    assert len(toolbar_separators) == 1
    assert [item.command_id for item in toolbar_commands] == [
        "plugin.standard_ui.save_project",
        "simulation.toggle",
        "simulation.stop",
    ]
    assert [item.command_id for item in menu_commands] == COMMAND_IDS
    assert [item.shortcut for item in menu_commands] == [
        "Ctrl+Shift+P", "Ctrl+S", "Alt+F4", "Ctrl+Z", "Ctrl+Y",
        "F1", "F2", None, None, None, "Ctrl+Shift+M", "Ctrl+Shift+E",
        "Ctrl+Shift+P", None, None, None,
    ]
    assert all(item.owner_plugin_id == "StandardUIPlugin" for item in parsed)
    assert all(dict(item.command_payload) == {} for item in menu_commands)
    assert dict(toolbar_commands[0].command_payload) == {}
    with pytest.raises(dataclasses.FrozenInstanceError):
        menu_separators[0].order = 999
    json.dumps(info["editor_contributions"], ensure_ascii=False)


def test_separator_contract_is_closed_and_rejects_command_fields() -> None:
    from core.VitaLoom.core import editor_contribution_contract as contract

    parsed = contract.parse_editor_contributions(
        "StandardUIPlugin",
        [
            {
                "id": "standard_ui.view.separator.primary",
                "kind": "menu_separator",
                "menu_path": [
                    {"id": "view", "label_key": "menu.view", "default_label": "??"}
                ],
                "order": 80,
            },
            {
                "id": "standard_ui.toolbar.separator",
                "kind": "toolbar_separator",
                "group": "standard",
                "order": 15,
            },
        ],
    )
    assert parsed[0].to_dict()["kind"] == "toolbar_separator"
    assert parsed[1].to_dict()["kind"] == "menu_separator"

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "StandardUIPlugin",
            [{
                "id": "bad.separator",
                "kind": "menu_separator",
                "menu_path": [{"id": "view", "label_key": "menu.view", "default_label": "??"}],
                "command_id": "forbidden",
                "order": 1,
            }],
        )
    assert captured.value.code == "contribution_field_unknown"


def test_module_metadata_import_is_qt_free_and_legacy_live_provider_is_removed(monkeypatch) -> None:
    source = STANDARD_SOURCE.read_text(encoding="utf-8-sig")
    assert "IMenuProvider" not in source
    assert "def get_menu_items(" not in source
    assert "def get_toolbar_items(" not in source
    assert "language_changed" not in source
    assert "refresh_legacy_menu_contributions" not in source
    assert "from PyQt6" not in "\n".join(source.splitlines()[:30])

    module_name = "builtin.editor_extensions.standard_ui_plugin"
    sys.modules.pop(module_name, None)
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError(f"metadata import touched Qt: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    module = importlib.import_module(module_name)
    assert len(module.StandardUIPlugin().get_plugin_info()["editor_contributions"]) == 22


def test_exposes_exact_standard_ui_canonical_commands() -> None:
    from builtin.editor_extensions.standard_ui_plugin import StandardUIPlugin

    specs = StandardUIPlugin().get_command_specs()
    assert [spec.id for spec in specs] == COMMAND_IDS
    assert all(spec.owner == "StandardUIPlugin" for spec in specs)
    assert all(spec.requires_gui is True for spec in specs)
    assert all(spec.undoable is False for spec in specs)
    assert all(spec.input_schema == {"type": "object", "properties": {}} for spec in specs)
    assert all(spec.output_schema == {"type": "object"} for spec in specs)


def test_event_lifecycle_keeps_status_and_project_events_only() -> None:
    from builtin.editor_extensions.standard_ui_plugin import StandardUIPlugin

    bus = _EventBus()
    plugin = StandardUIPlugin()
    plugin.on_load(_context(event_bus=bus))
    assert set(bus.callbacks) == {"ps_experiment_state", "project_opened"}
    assert len(bus.callbacks["ps_experiment_state"]) == 1
    assert len(bus.callbacks["project_opened"]) == 1

    plugin.on_unload()
    assert bus.callbacks["ps_experiment_state"] == []
    assert bus.callbacks["project_opened"] == []
    plugin.on_unload()


def test_adapter_projects_actions_and_structural_separators_without_legacy_enumeration(monkeypatch) -> None:
    from builtin.editor_extensions.standard_ui_plugin import StandardUIPlugin
    from core.VitaLoom.commands.registry import get_command_registry, reset_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import LegacyEditorPluginAdapter

    reset_command_registry()
    layout = _Layout()
    context = _context()
    kernel = SimpleNamespace(
        layout_manager=layout,
        get_context=lambda: context,
        plugin_loaded=SimpleNamespace(emit=lambda _value: None),
        plugin_unloaded=SimpleNamespace(emit=lambda _value: None),
    )
    context.kernel = kernel
    adapter = LegacyEditorPluginAdapter(kernel)
    plugin = StandardUIPlugin()
    plugin.get_menu_items = lambda: (_ for _ in ()).throw(
        AssertionError("legacy menu enumerated")
    )
    plugin.get_toolbar_items = lambda: (_ for _ in ()).throw(
        AssertionError("legacy toolbar enumerated")
    )
    host = RuntimePluginHost(
        activation_context_resolver=lambda _info: context,
        adapter=adapter,
    )
    host.register_plugin(plugin, protected=False)

    plugin_id = host.load_plugin(plugin)
    host.loaded_plugins[plugin_id] = plugin
    owner, menu_items = layout.menu_batches[-1]
    toolbar_owner, toolbar_items = layout.toolbar_batches[-1]
    assert owner == toolbar_owner == "StandardUIPlugin"
    assert len(menu_items) == 18
    assert sum(item.get("separator") is True for item in menu_items) == 2
    assert len(toolbar_items) == 4
    assert toolbar_items[0]["text"] == "保存"
    assert toolbar_items[1] == {"separator": True}
    assert [
        item.get("shortcut") for item in menu_items if not item.get("separator")
    ].count("Ctrl+Shift+P") == 2
    registry = get_command_registry()
    assert [registry.describe(command_id)["owner"] for command_id in COMMAND_IDS] == [
        "StandardUIPlugin"
    ] * len(COMMAND_IDS)

    command_calls: list[tuple[str, dict[str, Any]]] = []
    original_run = registry.run

    def recording_run(command_id, payload=None, context=None):
        normalized_payload = dict(payload or {})
        command_calls.append((command_id, normalized_payload))
        if command_id == "command.undo":
            return {
                "ok": True,
                "result": {
                    "status": "undone",
                    "scene_path": "C:/project/scenes/main.pond",
                },
            }
        if command_id == "scene.open":
            return {"ok": True, "result": {"status": "opened"}}
        return original_run(command_id, normalized_payload, context=context)

    monkeypatch.setattr(registry, "run", recording_run)
    undo_action = next(
        item["action"]
        for item in menu_items
        if item.get("shortcut") == "Ctrl+Z"
    )
    assert undo_action()["result"]["status"] == "undone"
    assert command_calls == [
        ("plugin.standard_ui.undo", {}),
        ("command.undo", {}),
        ("scene.open", {"scene_path": "C:/project/scenes/main.pond"}),
    ]
    stale_action = next(item["action"] for item in menu_items if item.get("action"))
    assert host.unload_plugin("StandardUIPlugin") is True
    assert stale_action()["error"]["code"] == "unknown_command"
    assert layout.removed_ui == ["StandardUIPlugin"]

def test_project_scene_history_layout_and_dialog_bridges_return_portable_results(monkeypatch) -> None:
    from builtin.editor_extensions import standard_ui_plugin

    calls: list[Any] = []

    class HistoryRegistry:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []
            self.responses = {
                "command.undo": {
                    "ok": True,
                    "result": {"status": "undone", "scene_path": "C:/project/scenes/main.pond"},
                },
                "command.redo": {
                    "ok": True,
                    "result": {"status": "redone", "scene_path": "C:/project/scenes/main.pond"},
                },
                "scene.open": {"ok": True, "result": {"status": "opened"}},
            }

        def run(self, command_id: str, payload: dict[str, Any]):
            self.calls.append((command_id, dict(payload)))
            return self.responses[command_id]

    class Dock:
        def setVisible(self, value): calls.append(("visible", value))
        def show(self): calls.append("show")
        def raise_(self): calls.append("raise")

    history_registry = HistoryRegistry()
    monkeypatch.setattr(
        standard_ui_plugin,
        "get_command_registry",
        lambda: history_registry,
    )
    layout = SimpleNamespace(
        viewport_providers={},
        docks={"Simulation": Dock()},
        switch_viewport=lambda value: calls.append(("viewport", value)),
        save_layout=lambda: calls.append("save_layout"),
        restore_layout=lambda: calls.append("restore_layout"),
        reset_layout=lambda: calls.append("reset_layout"),
        toggle_dock_floating=lambda value: calls.append(("toggle", value)),
    )
    kernel = SimpleNamespace(
        layout_manager=layout,
        project_world_session_host=SimpleNamespace(save_project=lambda: True),
        close=lambda: calls.append("close"),
    )
    plugin = standard_ui_plugin.StandardUIPlugin()
    plugin.on_load(_context(kernel=kernel, current_project_path="C:/project"))
    warnings: list[tuple[str, str]] = []
    critical: list[tuple[str, str]] = []
    about: list[tuple[str, str]] = []
    plugin._show_warning = lambda title, message: warnings.append((title, message))
    plugin._show_critical = lambda title, message: critical.append((title, message))
    plugin._show_about = lambda title, message: about.append((title, message))

    assert plugin.save_project()["result"]["status"] == "saved"
    assert plugin.undo()["result"]["status"] == "undone"
    assert plugin.redo()["result"]["status"] == "redone"
    assert history_registry.calls == [
        ("command.undo", {}),
        ("scene.open", {"scene_path": "C:/project/scenes/main.pond"}),
        ("command.redo", {}),
        ("scene.open", {"scene_path": "C:/project/scenes/main.pond"}),
    ]

    history_registry.responses["command.undo"] = {
        "ok": False,
        "error": {"code": "undo_empty", "message": "No undo operation is available"},
    }
    assert plugin.undo()["error"]["code"] == "undo_empty"
    assert history_registry.calls[-1] == ("command.undo", {})
    assert history_registry.calls.count(("scene.open", {"scene_path": "C:/project/scenes/main.pond"})) == 2

    assert plugin.switch_to_scene_view()["result"]["viewport_id"] == "scene"
    assert plugin.save_layout()["result"]["status"] == "saved"
    assert plugin.show_simulation_dock()["result"]["dock_id"] == "Simulation"
    assert plugin.toggle_inspector_float()["result"]["dock_id"] == "Inspector"
    assert plugin.exit_application()["result"]["status"] == "closed"
    assert plugin.show_about()["result"]["status"] == "shown"
    json.dumps(plugin.get_command_specs()[0].handler({}, {}), ensure_ascii=False)
    assert not warnings and not critical
    assert about