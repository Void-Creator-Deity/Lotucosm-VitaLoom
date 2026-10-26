# -*- coding: utf-8 -*-
"""E28 proofs for Package Manager consumption of the exact plugin Host capability."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin
from core.VitaLoom.core.runtime_capability_registry import (
    InMemoryRuntimeCapabilityRegistry,
)
from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION


PACKAGE_MANAGER_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
    / "builtin"
    / "editor_extensions"
    / "package_manager_plugin.py"
)


class _PluginHostCapability:
    def __init__(self, snapshot: dict) -> None:
        self.snapshot = snapshot
        self.unload_calls: list[str] = []

    def observe_plugins(self) -> dict:
        return self.snapshot

    def reload_plugin(self, plugin_id: str) -> dict:
        return {"status": "settled", "plugin_id": plugin_id}

    def unload_plugin(self, plugin_id: str) -> dict:
        self.unload_calls.append(plugin_id)
        return {"status": "settled", "plugin_id": plugin_id, "active": False}

    def scan_project_addons(self, project_path) -> dict:
        return {"status": "ready", "project_path": str(project_path or "")}

    def sync_plugins_for_project(self, project_data, *, repo_root=None) -> dict:
        return {"status": "settled"}


def _context_with_host(host: _PluginHostCapability):
    services = InMemoryRuntimeCapabilityRegistry()
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    return SimpleNamespace(
        services=services,
        i18n_tr=lambda _key, default="": default,
    )


class _List:
    def __init__(self) -> None:
        self.items = []

    def addItem(self, item) -> None:
        self.items.append(item)


class _MetadataPlugin:
    def __init__(self) -> None:
        self.calls = 0
        self.info = {
            "name": "MetadataPlugin",
            "version": "2.4.0",
            "description": "captured once",
            "dependencies": ["BasePlugin"],
            "provides": ["dock", {"not": "a UI object"}],
            "activation_context": "runtime",
        }

    def get_plugin_info(self):
        self.calls += 1
        return self.info

    def on_load(self, _context):
        pass

    def on_unload(self):
        pass


def _host():
    from core.VitaLoom.core.nested_plugin_host import NestedPluginHost

    return NestedPluginHost(
        activation_context_resolver=lambda _info: object(),
        repo_root_resolver=lambda: Path.cwd(),
        eager_mode_resolver=lambda: False,
        player_mode_resolver=lambda: False,
        bootstrap_plugin_ids_resolver=lambda _root: set(),
        active_plugin_ids_resolver=lambda _data, *, repo_root: set(),
        player_plugin_ids_resolver=lambda _data, *, repo_root: set(),
    )


def test_observation_uses_registration_time_copied_display_metadata() -> None:
    host = _host()
    plugin = _MetadataPlugin()
    runtime = host.runtime_plugin_host
    runtime.register_plugin(plugin, scope=runtime.SCOPE_USER, source="metadata.py")
    assert plugin.calls == 1

    plugin.info["description"] = "mutated after registration"
    plugin.info["provides"].append("late mutation")
    snapshot = host.observe_plugins()
    row = snapshot["catalog"][0]

    assert plugin.calls == 1
    assert row["description"] == "captured once"
    assert row["provides"] == ["dock", {"not": "a UI object"}]

    row["provides"].append("consumer mutation")
    assert host.observe_plugins()["catalog"][0]["provides"] == [
        "dock",
        {"not": "a UI object"},
    ]


def test_package_manager_list_uses_observed_active_ids_without_loader() -> None:
    host = _PluginHostCapability(
        {
            "status": "ready",
            "active_plugin_ids": ["AlphaPlugin"],
            "catalog": [
                {"plugin_id": "AlphaPlugin", "active": True, "protected": False},
                {"plugin_id": "BetaPlugin", "active": False, "protected": False},
            ],
        }
    )
    plugin = PackageManagerPlugin()
    plugin.context = _context_with_host(host)
    plugin.kernel = object()  # deliberately has no plugin_loader
    plugin.package_list = _List()
    plugin.search_input = None
    plugin.status_filter = SimpleNamespace(currentIndex=lambda: 1)
    plugin._packages = [
        {"id": "pkg.alpha", "display_name": "Alpha", "plugins": ["AlphaPlugin"]},
        {"id": "pkg.beta", "display_name": "Beta", "plugins": ["BetaPlugin"]},
    ]
    plugin._ensure_ui_refs = lambda: True
    plugin._get_project_disabled_plugins = lambda: []

    plugin._populate_plugin_list_tab()

    labels = [item.text() for item in plugin.package_list.items]
    assert len(labels) == 1
    assert "AlphaPlugin" in labels[0]


def test_package_manager_detail_uses_copied_catalog_metadata_without_loader() -> None:
    host = _PluginHostCapability(
        {
            "status": "ready",
            "active_plugin_ids": ["AlphaPlugin"],
            "catalog": [
                {
                    "plugin_id": "AlphaPlugin",
                    "active": True,
                    "protected": False,
                    "version": "3.1.4",
                    "description": "copied detail",
                    "provides": ["dock", "menu"],
                }
            ],
        }
    )
    plugin = PackageManagerPlugin()
    plugin.context = _context_with_host(host)
    plugin.kernel = object()  # deliberately has no plugin_loader/live plugin
    plugin.detail_text = MagicMock()
    plugin.operation_service = None
    plugin._packages = [
        {"id": "pkg.alpha", "display_name": "Alpha", "plugins": ["AlphaPlugin"]}
    ]

    plugin._render_plugin_detail("AlphaPlugin")

    rendered = plugin.detail_text.setPlainText.call_args.args[0]
    assert "3.1.4" in rendered
    assert "copied detail" in rendered
    assert "dock, menu" in rendered


def test_package_disable_uses_observed_protection_and_exact_host_unload() -> None:
    host = _PluginHostCapability(
        {
            "status": "ready",
            "active_plugin_ids": ["ProtectedPlugin", "MutablePlugin"],
            "catalog": [
                {"plugin_id": "ProtectedPlugin", "active": True, "protected": True},
                {"plugin_id": "MutablePlugin", "active": True, "protected": False},
            ],
        }
    )
    plugin = PackageManagerPlugin()
    plugin.context = _context_with_host(host)
    plugin.kernel = object()  # deliberately has no plugin_loader
    plugin._get_selected_plugin_id = lambda: None
    plugin._get_selected_package = lambda: {
        "id": "pkg.demo",
        "plugins": ["ProtectedPlugin", "MutablePlugin"],
    }
    plugin._run_project_plugin_command = MagicMock(return_value={"ok": True})
    plugin._handle_project_plugin_command_result = lambda result: bool(result.get("ok"))
    plugin._refresh = MagicMock()
    plugin._on_selection_changed = MagicMock()

    plugin._disable_selected()

    assert plugin._run_project_plugin_command.call_args_list == [
        call("plugin.disable", "MutablePlugin")
    ]
    assert host.unload_calls == ["MutablePlugin"]


def test_selected_plugin_disable_uses_observed_protection_and_exact_host_unload() -> None:
    host = _PluginHostCapability(
        {
            "status": "ready",
            "active_plugin_ids": ["ProtectedPlugin", "MutablePlugin"],
            "catalog": [
                {"plugin_id": "ProtectedPlugin", "active": True, "protected": True},
                {"plugin_id": "MutablePlugin", "active": True, "protected": False},
            ],
        }
    )
    plugin = PackageManagerPlugin()
    plugin.context = _context_with_host(host)
    plugin.kernel = object()
    selected = iter(["ProtectedPlugin", "MutablePlugin"])
    plugin._get_selected_plugin_id = lambda: next(selected)
    plugin._run_project_plugin_command = MagicMock(return_value={"ok": True})
    plugin._handle_project_plugin_command_result = lambda result: bool(result.get("ok"))
    plugin._append_result = MagicMock()
    plugin._refresh = MagicMock()
    plugin._on_selection_changed = MagicMock()

    plugin._disable_selected()
    plugin._disable_selected()

    assert plugin._run_project_plugin_command.call_args_list == [
        call("plugin.disable", "MutablePlugin")
    ]
    assert host.unload_calls == ["MutablePlugin"]


def test_package_manager_source_has_no_loader_or_live_plugin_object_consumption() -> None:
    source = PACKAGE_MANAGER_SOURCE.read_text(encoding="utf-8-sig")

    assert '"plugin_loader"' not in source
    assert ".loaded_plugins" not in source
    assert "loader[plugin_id].get_plugin_info()" not in source


@pytest.mark.parametrize(
    "snapshot",
    [
        None,
        {"status": "unavailable", "catalog": []},
        {"status": "partial", "catalog": "not-a-catalog"},
        {
            "status": "partial",
            "catalog": [
                None,
                "malformed catalog row",
                {"plugin_id": "OtherPlugin", "protected": False},
            ],
        },
    ],
    ids=[
        "non_mapping_snapshot",
        "unavailable_empty_catalog",
        "invalid_catalog",
        "malformed_or_absent_catalog_row",
    ],
)
def test_selected_plugin_disable_fails_closed_without_trustworthy_public_catalog_row(
    snapshot: object,
) -> None:
    """E79: selected-plugin disable must require a public catalog authorization."""

    host = _PluginHostCapability(snapshot)
    plugin = PackageManagerPlugin()
    plugin.context = _context_with_host(host)
    plugin.kernel = object()
    plugin._get_selected_plugin_id = lambda: "AlphaPlugin"
    plugin._run_project_plugin_command = MagicMock(return_value={"ok": True})
    plugin._handle_project_plugin_command_result = lambda result: bool(result.get("ok"))
    plugin._append_result = MagicMock()
    plugin._refresh = MagicMock()
    plugin._on_selection_changed = MagicMock()

    plugin._disable_selected()

    plugin._run_project_plugin_command.assert_not_called()
    assert host.unload_calls == []
    plugin._append_result.assert_not_called()
    plugin._refresh.assert_not_called()
    plugin._on_selection_changed.assert_not_called()


@pytest.mark.parametrize(
    "snapshot",
    [
        None,
        {"status": "unavailable", "catalog": []},
        {"status": "partial", "catalog": "not-a-catalog"},
        {
            "status": "partial",
            "catalog": [
                None,
                "malformed catalog row",
                {"plugin_id": "OtherPlugin", "protected": False},
            ],
        },
    ],
    ids=[
        "non_mapping_snapshot",
        "unavailable_empty_catalog",
        "invalid_catalog",
        "malformed_or_absent_catalog_row",
    ],
)
def test_package_disable_fails_closed_without_trustworthy_public_catalog_rows(
    snapshot: object,
) -> None:
    """E79: package disable must authorize every target through public rows."""

    host = _PluginHostCapability(snapshot)
    plugin = PackageManagerPlugin()
    plugin.context = _context_with_host(host)
    plugin.kernel = object()
    plugin._get_selected_plugin_id = lambda: None
    plugin._get_selected_package = lambda: {
        "id": "pkg.alpha",
        "plugins": ["AlphaPlugin"],
    }
    plugin._run_project_plugin_command = MagicMock(return_value={"ok": True})
    plugin._handle_project_plugin_command_result = lambda result: bool(result.get("ok"))
    plugin._append_result = MagicMock()
    plugin._refresh = MagicMock()
    plugin._on_selection_changed = MagicMock()

    plugin._disable_selected()

    plugin._run_project_plugin_command.assert_not_called()
    assert host.unload_calls == []
    plugin._append_result.assert_not_called()
    plugin._refresh.assert_not_called()
    plugin._on_selection_changed.assert_not_called()

@pytest.mark.parametrize(
    "snapshot",
    [
        None,
        {"status": "unavailable", "active_plugin_ids": None, "catalog": []},
        {"status": "partial", "active_plugin_ids": "AlphaPlugin", "catalog": []},
    ],
    ids=["non_mapping_snapshot", "none_active_ids", "string_active_ids"],
)
def test_plugin_list_display_treats_untrustworthy_active_ids_as_unknown(
    snapshot: object,
) -> None:
    """E80: display-only list reads must render unknown active facts safely."""

    host = _PluginHostCapability(snapshot)
    plugin = PackageManagerPlugin()
    plugin.context = _context_with_host(host)
    plugin.context.i18n_tr = lambda key, default="": {
        "package_manager.plugin.loaded": "MEMORY_ACTIVE",
        "package_manager.plugin.not_loaded": "MEMORY_INACTIVE",
        "package_manager.plugin.unknown": "MEMORY_UNKNOWN",
    }.get(key, default)
    plugin.kernel = object()
    plugin.package_list = _List()
    plugin.search_input = None
    plugin.status_filter = SimpleNamespace(currentIndex=lambda: 0)
    plugin._packages = [
        {"id": "pkg.alpha", "display_name": "Alpha", "plugins": ["AlphaPlugin"]}
    ]
    plugin._ensure_ui_refs = lambda: True
    plugin._get_project_disabled_plugins = lambda: []
    plugin._run_project_plugin_command = MagicMock()

    plugin._populate_plugin_list_tab()

    labels = [item.text() for item in plugin.package_list.items]
    assert labels and "AlphaPlugin" in labels[0]
    assert "MEMORY_UNKNOWN" in labels[0]
    assert "MEMORY_ACTIVE" not in labels[0]
    assert host.unload_calls == []
    plugin._run_project_plugin_command.assert_not_called()


@pytest.mark.parametrize(
    "snapshot",
    [
        None,
        {"status": "partial", "active_plugin_ids": None, "catalog": "not-a-catalog"},
        {
            "status": "partial",
            "active_plugin_ids": "AlphaPlugin",
            "catalog": [None, "malformed catalog row", {"plugin_id": "OtherPlugin"}],
        },
    ],
    ids=["non_mapping_snapshot", "invalid_catalog_and_active_ids", "malformed_or_absent_row"],
)
def test_plugin_detail_display_treats_untrustworthy_public_facts_as_unknown(
    snapshot: object,
) -> None:
    """E80: detail display must not crash or assert loaded/catalog metadata."""

    host = _PluginHostCapability(snapshot)
    plugin = PackageManagerPlugin()
    plugin.context = _context_with_host(host)
    plugin.context.i18n_tr = lambda key, default="": {
        "package_manager.plugin.loaded": "MEMORY_ACTIVE",
        "package_manager.plugin.not_loaded": "MEMORY_INACTIVE",
        "package_manager.plugin.unknown": "MEMORY_UNKNOWN",
    }.get(key, default)
    plugin.kernel = object()
    plugin.detail_text = MagicMock()
    plugin.operation_service = None
    plugin._packages = [
        {"id": "pkg.alpha", "display_name": "Alpha", "plugins": ["AlphaPlugin"]}
    ]
    plugin._get_project_disabled_plugins = lambda: []
    plugin._run_project_plugin_command = MagicMock()

    plugin._render_plugin_detail("AlphaPlugin")

    rendered = plugin.detail_text.setPlainText.call_args.args[0]
    assert "AlphaPlugin" in rendered
    assert "MEMORY_UNKNOWN" in rendered
    assert "MEMORY_ACTIVE" not in rendered
    assert "malformed catalog row" not in rendered
    assert host.unload_calls == []
    plugin._run_project_plugin_command.assert_not_called()

