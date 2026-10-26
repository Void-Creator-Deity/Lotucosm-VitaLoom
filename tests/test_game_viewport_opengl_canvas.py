# -*- coding: utf-8 -*-
from __future__ import annotations

from core.VitaLoom.viewports.game_viewport import GameViewport


def test_game_viewport_exposes_opengl_canvas_helpers() -> None:
    assert callable(getattr(GameViewport, "_build_sr_viewport_frame_snapshot"))
    assert callable(getattr(GameViewport, "_initialize_sr_opengl_canvas"))
    assert callable(getattr(GameViewport, "_resize_sr_opengl_canvas"))
    assert callable(getattr(GameViewport, "_paint_sr_opengl_canvas"))
    assert callable(getattr(GameViewport, "_paint_sr_qpainter_canvas"))
