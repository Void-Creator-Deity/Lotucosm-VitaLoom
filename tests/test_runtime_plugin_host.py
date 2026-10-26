# -*- coding: utf-8 -*-
"""E20 proofs for the Qt-free nested runtime plugin Host."""
from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


MODULE_NAME = "core.VitaLoom.core.runtime_plugin_host"


def test_runtime_plugin_host_module_is_qt_and_legacy_editor_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError(f"unexpected Qt import: {name}")
        if name == "core.VitaLoom.kernel.plugin_interfaces":
            raise AssertionError(f"unexpected legacy editor Interface import: {name}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    previous = sys.modules.pop(MODULE_NAME, None)
    try:
        module = importlib.import_module(MODULE_NAME)
        assert module.RuntimePluginHost.__name__ == "RuntimePluginHost"
    finally:
        sys.modules.pop(MODULE_NAME, None)
        if previous is not None:
            sys.modules[MODULE_NAME] = previous


def _plugin_class(plugin_id: str, events: list[str], dependencies=(), *, fail=False):
    from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin

    class Plugin(IRuntimePlugin):
        def get_plugin_info(self):
            return {
                "name": plugin_id,
                "version": "1.0.0",
                "dependencies": list(dependencies),
                "provides": [],
                "activation_context": "runtime",
            }

        def on_load(self, runtime_context):
            events.append(f"load:{plugin_id}")
            self.context = runtime_context
            if fail:
                raise RuntimeError(f"{plugin_id} failed")

        def on_unload(self):
            events.append(f"unload:{plugin_id}")

    return Plugin


def test_headless_host_executes_dependency_order_and_reverse_deactivation() -> None:
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    events: list[str] = []
    context = object()
    host = RuntimePluginHost(activation_context_resolver=lambda info: context)
    host.register_plugin(_plugin_class("BetaPlugin", events, ("AlphaPlugin",))())
    host.register_plugin(_plugin_class("AlphaPlugin", events)())

    activated = host.execute_lifecycle_target(
        {"BetaPlugin"}, source="test", allow_deactivate=True
    )
    assert activated["status"] == "settled"
    assert activated["completed"]["activated"] == ["AlphaPlugin", "BetaPlugin"]
    assert events == ["load:AlphaPlugin", "load:BetaPlugin"]
    assert host.loaded_plugins["AlphaPlugin"].context is context

    deactivated = host.execute_lifecycle_target(
        set(), source="test", allow_deactivate=True
    )
    assert deactivated["status"] == "settled"
    assert deactivated["completed"]["deactivated"] == ["BetaPlugin", "AlphaPlugin"]
    assert events == ["load:AlphaPlugin", "load:BetaPlugin", "unload:BetaPlugin", "unload:AlphaPlugin"]
    assert host.loaded_plugins == {}


def test_headless_host_reports_failure_and_skips_only_blocked_dependents() -> None:
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    events: list[str] = []
    host = RuntimePluginHost(activation_context_resolver=lambda info: object())
    host.register_plugin(_plugin_class("AlphaPlugin", events, fail=True)())
    host.register_plugin(_plugin_class("BetaPlugin", events, ("AlphaPlugin",))())
    host.register_plugin(_plugin_class("GammaPlugin", events)())

    report = host.execute_lifecycle_target(
        {"AlphaPlugin", "BetaPlugin", "GammaPlugin"}, source="test", allow_deactivate=True
    )

    assert report["status"] == "failed"
    assert report["failed_action"]["plugin_id"] == "AlphaPlugin"
    assert report["failed_action"]["action"] == "activate"
    assert report["skipped"]["activation"] == [
        {"plugin_id": "BetaPlugin", "blocked_by": ["AlphaPlugin"]}
    ]
    assert report["completed"]["activated"] == ["GammaPlugin"]
    assert events == ["load:AlphaPlugin", "load:GammaPlugin"]
    assert set(host.loaded_plugins) == {"GammaPlugin"}


def test_host_discovers_plain_runtime_plugin_with_stable_catalog_facts(
    tmp_path: Path,
) -> None:
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    plugin_file = tmp_path / "sample_plugin.py"
    plugin_file.write_text(
        """
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin

class SamplePlugin(IRuntimePlugin):
    def get_plugin_info(self):
        return {
            'name': 'SamplePlugin',
            'version': '2.3.4',
            'dependencies': [],
            'protected': True,
            'activation_context': 'runtime',
        }

    def on_load(self, runtime_context):
        self.context = runtime_context

    def on_unload(self):
        pass
""".strip()
        + "\n",
        encoding="utf-8",
    )

    host = RuntimePluginHost(activation_context_resolver=lambda info: object())
    host.scan_directory(tmp_path, host.SCOPE_USER)

    assert set(host.plugin_registry) == {"SamplePlugin"}
    assert host.plugin_dependencies["SamplePlugin"] == []
    assert host.plugin_scopes["SamplePlugin"] == host.SCOPE_USER
    assert host.plugin_files["SamplePlugin"] == str(plugin_file)
    assert host.protected_plugins == {"SamplePlugin"}
    entry = host.catalog_entries()[0]
    assert entry.plugin_id == "SamplePlugin"
    assert entry.version == "2.3.4"
    assert entry.activation_context == "runtime"
    assert entry.activation_context_explicit is True


def test_legacy_plugin_loader_composes_host_and_keeps_adapter_side_effects_once() -> None:
    from core.VitaLoom.kernel.plugin_interfaces import IEditorPlugin
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    events: list[str] = []

    class Signal:
        def emit(self, plugin_id: str) -> None:
            events.append(f"signal:{plugin_id}")

    class LegacyPlugin(IEditorPlugin):
        def get_plugin_info(self):
            return {
                "name": "LegacyPlugin",
                "version": "1.0.0",
                "dependencies": [],
                "provides": [],
            }

        def on_load(self, context):
            events.append("load:LegacyPlugin")

        def on_editor_ready(self):
            events.append("ready:LegacyPlugin")

        def on_unload(self):
            events.append("unload:LegacyPlugin")

    kernel = SimpleNamespace(
        get_context=lambda: object(),
        plugin_loaded=Signal(),
        plugin_unloaded=Signal(),
        layout_manager=None,
    )
    loader = PluginLoader(kernel)

    assert loader.plugin_registry is loader.runtime_plugin_host.plugin_registry
    assert loader.loaded_plugins is loader.runtime_plugin_host.loaded_plugins
    assert loader.plugin_dependencies is loader.runtime_plugin_host.plugin_dependencies
    assert loader.plugin_order is loader.runtime_plugin_host.plugin_order
    assert loader.scope_overrides is loader.runtime_plugin_host.scope_overrides

    loader.runtime_plugin_host.register_plugin(LegacyPlugin())
    report = loader._execute_lifecycle_target(
        {"LegacyPlugin"}, source="test", allow_deactivate=True
    )
    assert report["status"] == "settled"
    assert events == [
        "load:LegacyPlugin",
        "ready:LegacyPlugin",
        "signal:LegacyPlugin",
    ]

    assert loader.unload_plugin("LegacyPlugin") is True
    assert events == [
        "load:LegacyPlugin",
        "ready:LegacyPlugin",
        "signal:LegacyPlugin",
        "unload:LegacyPlugin",
        "signal:LegacyPlugin",
    ]

