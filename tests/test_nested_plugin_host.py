# -*- coding: utf-8 -*-
"""E23 proofs for the Qt-free nested plugin Host composition root."""
from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


MODULE_NAME = "core.VitaLoom.core.nested_plugin_host"


class _Plugin:
    def __init__(
        self,
        plugin_id: str,
        events: list[str] | None = None,
        *,
        version: str = "1.0.0",
        dependencies: tuple[str, ...] = (),
    ) -> None:
        self.plugin_id = plugin_id
        self.events = events if events is not None else []
        self.version = version
        self.dependencies = dependencies

    def get_plugin_info(self):
        return {
            "name": self.plugin_id,
            "version": self.version,
            "dependencies": list(self.dependencies),
            "activation_context": "runtime",
            "provides": [],
        }

    def on_load(self, _context):
        self.events.append(f"load:{self.plugin_id}:{self.version}")

    def on_unload(self):
        self.events.append(f"unload:{self.plugin_id}:{self.version}")


def _write_runtime_plugin(
    directory: Path,
    *,
    plugin_id: str,
    dependencies: tuple[str, ...] = (),
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{plugin_id.lower()}_plugin.py"
    source = f'''\
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin


class {plugin_id}(IRuntimePlugin):
    def get_plugin_info(self):
        return {{
            "name": "{plugin_id}",
            "version": "1.0.0",
            "dependencies": {list(dependencies)!r},
            "activation_context": "runtime",
            "provides": [],
        }}

    def on_load(self, runtime_context):
        self.runtime_context = runtime_context

    def on_unload(self):
        pass
'''
    path.write_text(source, encoding="utf-8")
    return path


def _nested_host(**overrides):
    from core.VitaLoom.core.nested_plugin_host import NestedPluginHost

    defaults = {
        "activation_context_resolver": lambda _info: object(),
        "repo_root_resolver": lambda: Path.cwd(),
        "eager_mode_resolver": lambda: False,
        "player_mode_resolver": lambda: False,
        "bootstrap_plugin_ids_resolver": lambda _repo_root: set(),
        "active_plugin_ids_resolver": lambda _data, *, repo_root: set(),
        "player_plugin_ids_resolver": lambda _data, *, repo_root: set(),
    }
    defaults.update(overrides)
    return NestedPluginHost(**defaults)


def test_nested_plugin_host_module_is_qt_and_legacy_loader_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        blocked = (
            name == "PyQt6"
            or name.startswith("PyQt6.")
            or name == "core.VitaLoom.kernel.plugin_interfaces"
            or name == "core.VitaLoom.kernel.plugin_loader"
        )
        if blocked:
            raise AssertionError(f"unexpected legacy Host import: {name}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    previous = sys.modules.pop(MODULE_NAME, None)
    try:
        module = importlib.import_module(MODULE_NAME)
        assert module.NestedPluginHost.__name__ == "NestedPluginHost"
    finally:
        sys.modules.pop(MODULE_NAME, None)
        if previous is not None:
            sys.modules[MODULE_NAME] = previous


def test_subhosts_share_exactly_one_runtime_registry_and_aliases() -> None:
    host = _nested_host()

    assert host.project_scoped_plugin_host.runtime_plugin_host is host.runtime_plugin_host
    assert host.manual_plugin_reload_host.runtime_plugin_host is host.runtime_plugin_host
    assert host.plugin_registry is host.runtime_plugin_host.plugin_registry
    assert host.loaded_plugins is host.runtime_plugin_host.loaded_plugins
    assert host.plugin_dependencies is host.runtime_plugin_host.plugin_dependencies
    assert host.plugin_order is host.runtime_plugin_host.plugin_order
    assert host.plugin_scopes is host.runtime_plugin_host.plugin_scopes


def test_headless_layered_discovery_bootstraps_only_selected_dependency_closure(
    tmp_path: Path,
) -> None:
    official = tmp_path / "official"
    user = tmp_path / "user"
    _write_runtime_plugin(official, plugin_id="BootstrapPlugin")
    _write_runtime_plugin(
        user,
        plugin_id="WorkspaceToolPlugin",
        dependencies=("BootstrapPlugin",),
    )
    host = _nested_host(
        repo_root_resolver=lambda: tmp_path,
        bootstrap_plugin_ids_resolver=lambda _repo_root: {"BootstrapPlugin"},
    )

    report = host.load_from_layered_directories(
        {
            host.SCOPE_OFFICIAL: [str(official)],
            host.SCOPE_USER: [str(user)],
        }
    )

    assert set(host.plugin_registry) == {"BootstrapPlugin", "WorkspaceToolPlugin"}
    assert set(host.loaded_plugins) == {"BootstrapPlugin"}
    assert report["status"] == "settled"
    assert report["source"] == "activation_only"
    assert report["completed"]["activated"] == ["BootstrapPlugin"]
    assert host.last_lifecycle_report is report
    assert host.runtime_plugin_host.last_lifecycle_report is report


def test_lifecycle_report_and_post_transition_adapter_receive_exact_fact() -> None:
    observed: list[dict] = []
    host = _nested_host(after_lifecycle_transition=observed.append)
    plugin = _Plugin("RuntimePlugin")
    host.runtime_plugin_host.register_plugin(
        plugin,
        scope=host.SCOPE_OFFICIAL,
        source="RuntimePlugin_plugin.py",
    )
    host.runtime_plugin_host.resolve_dependencies()

    report = host.execute_lifecycle_target(
        {"RuntimePlugin"}, source="test", allow_deactivate=True
    )

    assert observed == [report]
    assert observed[0] is report
    assert host.last_lifecycle_report is report
    assert host.runtime_plugin_host.last_lifecycle_report is report


def test_project_world_clear_publishes_one_composition_report() -> None:
    observed: list[dict] = []
    events: list[str] = []
    host = _nested_host(after_lifecycle_transition=observed.append)
    plugin = _Plugin("WorldAddonPlugin", events)
    runtime = host.runtime_plugin_host
    runtime.register_plugin(
        plugin,
        scope=runtime.SCOPE_EMBEDDED,
        source="WorldAddonPlugin_plugin.py",
    )
    runtime.loaded_plugins["WorldAddonPlugin"] = plugin
    runtime.resolve_dependencies()
    host.project_scoped_plugin_host.embedded_plugin_names.add("WorldAddonPlugin")

    report = host.clear_embedded_plugins()

    assert report["status"] == "settled"
    assert report["completed"]["deactivated"] == ["WorldAddonPlugin"]
    assert events == ["unload:WorldAddonPlugin:1.0.0"]
    assert observed == [report]
    assert host.last_lifecycle_report is report
    assert runtime.last_lifecycle_report is report
    assert "WorldAddonPlugin" not in runtime.plugin_registry
    assert "WorldAddonPlugin" not in runtime.plugin_metadata


def test_manual_reload_publishes_reload_and_composition_reports(tmp_path: Path) -> None:
    events: list[str] = []
    old = _Plugin("ReloadablePlugin", events)
    candidate = _Plugin("ReloadablePlugin", events, version="2.0.0")
    source = tmp_path / "reloadable_plugin.py"
    source.write_text("# reload source\n", encoding="utf-8")
    host = _nested_host(candidate_importer=lambda _path: ("ReloadablePlugin", candidate))
    runtime = host.runtime_plugin_host
    runtime.register_plugin(old, scope=runtime.SCOPE_USER, source=source)
    runtime.loaded_plugins["ReloadablePlugin"] = old
    runtime.resolve_dependencies()

    report = host.reload_plugin("ReloadablePlugin")

    assert report["status"] == "settled"
    assert host.last_reload_report == report
    assert host.last_lifecycle_report == report
    assert runtime.last_lifecycle_report == report
    assert runtime.plugin_registry["ReloadablePlugin"] is candidate
    assert runtime.loaded_plugins["ReloadablePlugin"] is candidate


def test_legacy_loader_uses_nested_composition_root_and_preserves_state_aliases() -> None:
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    kernel = SimpleNamespace(
        get_context=lambda: SimpleNamespace(repo_root=Path.cwd()),
        layout_manager=None,
    )
    loader = PluginLoader(kernel)

    assert loader.runtime_plugin_host is loader.nested_plugin_host.runtime_plugin_host
    assert (
        loader.project_scoped_plugin_host
        is loader.nested_plugin_host.project_scoped_plugin_host
    )
    assert (
        loader.manual_plugin_reload_host
        is loader.nested_plugin_host.manual_plugin_reload_host
    )
    assert loader.plugin_registry is loader.nested_plugin_host.plugin_registry
    assert loader.loaded_plugins is loader.nested_plugin_host.loaded_plugins
    assert loader.plugin_dependencies is loader.nested_plugin_host.plugin_dependencies

