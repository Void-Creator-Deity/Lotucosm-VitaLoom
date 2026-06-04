"""包依赖图解析：版本区间与拓扑排序（供 package_manager 安装前校验）。

职责: resolve_dependency_graph 产出安装顺序与 issues 列表。
时机: package_manager 安装/启用包前校验依赖。
不变量: enabled_ids 外的依赖视为未满足。
排错: 循环依赖 → issues 含 missing package；版本不满足 → _version_gte 失败。
"""
from __future__ import annotations

from typing import Dict, List, Set, Tuple

def _parse_version(version: str) -> tuple[int, int, int]:
    parts = (version or "0.0.0").split(".")
    nums = []
    for i in range(3):
        try:
            nums.append(int(parts[i]) if i < len(parts) else 0)
        except Exception:
            nums.append(0)
    return nums[0], nums[1], nums[2]


def _version_gte(actual: str, expected_min: str) -> bool:
    return _parse_version(actual) >= _parse_version(expected_min)


def _parse_dependency_expr(expr: str) -> tuple[str, str, str]:
    text = (expr or "").strip()
    if ">=" in text:
        pkg_id, ver = text.split(">=", 1)
        return pkg_id.strip(), ">=", ver.strip()
    return text, "", ""


def resolve_dependency_graph(
    package_id: str,
    lookup: Dict[str, Dict[str, object]],
    enabled_ids: Set[str],
) -> Tuple[List[str], List[str]]:
    order: List[str] = []
    issues: List[str] = []
    visited: Set[str] = set()

    def visit(pid: str):
        if pid in visited:
            return
        visited.add(pid)
        pkg = lookup.get(pid)
        if not isinstance(pkg, dict):
            issues.append(f"missing package: {pid}")
            return
        deps = pkg.get("dependencies", [])
        if not isinstance(deps, list):
            deps = []
        for dep_expr in deps:
            dep_id, op, ver = _parse_dependency_expr(str(dep_expr))
            dep_pkg = lookup.get(dep_id)
            if not isinstance(dep_pkg, dict):
                issues.append(f"missing dependency: {dep_expr}")
                continue
            dep_ver = str(dep_pkg.get("version", "0.0.0"))
            if op == ">=" and not _version_gte(dep_ver, ver):
                issues.append(f"incompatible dependency: {dep_expr}")
            if dep_id not in enabled_ids:
                issues.append(f"disabled dependency: {dep_expr}")
            visit(dep_id)
        conflicts = pkg.get("conflicts", [])
        if isinstance(conflicts, list):
            for cid in conflicts:
                if str(cid) in enabled_ids:
                    issues.append(f"conflict enabled: {cid}")
        order.append(pid)

    visit(package_id)
    return order, issues

