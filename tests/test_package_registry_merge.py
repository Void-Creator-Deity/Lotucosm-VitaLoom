"""Qt-free package registry merge contract."""
from __future__ import annotations

from builtin.editor_extensions.package_domain.catalog import merge_package_lists


PRIORITY = ["builtin", "file", "url", "unknown"]


def test_merge_prefers_builtin_over_url() -> None:
    merged = merge_package_lists(
        [[{"id": "pkg.a", "display_name": "A-remote", "source": "url"}], [{"id": "pkg.a", "display_name": "A", "source": "builtin"}]],
        PRIORITY,
    )

    assert merged == [{"id": "pkg.a", "display_name": "A", "source": "builtin"}]


def test_merge_deduplicates_by_package_id() -> None:
    merged = merge_package_lists(
        [[{"id": "pkg.a", "display_name": "A", "source": "file"}, {"id": "pkg.b", "display_name": "B", "source": "file"}]],
        PRIORITY,
    )

    assert {package["id"] for package in merged} == {"pkg.a", "pkg.b"}