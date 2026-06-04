"""SR 整细胞视觉：hub 分组与膜轮廓。"""

from __future__ import annotations

import os
import unittest

from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QApplication

from core.VitaLoom.viewports.sr_visual_renderer import (
    SrVisualRenderer,
    _build_cell_groups,
    _organic_membrane_path,
)


class _FakeEnt:
    def __init__(self, eid: str, etype: str, x: float, y: float, r: float = 14.0):
        self.id = eid
        self.entity_type = etype
        self.position = [x, y]
        self.radius = r


class SrCellVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def test_build_cell_groups_from_hub_edges(self) -> None:
        hub = _FakeEnt("o1", "organism", 100, 100, 28)
        s1 = _FakeEnt("s1", "sensor", 140, 90, 12)
        a1 = _FakeEnt("a1", "actuator", 80, 130, 10)
        entities = [hub, s1, a1]
        edges = [("o1", "s1"), ("o1", "a1")]
        groups = _build_cell_groups(entities, edges)
        self.assertEqual(len(groups), 1)
        hub_id, members = groups[0]
        self.assertEqual(hub_id, "o1")
        self.assertEqual(members, {"o1", "s1", "a1"})

    def test_organic_membrane_path_is_closed(self) -> None:
        path = _organic_membrane_path(
            50.0,
            50.0,
            [(50, 50, 20), (70, 45, 10), (40, 65, 10)],
            segments=20,
        )
        self.assertFalse(path.isEmpty())
        rect = path.boundingRect()
        self.assertGreater(rect.width(), 40)
        self.assertGreater(rect.height(), 40)

    def test_composite_cell_paint_frame(self) -> None:
        hub = _FakeEnt("o1", "organism", 120, 120, 26)
        s1 = _FakeEnt("s1", "sensor", 155, 105, 12)
        a1 = _FakeEnt("a1", "actuator", 95, 145, 11)
        nut = _FakeEnt("n1", "nutrient", 200, 200, 8)
        entities = [hub, s1, a1, nut]
        edges = [("o1", "s1"), ("o1", "a1")]
        sig = [{"start": "s1", "end": "a1", "channel": "chemo", "weight": 1.2}]
        img = QImage(320, 240, QImage.Format.Format_ARGB32)
        img.fill(0)
        p = QPainter(img)
        SrVisualRenderer().paint_frame(
            p,
            320,
            240,
            entities=entities,
            structural_edges=edges,
            signal_edges=sig,
            scene_time=2.5,
        )
        p.end()
        self.assertGreater(img.pixelColor(120, 120).alpha(), 0)


if __name__ == "__main__":
    unittest.main()
