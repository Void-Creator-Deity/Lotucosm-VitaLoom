# -*- coding: utf-8 -*-
"""E11 Project World capability catalog and legacy consumer decoupling."""
from __future__ import annotations

import builtins
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


_QAPPLICATION = None

RUNTIME_ROOT = (
    Path(__file__).resolve().parents[1]
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
)


class _Services:
    def __init__(self) -> None:
        self.items: dict[str, object] = {}

    def register(self, key: str, value: object) -> None:
        self.items[str(key)] = value

    def unregister(self, key: str) -> None:
        self.items.pop(str(key), None)

    def get(self, key: str, default=None):
        return self.items.get(str(key), default)

    def has(self, key: str) -> bool:
        return str(key) in self.items


class _TestProjectWorldHost:
    """Second functional Adapter used to prove the capability seams."""

    def __init__(self, project: Path) -> None:
        self.project = project
        self.config = {
            "name": project.name,
            "presentation": {"tagline_zh": "测试莲池"},
            "disabled_plugins": [],
        }
        self.created: list[tuple[str, str, str | None, str]] = []
        self.validation_count = 0

    def get_current_project_path(self):
        return str(self.project)

    def get_current_project_config(self):
        return self.config

    def update_project_config_fields(self, fields):
        self.config.update(dict(fields))
        return True

    def get_recent_projects(self):
        return [str(self.project), str(self.project / "other")]

    def get_available_templates(self):
        return ["blank", "ecosystem"]

    def create_project(self, project_name, project_path=None, template=None, description=""):
        self.created.append((project_name, str(project_path or ""), template, description))
        return str(Path(project_path or self.project.parent) / project_name)

    def refresh_current_project_manifest_validation(self):
        self.validation_count += 1
        return {
            "status": "validated",
            "project_path": str(self.project),
            "missing_packages": [],
        }


def _block_pyqt_imports(monkeypatch) -> None:
    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError(f"unexpected PyQt import: {name}")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)


def test_capability_catalog_is_qt_free_narrow_and_detached(tmp_path, monkeypatch) -> None:
    _block_pyqt_imports(monkeypatch)
    sys.modules.pop("core.VitaLoom.project.project_world_capabilities", None)

    from core.VitaLoom.project.project_world_capabilities import (
        PROJECT_WORLD_CONFIGURATION_HOST,
        PROJECT_WORLD_CREATION_HOST,
        PROJECT_WORLD_MANIFEST_VALIDATION_HOST,
        PROJECT_WORLD_READ_MODEL,
        PROJECT_WORLD_RECENT_REGISTRY,
        get_project_world_configuration_host,
        get_project_world_creation_host,
        get_project_world_manifest_validation_host,
        get_project_world_read_model,
        get_recent_project_world_registry,
        register_project_world_host_capabilities,
    )

    concrete = _TestProjectWorldHost(tmp_path / "world")
    services = _Services()
    registered = register_project_world_host_capabilities(services, concrete)
    context = SimpleNamespace(services=services)

    assert set(registered) == {
        PROJECT_WORLD_READ_MODEL,
        PROJECT_WORLD_CONFIGURATION_HOST,
        PROJECT_WORLD_RECENT_REGISTRY,
        PROJECT_WORLD_CREATION_HOST,
        PROJECT_WORLD_MANIFEST_VALIDATION_HOST,
    }
    assert all(value is not concrete for value in registered.values())
    assert len({id(value) for value in registered.values()}) == 5

    reader = get_project_world_read_model(context)
    config = reader.current_project_world_config()
    config["presentation"]["tagline_zh"] = "mutated"
    assert concrete.config["presentation"]["tagline_zh"] == "测试莲池"
    assert reader.current_project_world_path() == str((tmp_path / "world").resolve())
    json.dumps(config, ensure_ascii=False, allow_nan=False)

    writer = get_project_world_configuration_host(context)
    assert writer.update_current_project_world_config_fields({"disabled_plugins": ["x"]})
    assert concrete.config["disabled_plugins"] == ["x"]

    recent = get_recent_project_world_registry(context)
    assert recent.recent_project_world_paths()[0] == str((tmp_path / "world").resolve())

    creator = get_project_world_creation_host(context)
    assert creator.available_project_world_templates() == ("blank", "ecosystem")
    created = creator.create_project_world("new", str(tmp_path), "blank", "desc")
    assert created == str((tmp_path / "new").resolve())

    manifest = get_project_world_manifest_validation_host(context)
    report = manifest.refresh_current_project_manifest_validation()
    assert report["status"] == "validated"
    assert concrete.validation_count == 1


