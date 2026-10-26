# -*- coding: utf-8
"""SR 会话结局：胜利/失败/灭绝横幅与暂停（游戏轨与 PVAEC 轨分支）。"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.VitaLoom.viewports.game_viewport import GameViewport


def resolve_session_outcomes(host: "GameViewport") -> None:
    """统一入口：按 game_mode 与 goals 决定 notice / pause。"""
    host._maybe_try_sr_victory_pause()
    if getattr(host, "_sr_game_mode", False):
        host._maybe_try_sr_victory_notice()
        host._maybe_try_sr_defeat_pause()
    else:
        host._maybe_try_sr_play_goals_notice()
        host._maybe_try_sr_extinction_pause()
