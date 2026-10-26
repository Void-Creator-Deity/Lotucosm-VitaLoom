"""Qt-free package conflict normalization contract."""
from __future__ import annotations

from builtin.editor_extensions.package_domain.catalog import normalize_package


def test_normalize_package_defaults_conflicts_to_empty_list() -> None:
    package = normalize_package({"id": "a", "display_name": "A"}, "builtin")

    assert package["conflicts"] == []