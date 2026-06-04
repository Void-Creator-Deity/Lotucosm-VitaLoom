# -*- coding: utf-8 -*-
"""场景 (.pond) 依赖扫描（阶段 A）：提取路径/脚本引用并解析为工程内绝对路径。

从 JSON 中提取已知路径字段与实体脚本引用，解析为工程内的绝对路径，
并读取 project.json 的 active_scene；用于编辑器「透明依赖」与缺失引用告警。

排错: 见 `editor_workflow_plugin`、`builtin/README.md`。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Iterator

KNOWN_PATH_KEYS = frozenset(
    {
        "sprite_path",
        "prefab_path",
        "icon_path",
        "mesh_path",
        "texture_path",
        "audio_path",
        "asset_path",
        "file_path",
        "source_path",
    }
)


def _looks_like_file_path(value: str) -> bool:
    s = value.strip()
    if not s or len(s) > 4096:
        return False
    if "/" in s or "\\" in s:
        return True
    base = os.path.basename(s)
    root, ext = os.path.splitext(base)
    return bool(ext) and len(ext) <= 6 and root


def _resolve_asset_ref(raw: str, project_root: str, scene_dir: str) -> str:
    raw = raw.strip()
    if os.path.isabs(raw):
        return os.path.normpath(raw)
    candidate_proj = os.path.normpath(os.path.join(project_root, raw))
    candidate_scene = os.path.normpath(os.path.join(scene_dir, raw))
    if os.path.exists(candidate_proj):
        return candidate_proj
    if os.path.exists(candidate_scene):
        return candidate_scene
    return candidate_proj


def _resolve_script_entry(item: dict[str, Any], project_root: str, scene_dir: str) -> str | None:
    script_path = item.get("path")
    script_name = item.get("name") or ""
    if script_path:
        return _resolve_asset_ref(str(script_path), project_root, scene_dir)
    if script_name:
        name = str(script_name)
        if name.endswith(".py"):
            return os.path.normpath(os.path.join(project_root, "scripts", name))
        return os.path.normpath(os.path.join(project_root, "scripts", f"{name}.py"))
    return None


def _walk_scripts_array(
    arr: Any,
    scene_file: str,
    project_root: str,
    scene_dir: str,
    base_pointer: str,
) -> Iterator["DependencyEdge"]:
    if not isinstance(arr, list):
        return
    for i, item in enumerate(arr):
        ptr = f"{base_pointer}[{i}]"
        if isinstance(item, dict):
            resolved = _resolve_script_entry(item, project_root, scene_dir)
            if resolved:
                yield DependencyEdge(
                    scene_file=scene_file,
                    json_pointer=ptr,
                    kind="script",
                    raw_ref=str(item.get("path") or item.get("name") or ""),
                    resolved_path=resolved,
                    exists=os.path.isfile(resolved),
                )
        elif isinstance(item, str) and item.strip():
            raw = item.strip()
            if raw.endswith(".py"):
                resolved = os.path.normpath(os.path.join(project_root, "scripts", raw))
            else:
                resolved = os.path.normpath(os.path.join(project_root, "scripts", f"{raw}.py"))
            yield DependencyEdge(
                scene_file=scene_file,
                json_pointer=ptr,
                kind="script",
                raw_ref=raw,
                resolved_path=resolved,
                exists=os.path.isfile(resolved),
            )


def _walk_obj(
    obj: Any,
    scene_file: str,
    project_root: str,
    scene_dir: str,
    pointer: str,
) -> Iterator["DependencyEdge"]:
    if isinstance(obj, dict):
        if "scripts" in obj:
            yield from _walk_scripts_array(
                obj["scripts"], scene_file, project_root, scene_dir, f"{pointer}.scripts"
            )
        for key, val in obj.items():
            if key == "scripts":
                continue
            if isinstance(key, str) and (key in KNOWN_PATH_KEYS or key.endswith("_path")):
                if isinstance(val, str) and _looks_like_file_path(val):
                    resolved = _resolve_asset_ref(val, project_root, scene_dir)
                    yield DependencyEdge(
                        scene_file=scene_file,
                        json_pointer=f"{pointer}.{key}",
                        kind="asset",
                        raw_ref=val.strip(),
                        resolved_path=resolved,
                        exists=os.path.isfile(resolved) or os.path.isdir(resolved),
                    )
            elif isinstance(val, (dict, list)):
                yield from _walk_obj(val, scene_file, project_root, scene_dir, f"{pointer}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from _walk_obj(item, scene_file, project_root, scene_dir, f"{pointer}[{i}]")


@dataclass(frozen=True)
class DependencyEdge:
    scene_file: str
    json_pointer: str
    kind: str
    raw_ref: str
    resolved_path: str
    exists: bool


def scan_scene_file(scene_path: str, project_root: str) -> list[DependencyEdge]:
    """解析单个 `.pond` 文件中的依赖边。"""
    scene_path = os.path.abspath(scene_path)
    project_root = os.path.abspath(project_root)
    scene_dir = os.path.dirname(scene_path)
    with open(scene_path, encoding="utf-8") as f:
        data = json.load(f)
    return list(_walk_obj(data, scene_path, project_root, scene_dir, "$"))


def scan_project_json_active_scene(project_root: str) -> list[DependencyEdge]:
    """`project.json` 中 `active_scene` 指向的场景文件（与 ProjectManager 一致：默认位于 scenes/）。"""
    project_root = os.path.abspath(project_root)
    pj = os.path.join(project_root, "project.json")
    if not os.path.isfile(pj):
        return []
    try:
        with open(pj, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []

    active = data.get("active_scene")
    if not isinstance(active, str) or not active.strip():
        return []

    raw = active.strip()
    if raw.startswith(("scenes/", "scenes\\")):
        rel = raw.replace("\\", "/")
        if rel.startswith("scenes/"):
            rel = rel[len("scenes/") :]
        resolved = os.path.normpath(os.path.join(project_root, "scenes", rel))
    else:
        resolved = os.path.normpath(os.path.join(project_root, "scenes", raw))

    return [
        DependencyEdge(
            scene_file=pj,
            json_pointer="$.active_scene",
            kind="active_scene",
            raw_ref=raw,
            resolved_path=resolved,
            exists=os.path.isfile(resolved),
        )
    ]


def scan_project_dependencies(project_root: str) -> list[DependencyEdge]:
    """扫描工程：`project.json` 活动场景 + `scenes/` 下所有 `.pond`。"""
    project_root = os.path.abspath(project_root)
    edges: list[DependencyEdge] = []
    edges.extend(scan_project_json_active_scene(project_root))

    scenes_root = os.path.join(project_root, "scenes")
    if os.path.isdir(scenes_root):
        for dirpath, _, filenames in os.walk(scenes_root):
            for name in filenames:
                if not name.endswith(".pond"):
                    continue
                pond_path = os.path.join(dirpath, name)
                try:
                    edges.extend(scan_scene_file(pond_path, project_root))
                except (OSError, json.JSONDecodeError):
                    continue
    return edges


def reverse_index(edges: list[DependencyEdge]) -> dict[str, list[tuple[str, str]]]:
    """依赖绝对路径 → [(来源文件路径, json_pointer), ...]。"""
    out: dict[str, list[tuple[str, str]]] = {}
    for e in edges:
        out.setdefault(e.resolved_path, []).append((e.scene_file, e.json_pointer))
    return out


def dependency_summary(edges: list[DependencyEdge]) -> dict[str, Any]:
    """供 UI/CLI 展示的轻量汇总（不做缓存持久化）。"""
    by_kind: dict[str, int] = {}
    missing_by_kind: dict[str, int] = {}
    for e in edges:
        by_kind[e.kind] = by_kind.get(e.kind, 0) + 1
        if not e.exists:
            missing_by_kind[e.kind] = missing_by_kind.get(e.kind, 0) + 1
    return {
        "total_edges": len(edges),
        "by_kind": dict(sorted(by_kind.items())),
        "missing_total": sum(missing_by_kind.values()),
        "missing_by_kind": dict(sorted(missing_by_kind.items())),
    }

def format_dependency_scan_report(
    project_root: str,
    edges: list[DependencyEdge],
    summ: dict[str, Any],
) -> str:
    """生成多行纯文本报告（无 Qt），供控制台与对话框复用。"""
    lines = [
        f"[场景依赖] 工程: {project_root}",
        f"边总数: {summ.get('total_edges', 0)} | 按类型: {summ.get('by_kind')} | 缺失数: {summ.get('missing_total', 0)}",
    ]
    missing = [e for e in edges if not e.exists]
    if not missing:
        lines.append("无缺失引用。")
    else:
        lines.append(f"缺失 {len(missing)} 条:")
        for e in missing:
            lines.append(f"  [{e.kind}] {e.raw_ref}")
            lines.append(f"    -> {e.resolved_path}")
            lines.append(f"    @ {e.scene_file} {e.json_pointer}")
    return "\n".join(lines)

