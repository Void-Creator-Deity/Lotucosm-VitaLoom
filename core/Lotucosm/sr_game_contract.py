# -*- coding: utf-8
"""游戏 SR 契约：player_id、场景归一化、模式推断（合并 sr_game_defaults / sr_game_scene 入口）。"""

from __future__ import annotations

from typing import Any, Mapping

from core.Lotucosm.sr_game_defaults import (  # noqa: F401 re-export
    default_sr_visual_for_entity,
    infer_engine_game_project,
    infer_sr_game_mode,
    normalize_sr_play_goals_for_game_mode,
)
from core.Lotucosm.sr_game_entity_kind import is_wall_entity_data
from core.Lotucosm.sr_game_scene import (  # noqa: F401 re-export
    GAME_SCENE_PRESERVE_KEYS,
    normalize_entity_for_game,
    normalize_game_scene_data,
)

DEFAULT_PLAYER_ID = "player_rl"


def resolve_player_id(scene_data: Mapping[str, Any]) -> str:
    goals = scene_data.get("sr_play_goals")
    if isinstance(goals, dict):
        pid = goals.get("player_id")
        if isinstance(pid, str) and pid.strip():
            return pid.strip()
    pond = scene_data.get("pond_config")
    if isinstance(pond, dict):
        pid = pond.get("player_id")
        if isinstance(pid, str) and pid.strip():
            return pid.strip()
    return DEFAULT_PLAYER_ID


def is_player_entity(entity: Any, player_id: str) -> bool:
    return str(getattr(entity, "id", "")) == str(player_id)
