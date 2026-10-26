# -*- coding: utf-8 -*-
"""E47: Qt-free Hot Reload menu contributions and dialog bridge lifecycle."""
from __future__ import annotations

import dataclasses
import json
import os
import subprocess
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


class _PluginHostCapability:
    def __init__(self, snapshot: dict[str, Any], reports: dict[str, dict[str, Any]] | None = None):
        self.snapshot = snapshot
        self.reports = dict(reports or {})
        self.observe_calls = 0
        self.reload_calls: list[str] = []

    def observe_plugins(self) -> dict[str, Any]:
        self.observe_calls += 1
        return json.loads(json.dumps(self.snapshot))

    def reload_plugin(self, plugin_id: str) -> dict[str, Any]:
        self.reload_calls.append(plugin_id)
        return dict(
            self.reports.get(
                plugin_id,
                {"status": "settled", "plugin_id": plugin_id},
            )
        )

    def unload_plugin(self, plugin_id: str) -> dict[str, Any]:
        return {"status": "settled", "plugin_id": plugin_id}

    def scan_project_addons(self, project_path: object) -> dict[str, Any]:
        return {"status": "settled", "project_path": str(project_path)}

    def sync_plugins_for_project(
        self, project_data: dict[str, Any], *, repo_root: object | None = None
    ) -> dict[str, Any]:
        return {"status": "settled"}


def _context(host: _PluginHostCapability) -> SimpleNamespace:
    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
    )
    from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION

    services = InMemoryRuntimeCapabilityRegistry()
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    return SimpleNamespace(
        services=services,
        kernel=object(),
        i18n_tr=lambda _key, default="": default,
    )


def _normalized_info() -> dict[str, Any]:
    from builtin.editor_extensions.hot_reload_plugin import HotReloadPlugin
    from core.VitaLoom.core.editor_contribution_contract import (
        parse_editor_contributions,
    )

    info = HotReloadPlugin().get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "HotReloadPlugin",
                info["editor_contributions"],
            )
        ],
    }


class _Signal:
    def __init__(self, events: list[object], name: str) -> None:
        self.events = events
        self.name = name

    def emit(self, plugin_id: str) -> None:
        self.events.append((self.name, plugin_id))


class _Layout:
    def __init__(self, events: list[object]) -> None:
        self.events = events
        self.menu_batches: list[tuple[str, list[dict[str, Any]]]] = []

    def add_menu_items(self, items, plugin_id: str) -> None:
        copied = list(items)
        self.menu_batches.append((plugin_id, copied))
        self.events.append(("menu", plugin_id, copied))

    def add_toolbar_items(self, items, plugin_id: str) -> None:
        self.events.append(("toolbar", plugin_id, list(items)))

    def remove_plugin_ui(self, plugin_id: str) -> None:
        self.events.append(("remove", plugin_id))


def _kernel(events: list[object], context: object) -> SimpleNamespace:
    return SimpleNamespace(
        layout_manager=_Layout(events),
        get_context=lambda: context,
        plugin_loaded=_Signal(events, "loaded"),
        plugin_unloaded=_Signal(events, "unloaded"),
    )


def test_hot_reload_declares_two_immutable_json_safe_menu_commands() -> None:
    from builtin.editor_extensions.hot_reload_plugin import HotReloadPlugin
    from core.VitaLoom.core.editor_contribution_contract import (
        parse_editor_contributions,
    )

    info = HotReloadPlugin().get_plugin_info()
    assert info["provides"] == ["command", "editor_contribution"]
    parsed = parse_editor_contributions(
        "HotReloadPlugin", info["editor_contributions"]
    )

    assert [item.id for item in parsed] == [
        "hot_reload.choose",
        "hot_reload.user_mod",
    ]
    assert [item.command_id for item in parsed] == [
        "plugin.hot_reload.choose",
        "plugin.hot_reload.user_mod",
    ]
    assert [item.shortcut for item in parsed] == ["F5", "Ctrl+Shift+F5"]
    assert [item.order for item in parsed] == [10, 20]
    assert [segment.id for segment in parsed[0].menu_path] == ["develop"]
    assert parsed[0].owner_plugin_id == "HotReloadPlugin"
    with pytest.raises(dataclasses.FrozenInstanceError):
        parsed[0].shortcut = "F6"

    observed = [item.to_dict() for item in parsed]
    assert json.loads(json.dumps(observed, ensure_ascii=False)) == observed
    serialized = json.dumps(observed, ensure_ascii=False)
    for forbidden in ("QInputDialog", "PyQt6", "reload_selected_plugin", "<function"):
        assert forbidden not in serialized


