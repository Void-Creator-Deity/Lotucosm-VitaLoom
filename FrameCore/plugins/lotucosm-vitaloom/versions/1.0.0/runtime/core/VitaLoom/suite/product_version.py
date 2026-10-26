# -*- coding: utf-8 -*-
"""产品版本选择辅助函数。

职责: 从 FrameCore ProductRegistry 中按 project.json / project.lock.json 约束选择产品版本。
排错: 若返回 None，检查产品 id、版本约束以及 plugin_manifest.json 中登记的版本。
"""
from __future__ import annotations

from core.VitaLoom.project.project_manifest import (
    parse_version_tuple,
    version_matches_constraint,
)
from FrameCore.product_registry import ProductRegistry, ProductVersion


def select_product_version(
    registry: ProductRegistry,
    product_id: str,
    version_constraint: str,
) -> ProductVersion | None:
    """按约束选择产品版本；空约束返回默认版本。"""
    if not version_constraint:
        return registry.get_default_version(product_id)
    exact = registry.get_version(product_id, version_constraint)
    if exact is not None:
        return exact
    candidates = [
        v
        for (pid, _ver), v in registry.versions.items()
        if pid == product_id and version_matches_constraint(v.version, version_constraint)
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda v: parse_version_tuple(v.version), reverse=True)
    return candidates[0]
