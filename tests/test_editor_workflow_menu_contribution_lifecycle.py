# -*- coding: utf-8 -*-
"""E49 EditorWorkflow portable menu commands and bounded Qt bridge lifecycle."""
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
WORKFLOW_SOURCE = RUNTIME / "builtin" / "editor_extensions" / "editor_workflow_plugin.py"

COMMAND_IDS = [
    "plugin.editor_workflow.copy_pond_summary",
    "plugin.editor_workflow.export_pond",
    "plugin.editor_workflow.import_pond",
    "plugin.editor_workflow.scan_dependencies",
    "plugin.editor_workflow.export_player",
]


class _Signal:
    def emit(self, _value: str) -> None:
        return None


class _Layout:
    def __init__(self) -> None:
        self.menu_batches: list[tuple[str, list[dict[str, Any]]]] = []
        self.removed_ui: list[str] = []

    def add_menu_items(self, items, plugin_id: str) -> None:
        self.menu_batches.append((plugin_id, list(items)))

    def add_toolbar_items(self, items, plugin_id: str) -> None:
        raise AssertionError(f"unexpected toolbar projection: {plugin_id} {list(items)!r}")

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
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


def _normalized_info() -> dict[str, Any]:
    from builtin.editor_extensions.editor_workflow_plugin import EditorWorkflowPlugin
    from core.VitaLoom.core.editor_contribution_contract import parse_editor_contributions

    info = EditorWorkflowPlugin().get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "EditorWorkflowPlugin", info["editor_contributions"]
            )
        ],
    }


def test_declares_five_immutable_json_safe_menu_commands() -> None:
    from builtin.editor_extensions.editor_workflow_plugin import EditorWorkflowPlugin
    from core.VitaLoom.core.editor_contribution_contract import (
        EditorMenuCommandContribution,
        parse_editor_contributions,
    )

    info = EditorWorkflowPlugin().get_plugin_info()
    assert info["provides"] == ["command", "editor_contribution"]
    parsed = parse_editor_contributions(
        "EditorWorkflowPlugin", info["editor_contributions"]
    )
    assert len(parsed) == 5
    assert all(isinstance(item, EditorMenuCommandContribution) for item in parsed)
    assert [item.id for item in parsed] == [
        "editor_workflow.copy_pond_summary",
        "editor_workflow.export_pond",
        "editor_workflow.import_pond",
        "editor_workflow.scan_dependencies",
        "editor_workflow.export_player",
    ]
    assert [[segment.id for segment in item.menu_path] for item in parsed] == [
        ["edit"], ["file"], ["file"], ["file"], ["file"]
    ]
    assert [item.command_id for item in parsed] == COMMAND_IDS
    assert [item.label_key for item in parsed] == [
        "editor_workflow.copy_pond_summary",
        "editor_workflow.export_pond",
        "editor_workflow.import_pond",
        "editor_workflow.scan_dependencies",
        "editor_workflow.export_player",
    ]
    assert [item.order for item in parsed] == [10, 20, 30, 40, 50]
    assert all(dict(item.command_payload) == {} for item in parsed)
    assert all(item.shortcut is None for item in parsed)
    assert all(item.owner_plugin_id == "EditorWorkflowPlugin" for item in parsed)
    with pytest.raises(dataclasses.FrozenInstanceError):
        parsed[0].order = 99
    json.dumps(info["editor_contributions"], ensure_ascii=False)


def test_runtime_host_copies_metadata_and_canonical_owner() -> None:
    from builtin.editor_extensions.editor_workflow_plugin import EditorWorkflowPlugin
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    declaration = EditorWorkflowPlugin().get_plugin_info()

    class Plugin(EditorWorkflowPlugin):
        def get_plugin_info(self):
            return declaration

    host = RuntimePluginHost()
    plugin_id = host.register_plugin(Plugin())
    declaration["editor_contributions"][0]["order"] = 999
    observed = host.plugin_metadata[plugin_id]["editor_contributions"]
    assert [item["owner_plugin_id"] for item in observed] == [
        "EditorWorkflowPlugin"
    ] * 5
    assert [item["order"] for item in observed] == [10, 20, 30, 40, 50]
    json.dumps(observed, ensure_ascii=False)