def test_menu_shortcut_contract_accepts_plain_text_and_rejects_live_values() -> None:
    from core.VitaLoom.core.editor_contribution_contract import (
        EditorContributionContractError,
        parse_editor_contributions,
    )

    item = _normalized_info()["editor_contributions"][0]
    declaration = {key: value for key, value in item.items() if key != "owner_plugin_id"}
    assert parse_editor_contributions("HotReloadPlugin", [declaration])[0].shortcut == "F5"

    declaration["shortcut"] = lambda: None
    with pytest.raises(EditorContributionContractError) as captured:
        parse_editor_contributions("HotReloadPlugin", [declaration])
    assert captured.value.code == "contribution_live_value_forbidden"


def test_hot_reload_metadata_is_observable_without_importing_pyqt() -> None:
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(
        [str(RUNTIME), existing] if existing else [str(RUNTIME)]
    )
    code = r'''
import builtins, json
original_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == "PyQt6" or name.startswith("PyQt6."):
        raise RuntimeError("PyQt import forbidden while reading metadata")
    return original_import(name, *args, **kwargs)
builtins.__import__ = guarded
from builtin.editor_extensions.hot_reload_plugin import HotReloadPlugin
json.dumps(HotReloadPlugin().get_plugin_info())
'''
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        cwd=RUNTIME,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_runtime_host_copies_hot_reload_contributions_and_canonical_owner() -> None:
    from builtin.editor_extensions.hot_reload_plugin import HotReloadPlugin
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    declaration = HotReloadPlugin().get_plugin_info()

    class Plugin(HotReloadPlugin):
        def get_plugin_info(self):
            return declaration

    host = RuntimePluginHost()
    plugin_id = host.register_plugin(Plugin())
    declaration["editor_contributions"][0]["shortcut"] = "F12"

    observed = host.plugin_metadata[plugin_id]["editor_contributions"]
    assert observed[0]["owner_plugin_id"] == "HotReloadPlugin"
    assert observed[0]["shortcut"] == "F5"
    json.dumps(observed, ensure_ascii=False)


def test_legacy_projection_preserves_shortcuts_without_live_menu_enumeration() -> None:
    from builtin.editor_extensions.hot_reload_plugin import HotReloadPlugin
    from core.VitaLoom.commands.registry import reset_command_registry
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    reset_command_registry()
    events: list[object] = []
    host = _PluginHostCapability({"reloadable_plugin_ids": [], "catalog": []})
    context = _context(host)
    kernel = _kernel(events, context)
    context.kernel = kernel
    plugin = HotReloadPlugin()
    plugin.on_load(context)
    plugin.get_menu_items = lambda: (_ for _ in ()).throw(
        AssertionError("declarative projection must not enumerate legacy menu callbacks")
    )

    adapter = LegacyEditorPluginAdapter(kernel)
    adapter.after_plugin_load(plugin, "HotReloadPlugin", _normalized_info())

    plugin_id, items = kernel.layout_manager.menu_batches[-1]
    assert plugin_id == "HotReloadPlugin"
    assert [item["shortcut"] for item in items] == ["F5", "Ctrl+Shift+F5"]
    assert all(callable(item["action"]) for item in items)


