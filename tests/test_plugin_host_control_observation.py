# -*- coding: utf-8 -*-
"""E26 proofs for the Qt-free nested plugin Host control/observation Interface."""
from __future__ import annotations

import builtins
import importlib
import json
import math
import sys
from pathlib import Path

import pytest


MODULE = "core.VitaLoom.core.plugin_host_capabilities"


class _Plugin:
    def __init__(self, plugin_id: str, *, version: str = "1.0.0") -> None:
        self.plugin_id = plugin_id
        self.version = version

    def get_plugin_info(self):
        return {
            "name": self.plugin_id,
            "version": self.version,
            "dependencies": [],
            "activation_context": "runtime",
            "provides": [],
        }

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


def test_capability_module_is_qt_and_legacy_host_free(monkeypatch):
    original_import = builtins.__import__

    def guarded(name, globals=None, locals=None, fromlist=(), level=0):
        if (
            name == "PyQt6"
            or name.startswith("PyQt6.")
            or name == "core.VitaLoom.kernel.editor_kernel"
            or name == "core.VitaLoom.kernel.layout_manager"
            or name == "core.VitaLoom.kernel.plugin_loader"
        ):
            raise AssertionError(f"unexpected legacy import: {name}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded)
    previous = sys.modules.pop(MODULE, None)
    try:
        module = importlib.import_module(MODULE)
        assert module.PLUGIN_HOST_CONTROL_OBSERVATION
    finally:
        sys.modules.pop(MODULE, None)
        if previous is not None:
            sys.modules[MODULE] = previous


def test_observation_is_deterministic_json_safe_and_copy_isolated():
    host = _host()
    runtime = host.runtime_plugin_host
    beta = _Plugin("BetaPlugin")
    alpha = _Plugin("AlphaPlugin")
    runtime.register_plugin(beta, scope=runtime.SCOPE_USER, source="beta.py")
    runtime.register_plugin(alpha, scope=runtime.SCOPE_CORE, source="alpha.py")
    runtime.loaded_plugins["AlphaPlugin"] = alpha
    runtime.protected_plugins.add("AlphaPlugin")
    runtime.failed_plugins["BetaPlugin"] = RuntimeError("broken")
    runtime.discovery_errors["z.py"] = ValueError("bad")
    host.last_lifecycle_report = {"status": "settled", "metric": math.nan}

    first = host.observe_plugins()
    second = host.observe_plugins()

    assert first == second
    json.dumps(first, allow_nan=False)
    assert [row["plugin_id"] for row in first["catalog"]] == [
        "AlphaPlugin",
        "BetaPlugin",
    ]
    rows = {row["plugin_id"]: row for row in first["catalog"]}
    assert rows["AlphaPlugin"]["active"] is True
    assert rows["AlphaPlugin"]["protected"] is True
    assert rows["AlphaPlugin"]["reloadable"] is False
    assert rows["BetaPlugin"]["scope"] == runtime.SCOPE_USER
    assert first["active_plugin_ids"] == ["AlphaPlugin"]
    assert first["failed_plugin_ids"] == ["BetaPlugin"]
    assert all(not isinstance(value, _Plugin) for value in first.values())

    first["catalog"][0]["plugin_id"] = "mutated"
    first["lifecycle"]["status"] = "mutated"
    third = host.observe_plugins()
    assert third == second


def test_reload_control_delegates_to_exact_manual_reload_host(monkeypatch):
    host = _host()
    expected = {"status": "settled", "plugin_id": "AlphaPlugin"}
    calls = []
    monkeypatch.setattr(
        host.manual_plugin_reload_host,
        "reload_plugin",
        lambda plugin_id: calls.append(plugin_id) or expected,
    )

    assert host.reload_plugin("AlphaPlugin") is expected
    assert calls == ["AlphaPlugin"]


def test_unload_control_delegates_and_preserves_protected_rule(monkeypatch):
    host = _host()
    runtime = host.runtime_plugin_host
    plugin = _Plugin("AlphaPlugin")
    runtime.register_plugin(plugin, scope=runtime.SCOPE_USER, source="alpha.py")
    runtime.loaded_plugins["AlphaPlugin"] = plugin
    calls = []
    monkeypatch.setattr(
        runtime,
        "unload_plugin",
        lambda plugin_id: calls.append(plugin_id) or True,
    )

    report = host.unload_plugin("AlphaPlugin")
    assert report["status"] == "settled"
    assert calls == ["AlphaPlugin"]

    runtime.protected_plugins.add("AlphaPlugin")
    blocked = host.unload_plugin("AlphaPlugin")
    assert blocked["status"] == "blocked"
    assert calls == ["AlphaPlugin"]


def test_resolver_reads_exact_capability_and_unavailable_fails_closed():
    from core.VitaLoom.core.plugin_host_capabilities import (
        PLUGIN_HOST_CONTROL_OBSERVATION,
        resolve_plugin_host,
    )
    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
    )

    registry = InMemoryRuntimeCapabilityRegistry()
    host = _host()
    registry.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    assert resolve_plugin_host(registry) is host

    unavailable = resolve_plugin_host(None)
    assert unavailable.observe_plugins()["status"] == "unavailable"
    assert unavailable.reload_plugin("AlphaPlugin")["status"] == "blocked"
    assert unavailable.unload_plugin("AlphaPlugin")["status"] == "blocked"

