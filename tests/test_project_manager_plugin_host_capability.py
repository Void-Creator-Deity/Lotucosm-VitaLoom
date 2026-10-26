# -*- coding: utf-8 -*-
"""E27 proofs for ProjectManager's recursive plugin Host capability seam."""
from __future__ import annotations

import inspect
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QApplication

from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION
from core.VitaLoom.project.project_manager import ProjectManager


RUNTIME_ROOT = (
    Path(__file__).resolve().parents[1]
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
)
PROJECT_MANAGER_SOURCE = (
    RUNTIME_ROOT / "core" / "VitaLoom" / "project" / "project_manager.py"
)


@pytest.fixture(scope="session", autouse=True)
def _qt_app() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def manager(tmp_path: Path):
    context = get_editor_context()
    context._ensure_qobject_initialized()
    services = context.services
    services.unregister(PLUGIN_HOST_CONTROL_OBSERVATION)
    previous = {
        "kernel": getattr(context, "kernel", None),
        "repo_root": getattr(context, "repo_root", None),
        "project_root": getattr(context, "project_root", None),
        "current_project_path": getattr(context, "current_project_path", None),
        "project_modified": getattr(context, "project_modified", False),
        "current_project_config": getattr(context, "current_project_config", None),
        "project_manifest_validation": getattr(
            context, "project_manifest_validation", None
        ),
        "project_asset_registry_snapshot": getattr(
            context, "project_asset_registry_snapshot", None
        ),
    }
    ProjectManager._instance = None
    result = ProjectManager()
    result._system_config_dir = str(tmp_path / "state" / "system")
    try:
        yield result, context, services
    finally:
        services.unregister(PLUGIN_HOST_CONTROL_OBSERVATION)
        for name, value in previous.items():
            setattr(context, name, value)
        ProjectManager._instance = None
        result.deleteLater()


class _KernelLoaderTrap:
    def __getattr__(self, name: str):
        raise AssertionError(f"ProjectManager reached legacy kernel.plugin_loader.{name}")


class RecordingPluginHost:
    def __init__(
        self,
        *,
        discovery: dict | None = None,
        lifecycle: dict | None = None,
    ) -> None:
        self.discovery = discovery or {"status": "ready", "project_addons": []}
        self.lifecycle = lifecycle or {
            "status": "settled",
            "completed": {"deactivated": [], "activated": []},
        }
        self.calls: list[tuple] = []

    def observe_plugins(self) -> dict:
        return {"status": "ready"}

    def reload_plugin(self, plugin_id: str) -> dict:
        return {"status": "settled", "plugin_id": plugin_id}

    def unload_plugin(self, plugin_id: str) -> dict:
        return {"status": "settled", "plugin_id": plugin_id}

    def scan_project_addons(self, project_path: object) -> dict:
        self.calls.append(("scan", project_path))
        return dict(self.discovery)

    def sync_plugins_for_project(
        self, project_data: dict, *, repo_root: object | None = None
    ) -> dict:
        self.calls.append(("sync", project_data, repo_root))
        return dict(self.lifecycle)


def test_open_plugin_sync_resolves_exact_capability_without_kernel_loader(
    manager, tmp_path: Path
) -> None:
    project_manager, context, services = manager
    project_path = str((tmp_path / "world").resolve())
    repo_root = tmp_path / "runtime-root"
    project_data = {"name": "world", "plugins": {"enabled": ["weather"]}}
    host = RecordingPluginHost()
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    context.kernel = SimpleNamespace(plugin_loader=_KernelLoaderTrap())
    context.repo_root = repo_root

    report = project_manager._sync_project_plugins(project_data, project_path)

    assert host.calls == [
        ("scan", project_path),
        ("sync", project_data, repo_root),
    ]
    assert report["status"] == "settled"
    assert report["source"] == "project_open"
    assert report["discovery"] == {"status": "ready", "project_addons": []}


def test_open_plugin_sync_blocks_before_sync_when_discovery_is_not_ready(
    manager, tmp_path: Path
) -> None:
    project_manager, context, services = manager
    project_path = str((tmp_path / "world").resolve())
    discovery = {
        "status": "blocked",
        "code": "project_addon_discovery_failed",
        "diagnostics": [{"code": "broken_addon"}],
    }
    host = RecordingPluginHost(discovery=discovery)
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    context.kernel = None

    report = project_manager._sync_project_plugins({"name": "world"}, project_path)

    assert host.calls == [("scan", project_path)]
    assert report["status"] == "blocked"
    assert report["source"] == "project_open"
    assert report["discovery"] == discovery
    assert report["diagnostics"] == [{"code": "broken_addon"}]


def test_close_without_plugin_host_capability_fails_closed_and_preserves_world(
    manager, tmp_path: Path, monkeypatch
) -> None:
    project_manager, context, _services = manager
    project = tmp_path / "world"
    project.mkdir()
    (project / "project.json").write_text(
        json.dumps({"name": "world", "active_scene": ""}), encoding="utf-8"
    )
    context.current_project_path = str(project)
    context.current_project_config = {"name": "world"}
    context.kernel = None
    monkeypatch.setattr(
        project_manager,
        "flush_current_project",
        lambda: {"status": "flushed", "code": "", "report_id": "ok"},
    )
    emitted: list[bool] = []
    project_manager.project_closed.connect(lambda: emitted.append(True))

    report = project_manager.close_project()

    assert report["status"] == "partial"
    assert report["code"] == "project_addon_teardown_unsettled"
    assert report["plugin_lifecycle"]["status"] == "blocked"
    assert report["plugin_lifecycle"]["code"] == "plugin_host_unavailable"
    assert context.current_project_path == str(project)
    assert emitted == []



