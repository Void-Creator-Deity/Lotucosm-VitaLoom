"""Qt-free contract for package catalog rules."""
from __future__ import annotations

from builtin.editor_extensions.package_domain.catalog import (
    collect_update_candidates,
    matches_status_filter,
    merge_package_lists,
    normalize_package,
    parse_dependency_expr,
    parse_version,
    select_target_updates,
    should_block_enable,
    version_gte,
)


def test_normalize_package_supplies_catalog_defaults() -> None:
    package = normalize_package({"id": "pkg.alpha", "display_name": "Alpha"}, "builtin")
    assert package["source"] == "builtin"
    assert package["dependencies"] == []
    assert package["conflicts"] == []
    assert package["plugins"] == []


def test_merge_package_lists_obeys_source_priority_and_stable_order() -> None:
    merged = merge_package_lists(
        [
            [{"id": "pkg.alpha", "display_name": "Alpha", "source": "url", "version": "2.0.0"}],
            [{"id": "pkg.alpha", "display_name": "Alpha", "source": "builtin", "version": "1.0.0"}],
            [{"id": "pkg.beta", "display_name": "Beta", "source": "file", "version": "1.0.0"}],
        ],
        ["builtin", "file", "url", "unknown"],
    )
    assert [(item["id"], item["version"]) for item in merged] == [
        ("pkg.alpha", "1.0.0"),
        ("pkg.beta", "1.0.0"),
    ]


def test_dependency_and_version_contracts_match_package_manager_semantics() -> None:
    assert parse_dependency_expr("pkg.core>=1.2.3") == ("pkg.core", ">=", "1.2.3")
    assert parse_version("1.2") == (1, 2, 0)
    assert version_gte("1.2.0", "1.1.9")
    assert not version_gte("0.9.9", "1.0.0")
    assert not should_block_enable("warn", True)
    assert should_block_enable("block", True)
    assert not should_block_enable("fail-fast", True)


def test_status_filter_and_updates_are_not_ui_bound() -> None:
    assert matches_status_filter(False, False, "enabled", implicitly_enabled=True)
    assert not matches_status_filter(True, False, "disabled", implicitly_enabled=True)
    assert matches_status_filter(False, True, "issues")
    updates = collect_update_candidates(
        [
            [{"id": "pkg.alpha", "version": "1.0.0"}],
            [{"id": "pkg.alpha", "version": "1.2.0"}, {"id": "pkg.beta", "version": "2.0.0"}],
        ],
        [{"id": "pkg.alpha", "version": "1.0.0"}, {"id": "pkg.beta", "version": "2.0.0"}],
    )
    assert updates == {"pkg.alpha": "1.2.0"}
    assert select_target_updates({"pkg.alpha": "1.2.0", "pkg.beta": "2.0.0"}, {"pkg.beta"}) == {
        "pkg.beta": "2.0.0"
    }