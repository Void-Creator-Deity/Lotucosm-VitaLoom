# -*- coding: utf-8 -*-
"""插件 ID 单一真相：与 builtin/package_index.json 的 plugins[] 一致。"""
from __future__ import annotations

from typing import Iterable, List, Set


def canonical_plugin_id(name: str, class_name: str = "") -> str:
    """归一化插件 id；源码应直接使用 *Plugin 后缀。"""
    raw = (name or "").strip()
    if raw.endswith("Plugin"):
        return raw
    cls = (class_name or "").strip()
    if cls.endswith("Plugin"):
        return cls
    if raw:
        return f"{raw}Plugin"
    return cls or raw


def normalize_dependency_ids(deps: Iterable[str]) -> List[str]:
    return [canonical_plugin_id(str(d)) for d in deps if d]


def index_plugin_ids_from_catalog(packages: List[dict]) -> Set[str]:
    out: Set[str] = set()
    for pkg in packages:
        plugins = pkg.get("plugins", [])
        if isinstance(plugins, list):
            for p in plugins:
                if p:
                    out.add(str(p))
    return out
