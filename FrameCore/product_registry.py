# -*- coding: utf-8 -*-
"""Version registry for the Lotucosm-VitaLoom FrameCore plugin package."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProductVersion:
    product_id: str
    version: str
    version_root: Path = Path(".")
    entrypoints: dict[str, str] = field(default_factory=dict)
    physical_roots: tuple[str, ...] = ()
    builtin_capability_index: str = ""

    @property
    def runtime_root(self) -> Path:
        return self.version_root / "runtime"

    def entrypoint_path(self, name: str) -> Path:
        command = self.entrypoints.get(name, "")
        script = command.split(" ", 1)[0]
        return self.version_root / script

    def missing_physical_roots(self) -> list[str]:
        return [
            rel
            for rel in self.physical_roots
            if not (self.version_root / rel).exists()
        ]


@dataclass(frozen=True)
class ProductManifest:
    product_id: str
    default_version: str
    versions: tuple[str, ...]
    display_name: str = ""
    display_name_zh: str = ""
    kind: str = ""


@dataclass(frozen=True)
class ProductRegistry:
    suite_root: Path
    products: dict[str, ProductManifest]
    versions: dict[tuple[str, str], ProductVersion]

    def get_default_version(self, product_id: str) -> ProductVersion | None:
        product = self.products.get(product_id)
        if product is None:
            return None
        return self.versions.get((product_id, product.default_version))

    def get_version(self, product_id: str, version: str) -> ProductVersion | None:
        return self.versions.get((product_id, version))

    def has_version(self, product_id: str, version: str) -> bool:
        return (product_id, version) in self.versions


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def _manifest_path(plugin_root: Path) -> Path:
    return plugin_root / "plugin_manifest.json"


def _read_plugin_product(plugin_root: Path) -> tuple[ProductManifest, list[ProductVersion]]:
    manifest_path = _manifest_path(plugin_root)
    data = _load_json(manifest_path)
    product_id = str(data.get("product_id", "") or data.get("plugin_id", "") or "").strip()
    if not product_id:
        raise ValueError(f"{manifest_path} missing product_id")
    raw_versions = data.get("versions", [])
    if not isinstance(raw_versions, list) or not raw_versions:
        raise ValueError(f"{manifest_path} versions must be a non-empty list")
    versions = tuple(str(v or "").strip() for v in raw_versions if str(v or "").strip())
    default_version = str(data.get("default_version", "") or versions[0]).strip()
    product = ProductManifest(
        product_id=product_id,
        default_version=default_version,
        versions=versions,
        display_name=str(data.get("display_name", "") or ""),
        display_name_zh=str(data.get("display_name_zh", "") or ""),
        kind=str(data.get("kind", "") or ""),
    )
    loaded_versions: list[ProductVersion] = []
    for version in versions:
        version_root = plugin_root / "versions" / version
        version_path = version_root / "version_manifest.json"
        vdata = _load_json(version_path)
        roots = vdata.get("physical_roots", [])
        if not isinstance(roots, list):
            roots = []
        entrypoints = vdata.get("entrypoints", {})
        if not isinstance(entrypoints, dict):
            entrypoints = {}
        pv = ProductVersion(
            product_id=product_id,
            version=str(vdata.get("version", version) or version),
            version_root=version_root,
            entrypoints={str(k): str(v) for k, v in entrypoints.items()},
            physical_roots=tuple(str(r).replace("\\", "/") for r in roots),
            builtin_capability_index=str(vdata.get("builtin_capability_index", "") or ""),
        )
        if pv.version != version:
            raise ValueError(f"{version_path} version mismatch: {pv.version} != {version}")
        missing = pv.missing_physical_roots()
        if missing:
            raise ValueError(f"{version_path} missing physical_roots: {missing}")
        loaded_versions.append(pv)
    return product, loaded_versions


def load_product_registry(suite_root: str | Path) -> ProductRegistry:
    root = Path(suite_root).resolve()
    if not root.is_dir():
        return ProductRegistry(suite_root=root, products={}, versions={})
    product, product_versions = _read_plugin_product(root)
    products = {product.product_id: product}
    versions = {
        (product.product_id, version.version): version
        for version in product_versions
    }
    return ProductRegistry(suite_root=root, products=products, versions=versions)
