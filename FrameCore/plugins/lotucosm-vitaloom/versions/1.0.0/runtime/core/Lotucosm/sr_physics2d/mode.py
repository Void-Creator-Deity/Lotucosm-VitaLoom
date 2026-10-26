# -*- coding: utf-8
"""从场景/工程推断 SR 2D 物理模式（PVAEC 主世界 vs 游戏教程）。"""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping

from core.Lotucosm.sr_game_defaults import infer_sr_game_mode


class Physics2DMode(str, Enum):
    PVAEC = "pvaec"
    GAME = "game"


def infer_physics2d_mode(
    scene_data: Mapping[str, Any],
    project_path: str | None = None,
) -> Physics2DMode:
    if infer_sr_game_mode(scene_data, project_path):
        return Physics2DMode.GAME
    return Physics2DMode.PVAEC
