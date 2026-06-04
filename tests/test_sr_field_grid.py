# -*- coding: utf-8
"""sr_field_grid 扩散场。"""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from core.Lotucosm.sr_field_grid import SrFieldGrid, SrFieldGridConfig
from core.Lotucosm.scene_runtime_ambient import nutrient_gradient_at


class SrFieldGridTests(unittest.TestCase):
    def test_grid_step_and_gradient(self) -> None:
        cfg = SrFieldGridConfig(enabled=True, cell_size=40.0, diffusion=0.2, decay=0.02)
        grid = SrFieldGrid(400.0, 300.0, cfg)
        nut = SimpleNamespace(
            id="n1",
            entity_type="nutrient",
            position=[200.0, 150.0],
            radius=12.0,
            emission_strength=1.0,
        )
        grid.step([nut], {}, 0.05)
        for _ in range(8):
            grid.step([nut], {}, 0.05)
        pot, gx, gy = grid.nutrient_gradient_at(120.0, 150.0)
        self.assertGreater(pot, 0.0)
        self.assertGreater(gx, 0.0)

    def test_nutrient_gradient_fallback_without_grid(self) -> None:
        nut = SimpleNamespace(
            id="n1",
            entity_type="nutrient",
            position=[200.0, 150.0],
            radius=12.0,
        )
        pot, gx, _ = nutrient_gradient_at(100.0, 150.0, [nut], {})
        self.assertGreater(gx, 0.0)
        self.assertGreaterEqual(pot, 0.0)


if __name__ == "__main__":
    unittest.main()