def test_module_metadata_import_is_qt_free_and_legacy_live_menu_is_removed(monkeypatch) -> None:
    source = WORKFLOW_SOURCE.read_text(encoding="utf-8-sig")
    assert "IMenuProvider" not in source
    assert "def get_menu_items(" not in source
    assert "def get_toolbar_items(" not in source
    assert "language_changed" not in source
    assert "from PyQt6" not in "\n".join(source.splitlines()[:30])

    module_name = "builtin.editor_extensions.editor_workflow_plugin"
    sys.modules.pop(module_name, None)
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError(f"metadata import touched Qt: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    module = importlib.import_module(module_name)
    info = module.EditorWorkflowPlugin().get_plugin_info()
    assert len(info["editor_contributions"]) == 5


def test_exposes_exact_five_gui_required_canonical_commands() -> None:
    from builtin.editor_extensions.editor_workflow_plugin import EditorWorkflowPlugin

    specs = EditorWorkflowPlugin().get_command_specs()
    assert [spec.id for spec in specs] == COMMAND_IDS
    assert all(spec.owner == "EditorWorkflowPlugin" for spec in specs)
    assert all(spec.requires_gui is True for spec in specs)
    assert all(spec.mutates is True for spec in specs)
    assert all(spec.undoable is False for spec in specs)
    assert all(spec.input_schema == {"type": "object", "properties": {}} for spec in specs)
    assert all(spec.output_schema == {"type": "object"} for spec in specs)


def test_copy_summary_preserves_active_pond_shape_and_clipboard_bridge() -> None:
    from builtin.editor_extensions.editor_workflow_plugin import EditorWorkflowPlugin

    plugin = EditorWorkflowPlugin()
    assert hasattr(plugin, "_copy_pond_summary_command")
    assert hasattr(plugin, "_write_clipboard_text")
    plugin.on_load(_context())
    plugin._active_pond = lambda: SimpleNamespace(
        name="Alpha", time=12.5, organisms={"o2": object(), "o1": object()},
        floating_components=[1, 2],
    )
    copied: list[str] = []
    plugin._write_clipboard_text = copied.append

    result = plugin.copy_pond_summary()

    assert result["ok"] is True
    assert result["result"]["status"] == "copied"
    assert result["result"]["summary"] == {
        "name": "Alpha",
        "time": 12.5,
        "organisms": ["o2", "o1"],
        "floating_components": 2,
    }
    assert json.loads(copied[0]) == result["result"]["summary"]


def test_export_import_commands_preserve_json_serializer_and_cosmos_modes(monkeypatch, tmp_path) -> None:
    from builtin.editor_extensions.editor_workflow_plugin import EditorWorkflowPlugin

    saved: list[tuple[object, str, str]] = []
    loaded = SimpleNamespace(name="loaded")

    class Serializer:
        def __init__(self, save_format: str):
            self.save_format = save_format

        def save_pond(self, pond, path):
            saved.append((pond, str(path), self.save_format))
            return True

        def load_pond(self, path):
            assert str(path).endswith("input.json")
            assert self.save_format == "json"
            return loaded

    serializer_module = SimpleNamespace(PondSerializer=Serializer)
    monkeypatch.setitem(sys.modules, "builtin.systems.pond_serializer", serializer_module)

    active = SimpleNamespace(applied=[])
    active._apply_loaded_pond_state = active.applied.append

    class Cosmos:
        active_world_id = "active"
        worlds = {"active": active}

        def get_active_world(self):
            return self.worlds.get(self.active_world_id)

        def set_active_world(self, world_id):
            self.active_world_id = world_id

    cosmos = Cosmos()
    cosmos_module = SimpleNamespace(get_cosmos=lambda: cosmos)
    monkeypatch.setitem(sys.modules, "core.Lotucosm.cosmos", cosmos_module)

    plugin = EditorWorkflowPlugin()
    assert hasattr(plugin, "_export_pond_command")
    assert hasattr(plugin, "_import_pond_command")
    assert hasattr(plugin, "_choose_save_pond_path")
    assert hasattr(plugin, "_choose_open_pond_path")
    assert hasattr(plugin, "_choose_import_mode")
    plugin.on_load(_context())
    pond = SimpleNamespace(name="pond")
    plugin._active_pond = lambda: pond
    plugin._choose_save_pond_path = lambda: str(tmp_path / "output.json")
    plugin._choose_open_pond_path = lambda: str(tmp_path / "input.json")
    plugin._show_information = lambda *_args: None
    plugin._show_warning = lambda *_args: None

    exported = plugin.export_active_pond()
    assert exported["ok"] is True
    assert exported["result"]["status"] == "exported"
    assert saved == [(pond, str(tmp_path / "output.json"), "json")]

    plugin._choose_import_mode = lambda: "replace_active"
    replaced = plugin.import_pond_json()
    assert replaced["ok"] is True
    assert replaced["result"]["mode"] == "replace_active"
    assert active.applied == [loaded]
    assert cosmos.active_world_id == "active"

    plugin._choose_import_mode = lambda: "new_world"
    monkeypatch.setattr("uuid.uuid4", lambda: SimpleNamespace(hex="12345678abcdef"))
    created = plugin.import_pond_json()
    assert created["ok"] is True
    assert created["result"]["world_id"] == "imported_12345678"
    assert cosmos.worlds["imported_12345678"] is loaded
    assert cosmos.active_world_id == "imported_12345678"


def test_dependency_scan_preserves_console_escape_and_portable_result(monkeypatch, tmp_path) -> None:
    from builtin.editor_extensions.editor_workflow_plugin import EditorWorkflowPlugin
    from core.VitaLoom.core.service_keys import UI_CONSOLE_PANEL

    edge = SimpleNamespace(exists=False)
    scan_module = SimpleNamespace(
        scan_project_dependencies=lambda _path: [edge],
        dependency_summary=lambda _edges: {"total_edges": 1, "missing": 1},
        format_dependency_scan_report=lambda _path, _edges, _summary: "<missing>&",
    )
    monkeypatch.setitem(
        sys.modules, "builtin.editor_extensions.asset_dependency_scan", scan_module
    )
    console_calls: list[tuple[str, str]] = []
    panel = SimpleNamespace(log=lambda text, level: console_calls.append((text, level)))
    plugin = EditorWorkflowPlugin()
    assert hasattr(plugin, "_scan_dependencies_command")
    assert hasattr(plugin, "_show_dependency_missing_report")
    plugin.on_load(_context(current_project_path=str(tmp_path), services={UI_CONSOLE_PANEL: panel}))
    reports: list[str] = []
    plugin._show_dependency_missing_report = lambda report, *_args: reports.append(report)

    result = plugin.scan_scene_dependencies()

    assert result["ok"] is True
    assert result["result"]["status"] == "scanned"
    assert result["result"]["missing_count"] == 1
    assert result["result"]["console_published"] is True
    assert console_calls == [("&lt;missing&gt;&amp;", "warning")]
    assert reports == ["<missing>&"]


def test_adapter_projects_commands_without_legacy_enumeration_and_cleans_reload() -> None:
    from builtin.editor_extensions.editor_workflow_plugin import EditorWorkflowPlugin
    from core.VitaLoom.commands.registry import get_command_registry, reset_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import LegacyEditorPluginAdapter

    reset_command_registry()
    layout = _Layout()
    context = _context()
    kernel = SimpleNamespace(
        layout_manager=layout,
        get_context=lambda: context,
        plugin_loaded=_Signal(),
        plugin_unloaded=_Signal(),
    )
    context.kernel = kernel
    adapter = LegacyEditorPluginAdapter(kernel)
    first = EditorWorkflowPlugin()
    assert not hasattr(first, "get_menu_items")
    first._active_pond = lambda: SimpleNamespace(
        name="A", time=0, organisms={}, floating_components=[]
    )
    first._write_clipboard_text = lambda _text: None
    host = RuntimePluginHost(
        activation_context_resolver=lambda _info: context,
        adapter=adapter,
    )
    host.register_plugin(first)

    plugin_id = host.load_plugin(first)
    host.loaded_plugins[plugin_id] = first
    owner, items = layout.menu_batches[-1]
    assert owner == "EditorWorkflowPlugin"
    assert len(items) == 5
    assert [item["shortcut"] for item in items] == [None] * 5
    assert items[0]["action"]()["result"]["status"] == "copied"
    registry = get_command_registry()
    assert [registry.describe(command_id)["owner"] for command_id in COMMAND_IDS] == [
        "EditorWorkflowPlugin"
    ] * 5

    stale_action = items[0]["action"]
    assert host.unload_plugin("EditorWorkflowPlugin") is True
    assert stale_action()["error"]["code"] == "unknown_command"
    assert layout.removed_ui == ["EditorWorkflowPlugin"]
    for command_id in COMMAND_IDS:
        with pytest.raises(KeyError):
            registry.describe(command_id)

    second = EditorWorkflowPlugin()
    host.register_plugin(second)
    second_plugin_id = host.load_plugin(second)
    host.loaded_plugins[second_plugin_id] = second
    assert registry.describe(COMMAND_IDS[0])["owner"] == "EditorWorkflowPlugin"

def test_active_pond_falls_back_to_first_cosmos_world(monkeypatch) -> None:
    from builtin.editor_extensions.editor_workflow_plugin import EditorWorkflowPlugin

    fallback = SimpleNamespace(name="fallback")
    cosmos = SimpleNamespace(
        get_active_world=lambda: None,
        worlds={"first": fallback, "second": SimpleNamespace(name="second")},
    )
    monkeypatch.setitem(
        sys.modules,
        "core.Lotucosm.cosmos",
        SimpleNamespace(get_cosmos=lambda: cosmos),
    )

    assert EditorWorkflowPlugin()._active_pond() is fallback


def test_no_pond_and_dialog_cancellation_return_portable_results() -> None:
    from builtin.editor_extensions.editor_workflow_plugin import EditorWorkflowPlugin

    plugin = EditorWorkflowPlugin()
    plugin.on_load(_context())
    warnings: list[tuple[str, str]] = []
    plugin._show_warning = lambda title, text: warnings.append((title, text))
    plugin._active_pond = lambda: None

    copy_result = plugin.copy_pond_summary()
    export_no_pond = plugin.export_active_pond()
    assert copy_result["error"]["code"] == "editor_workflow_no_pond"
    assert export_no_pond["error"]["code"] == "editor_workflow_no_pond"
    assert len(warnings) == 2

    plugin._active_pond = lambda: SimpleNamespace()
    plugin._choose_save_pond_path = lambda: ""
    plugin._choose_open_pond_path = lambda: ""
    export_cancelled = plugin.export_active_pond()
    import_cancelled = plugin.import_pond_json()
    assert export_cancelled["result"] == {
        "status": "cancelled",
        "operation": "export_pond",
    }
    assert import_cancelled["result"]["stage"] == "file"


def test_import_mode_cancel_and_serializer_failures_are_deterministic(monkeypatch, tmp_path) -> None:
    from builtin.editor_extensions.editor_workflow_plugin import EditorWorkflowPlugin

    class Serializer:
        loaded: object | None = SimpleNamespace(name="loaded")
        save_ok = False

        def __init__(self, save_format: str):
            assert save_format == "json"

        def save_pond(self, _pond, _path):
            return self.save_ok

        def load_pond(self, _path):
            return self.loaded

    monkeypatch.setitem(
        sys.modules,
        "builtin.systems.pond_serializer",
        SimpleNamespace(PondSerializer=Serializer),
    )
    plugin = EditorWorkflowPlugin()
    plugin.on_load(_context())
    plugin._show_warning = lambda *_args: None
    plugin._show_information = lambda *_args: None
    plugin._active_pond = lambda: SimpleNamespace()
    plugin._choose_save_pond_path = lambda: str(tmp_path / "out.json")
    plugin._choose_open_pond_path = lambda: str(tmp_path / "in.json")

    export_failed = plugin.export_active_pond()
    assert export_failed["error"]["code"] == "pond_export_failed"

    Serializer.loaded = None
    import_failed = plugin.import_pond_json()
    assert import_failed["error"]["code"] == "pond_import_failed"

    Serializer.loaded = SimpleNamespace(name="loaded")
    plugin._choose_import_mode = lambda: None
    import_cancelled = plugin.import_pond_json()
    assert import_cancelled["ok"] is True
    assert import_cancelled["result"]["stage"] == "mode"


def test_project_validation_console_fallback_and_player_export_authority(monkeypatch, tmp_path) -> None:
    from builtin.editor_extensions.editor_workflow_plugin import EditorWorkflowPlugin
    from core.VitaLoom.core.service_keys import UI_CONSOLE_PANEL

    plugin = EditorWorkflowPlugin()
    plugin.on_load(_context())
    plugin._show_warning = lambda *_args: None
    assert plugin.scan_scene_dependencies()["error"]["code"] == (
        "editor_workflow_project_unavailable"
    )
    assert plugin.export_player_build()["error"]["code"] == (
        "editor_workflow_project_unavailable"
    )

    appended: list[str] = []
    plugin.context = _context(
        current_project_path=str(tmp_path),
        services={UI_CONSOLE_PANEL: SimpleNamespace(append_text=appended.append)},
    )
    assert plugin._push_dependency_report_to_console("<x>", False) is True
    assert appended == ["&lt;x&gt;"]

    output = tmp_path / "Player"
    calls: list[Path] = []
    monkeypatch.setitem(
        sys.modules,
        "tools.export_player",
        SimpleNamespace(export_project=lambda path: calls.append(path) or output),
    )
    plugin._show_information = lambda *_args: None
    exported = plugin.export_player_build()
    assert exported["ok"] is True
    assert exported["result"]["status"] == "exported"
    assert exported["result"]["output_path"] == str(output)
    assert calls == [tmp_path]

    def explode(_path):
        raise RuntimeError("player exploded")

    sys.modules["tools.export_player"] = SimpleNamespace(export_project=explode)
    failed = plugin.export_player_build()
    assert failed["error"]["code"] == "player_export_failed"
    assert failed["error"]["details"]["error"] == "player exploded"
