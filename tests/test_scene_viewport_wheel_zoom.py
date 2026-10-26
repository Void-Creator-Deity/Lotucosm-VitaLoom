# -*- coding: utf-8
"""场景视口滚轮缩放：pan_offset 须与 _chrome_top 一致。"""
from __future__ import annotations

import unittest


def _pan_after_zoom(
    mouse_x: float,
    mouse_y: float,
    chrome: float,
    pan_x: float,
    pan_y: float,
    zoom: float,
    new_zoom: float,
) -> tuple[float, float]:
    ey = mouse_y - chrome
    world_x = (mouse_x - pan_x) / zoom
    world_y = (ey - pan_y) / zoom
    return (
        mouse_x - world_x * new_zoom,
        ey - world_y * new_zoom,
    )


class SceneViewportWheelZoomTests(unittest.TestCase):
    def test_zoom_anchor_stable_with_toolbar_chrome(self):
        chrome = 28.0
        mouse_x, mouse_y = 420.0, 360.0
        pan_x, pan_y = 15.0, -8.0
        zoom = 1.25
        new_zoom = 1.375
        pan_new_x, pan_new_y = _pan_after_zoom(
            mouse_x, mouse_y, chrome, pan_x, pan_y, zoom, new_zoom
        )
        ey = mouse_y - chrome
        world_x = (mouse_x - pan_x) / zoom
        world_y = (ey - pan_y) / zoom
        screen_x = world_x * new_zoom + pan_new_x
        screen_y = world_y * new_zoom + pan_new_y + chrome
        self.assertAlmostEqual(screen_x, mouse_x, places=6)
        self.assertAlmostEqual(screen_y, mouse_y, places=6)

    def test_wrong_formula_drifts_by_chrome_each_step(self):
        chrome = 28.0
        mouse_y = 360.0
        pan_y = 0.0
        zoom = 1.0
        new_zoom = 1.1
        ey = mouse_y - chrome
        world_y = (ey - pan_y) / zoom
        wrong_pan_y = mouse_y - world_y * new_zoom
        screen_y = world_y * new_zoom + wrong_pan_y + chrome
        self.assertAlmostEqual(screen_y - mouse_y, chrome, places=6)


if __name__ == "__main__":
    unittest.main()
