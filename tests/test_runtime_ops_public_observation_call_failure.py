# -*- coding: utf-8 -*-
"""E84 regressions for public observation call-outage containment."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin
from builtin.editor_extensions.plugin_manager_plugin import PluginManagerPlugin
from builtin.editor_extensions.plugin_runtime_ops import PluginRuntimeOpsMixin
from core.VitaLoom.core.runtime_capability_registry import InMemoryRuntimeCapabilityRegistry
from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION


class _RaisingObservationHost:
    def __init__(self) -> None:
        self.observation_calls = 0
        self.unload_calls: list[str] = []
        self.reload_calls: list[str] = []

    def observe_plugins(self) -> object:
        self.observation_calls += 1
        raise RuntimeError("public observation unavailable")

    def unload_plugin(self, plugin_id: str) -> dict:
        self.unload_calls.append(plugin_id)
        return {"status": "settled"}

    def reload_plugin(self, plugin_id: str) -> dict:
        self.reload_calls.append(plugin_id)
        return {"status": "settled"}

    def scan_project_addons(self, project_path: object) -> dict:
        return {"status": "ready", "project_path": str(project_path or "")}

    def sync_plugins_for_project(self, project_data: dict, *, repo_root: object | None = None) -> dict:
        return {"status": "settled"}


def _context_with_host(host: _RaisingObservationHost) -> SimpleNamespace:
    services = InMemoryRuntimeCapabilityRegistry()
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    return SimpleNamespace(services=services, i18n_tr=lambda _key, default="": default)


class _List:
    def __init__(self) -> None:
        self.items = []

    def clear(self) -> None:
        self.items.clear()

    def addItem(self, item) -> None:
        self.items.append(item)


class _RuntimeOpsProbe(PluginRuntimeOpsMixin):
    def __init__(self, host: _RaisingObservationHost) -> None:
        self.context = _context_with_host(host)
        self.kernel = object()
        self.refresh_calls = 0
        self.project_command = MagicMock(return_value=True)

    def _runtime_selected_plugin_id(self) -> str:
        return "AlphaPlugin"

    def _runtime_refresh(self) -> None:
        self.refresh_calls += 1

    def _run_project_plugin_command(self, command_id: str, plugin_name: str) -> bool:
        return self.project_command(command_id, plugin_name)


def test_runtime_ops_converts_public_observation_call_exception_to_unknown_facts() -> None:
    host = _RaisingObservationHost()
    probe = _RuntimeOpsProbe(host)

    assert probe._runtime_plugin_observation() == {}
    assert host.observation_calls == 1


def test_runtime_ops_catalog_dependent_actions_are_denied_when_public_call_raises() -> None:
    host = _RaisingObservationHost()
    probe = _RuntimeOpsProbe(host)

    probe.reload_selected_plugin()
    probe.unload_selected_plugin()
    probe.disable_plugin_in_project()

    assert host.observation_calls == 3
    assert host.reload_calls == []
    assert host.unload_calls == []
    probe.project_command.assert_not_called()
    assert probe.refresh_calls == 0


def test_package_manager_display_projects_public_call_outage_as_unknown() -> None:
    host = _RaisingObservationHost()
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
    plugin._packages = [{"id": "pkg.alpha", "display_name": "Alpha", "plugins": ["AlphaPlugin"]}]
    plugin._ensure_ui_refs = lambda: True
    plugin._get_project_disabled_plugins = lambda: []

    plugin._populate_plugin_list_tab()

    labels = [item.text() for item in plugin.package_list.items]
    assert labels and "AlphaPlugin" in labels[0]
    assert "MEMORY_UNKNOWN" in labels[0]
    assert "MEMORY_ACTIVE" not in labels[0]
    assert host.unload_calls == []
    assert host.reload_calls == []


def test_legacy_plugin_manager_display_empties_outage_snapshot_without_exception() -> None:
    host = _RaisingObservationHost()
    plugin = PluginManagerPlugin()
    plugin.context = _context_with_host(host)
    plugin.kernel = object()
    plugin.plugin_list = _List()

    plugin._refresh_plugin_list()

    assert plugin.plugin_list.items == []
    assert host.unload_calls == []
    assert host.reload_calls == []

