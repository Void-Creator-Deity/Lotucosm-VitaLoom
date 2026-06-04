# -*- coding: utf-8 -*-
"""
niche_pressure_from_load / well_scale 边界。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

from __future__ import annotations

import unittest

from core.Lotucosm.scene_runtime_world_state import (
    niche_pressure_from_load,
    step_biosphere_load,
    well_scale_from_niche_pressure,
)


class SrNichePressureTests(unittest.TestCase):
    def test_niche_pressure_from_load_clamped(self) -> None:
        self.assertEqual(niche_pressure_from_load(0.0, load_max=50.0), 0.0)
        self.assertEqual(niche_pressure_from_load(25.0, load_max=50.0), 0.5)
        self.assertEqual(niche_pressure_from_load(50.0, load_max=50.0), 1.0)
        self.assertEqual(niche_pressure_from_load(99.0, load_max=50.0), 1.0)

    def test_well_scale_monotone(self) -> None:
        self.assertGreater(well_scale_from_niche_pressure(0.0), well_scale_from_niche_pressure(1.0))

    def test_step_biosphere_load_decay_without_emissions(self) -> None:
        dt = 0.05
        l0 = 10.0
        l1 = step_biosphere_load(l0, 0.0, dt, load_max=50.0)
        self.assertLess(l1, l0)

    def test_step_biosphere_load_intake(self) -> None:
        dt = 0.05
        l0 = 0.0
        l1 = step_biosphere_load(l0, 1.0, dt, intake_gain=10.0, decay_per_sec=0.0, load_max=50.0)
        self.assertGreater(l1, l0)


if __name__ == "__main__":
    unittest.main()
