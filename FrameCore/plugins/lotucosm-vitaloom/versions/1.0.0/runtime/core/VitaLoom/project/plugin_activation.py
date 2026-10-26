# -*- coding: utf-8
"""工程驱动的编辑器插件激活集（按需加载）。"""
from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Set

from core.VitaLoom.project.project_manifest import (
    collect_required_package_ids,
    load_package_catalog,
)

BOOTSTRAP_PACKAGE_ID = "vitalloom.editor_essentials"

# role=editor 包中 Player 仍需要的插件（视口 + 主题 + 基础 i18n）
PLAYER_EDITOR_PACKAGE_ALLOWLIST: frozenset[str] = frozenset(
    {
        "GameViewportPlugin",
        "UnityDarkThemePlugin",
        "LocalizationPlugin",
    }
)


def is_player_mode() -> bool:
    """VITALOOM_PLAYER_MODE=1：Player 瘦运行时（非完整编辑器）。"""
    return os.environ.get("VITALOOM_PLAYER_MODE", "0") == "1"


def eager_load_all_plugins() -> bool:
    """测试或调试：启动时加载全部已发现插件（旧行为）。"""
    return os.environ.get("VITALOOM_EAGER_PLUGINS", "0") == "1"


def package_to_plugins(catalog: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    out: Dict[str, Set[str]] = {}
    for pkg in catalog:
        if not isinstance(pkg, dict):
            continue
        pkg_id = str(pkg.get("id", "") or "")
        if not pkg_id:
            continue
        plugins = pkg.get("plugins", [])
        if not isinstance(plugins, list):
            plugins = []
        out[pkg_id] = {str(p) for p in plugins if p}
    return out


def get_bootstrap_plugin_ids(repo_root: str | os.PathLike[str]) -> Set[str]:
    """无工程 / 冷启动：至少加载织机编辑器基础包内插件。"""
    catalog = load_package_catalog(repo_root)
    mapping = package_to_plugins(catalog)
    return set(mapping.get(BOOTSTRAP_PACKAGE_ID, set()))


def collect_active_plugin_ids(
    project_data: Dict[str, Any],
    *,
    repo_root: str | os.PathLike[str],
    disabled_plugins: Iterable[str] | None = None,
) -> Set[str]:
    """按 required_packages + capabilities 推导应激活的插件（扣 disabled_plugins）。"""
    catalog = load_package_catalog(repo_root)
    mapping = package_to_plugins(catalog)
    required_pkg_ids = collect_required_package_ids(project_data)

    disabled_set: Set[str] = set()
    raw = project_data.get("disabled_plugins")
    if isinstance(raw, list):
        disabled_set.update(str(x) for x in raw if x is not None)
    if disabled_plugins:
        disabled_set.update(str(x) for x in disabled_plugins if x is not None)

    active: Set[str] = set()
    for pkg_id in required_pkg_ids:
        for plugin_id in mapping.get(pkg_id, set()):
            if plugin_id not in disabled_set:
                active.add(plugin_id)
    return active


def _package_role_map(catalog: List[Dict[str, Any]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for pkg in catalog:
        if not isinstance(pkg, dict):
            continue
        pkg_id = str(pkg.get("id", "") or "")
        if not pkg_id:
            continue
        role = str(pkg.get("role", "") or "hybrid").lower()
        out[pkg_id] = role
    return out


def collect_player_plugin_ids(
    project_data: Dict[str, Any],
    *,
    repo_root: str | os.PathLike[str],
    disabled_plugins: Iterable[str] | None = None,
) -> Set[str]:
    """Player 模式：排除纯 editor 包插件，保留 runtime/hybrid + 视口白名单。"""
    catalog = load_package_catalog(repo_root)
    mapping = package_to_plugins(catalog)
    roles = _package_role_map(catalog)
    required_pkg_ids = collect_required_package_ids(project_data)

    disabled_set: Set[str] = set()
    raw = project_data.get("disabled_plugins")
    if isinstance(raw, list):
        disabled_set.update(str(x) for x in raw if x is not None)
    if disabled_plugins:
        disabled_set.update(str(x) for x in disabled_plugins if x is not None)

    active: Set[str] = set()
    for plugin_id in PLAYER_EDITOR_PACKAGE_ALLOWLIST:
        if plugin_id not in disabled_set:
            active.add(plugin_id)

    for pkg_id in required_pkg_ids:
        role = roles.get(pkg_id, "hybrid")
        if role not in ("runtime",):
            continue
        for plugin_id in mapping.get(pkg_id, set()):
            if plugin_id in disabled_set:
                continue
            active.add(plugin_id)
    return active


def expand_with_plugin_dependencies(
    seeds: Set[str],
    plugin_dependencies: Dict[str, List[str]],
) -> Set[str]:
    """插件 get_plugin_info dependencies 闭包（仅已注册插件）。"""
    out = set(seeds)
    changed = True
    while changed:
        changed = False
        for name in list(out):
            for dep in plugin_dependencies.get(name, []):
                dep_id = str(dep)
                if dep_id in plugin_dependencies and dep_id not in out:
                    out.add(dep_id)
                    changed = True
    return out
