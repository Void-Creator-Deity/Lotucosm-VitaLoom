# -*- coding: utf-8 -*-
"""E87 proofs that Runtime Ops contains public mutation-call outages."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from builtin.editor_extensions.plugin_runtime_ops import PluginRuntimeOpsMixin
from core.VitaLoom.core.runtime_capability_registry import (
    InMemoryRuntimeCapabilityRegistry,
)
from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION


class _MutationOutageHost:
    def __init__(self, outage: str) -> None:
        self.outage = outage
        self.reload_calls: list[str] = []
        self.unload_calls: list[str] = []
        self.sync_calls: list[tuple[dict, object | None]] = []

    def observe_plugins(self) -> dict:
        return {
            "catalog": [
                {
                    "plugin_id": "AlphaPlugin",
                    "scope": "user_mod",
                    "protected": False,
                }
            ]
        }

    def reload_plugin(self, plugin_id: str) -> dict:
        self.reload_calls.append(plugin_id)
        if self.outage == "reload":
            raise RuntimeError("public reload unavailable")
        return {"status": "settled", "plugin_id": plugin_id}

    def unload_plugin(self, plugin_id: str) -> dict:
        self.unload_calls.append(plugin_id)
        if self.outage == "unload":
            raise RuntimeError("public unload unavailable")
        return {"status": "settled", "plugin_id": plugin_id}

    def scan_project_addons(self, project_path: object) -> dict:
        return {"status": "settled", "project_path": str(project_path)}

    def sync_plugins_for_project(
        self, project_data: dict, *, repo_root: object | None = None
    ) -> dict:
        self.sync_calls.append((project_data, repo_root))
        if self.outage == "sync":
            raise RuntimeError("public project sync unavailable")
        return {"status": "settled"}


def _context(host: _MutationOutageHost):
    services = InMemoryRuntimeCapabilityRegistry()
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    return SimpleNamespace(
        services=services,
        kernel=object(),
        repo_root="C:/runtime-root",
        i18n_tr=lambda _key, default="": default,
    )


class _RuntimeOps(PluginRuntimeOpsMixin):
    def __init__(self, context, selected: str = "AlphaPlugin") -> None:
        self.context = context
        self.kernel = context.kernel
        self.selected = selected
        self.refresh_count = 0

    def _runtime_selected_plugin_id(self):
        return self.selected

    def _runtime_refresh(self) -> None:
        self.refresh_count += 1


def test_reload_call_outage_is_contained_without_claiming_refresh() -> None:
    host = _MutationOutageHost("reload")
    ops = _RuntimeOps(_context(host))

    ops.reload_selected_plugin()

    assert host.reload_calls == ["AlphaPlugin"]
    assert ops.refresh_count == 0


def test_unload_call_outage_is_contained_without_claiming_refresh() -> None:
    host = _MutationOutageHost("unload")
    ops = _RuntimeOps(_context(host))

    ops.unload_selected_plugin()

    assert host.unload_calls == ["AlphaPlugin"]
    assert ops.refresh_count == 0


@pytest.mark.parametrize("command_id", ["plugin.enable", "plugin.disable"])
def test_project_sync_call_outage_is_contained_after_persisted_command(
    monkeypatch: pytest.MonkeyPatch, command_id: str
) -> None:
    import builtin.editor_extensions.plugin_runtime_ops as runtime_ops_module

    host = _MutationOutageHost("sync")
    ops = _RuntimeOps(_context(host))
    config = {"project_id": "demo", "plugins": ["AlphaPlugin"]}
    read_model = SimpleNamespace(current_project_world_config=lambda: config)
    command_calls: list[tuple[str, str]] = []
    ops._run_project_plugin_command = (
        lambda actual_command_id, plugin_id: command_calls.append(
            (actual_command_id, plugin_id)
        )
        or True
    )
    monkeypatch.setattr(
        runtime_ops_module,
        "get_project_world_read_model",
        lambda _context: read_model,
    )

    if command_id == "plugin.enable":
        ops.enable_plugin_in_project()
    else:
        ops.disable_plugin_in_project()

    assert command_calls == [(command_id, "AlphaPlugin")]
    assert host.sync_calls == [(config, "C:/runtime-root")]
    assert ops.refresh_count == 1


def test_mutation_containment_does_not_hide_host_resolution_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtin.editor_extensions.plugin_runtime_ops as runtime_ops_module

    ops = _RuntimeOps(SimpleNamespace(kernel=object()), "AlphaPlugin")
    monkeypatch.setattr(
        runtime_ops_module,
        "resolve_plugin_host",
        lambda _context: (_ for _ in ()).throw(RuntimeError("host unavailable")),
    )

    with pytest.raises(RuntimeError, match="host unavailable"):
        ops.reload_selected_plugin()
