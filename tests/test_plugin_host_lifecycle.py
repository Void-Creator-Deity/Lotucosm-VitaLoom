# -*- coding: utf-8 -*-
"""Qt-free downstream extension lifecycle authority tests."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


def _entry(
    plugin_id: str,
    *,
    deps: tuple[str, ...] = (),
    scope: str = "official_mod",
    source: str | None = None,
    protected: bool = False,
):
    from core.VitaLoom.project.plugin_host_lifecycle import PluginHostCatalogEntry

    return PluginHostCatalogEntry(
        plugin_id=plugin_id,
        scope=scope,
        source=source or f"/{scope}/{plugin_id}.py",
        version="1.0.0",
        dependencies=deps,
        protected=protected,
    )


def test_lifecycle_plan_is_dependency_first_and_reverse_dependency_on_deactivate() -> None:
    from core.VitaLoom.project.plugin_host_lifecycle import build_plugin_lifecycle_plan

    catalog = [
        _entry("BasePlugin"),
        _entry("MiddlePlugin", deps=("BasePlugin",)),
        _entry("LeafPlugin", deps=("MiddlePlugin",)),
        _entry("OtherPlugin"),
    ]

    activate = build_plugin_lifecycle_plan(
        catalog,
        active_plugin_ids={"OtherPlugin"},
        requested_plugin_ids={"LeafPlugin"},
    )
    assert activate.ok is True
    assert activate.target_plugin_ids == ("BasePlugin", "MiddlePlugin", "LeafPlugin")
    assert activate.deactivate_plugin_ids == ("OtherPlugin",)
    assert activate.activate_plugin_ids == ("BasePlugin", "MiddlePlugin", "LeafPlugin")

    deactivate = build_plugin_lifecycle_plan(
        catalog,
        active_plugin_ids={"BasePlugin", "MiddlePlugin", "LeafPlugin"},
        requested_plugin_ids={"BasePlugin"},
    )
    assert deactivate.ok is True
    assert deactivate.deactivate_plugin_ids == ("LeafPlugin", "MiddlePlugin")
    assert deactivate.activate_plugin_ids == ()


def test_missing_dependency_and_cycle_block_all_transition_actions() -> None:
    from core.VitaLoom.project.plugin_host_lifecycle import build_plugin_lifecycle_plan

    missing = build_plugin_lifecycle_plan(
        [_entry("BrokenPlugin", deps=("AbsentPlugin",))],
        active_plugin_ids=set(),
        requested_plugin_ids={"BrokenPlugin"},
    )
    assert missing.ok is False
    assert missing.activate_plugin_ids == ()
    assert missing.deactivate_plugin_ids == ()
    assert [item.code for item in missing.diagnostics] == ["plugin_dependency_missing"]

    cycle = build_plugin_lifecycle_plan(
        [
            _entry("AlphaPlugin", deps=("BetaPlugin",)),
            _entry("BetaPlugin", deps=("AlphaPlugin",)),
        ],
        active_plugin_ids=set(),
        requested_plugin_ids={"AlphaPlugin"},
    )
    assert cycle.ok is False
    assert cycle.activate_plugin_ids == ()
    assert cycle.deactivate_plugin_ids == ()
    assert [item.code for item in cycle.diagnostics] == ["plugin_dependency_cycle"]


def test_equal_priority_source_collision_blocks_but_higher_priority_source_wins() -> None:
    from core.VitaLoom.project.plugin_host_lifecycle import build_plugin_lifecycle_plan

    collision = build_plugin_lifecycle_plan(
        [
            _entry("SamePlugin", scope="user_mod", source="/a/same_plugin.py"),
            _entry("SamePlugin", scope="user_mod", source="/b/same_plugin.py"),
        ],
        active_plugin_ids=set(),
        requested_plugin_ids={"SamePlugin"},
    )
    assert collision.ok is False
    assert [item.code for item in collision.diagnostics] == ["plugin_source_collision"]

    priority = build_plugin_lifecycle_plan(
        [
            _entry("SamePlugin", scope="user_mod", source="/user/same_plugin.py"),
            _entry("SamePlugin", scope="official_mod", source="/official/same_plugin.py"),
        ],
        active_plugin_ids=set(),
        requested_plugin_ids={"SamePlugin"},
    )
    assert priority.ok is True
    assert priority.activate_plugin_ids == ("SamePlugin",)
    assert priority.catalog[0].scope == "official_mod"
    assert [item.code for item in priority.diagnostics] == ["lower_priority_source_ignored"]


def test_protected_plugin_is_retained_and_reported() -> None:
    from core.VitaLoom.project.plugin_host_lifecycle import build_plugin_lifecycle_plan

    plan = build_plugin_lifecycle_plan(
        [_entry("ProtectedPlugin", protected=True), _entry("RequestedPlugin")],
        active_plugin_ids={"ProtectedPlugin"},
        requested_plugin_ids={"RequestedPlugin"},
    )
    assert plan.ok is True
    assert plan.retained_plugin_ids == ("ProtectedPlugin",)
    assert plan.deactivate_plugin_ids == ()
    assert plan.activate_plugin_ids == ("RequestedPlugin",)
    assert [item.code for item in plan.diagnostics] == ["protected_plugin_retained"]


def _write_addon(
    project: Path,
    *,
    folder: str = "example",
    plugin_id: str = "ExamplePlugin",
    version: str = "1.2.3",
    runtime_constraint: str = ">=1.0.0,<2.0.0",
    entry: str = "example_plugin.py",
    dependencies: list[str] | None = None,
) -> Path:
    addon = project / "addons" / folder
    addon.mkdir(parents=True, exist_ok=True)
    (addon / entry).write_text("# adapter imports this later\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "id": plugin_id,
        "version": version,
        "entry": entry,
        "runtime": {
            "plugin_id": "lotucosm-vitaloom",
            "version": runtime_constraint,
        },
        "dependencies": dependencies or [],
    }
    (addon / "plugin.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return addon


def test_project_addon_manifest_discovery_is_contained_versioned_and_deterministic(
    tmp_path: Path,
) -> None:
    from core.VitaLoom.project.plugin_host_lifecycle import discover_project_addons

    project = tmp_path / "world"
    project.mkdir()
    _write_addon(
        project,
        plugin_id="ExamplePlugin",
        dependencies=["BasePlugin"],
    )

    result = discover_project_addons(project, runtime_version="1.0.0")
    assert result.ok is True
    assert len(result.sources) == 1
    source = result.sources[0]
    assert source.plugin_id == "ExamplePlugin"
    assert source.version == "1.2.3"
    assert source.dependencies == ("BasePlugin",)
    assert source.scope == "embedded_mod"
    assert source.entry_path == (project / "addons" / "example" / "example_plugin.py").resolve()
    assert result.to_dict()["status"] == "ready"


def test_project_addon_manifest_failures_are_closed_before_import(tmp_path: Path) -> None:
    from core.VitaLoom.project.plugin_host_lifecycle import discover_project_addons

    project = tmp_path / "world"
    project.mkdir()
    addon = project / "addons" / "broken"
    addon.mkdir(parents=True)
    (addon / "broken_plugin.py").write_text("raise AssertionError('must not import')\n", encoding="utf-8")

    missing = discover_project_addons(project, runtime_version="1.0.0")
    assert missing.ok is False
    assert [item.code for item in missing.diagnostics] == ["addon_manifest_missing"]

    (addon / "plugin.json").write_text("{", encoding="utf-8")
    malformed = discover_project_addons(project, runtime_version="1.0.0")
    assert malformed.ok is False
    assert [item.code for item in malformed.diagnostics] == ["addon_manifest_malformed"]

    _write_addon(project, folder="broken", plugin_id="BrokenPlugin", runtime_constraint=">=2.0.0")
    incompatible = discover_project_addons(project, runtime_version="1.0.0")
    assert incompatible.ok is False
    assert [item.code for item in incompatible.diagnostics] == ["addon_runtime_incompatible"]


def test_project_addon_entry_traversal_and_duplicate_ids_fail_closed(tmp_path: Path) -> None:
    from core.VitaLoom.project.plugin_host_lifecycle import discover_project_addons

    project = tmp_path / "world"
    project.mkdir()
    outside = project / "outside_plugin.py"
    outside.write_text("# outside\n", encoding="utf-8")
    addon = project / "addons" / "escape"
    addon.mkdir(parents=True)
    (addon / "plugin.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "EscapePlugin",
                "version": "1.0.0",
                "entry": "../../outside_plugin.py",
                "runtime": {"plugin_id": "lotucosm-vitaloom", "version": "1.0.0"},
                "dependencies": [],
            }
        ),
        encoding="utf-8",
    )
    escaped = discover_project_addons(project, runtime_version="1.0.0")
    assert escaped.ok is False
    assert [item.code for item in escaped.diagnostics] == ["addon_entry_invalid"]

    for child in (project / "addons").iterdir():
        if child.is_dir():
            for path in child.iterdir():
                path.unlink()
            child.rmdir()
    _write_addon(project, folder="one", plugin_id="DuplicatePlugin", entry="one_plugin.py")
    _write_addon(project, folder="two", plugin_id="DuplicatePlugin", entry="two_plugin.py")
    duplicate = discover_project_addons(project, runtime_version="1.0.0")
    assert duplicate.ok is False
    assert [item.code for item in duplicate.diagnostics] == ["addon_plugin_id_duplicate"]

def test_symlinked_project_addon_root_fails_closed_when_supported(tmp_path: Path) -> None:
    from core.VitaLoom.project.plugin_host_lifecycle import discover_project_addons

    project = tmp_path / "world"
    addons = project / "addons"
    addons.mkdir(parents=True)
    external = tmp_path / "external_addon"
    external.mkdir()
    (external / "external_plugin.py").write_text("# external\n", encoding="utf-8")
    try:
        os.symlink(external, addons / "linked", target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"directory symlink unavailable in this Windows session: {exc}")

    result = discover_project_addons(project, runtime_version="1.0.0")
    assert result.ok is False
    assert [item.code for item in result.diagnostics] == [
        "addon_root_symlink_rejected"
    ]


