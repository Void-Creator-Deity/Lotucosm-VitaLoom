# -*- coding: utf-8 -*-
"""E86 regressions for Hot Reload public reload-operation call containment."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from builtin.editor_extensions.hot_reload_plugin import HotReloadPlugin
from core.VitaLoom.core.runtime_capability_registry import InMemoryRuntimeCapabilityRegistry
from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION


class _RaisingReloadHost:
    """Complete public Host capability with valid facts but unavailable reload operation."""

    def __init__(self) -> None:
        self.observation_calls = 0
        self.reload_calls: list[str] = []

    def observe_plugins(self) -> dict[str, Any]:
        self.observation_calls += 1
        return {
            "reloadable_plugin_ids": ["AlphaPlugin", "BetaPlugin"],
            "catalog": [
                {"plugin_id": "AlphaPlugin", "scope": "user_mod"},
                {"plugin_id": "BetaPlugin", "scope": "user_mod"},
            ],
        }

    def reload_plugin(self, plugin_id: str) -> object:
        self.reload_calls.append(plugin_id)
        raise RuntimeError("public reload unavailable")

    def unload_plugin(self, plugin_id: str) -> dict[str, Any]:
        return {"status": "settled", "plugin_id": plugin_id}

    def scan_project_addons(self, project_path: object) -> dict[str, Any]:
        return {"status": "ready", "project_path": str(project_path or "")}

    def sync_plugins_for_project(
        self, project_data: dict[str, Any], *, repo_root: object | None = None
    ) -> dict[str, Any]:
        return {"status": "settled"}


def _loaded_plugin(host: _RaisingReloadHost) -> HotReloadPlugin:
    services = InMemoryRuntimeCapabilityRegistry()
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    plugin = HotReloadPlugin()
    plugin.on_load(
        SimpleNamespace(
            services=services,
            kernel=object(),
            i18n_tr=lambda _key, default="": default,
        )
    )
    return plugin


def test_reload_report_converts_public_reload_call_exception_to_failed_report() -> None:
    host = _RaisingReloadHost()
    plugin = _loaded_plugin(host)

    assert plugin._reload_plugin_report("AlphaPlugin") == {
        "status": "failed",
        "code": "plugin_reload_unavailable",
        "plugin_id": "AlphaPlugin",
    }
    assert host.reload_calls == ["AlphaPlugin"]


def test_choose_reload_returns_existing_failure_result_when_public_reload_call_raises() -> None:
    host = _RaisingReloadHost()
    plugin = _loaded_plugin(host)
    plugin._choose_reload_candidate = lambda candidates: candidates[0]

    result = plugin.reload_selected_plugin()

    assert result["ok"] is False
    assert result["error"]["code"] == "plugin_reload_failed"
    assert result["error"]["details"] == {
        "plugin_id": "AlphaPlugin",
        "report": {
            "status": "failed",
            "code": "plugin_reload_unavailable",
            "plugin_id": "AlphaPlugin",
        },
    }
    assert host.reload_calls == ["AlphaPlugin"]


def test_user_mod_batch_returns_existing_partial_failure_when_public_reload_calls_raise() -> None:
    host = _RaisingReloadHost()
    plugin = _loaded_plugin(host)

    result = plugin.reload_user_mod_plugins()

    assert result["ok"] is False
    assert result["error"]["code"] == "plugin_reload_batch_partial"
    assert result["error"]["details"]["targets"] == ["AlphaPlugin", "BetaPlugin"]
    assert result["error"]["details"]["settled"] == []
    assert result["error"]["details"]["failed"] == ["AlphaPlugin", "BetaPlugin"]
    assert result["error"]["details"]["reports"] == {
        "AlphaPlugin": {
            "status": "failed",
            "code": "plugin_reload_unavailable",
            "plugin_id": "AlphaPlugin",
        },
        "BetaPlugin": {
            "status": "failed",
            "code": "plugin_reload_unavailable",
            "plugin_id": "BetaPlugin",
        },
    }
    assert host.reload_calls == ["AlphaPlugin", "BetaPlugin"]
