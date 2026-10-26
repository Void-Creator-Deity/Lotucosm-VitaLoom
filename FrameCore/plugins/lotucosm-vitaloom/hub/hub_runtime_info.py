# -*- coding: utf-8 -*-
"""Runtime summary data for the Suite Hub."""
from __future__ import annotations

from typing import Any, Dict, List

from FrameCore.project_lock import load_package_catalog
from FrameCore.product_registry import load_product_registry
from hub.hub_paths import application_root, is_frozen_bundle, resource_root, suite_root


def load_bundled_package_catalog() -> List[Dict[str, Any]]:
    return load_package_catalog(resource_root())


def count_official_plugin_files() -> int:
    registry = load_product_registry(suite_root())
    version = registry.get_default_version("lotucosm-vitaloom")
    if version is None:
        return 0
    ext_dir = version.runtime_root / "builtin" / "editor_extensions"
    return len(list(ext_dir.glob("*_plugin.py")))


def build_runtime_summary() -> Dict[str, Any]:
    packages = load_bundled_package_catalog()
    core_pkg = next(
        (p for p in packages if str(p.get("id", "")) == "vitalloom.core.platform"),
        {},
    )
    official: List[Dict[str, Any]] = []
    for pkg in packages:
        origin = str(pkg.get("origin", "") or "")
        category = str(pkg.get("category", "") or "")
        if origin in ("official", "core") or category in ("official", "core"):
            plugins = pkg.get("plugins", [])
            official.append(
                {
                    "id": str(pkg.get("id", "")),
                    "name": str(
                        pkg.get("display_name_zh")
                        or pkg.get("display_name")
                        or pkg.get("id", "")
                    ),
                    "version": str(pkg.get("version", "")),
                    "plugin_count": len(plugins) if isinstance(plugins, list) else 0,
                }
            )
    provides = core_pkg.get("provides", [])
    if not isinstance(provides, list):
        provides = []
    return {
        "install_dir": str(application_root()),
        "is_frozen": is_frozen_bundle(),
        "plugin_file_count": count_official_plugin_files(),
        "core_provides": [str(x) for x in provides if x],
        "official_packages": official,
    }
