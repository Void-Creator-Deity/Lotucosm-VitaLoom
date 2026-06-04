# -*- coding: utf-8
"""游戏实体分类：墙 / 可动单位（单一真相源，避免四处复制判定）。"""

from __future__ import annotations

from typing import Any, Mapping


def entity_sprite(entity: Any) -> str:
    vis = getattr(entity, "sr_visual", None)
    if vis is not None:
        return str(getattr(vis, "sprite", "") or "")
    if isinstance(entity, Mapping):
        raw = entity.get("sr_visual")
        if isinstance(raw, dict):
            return str(raw.get("sprite", "") or "")
    return ""


def is_wall_entity_id(entity_id: str) -> bool:
    return str(entity_id).startswith("wall") or str(entity_id).startswith("proc_wall_")


def is_wall_entity_data(entity: Mapping[str, Any]) -> bool:
    eid = str(entity.get("id", ""))
    et = str(entity.get("type", ""))
    if is_wall_entity_id(eid) or entity_sprite(entity) == "wall":
        return True
    return et == "environment_well" and ("墙" in str(entity.get("name", "")) or eid.startswith("wall"))


def is_game_wall(entity: Any) -> bool:
    eid = str(getattr(entity, "id", ""))
    if is_wall_entity_id(eid):
        return True
    if entity_sprite(entity) == "wall":
        return True
    return str(getattr(entity, "entity_type", "")) == "environment_well" and eid.startswith("wall")


def is_game_mover(entity: Any) -> bool:
    if getattr(entity, "pinned", False):
        return False
    et = str(getattr(entity, "entity_type", ""))
    return et in ("game_actor", "organism")


def is_game_actor_entity(entity: Any) -> bool:
    return str(getattr(entity, "entity_type", "")) in ("game_actor", "organism")
