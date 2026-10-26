# -*- coding: utf-8 -*-
"""游戏模式战斗反馈的 Qt-free 状态与生命周期模型。

绘制实现位于 ``core.VitaLoom.viewports.sr_game_fx_painter``，避免把
PyQt/QPainter 依赖带入 Lotucosm runtime。保留绘制函数的惰性兼容转发，
以免旧版 Host Adapter 的导入路径立即失效。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass
class SrGameFxState:
    floats: list[dict[str, Any]] = field(default_factory=list)
    swings: list[dict[str, Any]] = field(default_factory=list)


def create_fx_state() -> SrGameFxState:
    return SrGameFxState()


def ingest_fx_requests(state: SrGameFxState, requests: Sequence[Mapping[str, Any]]) -> None:
    for req in requests:
        kind = str(req.get("type", ""))
        if kind == "float":
            state.floats.append(
                {
                    "x": float(req.get("x", 0.0)),
                    "y": float(req.get("y", 0.0)),
                    "text": str(req.get("text", "")),
                    "life": float(req.get("life", 0.65)),
                    "color": str(req.get("color", "#ffeb99")),
                    "vy": float(req.get("vy", -48.0)),
                }
            )
        elif kind == "swing":
            state.swings.append(
                {
                    "x": float(req.get("x", 0.0)),
                    "y": float(req.get("y", 0.0)),
                    "angle": float(req.get("angle", 0.0)),
                    "range": float(req.get("range", 28.0)),
                    "arc_half": float(req.get("arc_half", 0.65)),
                    "life": float(req.get("life", 0.14)),
                    "color": str(req.get("color", "#c8e0ff")),
                }
            )


def update_game_fx(state: SrGameFxState, dt: float) -> None:
    next_floats: list[dict[str, Any]] = []
    for item in state.floats:
        item["life"] -= dt
        item["y"] += item["vy"] * dt
        if item["life"] > 0.0:
            next_floats.append(item)
    state.floats = next_floats

    next_swings: list[dict[str, Any]] = []
    for item in state.swings:
        item["life"] -= dt
        if item["life"] > 0.0:
            next_swings.append(item)
    state.swings = next_swings


def entity_hit_flash(entity: Any) -> float:
    hud = getattr(entity, "sr_debug_hud", None)
    if not isinstance(hud, dict):
        return 0.0
    try:
        return max(0.0, float(hud.get("hit_flash", 0.0)))
    except (TypeError, ValueError):
        return 0.0


def paint_hit_flash_overlay(*args: Any, **kwargs: Any) -> None:
    """Compatibility forwarder for the legacy Qt Host Adapter import path."""
    from core.VitaLoom.viewports.sr_game_fx_painter import paint_hit_flash_overlay as paint

    paint(*args, **kwargs)


def paint_game_fx(*args: Any, **kwargs: Any) -> None:
    """Compatibility forwarder for the legacy Qt Host Adapter import path."""
    from core.VitaLoom.viewports.sr_game_fx_painter import paint_game_fx as paint

    paint(*args, **kwargs)


def paint_game_aim_line(*args: Any, **kwargs: Any) -> None:
    """Compatibility forwarder for the legacy Qt Host Adapter import path."""
    from core.VitaLoom.viewports.sr_game_fx_painter import paint_game_aim_line as paint

    paint(*args, **kwargs)


__all__ = [
    "SrGameFxState",
    "create_fx_state",
    "entity_hit_flash",
    "ingest_fx_requests",
    "paint_game_aim_line",
    "paint_game_fx",
    "paint_hit_flash_overlay",
    "update_game_fx",
]