def test_hot_reload_registers_exactly_two_host_owned_gui_commands() -> None:
    from builtin.editor_extensions.hot_reload_plugin import HotReloadPlugin
    from core.VitaLoom.commands.registry import get_command_registry, reset_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    reset_command_registry()
    plugin = HotReloadPlugin()
    specs = plugin.get_command_specs()
    assert [spec.id for spec in specs] == [
        "plugin.hot_reload.choose",
        "plugin.hot_reload.user_mod",
    ]
    assert all(spec.requires_gui for spec in specs)
    assert all(spec.mutates for spec in specs)

    context = _context(
        _PluginHostCapability({"reloadable_plugin_ids": [], "catalog": []})
    )
    declared_info = plugin.get_plugin_info()
    plugin.get_plugin_info = lambda: {
        **declared_info,
        "name": "CanonicalHotReloadPlugin",
    }
    host = RuntimePluginHost(activation_context_resolver=lambda _info: context)
    host.register_plugin(plugin)
    report = host.execute_lifecycle_target(
        {"CanonicalHotReloadPlugin"}, source="test", allow_deactivate=True
    )
    assert report["status"] == "settled"

    registry = get_command_registry()
    assert registry.describe("plugin.hot_reload.choose")["owner"] == (
        "CanonicalHotReloadPlugin"
    )
    assert registry.describe("plugin.hot_reload.user_mod")["owner"] == (
        "CanonicalHotReloadPlugin"
    )

def test_choose_command_handles_no_candidates_without_opening_dialog() -> None:
    from builtin.editor_extensions.hot_reload_plugin import HotReloadPlugin

    host = _PluginHostCapability({"reloadable_plugin_ids": [], "catalog": []})
    plugin = HotReloadPlugin()
    plugin.on_load(_context(host))
    plugin._choose_reload_candidate = lambda _items: (_ for _ in ()).throw(
        AssertionError("dialog must not open without candidates")
    )

    result = plugin._choose_reload_command({}, {})

    assert result["ok"] is True
    assert result["result"] == {"status": "no_candidates", "candidates": []}
    assert host.reload_calls == []


def test_choose_command_handles_cancel_choice_and_failed_report() -> None:
    from builtin.editor_extensions.hot_reload_plugin import HotReloadPlugin

    snapshot = {"reloadable_plugin_ids": ["BetaPlugin", "AlphaPlugin"], "catalog": []}
    host = _PluginHostCapability(
        snapshot,
        reports={"AlphaPlugin": {"status": "failed", "code": "reload_failed"}},
    )
    plugin = HotReloadPlugin()
    plugin.on_load(_context(host))

    plugin._choose_reload_candidate = lambda candidates: None
    cancelled = plugin._choose_reload_command({}, {})
    assert cancelled["ok"] is True
    assert cancelled["result"]["status"] == "cancelled"
    assert cancelled["result"]["candidates"] == ["AlphaPlugin", "BetaPlugin"]
    assert host.reload_calls == []

    plugin._choose_reload_candidate = lambda candidates: "AlphaPlugin"
    failed = plugin._choose_reload_command({}, {})
    assert failed["ok"] is False
    assert failed["error"]["code"] == "plugin_reload_failed"
    assert failed["error"]["details"]["plugin_id"] == "AlphaPlugin"
    assert host.reload_calls == ["AlphaPlugin"]


def test_choose_command_reloads_selected_candidate_and_returns_report() -> None:
    from builtin.editor_extensions.hot_reload_plugin import HotReloadPlugin

    host = _PluginHostCapability(
        {"reloadable_plugin_ids": ["BetaPlugin", "AlphaPlugin"], "catalog": []}
    )
    plugin = HotReloadPlugin()
    plugin.on_load(_context(host))
    plugin._choose_reload_candidate = lambda candidates: candidates[0]

    result = plugin._choose_reload_command({}, {})

    assert result["ok"] is True
    assert result["result"]["status"] == "settled"
    assert result["result"]["plugin_id"] == "AlphaPlugin"
    assert result["result"]["report"]["status"] == "settled"
    assert host.reload_calls == ["AlphaPlugin"]