class ExplodingPluginHost(RecordingPluginHost):
    def __init__(self, action: str) -> None:
        super().__init__()
        self.action = action

    def scan_project_addons(self, project_path: object) -> dict:
        self.calls.append(("scan", project_path))
        if self.action == "scan":
            raise RuntimeError("scan exploded")
        return dict(self.discovery)

    def sync_plugins_for_project(
        self, project_data: dict, *, repo_root: object | None = None
    ) -> dict:
        self.calls.append(("sync", project_data, repo_root))
        if self.action == "sync":
            raise RuntimeError("sync exploded")
        return dict(self.lifecycle)


def test_open_plugin_host_exception_remains_a_truthful_failed_report(
    manager, tmp_path: Path
) -> None:
    project_manager, context, services = manager
    project_path = str((tmp_path / "world").resolve())
    host = ExplodingPluginHost("scan")
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    context.kernel = None

    report = project_manager._sync_project_plugins({"name": "world"}, project_path)

    assert report["status"] == "failed"
    assert report["source"] == "project_open"
    assert report["diagnostics"][0]["code"] == "plugin_lifecycle_adapter_exception"
    assert report["diagnostics"][0]["message"] == "scan exploded"
    assert host.calls == [("scan", project_path)]


def test_close_plugin_host_exception_preserves_world_and_reports_partial(
    manager, tmp_path: Path, monkeypatch
) -> None:
    project_manager, context, services = manager
    project = tmp_path / "world"
    project.mkdir()
    (project / "project.json").write_text(
        json.dumps({"name": "world", "active_scene": ""}), encoding="utf-8"
    )
    context.current_project_path = str(project)
    context.current_project_config = {"name": "world"}
    host = ExplodingPluginHost("sync")
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    monkeypatch.setattr(
        project_manager,
        "flush_current_project",
        lambda: {"status": "flushed", "code": "", "report_id": "ok"},
    )
    emitted: list[bool] = []
    project_manager.project_closed.connect(lambda: emitted.append(True))

    report = project_manager.close_project()

    assert report["status"] == "partial"
    assert report["code"] == "project_addon_teardown_exception"
    assert report["plugin_lifecycle"]["status"] == "failed"
    assert report["plugin_lifecycle"]["diagnostics"][0]["code"] == (
        "project_close_plugin_cleanup_failed"
    )
    assert host.calls == [("scan", None), ("sync", {}, None)]
    assert context.current_project_path == str(project)
    assert emitted == []

def test_open_plugin_sync_exception_remains_a_truthful_failed_report(
    manager, tmp_path: Path
) -> None:
    project_manager, context, services = manager
    project_path = str((tmp_path / "world").resolve())
    project_data = {"name": "world"}
    host = ExplodingPluginHost("sync")
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    context.kernel = None

    report = project_manager._sync_project_plugins(project_data, project_path)

    assert report["status"] == "failed"
    assert report["source"] == "project_open"
    assert report["diagnostics"][0]["code"] == "plugin_lifecycle_adapter_exception"
    assert report["diagnostics"][0]["message"] == "sync exploded"
    assert host.calls[0] == ("scan", project_path)
    assert host.calls[1][0] == "sync"


def test_close_plugin_discovery_exception_preserves_world_and_reports_partial(
    manager, tmp_path: Path, monkeypatch
) -> None:
    project_manager, context, services = manager
    project = tmp_path / "world"
    project.mkdir()
    (project / "project.json").write_text(
        json.dumps({"name": "world", "active_scene": ""}), encoding="utf-8"
    )
    context.current_project_path = str(project)
    context.current_project_config = {"name": "world"}
    host = ExplodingPluginHost("scan")
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    monkeypatch.setattr(
        project_manager,
        "flush_current_project",
        lambda: {"status": "flushed", "code": "", "report_id": "ok"},
    )
    emitted: list[bool] = []
    project_manager.project_closed.connect(lambda: emitted.append(True))

    report = project_manager.close_project()

    assert report["status"] == "partial"
    assert report["code"] == "project_addon_teardown_exception"
    assert report["plugin_lifecycle"]["status"] == "failed"
    assert report["plugin_lifecycle"]["diagnostics"][0]["code"] == (
        "project_close_plugin_cleanup_failed"
    )
    assert host.calls == [("scan", None)]
    assert context.current_project_path == str(project)
    assert emitted == []


def test_open_plugin_sync_keeps_incomplete_public_host_interface_visible(
    manager, tmp_path: Path
) -> None:
    project_manager, context, services = manager
    project_path = str((tmp_path / "world").resolve())
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, object())
    context.kernel = None

    with pytest.raises(TypeError, match="incomplete Interface"):
        project_manager._sync_project_plugins({"name": "world"}, project_path)


def test_project_manager_source_has_no_legacy_loader_or_parallel_host_authority() -> None:
    source = PROJECT_MANAGER_SOURCE.read_text(encoding="utf-8")
    tree_source = inspect.cleandoc(source)

    assert "kernel.plugin_loader" not in tree_source
    assert "PluginLoader" not in tree_source
    assert "NestedPluginHost" not in tree_source
    assert "ProjectScopedPluginHost" not in tree_source
    assert "InMemoryRuntimeCapabilityRegistry" not in tree_source
    assert "resolve_plugin_host" in tree_source
