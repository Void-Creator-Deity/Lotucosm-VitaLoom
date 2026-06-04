"""GameViewport 画布绘制回归：_paint_sr_canvas 独立于 HUD 刷新。"""

from __future__ import annotations

import os
import unittest

from PyQt6.QtWidgets import QApplication

from core.VitaLoom.viewports.game_viewport import GameViewport


class GameViewportCanvasPaintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def test_paint_sr_canvas_on_internal_canvas(self) -> None:
        gv = GameViewport()
        self.assertTrue(hasattr(gv, "_paint_sr_canvas"))
        self.assertTrue(callable(getattr(gv, "_paint_sr_canvas")))
        canvas = gv._canvas
        canvas.resize(640, 480)
        gv._paint_sr_canvas(canvas, None)

    def test_refresh_entry_hud_hint_does_not_paint(self) -> None:
        gv = GameViewport()
        gv._refresh_entry_hud_hint()


if __name__ == "__main__":
    unittest.main()
