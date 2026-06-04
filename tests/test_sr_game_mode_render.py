# -*- coding: utf-8
"""游戏模式 paint_frame 不绘制 PVAEC 细胞层。"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from PyQt6.QtGui import QPainter, QPixmap


class SrGameModeRenderTests(unittest.TestCase):
    def test_game_mode_skips_composite_cells(self) -> None:
        from core.Lotucosm.sr_entity_visual import SrEntityVisual
        from core.VitaLoom.viewports.sr_visual_renderer import SrVisualRenderer

        ent = MagicMock()
        ent.id = "player_rl"
        ent.entity_type = "game_actor"
        ent.position = [100.0, 100.0]
        ent.radius = 20.0
        ent.sr_visual = SrEntityVisual(sprite="player")

        cat = MagicMock()
        cat.can_paint.return_value = True
        cat.paint_entity = MagicMock()

        pix = QPixmap(320, 240)
        p = QPainter(pix)
        with patch(
            "core.VitaLoom.viewports.sr_visual_renderer.paint_composite_cells"
        ) as composite:
            SrVisualRenderer().paint_frame(
                p,
                320,
                240,
                entities=[ent],
                structural_edges=[],
                signal_edges=[],
                scene_time=0.0,
                sprite_catalog=cat,
                game_mode=True,
            )
            composite.assert_not_called()
            cat.paint_entity.assert_called()
        p.end()


if __name__ == "__main__":
    unittest.main()
