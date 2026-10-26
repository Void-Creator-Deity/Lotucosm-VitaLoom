# -*- coding: utf-8 -*-
"""按 package role 解析 Player 导出所需的运行时包闭包。"""
from __future__ import annotations

from typing import Any, Dict, List, Set

from core.VitaLoom.project.project_manifest import (
    collect_required_package_ids,
    load_package_catalog,
)


def _index_packages(catalog: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for pkg in catalog:
        if isinstance(pkg, dict):
            pid = str(pkg.get("id", "") or "")
            if pid:
                out[pid] = pkg
    return out


def collect_runtime_package_ids(
    project_data: Dict[str, Any],
    catalog: List[Dict[str, Any]] | None = None,
    *,
    repo_root: str | None = None,
) -> List[str]:
    """required_packages 中排除 role=editor / resource 的包。"""
    if catalog is None:
        if not repo_root:
            return []
        catalog = load_package_catalog(repo_root)
    by_id = _index_packages(catalog)
    required = collect_required_package_ids(project_data)
    out: List[str] = []
    seen: Set[str] = set()
    for pkg_id in required:
        pkg = by_id.get(pkg_id)
        if not pkg:
            continue
        role = str(pkg.get("role", "hybrid") or "hybrid").lower()
        if role in ("editor", "resource"):
            continue
        if pkg_id not in seen:
            seen.add(pkg_id)
            out.append(pkg_id)
    return out


def collect_physical_roots_for_packages(
    package_ids: List[str],
    catalog: List[Dict[str, Any]],
) -> List[str]:
    by_id = _index_packages(catalog)
    roots: List[str] = []
    seen: Set[str] = set()
    for pkg_id in package_ids:
        pkg = by_id.get(pkg_id)
        if not pkg:
            continue
        raw = pkg.get("physical_roots", [])
        if not isinstance(raw, list):
            continue
        for rel in raw:
            s = str(rel or "").replace("\\", "/").strip()
            if s and s not in seen:
                seen.add(s)
                roots.append(s)
    return roots
