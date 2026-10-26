# -*- coding: utf-8 -*-
"""工程 manifest：版本与 required_packages 校验（对标 Unity manifest + ProjectVersion）。"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

LOOM_EDITOR_VERSION = "1.0.0"

IMPLICIT_PACKAGES = (
    "vitalloom.core.platform",
    "vitalloom.editor_essentials",
    "vitalloom.lotuspond.runtime",
)

CAPABILITY_PACKAGES: Dict[str, List[str]] = {
    "sr2d": ["vitalloom.engine.sr2d"],
    "game_script": ["vitalloom.engine.sr2d"],
    "pvaec": ["vitalloom.pvaec.simulation"],
}


@dataclass
class ManifestIssue:
    level: str  # error | warning | info
    code: str
    message: str


@dataclass
class ManifestValidationResult:
    ok: bool
    issues: List[ManifestIssue] = field(default_factory=list)
    required_packages: List[str] = field(default_factory=list)
    missing_packages: List[str] = field(default_factory=list)

    def summary_text(self) -> str:
        if not self.issues:
            return ""
        return "; ".join(i.message for i in self.issues[:5])


def parse_version_tuple(version: str) -> Tuple[int, int, int]:
    parts = (version or "0.0.0").strip().split(".")
    nums: List[int] = []
    for i in range(3):
        try:
            nums.append(int(parts[i]) if i < len(parts) else 0)
        except ValueError:
            nums.append(0)
    return nums[0], nums[1], nums[2]


def version_matches_constraint(editor_version: str, constraint: str) -> bool:
    """支持 1.0.0、>=1.0.0、>=1.0.0,<2.0.0。"""
    text = (constraint or "").strip()
    if not text:
        return True
    ev = parse_version_tuple(editor_version)
    clauses = [c.strip() for c in text.split(",") if c.strip()]
    if not clauses:
        return True
    if not any(c[0] in "<>=" for c in clauses):
        return ev == parse_version_tuple(text)
    for clause in clauses:
        m = re.match(r"^(>=|<=|>|<|==|=)\s*(\d+\.\d+\.\d+)$", clause)
        if not m:
            return False
        op, ver = m.group(1), parse_version_tuple(m.group(2))
        if op == ">=" and ev < ver:
            return False
        if op == "<=" and ev > ver:
            return False
        if op == ">" and ev <= ver:
            return False
        if op == "<" and ev >= ver:
            return False
        if op in ("==", "=") and ev != ver:
            return False
    return True


def collect_required_package_ids(project_data: Dict[str, Any]) -> List[str]:
    required = project_data.get("required_packages")
    if not isinstance(required, list) or not required:
        required = project_data.get("recommended_packages", [])
    if not isinstance(required, list):
        required = []
    required_capabilities = project_data.get("required_capabilities", {})
    ids: List[str] = []
    seen: Set[str] = set()
    extra_required: List[str] = []
    if isinstance(required_capabilities, dict):
        extra_required.extend(str(k) for k in required_capabilities.keys())
    elif isinstance(required_capabilities, list):
        extra_required.extend(str(x) for x in required_capabilities)
    for pkg_id in list(IMPLICIT_PACKAGES) + list(required) + extra_required:
        s = str(pkg_id or "").strip()
        if s and s not in seen:
            seen.add(s)
            ids.append(s)
    caps = project_data.get("capabilities", [])
    if isinstance(caps, list):
        for cap in caps:
            key = str(cap or "").strip().lower()
            for pid in CAPABILITY_PACKAGES.get(key, []):
                if pid not in seen:
                    seen.add(pid)
                    ids.append(pid)
    return ids


def collect_required_capability_constraints(project_data: Dict[str, Any]) -> Dict[str, str]:
    """返回 required_capabilities 中声明的包版本约束。"""
    required_capabilities = project_data.get("required_capabilities", {})
    constraints: Dict[str, str] = {}
    if not isinstance(required_capabilities, dict):
        return constraints
    for raw_id, raw_constraint in required_capabilities.items():
        pkg_id = str(raw_id or "").strip()
        constraint = str(raw_constraint or "").strip()
        if pkg_id and constraint:
            constraints[pkg_id] = constraint
    return constraints


def load_package_catalog(repo_root: str | Path) -> List[Dict[str, Any]]:
    from core.VitaLoom.core.bundle_paths import resource_root

    candidates = [
        Path(repo_root) / "builtin" / "package_index.json",
        Path(repo_root) / "runtime" / "builtin" / "package_index.json",
        resource_root() / "builtin" / "package_index.json",
    ]
    path = next((p for p in candidates if p.is_file()), candidates[0])
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        packages = data.get("packages", [])
        return packages if isinstance(packages, list) else []
    except Exception:
        return []


def _package_roots_exist(repo_root: Path, pkg: Dict[str, Any]) -> bool:
    from core.VitaLoom.core.bundle_paths import physical_root_exists

    roots = pkg.get("physical_roots", [])
    if not isinstance(roots, list) or not roots:
        return True
    for rel in roots:
        if physical_root_exists(str(rel), repo_root=repo_root):
            return True
    return False


def _package_enabled(
    pkg: Dict[str, Any],
    disabled_plugins: Set[str],
    repo_root: Path,
    installed: Dict[str, Any],
) -> bool:
    pkg_id = str(pkg.get("id", "") or "")
    status = str(pkg.get("status", "")).lower()
    if status == "required":
        return _package_roots_exist(repo_root, pkg)
    plugins = pkg.get("plugins", [])
    if not isinstance(plugins, list):
        plugins = []
    if plugins:
        if all(str(p) in disabled_plugins for p in plugins):
            return False
        return True
    inst = installed.get(pkg_id)
    if isinstance(inst, dict) and inst:
        return True
    return _package_roots_exist(repo_root, pkg)


def validate_project_manifest(
    project_data: Dict[str, Any],
    *,
    repo_root: str | Path,
    editor_version: str = LOOM_EDITOR_VERSION,
    disabled_plugins: Optional[List[str]] = None,
) -> ManifestValidationResult:
    issues: List[ManifestIssue] = []
    required_ids = collect_required_package_ids(project_data)
    capability_constraints = collect_required_capability_constraints(project_data)
    missing: List[str] = []

    constraint = str(project_data.get("loom_editor_version", "") or "").strip()
    if constraint and not version_matches_constraint(editor_version, constraint):
        issues.append(
            ManifestIssue(
                level="warning",
                code="editor_version_mismatch",
                message=(
                    f"工程要求织机版本 {constraint}，当前编辑器为 {editor_version}"
                ),
            )
        )

    repo = Path(repo_root)
    catalog = {str(p.get("id", "")): p for p in load_package_catalog(repo) if p.get("id")}
    disabled_set: Set[str] = set()
    raw_disabled = project_data.get("disabled_plugins")
    if isinstance(raw_disabled, list):
        disabled_set.update(str(x) for x in raw_disabled if x is not None)
    if disabled_plugins:
        disabled_set.update(str(x) for x in disabled_plugins if x is not None)

    state = project_data.get("package_state", {})
    installed: Dict[str, Any] = {}
    if isinstance(state, dict):
        raw = state.get("installed", {})
        if isinstance(raw, dict):
            installed = raw

    for pkg_id in required_ids:
        pkg = catalog.get(pkg_id)
        if pkg is None:
            missing.append(pkg_id)
            issues.append(
                ManifestIssue(
                    level="error",
                    code="package_unknown",
                    message=f"未知包 id: {pkg_id}",
                )
            )
            continue
        if str(pkg.get("status", "")).lower() == "planned":
            missing.append(pkg_id)
            issues.append(
                ManifestIssue(
                    level="error",
                    code="package_planned",
                    message=f"包尚未实现: {pkg_id}",
                )
            )
            continue
        constraint = capability_constraints.get(pkg_id, "")
        package_version = str(pkg.get("version", "") or "").strip()
        if constraint and not version_matches_constraint(package_version, constraint):
            missing.append(pkg_id)
            issues.append(
                ManifestIssue(
                    level="error",
                    code="capability_version_mismatch",
                    message=(
                        f"能力包 {pkg_id} 版本 {package_version or '未知'} "
                        f"不满足工程约束 {constraint}"
                    ),
                )
            )
            continue
        if not _package_enabled(pkg, disabled_set, repo, installed):
            missing.append(pkg_id)
            issues.append(
                ManifestIssue(
                    level="error",
                    code="package_disabled",
                    message=f"包未启用（检查 disabled_plugins 或安装）: {pkg_id}",
                )
            )

    has_error = any(i.level == "error" for i in issues)
    mode = str(project_data.get("manifest_validation_mode", "warn") or "warn").lower()
    ok = not has_error or mode != "block"
    return ManifestValidationResult(
        ok=ok,
        issues=issues,
        required_packages=required_ids,
        missing_packages=missing,
    )


def get_loom_editor_version_from_pyproject(repo_root: str | Path) -> str:
    path = Path(repo_root) / "pyproject.toml"
    if not path.is_file():
        return LOOM_EDITOR_VERSION
    try:
        text = path.read_text(encoding="utf-8")
        m = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        if m:
            return m.group(1).strip()
    except Exception:
        __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)
    return LOOM_EDITOR_VERSION
