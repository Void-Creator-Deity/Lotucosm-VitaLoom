# -*- coding: utf-8 -*-
"""E26 behavior proofs for legacy UI Adapters consuming the plugin Host seam."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from builtin.editor_extensions.hot_reload_plugin import HotReloadPlugin
from builtin.editor_extensions.plugin_runtime_ops import PluginRuntimeOpsMixin
from core.VitaLoom.core.runtime_capability_registry import (
    InMemoryRuntimeCapabilityRegistry,
)
from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION


class _PluginHostCapability:
    def __init__(self, snapshot: dict) -> None:
        self.snapshot = snapshot
        self.reload_calls: list[str] = []
        self.unload_calls: list[str] = []
        self.sync_calls: list[tuple[dict, object | None]] = []

    def observe_plugins(self) -> dict:
        return self.snapshot

    def reload_plugin(self, plugin_id: str) -> dict:
        self.reload_calls.append(plugin_id)
        return {"status": "settled", "plugin_id": plugin_id}

    def unload_plugin(self, plugin_id: str) -> dict:
        self.unload_calls.append(plugin_id)
        return {"status": "settled", "plugin_id": plugin_id}

    def scan_project_addons(self, project_path: object) -> dict:
        return {"status": "settled", "project_path": str(project_path)}

    def sync_plugins_for_project(
        self, project_data: dict, *, repo_root: object | None = None
    ) -> dict:
        self.sync_calls.append((project_data, repo_root))
        return {"status": "settled"}


def _context(host: _PluginHostCapability):
    services = InMemoryRuntimeCapabilityRegistry()
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    return SimpleNamespace(
        services=services,
        kernel=object(),
        repo_root="C:/runtime-root",
        i18n_tr=lambda _key, default="": default,
    )


class _RuntimeOps(PluginRuntimeOpsMixin):
    def __init__(self, context, selected: str) -> None:
        self.context = context
        self.kernel = context.kernel
        self.selected = selected
        self.refresh_count = 0

    def _runtime_selected_plugin_id(self):
        return self.selected

    def _runtime_refresh(self) -> None:
        self.refresh_count += 1


def test_runtime_ops_reload_and_unload_delegate_to_exact_capability() -> None:
    host = _PluginHostCapability(
        {
            "catalog": [
                {"plugin_id": "AlphaPlugin", "scope": "user_mod", "protected": False}
            ]
        }
    )
    ops = _RuntimeOps(_context(host), "AlphaPlugin")

    ops.reload_selected_plugin()
    ops.unload_selected_plugin()

    assert host.reload_calls == ["AlphaPlugin"]
    assert host.unload_calls == ["AlphaPlugin"]
    assert ops.refresh_count == 2


def test_runtime_ops_protected_and_core_rules_fail_closed() -> None:
    host = _PluginHostCapability(
        {
            "catalog": [
                {"plugin_id": "Protected", "scope": "user_mod", "protected": True},
                {"plugin_id": "CorePlugin", "scope": "core_mod", "protected": False},
            ]
        }
    )
    ops = _RuntimeOps(_context(host), "Protected")
    command_calls: list[tuple[str, str]] = []
    ops._run_project_plugin_command = (
        lambda command_id, plugin_id: command_calls.append((command_id, plugin_id)) or True
    )

    ops.reload_selected_plugin()
    ops.unload_selected_plugin()
    ops.disable_plugin_in_project()
    ops.selected = "CorePlugin"
    ops.disable_plugin_in_project()

    assert host.reload_calls == []
    assert host.unload_calls == []
    assert command_calls == []
    assert ops.refresh_count == 0


def test_runtime_ops_sync_delegates_project_config_to_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtin.editor_extensions.plugin_runtime_ops as runtime_ops_module

    host = _PluginHostCapability({"catalog": []})
    context = _context(host)
    ops = _RuntimeOps(context, "AlphaPlugin")
    config = {"project_id": "demo", "plugins": ["AlphaPlugin"]}
    read_model = SimpleNamespace(current_project_world_config=lambda: config)
    monkeypatch.setattr(
        runtime_ops_module,
        "get_project_world_read_model",
        lambda _context: read_model,
    )

    ops._sync_plugins_for_current_project()

    assert host.sync_calls == [(config, "C:/runtime-root")]


def test_hot_reload_adapter_filters_user_mods_from_observation() -> None:
    host = _PluginHostCapability(
        {
            "reloadable_plugin_ids": ["AlphaPlugin", "BetaPlugin"],
            "catalog": [
                {"plugin_id": "AlphaPlugin", "scope": "user_mod"},
                {"plugin_id": "BetaPlugin", "scope": "official_mod"},
            ],
        }
    )
    plugin = HotReloadPlugin()
    plugin.on_load(_context(host))
    try:
        assert plugin._reloadable_plugins() == ["AlphaPlugin", "BetaPlugin"]
        plugin.reload_user_mod_plugins()
        assert host.reload_calls == ["AlphaPlugin"]
    finally:
        plugin.on_unload()

@pytest.mark.parametrize(
    ("snapshot", "command", "expected_status"),
    [
        (None, "choose", "no_candidates"),
        (
            {"reloadable_plugin_ids": None, "catalog": []},
            "choose",
            "no_candidates",
        ),
        (
            {"reloadable_plugin_ids": "AlphaPlugin", "catalog": []},
            "choose",
            "no_candidates",
        ),
        (
            {"reloadable_plugin_ids": ["AlphaPlugin"], "catalog": None},
            "user_mod",
            "no_targets",
        ),
        (
            {
                "reloadable_plugin_ids": ["AlphaPlugin"],
                "catalog": "not-a-catalog-sequence",
            },
            "user_mod",
            "no_targets",
        ),
    ],
    ids=[
        "non_mapping_snapshot",
        "none_reloadable_ids",
        "string_reloadable_ids",
        "none_catalog",
        "string_catalog",
    ],
)
def test_hot_reload_malformed_public_observation_fails_closed_without_action(
    snapshot: object,
    command: str,
    expected_status: str,
) -> None:
    """E82: copied observation facts may shape candidates but never authorize reload."""

    host = _PluginHostCapability(snapshot)
    plugin = HotReloadPlugin()
    plugin.on_load(_context(host))
    dialog_calls: list[list[str]] = []
    plugin._choose_reload_candidate = (
        lambda candidates: dialog_calls.append(list(candidates)) or "AlphaPlugin"
    )
    try:
        if command == "choose":
            result = plugin._choose_reload_command({}, {})
        else:
            result = plugin._reload_user_mod_command({}, {})
    finally:
        plugin.on_unload()

    assert result["ok"] is True
    assert result["result"]["status"] == expected_status
    assert dialog_calls == []
    assert host.reload_calls == []


def test_legacy_consumers_accept_complete_public_catalog_rows() -> None:
    """E77: legacy consumers rely only on the public catalog fields they need."""

    complete_row = {
        "plugin_id": "AlphaPlugin",
        "scope": "user_mod",
        "source": "mods/alpha.py",
        "version": "9.4.1",
        "description": "complete public catalog row",
        "provides": ["command", {"channel": "diagnostic", "levels": ["info"]}],
        "dependencies": ["BasePlugin"],
        "protected": False,
        "activation_context": "runtime",
        "activation_context_explicit": True,
        "activation_context_source": "declared",
        "declared_name": "Alpha display name",
        "editor_contributions": [
            {
                "id": "alpha.separator",
                "kind": "toolbar_separator",
                "owner_plugin_id": "AlphaPlugin",
                "group": "tools",
                "order": 4,
            }
        ],
        "active": True,
        "reloadable": True,
    }
    host = _PluginHostCapability(
        {
            "status": "settled",
            "catalog": [complete_row],
            "plugin_ids": ["AlphaPlugin"],
            "active_plugin_ids": ["AlphaPlugin"],
            "reloadable_plugin_ids": ["AlphaPlugin"],
            "failed_plugin_ids": [],
            "failed_plugins": {},
            "discovery_errors": {},
            "lifecycle": {},
            "reload": {},
            "counts": {
                "catalog": 1,
                "active": 1,
                "reloadable": 1,
                "failed": 0,
                "discovery_errors": 0,
            },
        }
    )
    context = _context(host)
    ops = _RuntimeOps(context, "AlphaPlugin")
    hot_reload = HotReloadPlugin()
    hot_reload.on_load(context)
    try:
        # The fake capability intentionally exposes no RuntimePluginHost internals.
        # Both consumers must operate only on documented public observation facts.
        assert ops._runtime_plugin_row("AlphaPlugin") == complete_row
        ops.reload_selected_plugin()
        hot_reload.reload_user_mod_plugins()
    finally:
        hot_reload.on_unload()

    assert host.reload_calls == ["AlphaPlugin", "AlphaPlugin"]
    assert ops.refresh_count == 1

@pytest.mark.parametrize(
    "snapshot",
    [
        None,
        {"status": "unavailable", "catalog": []},
        {
            "status": "partial",
            "catalog": [
                None,
                "malformed catalog row",
                {"plugin_id": "OtherPlugin", "scope": "user_mod", "protected": False},
            ],
        },
    ],
    ids=["non_mapping_snapshot", "unavailable_empty_catalog", "malformed_catalog_rows"],
)
def test_runtime_ops_fail_closed_when_public_observation_cannot_authorize_plugin(
    snapshot: object,
) -> None:
    """E78: destructive runtime operations require a trustworthy catalog row."""

    host = _PluginHostCapability(snapshot)
    ops = _RuntimeOps(_context(host), "AlphaPlugin")
    command_calls: list[tuple[str, str]] = []
    ops._run_project_plugin_command = (
        lambda command_id, plugin_id: command_calls.append((command_id, plugin_id)) or True
    )

    assert ops._runtime_plugin_row("AlphaPlugin") == {}

    ops.reload_selected_plugin()
    ops.unload_selected_plugin()
    ops.disable_plugin_in_project()

    assert host.reload_calls == []
    assert host.unload_calls == []
    assert command_calls == []
    assert host.sync_calls == []
    assert ops.refresh_count == 0
