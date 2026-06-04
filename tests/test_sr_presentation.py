"""SR 会话横幅与贴图目录 smoke。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import QApplication


class SrPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication(sys.argv)

    def test_session_banner_overlay_runs(self):
        from core.VitaLoom.viewports.sr_visual_renderer import paint_session_banner_overlay

        pix = QPixmap(320, 240)
        pix.fill(0)
        p = QPainter(pix)
        paint_session_banner_overlay(
            p,
            320,
            240,
            kind="victory",
            message="演示目标已全部达成",
            elapsed=0.6,
            scene_time=10.0,
        )
        p.end()
        self.assertFalse(pix.isNull())

    def test_sprite_catalog_loads_manifest(self):
        from core.VitaLoom.viewports.sr_sprite_assets import SrSpriteCatalog

        with tempfile.TemporaryDirectory() as tmp:
            assets = Path(tmp) / "assets"
            sprites = assets / "sprites"
            sprites.mkdir(parents=True)
            QPixmap(16, 16).save(str(sprites / "nutrient.png"))
            (assets / "manifest.json").write_text(
                json.dumps({"sprites": {"nutrient": "sprites/nutrient.png"}}),
                encoding="utf-8",
            )
            SrSpriteCatalog.invalidate_cache()
            cat = SrSpriteCatalog.for_project(tmp)
            self.assertIsNotNone(cat)
            assert cat is not None
            self.assertTrue(cat.has_sprite("nutrient"))
            ent = MagicMock()
            ent.entity_type = "nutrient"
            ent.position = [10.0, 10.0]
            ent.radius = 12.0
            pix = QPixmap(64, 64)
            p = QPainter(pix)
            cat.paint_entity(p, ent, 0.0)
            p.end()
            self.assertFalse(pix.isNull())

    def test_sprite_catalog_flip_and_anim(self):
        from core.Lotucosm.sr_entity_visual import SrEntityVisual
        from core.VitaLoom.viewports.sr_sprite_assets import SrSpriteCatalog

        with tempfile.TemporaryDirectory() as tmp:
            assets = Path(tmp) / "assets"
            sprites = assets / "sprites"
            sprites.mkdir(parents=True)
            QPixmap(16, 16).save(str(sprites / "a0.png"))
            pix1 = QPixmap(16, 16)
            pix1.fill(0xFF00FF00)
            pix1.save(str(sprites / "a1.png"))
            (assets / "manifest.json").write_text(
                json.dumps(
                    {
                        "sprites": {"hero": "sprites/a0.png"},
                        "animations": {"hero_walk": ["sprites/a0.png", "sprites/a1.png"]},
                    }
                ),
                encoding="utf-8",
            )
            SrSpriteCatalog.invalidate_cache()
            cat = SrSpriteCatalog.for_project(tmp)
            assert cat is not None
            ent = MagicMock()
            ent.entity_type = "organism"
            ent.position = [10.0, 10.0]
            ent.radius = 12.0
            ent.sr_visual = SrEntityVisual(sprite="hero", anim="hero_walk", flip_x=True, frame=1)
            self.assertTrue(cat.can_paint(ent))
            pix = QPixmap(64, 64)
            p = QPainter(pix)
            cat.paint_entity(p, ent, 0.5)
            p.end()


    def test_confetti_burst_runs(self):
        from core.VitaLoom.viewports.sr_visual_renderer import paint_session_banner_overlay

        pix = QPixmap(400, 300)
        p = QPainter(pix)
        paint_session_banner_overlay(
            p,
            400,
            300,
            kind="victory",
            message="达成",
            elapsed=0.8,
            scene_time=5.0,
        )
        p.end()
        self.assertFalse(pix.isNull())

    def test_play_session_feedback_no_crash(self):
        from core.VitaLoom.feedback.sr_session_feedback import play_session_feedback

        play_session_feedback("victory")
        play_session_feedback("extinction")
        play_session_feedback("unknown")


if __name__ == "__main__":
    unittest.main()
