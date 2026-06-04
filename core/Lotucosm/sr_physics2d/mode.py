# -*- coding: utf-8
"""从场景/工程推断 SR 2D 物理模式（PVAEC 主世界 vs 织机教程）。"""

from __future__ import annotations

from typing import Any, Mapping

from core.Lotucosm.sr_game_defaults import infer_sr_game_mode
from core.Lotucosm.sr_physics2d.world import Physics2DMode


def infer_physics2d_mode(
    scene_data: Mapping[str, Any],
    project_path: str | None = None,
) -> Physics2DMode:
    if infer_sr_game_mode(scene_data, project_path):
        return Physics2DMode.GAME
    return Physics2DMode.PVAEC