def test_user_mod_command_filters_copied_scope_in_deterministic_order() -> None:
    from builtin.editor_extensions.hot_reload_plugin import HotReloadPlugin

    host = _PluginHostCapability(
        {
            "reloadable_plugin_ids": ["ZuluPlugin", "AlphaPlugin", "OfficialPlugin", "AlphaPlugin"],
            "catalog": [
                {"plugin_id": "ZuluPlugin", "scope": "user_mod"},
                {"plugin_id": "OfficialPlugin", "scope": "official_mod"},
                {"plugin_id": "AlphaPlugin", "scope": "user_mod"},
            ],
        }
    )
    plugin = HotReloadPlugin()
    plugin.on_load(_context(host))

    result = plugin._reload_user_mod_command({}, {})

    assert result["ok"] is True
    assert result["result"] == {
        "status": "settled",
        "targets": ["AlphaPlugin", "ZuluPlugin"],
        "settled": ["AlphaPlugin", "ZuluPlugin"],
        "failed": [],
    }
    assert host.observe_calls == 1
    assert host.reload_calls == ["AlphaPlugin", "ZuluPlugin"]


def test_user_mod_command_reports_partial_failure_and_no_targets() -> None:
    from builtin.editor_extensions.hot_reload_plugin import HotReloadPlugin

    host = _PluginHostCapability(
        {
            "reloadable_plugin_ids": ["BetaPlugin", "AlphaPlugin"],
            "catalog": [
                {"plugin_id": "AlphaPlugin", "scope": "user_mod"},
                {"plugin_id": "BetaPlugin", "scope": "user_mod"},
            ],
        },
        reports={"BetaPlugin": {"status": "failed", "code": "boom"}},
    )
    plugin = HotReloadPlugin()
    plugin.on_load(_context(host))
    partial = plugin._reload_user_mod_command({}, {})

    assert partial["ok"] is False
    assert partial["error"]["code"] == "plugin_reload_batch_partial"
    assert partial["error"]["details"]["settled"] == ["AlphaPlugin"]
    assert partial["error"]["details"]["failed"] == ["BetaPlugin"]

    host.snapshot = {
        "reloadable_plugin_ids": ["OfficialPlugin"],
        "catalog": [{"plugin_id": "OfficialPlugin", "scope": "official_mod"}],
    }
    empty = plugin._reload_user_mod_command({}, {})
    assert empty["ok"] is True
    assert empty["result"] == {
        "status": "no_targets",
        "targets": [],
        "settled": [],
        "failed": [],
    }


def test_unload_reload_cleans_commands_and_old_actions_without_stale_owner() -> None:
    from builtin.editor_extensions.hot_reload_plugin import HotReloadPlugin
    from core.VitaLoom.commands.registry import get_command_registry, reset_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    reset_command_registry()
    events: list[object] = []
    capability = _PluginHostCapability({"reloadable_plugin_ids": [], "catalog": []})
    context = _context(capability)
    kernel = _kernel(events, context)
    context.kernel = kernel
    adapter = LegacyEditorPluginAdapter(kernel)
    runtime_host = RuntimePluginHost(
        activation_context_resolver=lambda _info: context,
        adapter=adapter,
    )

    first = HotReloadPlugin()
    runtime_host.register_plugin(first)
    first_report = runtime_host.execute_lifecycle_target(
        {"HotReloadPlugin"}, source="test", allow_deactivate=True
    )
    assert first_report["status"] == "settled"
    old_action = kernel.layout_manager.menu_batches[-1][1][0]["action"]
    assert runtime_host.unload_plugin("HotReloadPlugin") is True

    registry = get_command_registry()
    with pytest.raises(KeyError):
        registry.describe("plugin.hot_reload.choose")
    assert old_action()["error"]["code"] == "unknown_command"
    assert ("remove", "HotReloadPlugin") in events

    second = HotReloadPlugin()
    runtime_host.register_plugin(second)
    second_report = runtime_host.execute_lifecycle_target(
        {"HotReloadPlugin"}, source="test", allow_deactivate=True
    )
    assert second_report["status"] == "settled"
    assert registry.describe("plugin.hot_reload.choose")["owner"] == "HotReloadPlugin"
    assert registry.describe("plugin.hot_reload.user_mod")["owner"] == "HotReloadPlugin"

