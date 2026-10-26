# -*- coding: utf-8 -*-
"""E85 regressions for Hot Reload public observation call-outage containment."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from builtin.editor_extensions.hot_reload_plugin import HotReloadPlugin
from core.VitaLoom.core.runtime_capability_registry import InMemoryRuntimeCapabilityRegistry
from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION


class _RaisingObservationHost:
    """Complete public Host capability whose observation operation is unavailable."""

    def __init__(self) -> None:
        self.observation_calls = 0
        self.reload_calls: list[str] = []

    def observe_plugins(self) -> object:
        self.observation_calls += 1
        raise RuntimeError("public observation unavailable")

    def reload_plugin(self, plugin_id: str) -> dict[str, Any]:
        self.reload_calls.append(plugin_id)
        return {"status": "settled", "plugin_id": plugin_id}

    def unload_plugin(self, plugin_id: str) -> dict[str, Any]:
        return {"status": "settled", "plugin_id": plugin_id}

    def scan_project_addons(self, project_path: object) -> dict[str, Any]:
        return {"status": "ready", "project_path": str(project_path or "")}

    def sync_plugins_for_project(
        self, project_data: dict[str, Any], *, repo_root: object | None = None
    ) -> dict[str, Any]:
        return {"status": "settled"}


def _context_with_host(host: _RaisingObservationHost) -> SimpleNamespace:
    services = InMemoryRuntimeCapabilityRegistry()
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    return SimpleNamespace(
        services=services,
        kernel=object(),
        i18n_tr=lambda _key, default="": default,
    )


def _loaded_plugin(host: _RaisingObservationHost) -> HotReloadPlugin:
    plugin = HotReloadPlugin()
    plugin.on_load(_context_with_host(host))
    return plugin


def test_hot_reload_converts_public_observation_call_exception_to_empty_facts() -> None:
    host = _RaisingObservationHost()
    plugin = _loaded_plugin(host)

    assert plugin._observe_plugins() == {
        "reloadable_plugin_ids": [],
        "catalog": [],
    }
    assert host.observation_calls == 1


def test_choose_reload_is_denied_without_dialog_or_reload_when_public_call_raises() -> None:
    host = _RaisingObservationHost()
    plugin = _loaded_plugin(host)
    plugin._choose_reload_candidate = MagicMock()

    result = plugin.reload_selected_plugin()

    assert result["ok"] is True
    assert result["result"] == {"status": "no_candidates", "candidates": []}
    plugin._choose_reload_candidate.assert_not_called()
    assert host.reload_calls == []


def test_user_mod_batch_is_denied_without_reload_when_public_call_raises() -> None:
    host = _RaisingObservationHost()
    plugin = _loaded_plugin(host)

    result = plugin.reload_user_mod_plugins()

    assert result["ok"] is True
    assert result["result"] == {
        "status": "no_targets",
        "targets": [],
        "settled": [],
        "failed": [],
    }
    assert host.reload_calls == []
