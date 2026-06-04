# -*- coding: utf-8
"""SR 游戏/教程工程：默认 sr_visual 与 game_mode 推断（编辑器保存丢失字段时的兜底）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional

from core.Lotucosm.sr_entity_visual import SrEntityVisual, parse_sr_visual


def infer_engine_game_project(project_path: Optional[str]) -> bool:
    if not project_path:
        return False
    root = Path(project_path)
    manifest = root / "assets" / "manifest.json"
    if not manifest.is_file():
        return False
    cfg_path = root / "project.json"
    if cfg_path.is_file():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            cfg = {}
        if str(cfg.get("sr_engine_mode", "")).lower() == "game":
            return True
        desc = str(cfg.get("description", ""))
        if "非 PVAEC" in desc or "引擎教学" in desc:
            return True
    return "织机教程" in root.name


def infer_sr_game_mode(scene_data: Mapping[str, Any], project_path: Optional[str]) -> bool:
    if scene_data.get("sr_game_mode") is True:
        return True
    return infer_engine_game_project(project_path)


def normalize_sr_play_goals_for_game_mode(goals: Mapping[str, Any]) -> dict[str, Any]:
    """游戏引擎 demo：通关只写 HUD，不自动 pause（PVAEC 演示才 pause_on_complete）。"""
    out = dict(goals) if isinstance(goals, Mapping) else {}
    out["pause_on_complete"] = False
    return out


def default_sr_visual_for_entity(entity_id: str, entity_type: str) -> SrEntityVisual:
    eid = str(entity_id)
    et = str(entity_type)
    if eid == "player_rl" or eid.startswith("player"):
        return SrEntityVisual(sprite="player")
    if eid.startswith("enemy_"):
        return SrEntityVisual(sprite="slime")
    if eid == "exit_gate" or et == "nutrient":
        return SrEntityVisual(sprite="exit")
    if eid.startswith("wall") or et == "environment_well":
        return SrEntityVisual(sprite="wall", alpha=0.9)
    if et in ("game_actor", "game_prop"):
        return SrEntityVisual(sprite="player" if et == "game_actor" else "wall")
    return SrEntityVisual()
