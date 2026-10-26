# -*- coding: utf-8 -*-
"""E21 proofs for Qt-free Project World nested-plugin orchestration."""
from __future__ import annotations

import builtins
import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


MODULE_NAME = "core.VitaLoom.project.project_scoped_plugin_host"


def _write_addon(
    project: Path,
    *,
    folder: str,
    plugin_id: str,
    dependencies: tuple[str, ...] = (),
    code_version: str = "1.0.0",
    manifest_version: str = "1.0.0",
    events_file: Path | None = None,
) -> None:
    addon = project / "addons" / folder
    addon.mkdir(parents=True, exist_ok=True)
    entry = f"{folder}_plugin.py"
    event_load = ""
    event_unload = ""
    if events_file is not None:
        event_load = (
            f"Path({str(events_file)!r}).open('a', encoding='utf-8').write(" 
            f"'load:{plugin_id}\\n')"
        )
        event_unload = (
            f"Path({str(events_file)!r}).open('a', encoding='utf-8').write(" 
            f"'unload:{plugin_id}\\n')"
        )
    (addon / entry).write_text(
        f"""
from pathlib import Path
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin

class {plugin_id}(IRuntimePlugin):
    def get_plugin_info(self):
        return {{
            "name": "{plugin_id}",
            "version": "{code_version}",
            "dependencies": {list(dependencies)!r},
            "activation_context": "runtime",
        }}

    def on_load(self, runtime_context):
        self.context = runtime_context
        {event_load or 'pass'}

    def on_unload(self):
        {event_unload or 'pass'}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (addon / "plugin.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": plugin_id,
                "version": manifest_version,
                "entry": entry,
                "activation_context": "runtime",
                "runtime": {
                    "plugin_id": "lotucosm-vitaloom",
                    "version": ">=1.0.0,<2.0.0",
                },
                "dependencies": list(dependencies),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


from core.VitaLoom.project.plugin_host_operator import canonical_project_path

def _headless_host():
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
    from core.VitaLoom.project.project_scoped_plugin_host import ProjectScopedPluginHost

    runtime_context = SimpleNamespace(project_root="")
    runtime_host = RuntimePluginHost(
        activation_context_resolver=lambda _info: runtime_context
    )
    project_host = ProjectScopedPluginHost(
        runtime_host,
        runtime_version_resolver=lambda: "1.0.0",
        repo_root_resolver=lambda: Path.cwd(),
        eager_mode_resolver=lambda: False,
        active_plugin_ids_resolver=lambda _data, *, repo_root: set(),
        player_plugin_ids_resolver=lambda _data, *, repo_root: set(),
    )
    return runtime_host, project_host, runtime_context


def test_project_scoped_host_module_is_qt_and_legacy_loader_free(
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
        assert module.ProjectScopedPluginHost.__name__ == "ProjectScopedPluginHost"
    finally:
        sys.modules.pop(MODULE_NAME, None)
        if previous is not None:
            sys.modules[MODULE_NAME] = previous


def test_headless_project_host_discovers_and_activates_plain_runtime_addon(
    tmp_path: Path,
) -> None:
    runtime_host, project_host, runtime_context = _headless_host()
    project = tmp_path / "world"
    project.mkdir()
    _write_addon(project, folder="sample", plugin_id="SamplePlugin")

    discovery = project_host.scan_project_addons(project)
    lifecycle = project_host.sync_plugins_for_project({}, repo_root=tmp_path)

    assert discovery["status"] == "ready"
    assert lifecycle["status"] == "settled"
    assert set(runtime_host.loaded_plugins) == {"SamplePlugin"}
    assert runtime_host.loaded_plugins["SamplePlugin"].context is runtime_context
    assert project_host.operator_project_path == canonical_project_path(project)
    assert project_host.embedded_catalog_project_path == canonical_project_path(project)
    receipts = lifecycle["addon_runtime_receipts"]
    assert len(receipts) == 1
    assert receipts[0]["kind"] == "project_addon"
    assert receipts[0]["outcome"] == "runtime_loaded"
    assert len(receipts[0]["entry_sha256"]) == 64
    assert len(receipts[0]["manifest_sha256"]) == 64
    evidence = project_host.lifecycle_evidence()
    assert evidence["addon_runtime_receipts"] == receipts
    assert len(evidence["digest"]) == 64


def test_project_addon_source_replacement_after_discovery_is_blocked(
    tmp_path: Path,
) -> None:
    runtime_host, project_host, _context = _headless_host()
    project = tmp_path / "world"
    project.mkdir()
    _write_addon(project, folder="sample", plugin_id="SamplePlugin")
    discovery = project_host.scan_project_addons(project)
    assert discovery["status"] == "ready"
    entry = project / "addons" / "sample" / "sample_plugin.py"
    entry.write_text(entry.read_text(encoding="utf-8") + "\n# replaced\n", encoding="utf-8")

    lifecycle = project_host.sync_plugins_for_project({}, repo_root=tmp_path)
    assert lifecycle["status"] == "blocked"
    assert any(
        item["code"] == "addon_source_digest_changed"
        for item in lifecycle["diagnostics"]
    )
    assert not runtime_host.loaded_plugins
    assert project_host.lifecycle_evidence()["addon_runtime_receipts"] == []


def test_project_switch_deactivates_old_catalog_in_reverse_order_then_activates_new(
    tmp_path: Path,
) -> None:
    runtime_host, project_host, _context = _headless_host()
    events_file = tmp_path / "events.txt"
    world_a = tmp_path / "world-a"
    world_a.mkdir()
    _write_addon(
        world_a,
        folder="alpha",
        plugin_id="AlphaPlugin",
        events_file=events_file,
    )
    _write_addon(
        world_a,
        folder="beta",
        plugin_id="BetaPlugin",
        dependencies=("AlphaPlugin",),
        events_file=events_file,
    )
    world_b = tmp_path / "world-b"
    world_b.mkdir()
    _write_addon(
        world_b,
        folder="gamma",
        plugin_id="GammaPlugin",
        events_file=events_file,
    )

    assert project_host.scan_project_addons(world_a)["status"] == "ready"
    assert project_host.sync_plugins_for_project({}, repo_root=tmp_path)["status"] == "settled"
    switched = project_host.scan_project_addons(world_b)
    assert switched["status"] == "ready"
    assert project_host.sync_plugins_for_project({}, repo_root=tmp_path)["status"] == "settled"

    assert events_file.read_text(encoding="utf-8").splitlines() == [
        "load:AlphaPlugin",
        "load:BetaPlugin",
        "unload:BetaPlugin",
        "unload:AlphaPlugin",
        "load:GammaPlugin",
    ]
    assert set(runtime_host.plugin_registry) == {"GammaPlugin"}
    assert set(runtime_host.loaded_plugins) == {"GammaPlugin"}


def test_failed_project_switch_preserves_previous_catalog_but_reports_requested_world(
    tmp_path: Path,
) -> None:
    runtime_host, project_host, _context = _headless_host()
    world_a = tmp_path / "world-a"
    world_a.mkdir()
    _write_addon(world_a, folder="alpha", plugin_id="AlphaPlugin")
    assert project_host.scan_project_addons(world_a)["status"] == "ready"
    assert project_host.sync_plugins_for_project({}, repo_root=tmp_path)["status"] == "settled"

    world_b = tmp_path / "world-b"
    world_b.mkdir()
    _write_addon(
        world_b,
        folder="broken",
        plugin_id="BrokenPlugin",
        code_version="2.0.0",
    )
    blocked = project_host.scan_project_addons(world_b)
    inspection = project_host.inspect_plugin_host()

    assert blocked["status"] == "blocked"
    assert set(runtime_host.plugin_registry) == {"AlphaPlugin"}
    assert set(runtime_host.loaded_plugins) == {"AlphaPlugin"}
    assert inspection["project_path"] == canonical_project_path(world_b)
    assert inspection["embedded_catalog_project_path"] == canonical_project_path(world_a)


def test_project_switch_unload_failure_keeps_active_catalog_without_stale_receipts(
    tmp_path: Path,
) -> None:
    runtime_host, project_host, _context = _headless_host()
    world_a = tmp_path / "world-a"
    world_a.mkdir()
    _write_addon(world_a, folder="alpha", plugin_id="AlphaPlugin")
    assert project_host.scan_project_addons(world_a)["status"] == "ready"
    assert project_host.sync_plugins_for_project({}, repo_root=tmp_path)["status"] == "settled"

    def fail_unload() -> None:
        raise RuntimeError("unload blocked")

    runtime_host.loaded_plugins["AlphaPlugin"].on_unload = fail_unload
    world_b = tmp_path / "world-b"
    world_b.mkdir()
    _write_addon(world_b, folder="beta", plugin_id="BetaPlugin")

    switched = project_host.scan_project_addons(world_b)
    assert switched["status"] == "failed"
    assert set(runtime_host.loaded_plugins) == {"AlphaPlugin"}
    assert not project_host.lifecycle_evidence()["addon_runtime_receipts"]
    assert project_host.last_lifecycle_report["status"] == "failed"


def test_legacy_loader_delegates_project_host_and_settles_pending_layout_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    monkeypatch.setenv("VITALOOM_EAGER_PLUGINS", "0")

    class Signal:
        def emit(self, _plugin_id: str) -> None:
            return None

    class Layout:
        def __init__(self) -> None:
            self.calls = 0

        def process_pending_dock_tabify(self) -> None:
            self.calls += 1

    layout = Layout()
    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
    )
    from core.VitaLoom.core.runtime_event_bus import InMemoryRuntimeEventBus

    context = SimpleNamespace(
        repo_root=str(tmp_path),
        project_root=str(tmp_path),
        services=InMemoryRuntimeCapabilityRegistry(),
        event_bus=InMemoryRuntimeEventBus(),
    )
    kernel = SimpleNamespace(
        get_context=lambda: context,
        plugin_loaded=Signal(),
        plugin_unloaded=Signal(),
        layout_manager=layout,
    )
    loader = PluginLoader(kernel)
    project = tmp_path / "world"
    project.mkdir()
    _write_addon(project, folder="sample", plugin_id="SamplePlugin")

    assert loader.project_scoped_plugin_host.runtime_plugin_host is loader.runtime_plugin_host
    assert loader.scan_project_addons(project)["status"] == "ready"
    from unittest.mock import patch

    with patch(
        "core.VitaLoom.project.plugin_activation.collect_active_plugin_ids",
        return_value=set(),
    ):
        report = loader.sync_plugins_for_project({}, repo_root=tmp_path)

    assert report["status"] == "settled"
    assert set(loader.loaded_plugins) == {"SamplePlugin"}
    assert loader.last_project_addon_discovery_report is (
        loader.project_scoped_plugin_host.last_project_addon_discovery_report
    )
    assert layout.calls == 1


def test_headless_project_host_recovery_requires_current_report_and_confirmation(
    tmp_path: Path,
) -> None:
    from core.VitaLoom.project.plugin_host_operator import PluginHostOperatorError

    runtime_host, project_host, _context = _headless_host()
    project = tmp_path / "world"
    project.mkdir()
    (project / "project.json").write_text(
        json.dumps({"name": "world", "disabled_plugins": []}),
        encoding="utf-8",
    )
    broken = project / "addons" / "broken"
    broken.mkdir(parents=True)
    (broken / "broken_plugin.py").write_text(
        "# missing plugin manifest\\n", encoding="utf-8"
    )

    assert project_host.scan_project_addons(project)["status"] == "blocked"
    inspection = project_host.inspect_plugin_host()
    recovery = inspection["recoveries"][0]

    with pytest.raises(PluginHostOperatorError) as error:
        project_host.resolve_plugin_host_recovery(
            project_path=str(project),
            report_id=inspection["report_id"],
            action=recovery["action"],
            operator_confirmation="not-the-bound-confirmation",
        )

    assert error.value.code == "plugin_host_recovery_confirmation_required"
    assert project_host.last_project_addon_discovery_report["status"] == "blocked"
    assert not runtime_host.plugin_registry
    assert "force" not in project_host.resolve_plugin_host_recovery.__code__.co_varnames

