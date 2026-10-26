# -*- coding: utf-8 -*-
"""Product runtime bootstrap validation."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from FrameCore.product_registry import ProductRegistry, ProductVersion, load_product_registry
from FrameCore.suite_registry import SuiteManifest, load_suite_manifest


DEFAULT_PRODUCT_ID = "lotucosm-vitaloom"


@dataclass(frozen=True)
class SuiteRuntime:
    root: Path
    suite: SuiteManifest
    products: ProductRegistry
    product_version: ProductVersion


def _suite_root() -> Path:
    raw = os.environ.get("VITALOOM_SUITE_ROOT")
    if raw:
        return Path(raw).resolve()
    from core.VitaLoom.core.bundle_paths import suite_root

    return suite_root()


def _product_version_root() -> Path:
    raw = os.environ.get("VITALOOM_PRODUCT_VERSION_ROOT")
    if raw:
        return Path(raw).resolve()
    from core.VitaLoom.core.bundle_paths import product_version_root

    return product_version_root()


def _entrypoint_exists(version: ProductVersion, command: str) -> bool:
    entry = str(command or "").strip()
    if not entry:
        return False
    return (version.version_root / entry.split(" ", 1)[0]).exists()


def bootstrap_suite_runtime(
    _root: str | Path | None = None,
    *,
    product_id: str = DEFAULT_PRODUCT_ID,
) -> SuiteRuntime:
    suite_root = _suite_root()
    try:
        suite = load_suite_manifest(suite_root)
        registry = load_product_registry(suite_root)
    except (FileNotFoundError, ValueError) as exc:
        raise RuntimeError(f"invalid FrameCore plugin registry: {exc}") from exc
    if product_id not in suite.products:
        raise RuntimeError(f"suite does not expose product: {product_id}")
    product = registry.products.get(product_id)
    if product is None:
        raise RuntimeError(f"missing product manifest: {product_id}")
    selected_root = _product_version_root()
    version = None
    for candidate in product.versions:
        pv = registry.get_version(product_id, candidate)
        if pv is not None and pv.version_root == selected_root:
            version = pv
            break
    if version is None:
        version = registry.get_default_version(product_id)
    if version is None:
        raise RuntimeError(
            f"missing default product version: {product_id}@{product.default_version}"
        )
    missing = version.missing_physical_roots()
    if missing:
        raise RuntimeError(
            f"missing product physical_roots: {product_id}@{version.version} {missing}"
        )
    for name, command in sorted(version.entrypoints.items()):
        if not _entrypoint_exists(version, command):
            raise RuntimeError(
                f"missing product entrypoint: {product_id}@{version.version} "
                f"{name}={command}"
            )
    if suite.capability_catalog and not (suite_root / suite.capability_catalog).is_file():
        raise RuntimeError(f"missing capability catalog: {suite.capability_catalog}")
    if version.builtin_capability_index and not (
        version.version_root / version.builtin_capability_index
    ).is_file():
        raise RuntimeError(
            f"missing builtin capability index: {version.builtin_capability_index}"
        )
    return SuiteRuntime(
        root=version.runtime_root,
        suite=suite,
        products=registry,
        product_version=version,
    )
