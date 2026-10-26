# -*- coding: utf-8 -*-
"""FrameCore 迁移收口回归：project lock 单一 Implementation 与 Hub 版本选择。"""
from __future__ import annotations

import importlib
import json
import sys
import types
from pathlib import Path

import pytest

from FrameCore import project_lock as frame_project_lock


def _write_product_plugin(root: Path, versions: tuple[str, ...], default: str) -> None:
    (root / "hub").mkdir(parents=True)
    (root / "plugin_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "plugin_id": "lotucosm-vitaloom",
                "suite_id": "lotucosm.vitaloom.suite",
                "product_id": "lotucosm-vitaloom",
                "entry": "hub",
                "default_version": default,
                "versions": list(versions),
            }
        ),
        encoding="utf-8",
    )
    for version in versions:
        version_root = root / "versions" / version
        runtime_root = version_root / "runtime"
        runtime_root.mkdir(parents=True)
        (runtime_root / "main.py").write_text("# test editor entry\n", encoding="utf-8")
        builtin_root = runtime_root / "builtin"
        builtin_root.mkdir()
        packages = [
            {"id": package_id, "version": "1.0.0"}
            for package_id in frame_project_lock.IMPLICIT_PACKAGES
        ]
        packages.append({"id": "versioned.capability", "version": version})
        (builtin_root / "package_index.json").write_text(
            json.dumps({"packages": packages}),
            encoding="utf-8",
        )
        (version_root / "version_manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "version": version,
                    "entrypoints": {"editor": "runtime/main.py --editor"},
                    "physical_roots": ["runtime"],
                    "builtin_capability_index": "runtime/builtin/package_index.json",
                }
            ),
            encoding="utf-8",
        )


def _write_project(project: Path, version: str) -> None:
    project.mkdir(parents=True)
    (project / "project.json").write_text(
        json.dumps({"name": "locked-project", "loom_editor_version": version}),
        encoding="utf-8",
    )
    (project / "project.lock.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "resolved_suite": {"id": "lotucosm.vitaloom.suite", "version": "1.0.0"},
                "resolved_product": {"id": "lotucosm-vitaloom", "version": version},
                "resolved_capabilities": {
                    package_id: "1.0.0"
                    for package_id in frame_project_lock.IMPLICIT_PACKAGES
                },
            }
        ),
        encoding="utf-8",
    )


def _import_hub_launcher():
    try:
        return importlib.import_module("hub.hub_launcher")
    except ModuleNotFoundError as exc:
        if exc.name != "PyQt6":
            raise
        qt = types.ModuleType("PyQt6")
        qt_core = types.ModuleType("PyQt6.QtCore")
        qt_widgets = types.ModuleType("PyQt6.QtWidgets")
        qt_core.QProcess = type("QProcess", (), {})
        qt_core.QProcessEnvironment = type("QProcessEnvironment", (), {})
        qt_widgets.QMessageBox = type("QMessageBox", (), {})
        qt_widgets.QWidget = type("QWidget", (), {})
        sys.modules.update(
            {
                "PyQt6": qt,
                "PyQt6.QtCore": qt_core,
                "PyQt6.QtWidgets": qt_widgets,
            }
        )
        return importlib.import_module("hub.hub_launcher")


def test_runtime_project_lock_is_a_framecore_compatibility_adapter() -> None:
    runtime_project_lock = importlib.import_module("core.VitaLoom.suite.project_lock")
    assert runtime_project_lock.ProjectRuntimeResolution is frame_project_lock.ProjectRuntimeResolution
    assert runtime_project_lock.resolve_project_runtime is frame_project_lock.resolve_project_runtime
    assert runtime_project_lock.build_project_lock is frame_project_lock.build_project_lock


def test_framecore_project_lock_recognizes_project_installed_capability(tmp_path: Path) -> None:
    package_id = "community.example.capability"
    project_data = {
        "name": "installed-capability",
        "required_packages": [package_id],
        "package_state": {"installed": {package_id: {"version": "2.3.4"}}},
    }
    project = tmp_path / "project"
    project.mkdir()
    (project / "project.json").write_text(json.dumps(project_data), encoding="utf-8")

    lock = frame_project_lock.build_project_lock(project_data, repo_root=Path(__file__).resolve().parents[1])
    assert lock["resolved_capabilities"][package_id] == "2.3.4"

    (project / "project.lock.json").write_text(json.dumps(lock), encoding="utf-8")
    resolved = frame_project_lock.resolve_project_runtime(
        project, repo_root=Path(__file__).resolve().parents[1]
    )
    assert package_id not in resolved.missing_capabilities
    assert package_id not in resolved.capability_version_mismatches
    assert resolved.lock_status_text == "已锁定"


