# -*- coding: utf-8 -*-
"""E19 proofs for the Qt-free runtime plugin lifecycle contract."""
from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path
from types import SimpleNamespace


MODULE_NAME = "core.VitaLoom.core.runtime_plugin_contract"
RUNTIME_ROOT = (
    Path(__file__).resolve().parents[1]
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
)


class _SignalStub:
    def __init__(self) -> None:
        self.events: list[str] = []

    def emit(self, name: str) -> None:
        self.events.append(name)


class _KernelStub:
    def __init__(self) -> None:
        from core.VitaLoom.core.runtime_capability_registry import (
            InMemoryRuntimeCapabilityRegistry,
        )
        from core.VitaLoom.core.runtime_event_bus import InMemoryRuntimeEventBus

        self.plugin_loaded = _SignalStub()
        self.plugin_unloaded = _SignalStub()
        self.layout_manager = None
        self._context = SimpleNamespace(
            services=InMemoryRuntimeCapabilityRegistry(),
            event_bus=InMemoryRuntimeEventBus(),
            kernel=object(),
        )

    def get_context(self):
        return self._context


def test_runtime_plugin_contract_module_is_qt_free(monkeypatch) -> None:
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError(f"unexpected PyQt import: {name}")
        return real_import(name, globals, locals, fromlist, level)

    previous = sys.modules.pop(MODULE_NAME, None)
    monkeypatch.setattr(builtins, "__import__", guarded_import)
    try:
        module = importlib.import_module(MODULE_NAME)
        assert module.IRuntimePlugin.__name__ == "IRuntimePlugin"
    finally:
        sys.modules.pop(MODULE_NAME, None)
        if previous is not None:
            sys.modules[MODULE_NAME] = previous


def test_legacy_editor_interfaces_are_runtime_compatible_adapters() -> None:
    from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
    from core.VitaLoom.kernel.plugin_interfaces import (
        IDockProvider,
        IEditorPlugin,
        IThemeProvider,
        IViewportProvider,
    )

    assert issubclass(IEditorPlugin, IRuntimePlugin)
    for provider in (IDockProvider, IViewportProvider, IThemeProvider):
        assert issubclass(provider, IEditorPlugin)


def test_domain_provider_legacy_imports_adapt_qt_free_authority() -> None:
    from core.VitaLoom.core.runtime_plugin_contract import (
        IComponentTypeProvider as RuntimeComponentProvider,
        IEntityTypeProvider as RuntimeEntityProvider,
        IRuntimePlugin,
    )
    from core.VitaLoom.kernel.plugin_interfaces import (
        IComponentTypeProvider as LegacyComponentProvider,
        IEditorPlugin,
        IEntityTypeProvider as LegacyEntityProvider,
    )

    assert issubclass(RuntimeComponentProvider, IRuntimePlugin)
    assert issubclass(RuntimeEntityProvider, IRuntimePlugin)
    assert issubclass(LegacyComponentProvider, RuntimeComponentProvider)
    assert issubclass(LegacyEntityProvider, RuntimeEntityProvider)
    assert issubclass(LegacyComponentProvider, IEditorPlugin)
    assert issubclass(LegacyEntityProvider, IEditorPlugin)


def test_plain_runtime_plugin_is_discovered_loaded_and_unloaded_without_editor_ready(
    tmp_path,
) -> None:
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    plugin_file = tmp_path / "plain_runtime_plugin.py"
    plugin_file.write_text(
        r"""
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin

class PlainRuntimePlugin(IRuntimePlugin):
    def __init__(self):
        self.ready_lookup_count = 0
        self.unloaded = False

    def __getattr__(self, name):
        if name == "on_editor_ready":
            self.ready_lookup_count += 1
        raise AttributeError(name)

    def get_plugin_info(self):
        return {
            "name": "PlainRuntimePlugin",
            "version": "1.0.0",
            "dependencies": [],
            "provides": [],
            "activation_context": "runtime",
        }

    def on_load(self, runtime_context):
        self.loaded_context = runtime_context

    def on_unload(self):
        self.unloaded = True
""".strip()
        + "\n",
        encoding="utf-8",
    )

    kernel = _KernelStub()
    loader = PluginLoader(kernel)
    loader.load_from_directories([str(tmp_path)])

    plugin = loader.loaded_plugins["PlainRuntimePlugin"]
    assert plugin.loaded_context.services is kernel.get_context().services
    assert plugin.loaded_context.event_bus is kernel.get_context().event_bus
    assert not hasattr(plugin.loaded_context, "kernel")
    # E56 checks the Adapter-local optional capability exactly once; absence
    # remains non-fatal and does not change the Host lifecycle result.
    assert plugin.ready_lookup_count == 1
    assert kernel.plugin_loaded.events == ["PlainRuntimePlugin"]

    loader.unload_plugin("PlainRuntimePlugin")
    assert plugin.unloaded is True
    assert kernel.plugin_unloaded.events == ["PlainRuntimePlugin"]


def test_runtime_plugin_hot_reload_instantiation_accepts_runtime_contract(tmp_path) -> None:
    from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    plugin_file = tmp_path / "reloadable_runtime_plugin.py"
    plugin_file.write_text(
        r"""
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin

class ReloadableRuntimePlugin(IRuntimePlugin):
    def get_plugin_info(self):
        return {
            "name": "ReloadableRuntimePlugin",
            "version": "1.0.0",
            "dependencies": [],
            "provides": [],
            "activation_context": "runtime",
        }

    def on_load(self, runtime_context):
        self.context = runtime_context

    def on_unload(self):
        self.context = None
""".strip()
        + "\n",
        encoding="utf-8",
    )

    loader = PluginLoader(_KernelStub())
    plugin_name, plugin = loader._instantiate_plugin_from_file(plugin_file)

    assert plugin_name == "ReloadableRuntimePlugin"
    assert isinstance(plugin, IRuntimePlugin)


