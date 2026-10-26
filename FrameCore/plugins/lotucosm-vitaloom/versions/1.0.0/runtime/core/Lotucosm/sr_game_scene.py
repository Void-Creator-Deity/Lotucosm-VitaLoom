# -*- coding: utf-8
"""游戏教程场景：加载/保存时归一化实体类型、贴图与演示目标。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from core.Lotucosm.sr_game_entity_kind import is_wall_entity_data
from core.Lotucosm.sr_game_defaults import (
    default_sr_visual_for_entity,
    infer_engine_game_project,
    normalize_sr_play_goals_for_game_mode,
)

GAME_SCENE_PRESERVE_KEYS = frozenset(
    (
        "name",
        "version",
        "sr_game_mode",
        "sr_demo_legend",
        "sr_play_goals",
        "sr_pause_on_extinction",
        "pond_config",
        "entities",
        "connections",
        "viewport_state",
        "modified_at",
    )
)

_DEFAULT_LEGEND: dict[str, Any] = {
    "title": "教程 · Roguelike",
    "lines": [
        "WASD / 方向键移动 · Space 或贴近史莱姆攻击",
        "贴图来自 assets/manifest.json（非细胞绘制）",
        "清史莱姆后抵近右侧出口 · HUD 提示，模拟持续运行",
        "HP 归零 Game Over · 点 ⏹ 结束",
    ],
}


def _entity_visual_dict(entity_id: str, entity_type: str) -> dict[str, Any] | None:
    vis = default_sr_visual_for_entity(entity_id, entity_type)
    if not vis.sprite:
        return None
    out: dict[str, Any] = {"sprite": vis.sprite}
    if vis.alpha < 0.999:
        out["alpha"] = vis.alpha
    return out


def normalize_entity_for_game(entity: Mapping[str, Any]) -> dict[str, Any]:
    e: dict[str, Any] = dict(entity)
    eid = str(e.get("id", ""))
    et = str(e.get("type", ""))

    if eid.startswith("player"):
        e["type"] = "game_actor"
    elif eid.startswith("enemy_"):
        e["type"] = "game_actor"
    elif eid == "exit_gate":
        e["type"] = "game_prop"

    if is_wall_entity_data(e):
        e["type"] = "game_prop"
        try:
            radius = float(e.get("radius", 28.0))
        except (TypeError, ValueError):
            radius = 28.0
        if radius > 80.0:
            e["radius"] = 28.0
        e["pinned"] = True
        vis = dict(e["sr_visual"]) if isinstance(e.get("sr_visual"), dict) else {}
        vis.setdefault("sprite", "wall")
        vis.setdefault("alpha", 0.9)
        e["sr_visual"] = vis

    et = str(e.get("type", ""))
    if not isinstance(e.get("sr_visual"), dict) or not e["sr_visual"].get("sprite"):
        fallback = _entity_visual_dict(eid, et)
        if fallback:
            e["sr_visual"] = fallback

    if et in ("game_actor", "game_prop") or eid in ("exit_gate",) or eid.startswith("enemy_"):
        e.pop("energy", None)

    return e


def normalize_game_scene_data(
    scene_data: Mapping[str, Any],
    project_path: str | None,
) -> dict[str, Any]:
    if not infer_engine_game_project(project_path):
        return dict(scene_data)

    out = deepcopy(dict(scene_data))
    out["sr_game_mode"] = True
    out["sr_pause_on_extinction"] = False

    raw_entities = out.get("entities")
    if isinstance(raw_entities, list):
        out["entities"] = [normalize_entity_for_game(e) for e in raw_entities if isinstance(e, dict)]

    out["sr_play_goals"] = normalize_sr_play_goals_for_game_mode(out.get("sr_play_goals") or {})

    legend = out.get("sr_demo_legend")
    if not isinstance(legend, dict) or not legend.get("lines"):
        out["sr_demo_legend"] = dict(_DEFAULT_LEGEND)

    pond = out.get("pond_config")
    if isinstance(pond, dict):
        pond = dict(pond)
        pond["initial_organisms"] = 0
        pond["initial_components"] = 0
        out["pond_config"] = pond

    return out