def test_framecore_uses_locked_product_version_capability_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plugin_root = tmp_path / "FrameCore" / "plugins" / "lotucosm-vitaloom"
    _write_product_plugin(plugin_root, ("1.0.0", "2.0.0"), "1.0.0")
    monkeypatch.setenv("VITALOOM_SUITE_ROOT", str(plugin_root))
    project_data = {
        "name": "versioned-catalog",
        "loom_editor_version": "2.0.0",
        "required_packages": ["versioned.capability"],
    }

    lock = frame_project_lock.build_project_lock(project_data, repo_root=tmp_path)

    assert lock["resolved_product"]["version"] == "2.0.0"
    assert lock["resolved_capabilities"]["versioned.capability"] == "2.0.0"


def test_exported_runtime_resolution_does_not_require_plugin_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_root = tmp_path / "runtime"
    builtin_root = runtime_root / "builtin"
    builtin_root.mkdir(parents=True)
    packages = [
        {"id": package_id, "version": "1.0.0"}
        for package_id in frame_project_lock.IMPLICIT_PACKAGES
    ]
    (builtin_root / "package_index.json").write_text(
        json.dumps({"packages": packages}), encoding="utf-8"
    )
    project = tmp_path / "project"
    _write_project(project, "1.0.0")
    lock = json.loads((project / "project.lock.json").read_text(encoding="utf-8"))
    lock["resolved_capabilities"] = {
        package["id"]: package["version"] for package in packages
    }
    (project / "project.lock.json").write_text(json.dumps(lock), encoding="utf-8")
    monkeypatch.setenv("VITALOOM_EXPORT_ROOT", str(tmp_path))

    resolved = frame_project_lock.resolve_project_runtime(project, repo_root=runtime_root)

    assert resolved.product_version == "1.0.0"
    assert not resolved.product_version_missing
    assert not resolved.has_blocking_issues
    assert resolved.lock_status_text == "已锁定"


def test_hub_editor_command_uses_project_locked_product_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plugin_root = tmp_path / "FrameCore" / "plugins" / "lotucosm-vitaloom"
    _write_product_plugin(plugin_root, ("1.0.0", "2.0.0"), "1.0.0")
    project = tmp_path / "workspace" / "projects" / "locked"
    _write_project(project, "2.0.0")
    monkeypatch.setenv("VITALOOM_APP_ROOT", str(tmp_path))
    monkeypatch.setenv("VITALOOM_SUITE_ROOT", str(plugin_root))

    launcher = _import_hub_launcher()
    _program, args, selected = launcher.editor_subprocess_command(str(project))

    assert selected.version == "2.0.0"
    assert args[0] == str(plugin_root / "versions" / "2.0.0" / "runtime" / "main.py")


def test_hub_editor_command_resolves_unlocked_project_constraint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plugin_root = tmp_path / "FrameCore" / "plugins" / "lotucosm-vitaloom"
    _write_product_plugin(plugin_root, ("1.0.0", "2.0.0"), "1.0.0")
    project = tmp_path / "workspace" / "projects" / "unlocked"
    project.mkdir(parents=True)
    (project / "project.json").write_text(
        json.dumps({"name": "unlocked", "loom_editor_version": "2.0.0"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("VITALOOM_APP_ROOT", str(tmp_path))
    monkeypatch.setenv("VITALOOM_SUITE_ROOT", str(plugin_root))

    launcher = _import_hub_launcher()
    _program, args, selected = launcher.editor_subprocess_command(str(project))

    assert selected.version == "2.0.0"
    assert args[0] == str(plugin_root / "versions" / "2.0.0" / "runtime" / "main.py")


def test_hub_editor_command_rejects_missing_locked_product_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plugin_root = tmp_path / "FrameCore" / "plugins" / "lotucosm-vitaloom"
    _write_product_plugin(plugin_root, ("1.0.0",), "1.0.0")
    project = tmp_path / "workspace" / "projects" / "missing-version"
    _write_project(project, "9.0.0")
    monkeypatch.setenv("VITALOOM_APP_ROOT", str(tmp_path))
    monkeypatch.setenv("VITALOOM_SUITE_ROOT", str(plugin_root))

    launcher = _import_hub_launcher()
    with pytest.raises(RuntimeError, match="9\\.0\\.0"):
        launcher.editor_subprocess_command(str(project))


def test_hub_editor_command_rejects_blocking_capability_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plugin_root = tmp_path / "FrameCore" / "plugins" / "lotucosm-vitaloom"
    _write_product_plugin(plugin_root, ("1.0.0",), "1.0.0")
    project = tmp_path / "workspace" / "projects" / "missing-capability"
    _write_project(project, "1.0.0")
    data = json.loads((project / "project.json").read_text(encoding="utf-8"))
    data["required_capabilities"] = {"versioned.capability": ">=1.0.0"}
    (project / "project.json").write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setenv("VITALOOM_APP_ROOT", str(tmp_path))
    monkeypatch.setenv("VITALOOM_SUITE_ROOT", str(plugin_root))

    launcher = _import_hub_launcher()
    with pytest.raises(RuntimeError, match="missing capabilities"):
        launcher.editor_subprocess_command(str(project))
