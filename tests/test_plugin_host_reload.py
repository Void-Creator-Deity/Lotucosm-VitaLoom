# -*- coding: utf-8 -*-
"""Qt-free hot-reload planning authority for L3 engine extensions."""
from __future__ import annotations

from pathlib import Path

import pytest


def _entry(
    plugin_id: str,
    *,
    scope: str = "user_mod",
    dependencies: tuple[str, ...] = (),
    protected: bool = False,
):
    from core.VitaLoom.project.plugin_host_lifecycle import PluginHostCatalogEntry

    return PluginHostCatalogEntry(
        plugin_id=plugin_id,
        scope=scope,
        source=f"/plugins/{plugin_id}.py",
        version="1.0.0",
        dependencies=dependencies,
        protected=protected,
    )


def test_active_reload_orders_dependents_and_new_dependency() -> None:
    from core.VitaLoom.project.plugin_host_reload import build_plugin_reload_plan

    catalog = [
        _entry("BasePlugin"),
        _entry("TargetPlugin", dependencies=("BasePlugin",)),
        _entry("MiddlePlugin", dependencies=("TargetPlugin",)),
        _entry("LeafPlugin", dependencies=("MiddlePlugin",)),
        _entry("NewDependencyPlugin"),
    ]
    candidate = _entry(
        "TargetPlugin",
        dependencies=("BasePlugin", "NewDependencyPlugin"),
    )

    plan = build_plugin_reload_plan(
        catalog,
        target_plugin_id="TargetPlugin",
        candidate=candidate,
        active_plugin_ids={"BasePlugin", "TargetPlugin", "MiddlePlugin", "LeafPlugin"},
    )

    assert plan.ok is True
    assert plan.target_was_active is True
    assert plan.affected_plugin_ids == (
        "TargetPlugin",
        "MiddlePlugin",
        "LeafPlugin",
    )
    assert plan.deactivate_plugin_ids == (
        "LeafPlugin",
        "MiddlePlugin",
        "TargetPlugin",
    )
    assert plan.activate_plugin_ids == (
        "NewDependencyPlugin",
        "TargetPlugin",
        "MiddlePlugin",
        "LeafPlugin",
    )
    assert plan.to_dict()["status"] == "ready"


def test_inactive_reload_replaces_registry_without_callbacks() -> None:
    from core.VitaLoom.project.plugin_host_reload import build_plugin_reload_plan

    current = _entry("TargetPlugin", dependencies=("BasePlugin",))
    candidate = _entry("TargetPlugin", dependencies=("BasePlugin",))
    plan = build_plugin_reload_plan(
        [_entry("BasePlugin"), current],
        target_plugin_id="TargetPlugin",
        candidate=candidate,
        active_plugin_ids={"BasePlugin"},
    )

    assert plan.ok is True
    assert plan.target_was_active is False
    assert plan.affected_plugin_ids == ()
    assert plan.deactivate_plugin_ids == ()
    assert plan.activate_plugin_ids == ()


@pytest.mark.parametrize(
    ("scope", "protected", "code"),
    [
        ("core_mod", False, "reload_scope_forbidden"),
        ("embedded_mod", False, "reload_scope_forbidden"),
        ("unknown", False, "reload_scope_forbidden"),
        ("user_mod", True, "reload_protected_plugin"),
    ],
)
def test_non_l3_or_protected_target_is_blocked(
    scope: str,
    protected: bool,
    code: str,
) -> None:
    from core.VitaLoom.project.plugin_host_reload import build_plugin_reload_plan

    current = _entry("TargetPlugin", scope=scope, protected=protected)
    plan = build_plugin_reload_plan(
        [current],
        target_plugin_id="TargetPlugin",
        candidate=current,
        active_plugin_ids={"TargetPlugin"},
    )

    assert plan.ok is False
    assert plan.deactivate_plugin_ids == ()
    assert plan.activate_plugin_ids == ()
    assert code in {item.code for item in plan.diagnostics}


def test_missing_candidate_dependency_blocks_before_mutation() -> None:
    from core.VitaLoom.project.plugin_host_reload import build_plugin_reload_plan

    current = _entry("TargetPlugin")
    candidate = _entry("TargetPlugin", dependencies=("MissingPlugin",))
    plan = build_plugin_reload_plan(
        [current],
        target_plugin_id="TargetPlugin",
        candidate=candidate,
        active_plugin_ids={"TargetPlugin"},
    )

    assert plan.ok is False
    assert plan.deactivate_plugin_ids == ()
    assert plan.activate_plugin_ids == ()
    assert "plugin_dependency_missing" in {item.code for item in plan.diagnostics}


def test_candidate_dependency_cycle_blocks_before_mutation() -> None:
    from core.VitaLoom.project.plugin_host_reload import build_plugin_reload_plan

    current = _entry("TargetPlugin")
    dependent = _entry("DependencyPlugin", dependencies=("TargetPlugin",))
    candidate = _entry("TargetPlugin", dependencies=("DependencyPlugin",))
    plan = build_plugin_reload_plan(
        [current, dependent],
        target_plugin_id="TargetPlugin",
        candidate=candidate,
        active_plugin_ids={"TargetPlugin"},
    )

    assert plan.ok is False
    assert "plugin_dependency_cycle" in {item.code for item in plan.diagnostics}


def test_reload_authority_module_is_qt_free() -> None:
    runtime = (
        Path(__file__).resolve().parents[1]
        / "FrameCore"
        / "plugins"
        / "lotucosm-vitaloom"
        / "versions"
        / "1.0.0"
        / "runtime"
    )
    source = (
        runtime / "core" / "VitaLoom" / "project" / "plugin_host_reload.py"
    ).read_text(encoding="utf-8")

    assert "PyQt" not in source
    assert "EditorContext" not in source
    assert "importlib" not in source


def test_hot_reload_failure_does_not_offer_project_lifecycle_recovery(tmp_path: Path) -> None:
    from core.VitaLoom.project.plugin_host_operator import build_plugin_host_inspection

    inspection = build_plugin_host_inspection(
        project_path=tmp_path,
        embedded_catalog_project_path=tmp_path,
        catalog_entries=[],
        active_plugin_ids=[],
        failed_plugins={},
        discovery_report={"status": "ready", "diagnostics": []},
        lifecycle_report={
            "status": "partial",
            "source": "hot_reload",
            "completed": {"deactivated": ["TargetPlugin"]},
            "diagnostics": [],
        },
    )

    assert inspection["status"] == "partial"
    assert inspection["recoveries"] == []
