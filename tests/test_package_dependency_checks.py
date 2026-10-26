"""Qt-free package dependency, version, filtering, and update contracts."""
from __future__ import annotations

from builtin.editor_extensions.package_domain.catalog import (
    apply_version_overrides,
    collect_update_candidates,
    matches_status_filter,
    parse_dependency_expr,
    select_target_updates,
    should_block_enable,
    version_gte,
)
from builtin.editor_extensions.package_domain.resolver import resolve_dependency_graph


def test_parse_dependency_expr() -> None:
    assert parse_dependency_expr("pkg.core>=1.2.3") == ("pkg.core", ">=", "1.2.3")


def test_version_gte() -> None:
    assert version_gte("1.2.0", "1.1.9")
    assert version_gte("1.0.0", "1.0.0")
    assert not version_gte("0.9.9", "1.0.0")


def test_should_block_enable_only_in_block_mode() -> None:
    assert not should_block_enable("warn", True)
    assert should_block_enable("block", True)
    assert not should_block_enable("block", False)


def test_dependency_graph_reports_disabled_dependency() -> None:
    lookup = {
        "pkg.base": {"id": "pkg.base", "version": "1.0.0"},
        "pkg.target": {"id": "pkg.target", "version": "1.0.0", "dependencies": ["pkg.base>=1.0.0"]},
    }

    order, issues = resolve_dependency_graph("pkg.target", lookup, {"pkg.target"})

    assert order == ["pkg.base", "pkg.target"]
    assert issues == ["disabled dependency: pkg.base>=1.0.0"]


def test_matches_status_filter() -> None:
    assert matches_status_filter(True, False, "enabled")
    assert matches_status_filter(False, False, "disabled")
    assert matches_status_filter(False, True, "issues")
    assert not matches_status_filter(False, False, "issues")


def test_collect_update_candidates() -> None:
    loaded_lists = [
        [{"id": "pkg.a", "version": "1.0.0"}],
        [{"id": "pkg.a", "version": "1.2.0"}, {"id": "pkg.b", "version": "2.0.0"}],
    ]
    merged = [{"id": "pkg.a", "version": "1.0.0"}, {"id": "pkg.b", "version": "2.0.0"}]

    assert collect_update_candidates(loaded_lists, merged) == {"pkg.a": "1.2.0"}


def test_apply_project_version_overrides() -> None:
    merged = [{"id": "pkg.a", "version": "1.0.0"}, {"id": "pkg.b", "version": "2.0.0"}]

    assert apply_version_overrides(merged, {"pkg.a": "1.2.0"}) == [
        {"id": "pkg.a", "version": "1.2.0"},
        {"id": "pkg.b", "version": "2.0.0"},
    ]


def test_select_target_updates() -> None:
    updates = {"pkg.a": "1.2.0", "pkg.b": "2.0.0"}

    assert select_target_updates(updates, {"pkg.b"}) == {"pkg.b": "2.0.0"}
    assert select_target_updates(updates, set()) == updates