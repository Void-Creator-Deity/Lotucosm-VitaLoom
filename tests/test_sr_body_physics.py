# -*- coding: utf-8
"""PVAEC SR 圆体接触物理。"""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from core.Lotucosm.sr_body_physics import resolve_sr_body_contacts


def _org(x: float, y: float, *, vx: float = 0.0, vy: float = 0.0, r: float = 20.0):
    return SimpleNamespace(
        entity_type="organism",
        position=[x, y],
        velocity=[vx, vy],
        radius=r,
        pinned=False,
        membrane_locked=False,
    )


def _nut(x: float, y: float, *, r: float = 14.0):
    return SimpleNamespace(
        entity_type="nutrient",
        position=[x, y],
        velocity=[0.0, 0.0],
        radius=r,
        pinned=True,
        membrane_locked=False,
    )


class SrBodyPhysicsTests(unittest.TestCase):
    def test_organisms_separate_and_bounce(self) -> None:
        a = _org(100.0, 100.0, vx=80.0, vy=0.0)
        b = _org(118.0, 100.0, vx=0.0, vy=0.0, r=20.0)
        resolve_sr_body_contacts([a, b], width=400, height=400, iterations=4)
        dist = ((a.position[0] - b.position[0]) ** 2 + (a.position[1] - b.position[1]) ** 2) ** 0.5
        self.assertGreaterEqual(dist, a.radius + b.radius - 0.5)
        self.assertLess(a.velocity[0], 80.0)

    def test_organism_pushed_off_nutrient(self) -> None:
        org = _org(50.0, 50.0, vx=0.0, vy=0.0, r=22.0)
        nut = _nut(50.0, 50.0, r=16.0)
        resolve_sr_body_contacts([org, nut], width=400, height=400, iterations=4)
        dist = ((org.position[0] - nut.position[0]) ** 2 + (org.position[1] - nut.position[1]) ** 2) ** 0.5
        self.assertGreaterEqual(dist, org.radius + nut.radius - 1.0)

    def test_static_nutrient_does_not_move(self) -> None:
        org = _org(60.0, 60.0, vx=-80.0, vy=0.0)
        nut = _nut(60.0, 60.0)
        nx, ny = nut.position[0], nut.position[1]
        resolve_sr_body_contacts([org, nut], width=400, height=400, iterations=4)
        self.assertAlmostEqual(nut.position[0], nx)
        self.assertAlmostEqual(nut.position[1], ny)


if __name__ == "__main__":
    unittest.main()
