# -*- coding: utf-8 -*-
"""Product registry access from inside the product runtime."""
from __future__ import annotations

from pathlib import Path

from FrameCore.product_registry import (
    ProductManifest,
    ProductRegistry,
    ProductVersion,
    load_product_registry as _load_product_registry,
)


def _as_suite_root(root: str | Path) -> Path:
    path = Path(root).resolve()
    if (path / "plugin_manifest.json").is_file():
        return path
    candidate = path / "FrameCore" / "plugins" / "lotucosm-vitaloom"
    if candidate.is_dir():
        return candidate
    from core.VitaLoom.core.bundle_paths import suite_root

    return suite_root()


def load_product_registry(root: str | Path) -> ProductRegistry:
    return _load_product_registry(_as_suite_root(root))
