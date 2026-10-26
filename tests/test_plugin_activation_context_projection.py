# -*- coding: utf-8 -*-
"""E16 proofs for runtime plugin activation projection and legacy UI compatibility."""
from __future__ import annotations

import builtins
import importlib
import sys
from types import SimpleNamespace

import pytest


MODULE_NAME = "core.VitaLoom.core.plugin_activation_context"


def _module():
    return importlib.import_module(MODULE_NAME)


def test_plugin_activation_projection_module_is_qt_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError(f"unexpected PyQt import: {name}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    previous = sys.modules.pop(MODULE_NAME, None)
    try:
        module = importlib.import_module(MODULE_NAME)
        assert module.RuntimePluginActivationContext.__name__ == (
            "RuntimePluginActivationContext"
        )
    finally:
        sys.modules.pop(MODULE_NAME, None)
        if previous is not None:
            sys.modules[MODULE_NAME] = previous


def test_runtime_projection_is_narrow_and_preserves_composed_identities() -> None:
    module = _module()
    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
    )
    from core.VitaLoom.core.runtime_event_bus import InMemoryRuntimeEventBus

    registry = InMemoryRuntimeCapabilityRegistry()
    event_bus = InMemoryRuntimeEventBus()
    legacy = SimpleNamespace(
        services=registry,
        event_bus=event_bus,
        kernel=object(),
        current_scene=object(),
    )

    projection = module.project_runtime_plugin_activation_context(legacy)

    assert projection.services is registry
    assert projection.event_bus is event_bus
    assert isinstance(projection, module.RuntimePluginActivationContext)
    assert not hasattr(projection, "kernel")
    assert not hasattr(projection, "current_scene")
    with pytest.raises((AttributeError, TypeError)):
        projection.kernel = object()


def test_runtime_projection_rejects_incomplete_or_invalid_host_context() -> None:
    module = _module()
    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
    )
    from core.VitaLoom.core.runtime_event_bus import InMemoryRuntimeEventBus

    with pytest.raises(TypeError, match="runtime capability registry"):
        module.project_runtime_plugin_activation_context(
            SimpleNamespace(event_bus=InMemoryRuntimeEventBus())
        )
    with pytest.raises(TypeError, match="runtime event bus"):
        module.project_runtime_plugin_activation_context(
            SimpleNamespace(services=InMemoryRuntimeCapabilityRegistry())
        )


def test_plugin_loader_routes_runtime_and_legacy_contexts_without_inference() -> None:
    module = _module()
    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
    )
    from core.VitaLoom.core.runtime_event_bus import InMemoryRuntimeEventBus
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    legacy = SimpleNamespace(
        services=InMemoryRuntimeCapabilityRegistry(),
        event_bus=InMemoryRuntimeEventBus(),
        kernel=object(),
    )
    kernel = SimpleNamespace(get_context=lambda: legacy)
    loader = PluginLoader(kernel)

    runtime_first = loader._activation_context_for(
        {"name": "RuntimeA", "activation_context": "runtime"}
    )
    runtime_second = loader._activation_context_for(
        {"name": "RuntimeB", "activation_context": "runtime"}
    )
    legacy_result = loader._activation_context_for(
        {"name": "Legacy", "provides": []}
    )

    assert runtime_first is runtime_second
    assert runtime_first.services is legacy.services
    assert runtime_first.event_bus is legacy.event_bus
    assert legacy_result is legacy
    assert isinstance(runtime_first, module.RuntimePluginActivationContext)


def test_unknown_activation_context_kind_fails_before_plugin_callback() -> None:
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    called: list[object] = []
    legacy = SimpleNamespace()
    loader = PluginLoader(SimpleNamespace(get_context=lambda: legacy))

    class Plugin:
        def get_plugin_info(self):
            return {
                "name": "InvalidContextPlugin",
                "provides": [],
                "activation_context": "mystery",
            }

        def on_load(self, context):
            called.append(context)

    with pytest.raises(ValueError, match="activation_context"):
        loader._load_plugin(Plugin())
    assert called == []


def test_real_runtime_plugins_declare_runtime_projection_and_accept_it(tmp_path) -> None:
    module = _module()
    from builtin.editor_extensions.cell_simulation_plugin import CellSimulationPlugin
    from builtin.editor_extensions.downloader_plugin import DownloaderPlugin
    from builtin.editor_extensions.ps_replay_overlay_plugin import PsReplayOverlayPlugin
    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
    )
    from core.VitaLoom.core.runtime_event_bus import InMemoryRuntimeEventBus

    registry = InMemoryRuntimeCapabilityRegistry()
    event_bus = InMemoryRuntimeEventBus()
    projection = module.RuntimePluginActivationProjection(
        services=registry,
        event_bus=event_bus,
    )

    cell = CellSimulationPlugin()
    downloader = DownloaderPlugin()
    replay = PsReplayOverlayPlugin()
    assert cell.get_plugin_info()["activation_context"] == "runtime"
    assert downloader.get_plugin_info()["activation_context"] == "runtime"
    assert replay.get_plugin_info()["activation_context"] == "runtime"

    cell.on_load(projection)
    downloader.on_load(projection)
    replay.on_load(projection)
    try:
        assert cell.context is projection
        from core.VitaLoom.core.service_keys import DOWNLOADER
        assert registry.has(DOWNLOADER)
    finally:
        cell.on_unload()
        downloader.on_unload()
        replay.on_unload()
    assert not registry.has(DOWNLOADER)


def test_load_plugin_passes_selected_context_to_callbacks_and_emits() -> None:
    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
    )
    from core.VitaLoom.core.runtime_event_bus import InMemoryRuntimeEventBus
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    emitted: list[str] = []
    legacy = SimpleNamespace(
        services=InMemoryRuntimeCapabilityRegistry(),
        event_bus=InMemoryRuntimeEventBus(),
        kernel=object(),
    )
    kernel = SimpleNamespace(
        get_context=lambda: legacy,
        plugin_loaded=SimpleNamespace(emit=emitted.append),
    )
    loader = PluginLoader(kernel)
    received: dict[str, object] = {}

    class Plugin:
        def __init__(self, name: str, kind: str | None) -> None:
            self.name = name
            self.kind = kind

        def get_plugin_info(self):
            info = {"name": self.name, "provides": []}
            if self.kind is not None:
                info["activation_context"] = self.kind
            return info

        def on_load(self, context):
            received[self.name] = context

        def on_editor_ready(self):
            return None

    loader._load_plugin(Plugin("RuntimeRealPath", "runtime"))
    loader._load_plugin(Plugin("LegacyRealPath", None))

    assert received["RuntimeRealPath"] is loader._runtime_activation_context
    assert received["RuntimeRealPath"].services is legacy.services
    assert received["LegacyRealPath"] is legacy
    assert emitted == ["RuntimeRealPath", "LegacyRealPath"]