def test_observation_catalog_uses_complete_serialized_entry_contract():
    """Public observation must preserve every catalog-entry export fact."""

    class CompletePlugin:
        def get_plugin_info(self):
            return {
                "name": "DeclaredSerializationPlugin",
                "version": "9.4.1",
                "description": "complete serialized catalog entry",
                "dependencies": ["BasePlugin", "SharedPlugin"],
                "provides": ("command", {"channel": "diagnostic", "levels": {"info", "warning"}}),
                "activation_context": "runtime",
                "editor_contributions": [
                    {
                        "id": "serialization.separator",
                        "kind": "toolbar_separator",
                        "group": "serialization",
                        "order": 7,
                    }
                ],
            }

        def on_load(self, _context):
            pass

        def on_unload(self):
            pass

    host = _host()
    runtime = host.runtime_plugin_host
    plugin = CompletePlugin()
    plugin_id = runtime.register_plugin(
        plugin,
        scope=runtime.SCOPE_USER,
        source="serialization.py",
    )
    runtime.loaded_plugins[plugin_id] = plugin

    row = host.observe_plugins()["catalog"][0]
    entry = runtime.catalog_entries()[0]
    expected = entry.to_dict() | {"active": True, "reloadable": False}
    lifecycle_report = runtime.execute_lifecycle_target(
        {plugin_id},
        source="serialization-contract-audit",
        allow_deactivate=False,
    )

    assert row == expected
    assert lifecycle_report["catalog"] == [entry.to_dict()]
    json.dumps(lifecycle_report, allow_nan=False)
    assert set(row) == {
        "plugin_id",
        "scope",
        "source",
        "version",
        "description",
        "provides",
        "dependencies",
        "protected",
        "activation_context",
        "activation_context_explicit",
        "activation_context_source",
        "declared_name",
        "editor_contributions",
        "active",
        "reloadable",
    }
    assert row["activation_context_source"] == "declared"
    assert row["declared_name"] == "DeclaredSerializationPlugin"
    assert row["provides"] == [
        "command",
        {"channel": "diagnostic", "levels": ["info", "warning"]},
    ]
    assert row["dependencies"] == ["BasePlugin", "SharedPlugin"]
    assert row["editor_contributions"] == [
        {
            "owner_plugin_id": plugin_id,
            "id": "serialization.separator",
            "kind": "toolbar_separator",
            "group": "serialization",
            "order": 7,
        }
    ]
    json.dumps(row, allow_nan=False)

    row["editor_contributions"][0]["group"] = "consumer-mutation"
    assert host.observe_plugins()["catalog"][0]["editor_contributions"][0]["group"] == (
        "serialization"
    )

def test_observation_catalog_preserves_default_context_source():
    """The catalog keeps the default-context provenance exported by the entry."""

    class DefaultContextPlugin:
        def get_plugin_info(self):
            return {"name": "DefaultContextSerializationPlugin"}

        def on_load(self, _context):
            pass

        def on_unload(self):
            pass

    host = _host()
    runtime = host.runtime_plugin_host
    plugin_id = runtime.register_plugin(
        DefaultContextPlugin(),
        scope=runtime.SCOPE_USER,
        source="default-context-serialization.py",
    )

    row = host.observe_plugins()["catalog"][0]
    assert row["plugin_id"] == plugin_id
    assert row["activation_context"] == "legacy_ui"
    assert row["activation_context_explicit"] is False
    assert row["activation_context_source"] == "default"
    assert row == runtime.catalog_entries()[0].to_dict() | {
        "active": False,
        "reloadable": False,
    }

