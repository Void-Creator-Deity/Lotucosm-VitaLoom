# -*- coding: utf-8 -*-
"""E25 red proofs for PluginLoader remaining a narrow shutdown facade."""
from __future__ import annotations

import inspect
from types import SimpleNamespace


def test_loader_shutdown_delegates_exactly_to_nested_host() -> None:
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    report = {"status": "settled", "source": "shutdown"}
    calls: list[str] = []
    loader = PluginLoader.__new__(PluginLoader)
    loader.nested_plugin_host = SimpleNamespace(
        shutdown_plugins=lambda: calls.append("nested") or report
    )
    loader.runtime_plugin_host = SimpleNamespace(
        shutdown_plugins=lambda: (_ for _ in ()).throw(
            AssertionError("Loader must publish through NestedPluginHost")
        )
    )

    result = PluginLoader.shutdown_plugins(loader)

    assert result is report
    assert calls == ["nested"]


def test_loader_shutdown_interface_contains_no_second_authority() -> None:
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    source = inspect.getsource(PluginLoader.shutdown_plugins)

    assert "nested_plugin_host.shutdown_plugins()" in source
    assert "loaded_plugins" not in source
    assert "unload_plugin(" not in source
    assert "build_plugin_lifecycle_plan" not in source
    assert "for " not in source