def test_partial_host_registers_only_complete_capability_groups(tmp_path) -> None:
    from core.VitaLoom.project.project_world_capabilities import (
        PROJECT_WORLD_READ_MODEL,
        get_project_world_configuration_host,
        get_project_world_read_model,
        register_project_world_host_capabilities,
    )

    class ReadOnlyHost:
        def get_current_project_path(self):
            return str(tmp_path / "world")

        def get_current_project_config(self):
            return {"name": "read-only"}

    services = _Services()
    registered = register_project_world_host_capabilities(services, ReadOnlyHost())
    context = SimpleNamespace(services=services)

    assert set(registered) == {PROJECT_WORLD_READ_MODEL}
    assert get_project_world_read_model(context).current_project_world_config() == {
        "name": "read-only"
    }
    assert not get_project_world_configuration_host(
        context
    ).update_current_project_world_config_fields({"name": "blocked"})

    class IncompleteReadHost:
        def get_current_project_path(self):
            return str(tmp_path / "broken")

    with pytest.raises(TypeError, match="incomplete project_world.read_model"):
        register_project_world_host_capabilities(_Services(), IncompleteReadHost())

def test_unavailable_capabilities_are_deterministic_without_gui_context(monkeypatch) -> None:
    _block_pyqt_imports(monkeypatch)
    sys.modules.pop("core.VitaLoom.project.project_world_capabilities", None)

    from core.VitaLoom.project.project_world_capabilities import (
        get_project_world_configuration_host,
        get_project_world_creation_host,
        get_project_world_manifest_validation_host,
        get_project_world_read_model,
        get_recent_project_world_registry,
    )

    context = SimpleNamespace(services=_Services())
    assert get_project_world_read_model(context).current_project_world_path() == ""
    assert get_project_world_read_model(context).current_project_world_config() == {}
    assert not get_project_world_configuration_host(
        context
    ).update_current_project_world_config_fields({"x": 1})
    assert get_recent_project_world_registry(context).recent_project_world_paths() == ()
    assert get_project_world_creation_host(context).available_project_world_templates() == ()
    assert get_project_world_creation_host(context).create_project_world("x") is None
    assert get_project_world_manifest_validation_host(
        context
    ).refresh_current_project_manifest_validation() == {
        "status": "unavailable",
        "code": "project_world_manifest_validation_host_unavailable",
        "project_path": "",
        "missing_packages": [],
    }


def test_package_operation_service_accepts_only_read_and_configuration_capabilities(tmp_path) -> None:
    from builtin.editor_extensions.package_services import PackageOperationService
    from core.VitaLoom.project.project_world_capabilities import (
        get_project_world_configuration_host,
        get_project_world_read_model,
        register_project_world_host_capabilities,
    )

    concrete = _TestProjectWorldHost(tmp_path / "world")
    services = _Services()
    register_project_world_host_capabilities(services, concrete)
    context = SimpleNamespace(services=services)
    operations = PackageOperationService(
        get_project_world_read_model(context),
        get_project_world_configuration_host(context),
    )

    assert operations.get_disabled_plugins() == []
    assert operations.write_disabled_plugins(["plugin.demo"])
    assert operations.get_disabled_plugins() == ["plugin.demo"]
    assert not hasattr(operations, "project_manager")


def test_real_pyqt_project_manager_registers_as_legacy_adapter(tmp_path) -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    global _QAPPLICATION
    _QAPPLICATION = QApplication.instance() or QApplication([])
    assert _QAPPLICATION is not None

    from core.VitaLoom.core.editor_context import get_editor_context
    from core.VitaLoom.project.project_manager import ProjectManager
    from core.VitaLoom.project.project_world_capabilities import (
        get_project_world_read_model,
        register_project_world_host_capabilities,
    )

    context = get_editor_context()
    context._ensure_qobject_initialized()
    context.current_project_path = str(tmp_path.resolve())
    context.current_project_config = {"name": "real-host"}
    ProjectManager._instance = None
    manager = ProjectManager()
    registered = register_project_world_host_capabilities(context.services, manager)

    reader = get_project_world_read_model(context)
    assert reader is registered["project_world.read_model"]
    assert reader is not manager
    assert reader.current_project_world_path() == str(tmp_path.resolve())
    assert reader.current_project_world_config() == {"name": "real-host"}

    context.current_project_path = None
    context.current_project_config = None
    ProjectManager._instance = None


def test_migrated_consumers_do_not_import_concrete_project_manager() -> None:
    migrated = [
        "builtin/editor_extensions/standard_ui_plugin.py",
        "builtin/editor_extensions/plugin_runtime_ops.py",
        "builtin/editor_extensions/package_manager_plugin.py",
        "core/VitaLoom/feedback/sr_session_feedback.py",
        "core/VitaLoom/project/asset_dependency.py",
        "core/VitaLoom/project/evolution_context.py",
        "core/VitaLoom/project/project_wizard.py",
        "core/VitaLoom/viewports/game_viewport.py",
    ]
    for relative in migrated:
        source = (RUNTIME_ROOT / relative).read_text(encoding="utf-8-sig")
        assert "project.project_manager" not in source, relative
        assert "get_project_manager" not in source, relative

    standard_ui = (RUNTIME_ROOT / migrated[0]).read_text(encoding="utf-8-sig")
    assert "recent_projects_changed" not in standard_ui
    assert "_recent_project_menu_items" not in standard_ui

    package_manager = (RUNTIME_ROOT / migrated[2]).read_text(encoding="utf-8-sig")
    assert "_validate_and_apply_project_manifest" not in package_manager