def test_builtin_runtime_plugins_depend_only_on_qt_free_contract() -> None:
    plugin_files = {
        "DownloaderPlugin": RUNTIME_ROOT
        / "builtin"
        / "editor_extensions"
        / "downloader_plugin.py",
        "CellSimulationPlugin": RUNTIME_ROOT
        / "builtin"
        / "editor_extensions"
        / "cell_simulation_plugin.py",
        "PsReplayOverlayPlugin": RUNTIME_ROOT
        / "builtin"
        / "editor_extensions"
        / "ps_replay_overlay_plugin.py",
    }

    for plugin_id, plugin_file in plugin_files.items():
        source = plugin_file.read_text(encoding="utf-8-sig")
        assert "core.VitaLoom.kernel.plugin_interfaces" not in source
        assert "core.VitaLoom.core.runtime_plugin_contract" in source

        module_name = f"e19_{plugin_file.stem}_{id(plugin_file)}"
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
            plugin_class = getattr(module, plugin_id)
            info = plugin_class().get_plugin_info()
        finally:
            sys.modules.pop(module_name, None)

        assert info["name"] == plugin_id
        assert info["activation_context"] == "runtime"



def test_legacy_public_interface_module_is_qt_free_and_exposes_stable_names(
    monkeypatch,
) -> None:
    module_name = "core.VitaLoom.kernel.plugin_interfaces"
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError(f"unexpected PyQt import: {name}")
        return real_import(name, globals, locals, fromlist, level)

    previous = sys.modules.pop(module_name, None)
    monkeypatch.setattr(builtins, "__import__", guarded_import)
    try:
        module = importlib.import_module(module_name)
        assert {
            "IEditorPlugin",
            "IDockProvider",
            "IViewportProvider",
            "IThemeProvider",
            "IEntityTypeProvider",
            "IComponentTypeProvider",
        }.issubset(vars(module))
    finally:
        sys.modules.pop(module_name, None)
        if previous is not None:
            sys.modules[module_name] = previous


def test_legacy_public_interface_abstract_surface_and_mro_are_stable() -> None:
    from core.VitaLoom.core.runtime_plugin_contract import (
        IComponentTypeProvider as RuntimeComponentProvider,
        IEntityTypeProvider as RuntimeEntityProvider,
    )
    from core.VitaLoom.kernel.plugin_interfaces import (
        IComponentTypeProvider,
        IDockProvider,
        IEditorPlugin,
        IEntityTypeProvider,
        IThemeProvider,
        IViewportProvider,
    )

    assert {"create_dock_widget", "get_dock_config"}.issubset(
        IDockProvider.__abstractmethods__
    )
    assert {
        "create_viewport_widget",
        "get_viewport_id",
        "get_viewport_name",
    }.issubset(IViewportProvider.__abstractmethods__)
    assert {
        "get_theme_name",
        "get_stylesheet",
        "get_color_scheme",
    }.issubset(IThemeProvider.__abstractmethods__)
    assert IEntityTypeProvider.__bases__ == (IEditorPlugin, RuntimeEntityProvider)
    assert IComponentTypeProvider.__bases__ == (
        IEditorPlugin,
        RuntimeComponentProvider,
    )


def test_legacy_interface_docs_describe_compatibility_not_new_authority() -> None:
    project_root = Path(__file__).resolve().parents[1]
    guide = (
        project_root / "docs" / "guides" / "LEGACY_PLUGIN_INTERFACE_COMPATIBILITY.md"
    ).read_text(encoding="utf-8")
    runtime_readme = (
        project_root
        / "FrameCore"
        / "plugins"
        / "lotucosm-vitaloom"
        / "versions"
        / "1.0.0"
        / "runtime"
        / "core"
        / "VitaLoom"
        / "README.md"
    ).read_text(encoding="utf-8")
    troubleshooting = (
        project_root / "docs" / "lotucosm_core_troubleshooting.md"
    ).read_text(encoding="utf-8")

    assert "does **not** use" in guide
    assert "not a structural fallback gate" in guide
    assert "New plugins" in guide
    assert "dock_surface" in runtime_readme
    assert "fallback" in runtime_readme
    assert "dock_surface" in troubleshooting
    assert "fallback" in troubleshooting

def test_legacy_ui_provider_types_are_quarantined_to_the_public_compatibility_module() -> None:
    runtime_root = RUNTIME_ROOT / "core" / "VitaLoom"
    compatibility_module = runtime_root / "kernel" / "plugin_interfaces.py"
    legacy_ui_types = (
        "IEditorPlugin",
        "IDockProvider",
        "IViewportProvider",
        "IThemeProvider",
    )
    leaks: list[str] = []

    for source_path in runtime_root.rglob("*.py"):
        if source_path == compatibility_module:
            continue
        source = source_path.read_text(encoding="utf-8-sig")
        for legacy_type in legacy_ui_types:
            if legacy_type in source:
                leaks.append(f"{source_path.relative_to(runtime_root)}:{legacy_type}")

    assert not leaks, (
        "legacy UI provider types must remain public compatibility definitions "
        f"only; found non-Adapter authority leaks: {leaks}"
    )