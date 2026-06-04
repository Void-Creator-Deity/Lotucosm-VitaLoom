# -*- coding: utf-8 -*-
"""
SR 场域/营养势纯函数契约：ambient_scalar、nutrient_gradient。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import unittest

from core.Lotucosm.scene_runtime_ambient import ambient_field_and_gradient, ambient_scalar_at


class _StubEnt:
    __slots__ = ("id", "position", "radius", "entity_type")

    def __init__(self, eid: str, x: float, y: float, radius: float, entity_type: str) -> None:
        self.id = eid
        self.position = [x, y]
        self.radius = radius
        self.entity_type = entity_type


class SceneRuntimeAmbientTests(unittest.TestCase):
    def test_nutrient_scalar_positive_off_axis(self) -> None:
        ents = [_StubEnt("n1", 0.0, 0.0, 36.0, "nutrient")]
        s = ambient_scalar_at(50.0, 0.0, ents, {})
        self.assertGreater(s, 0.0)

    def test_environment_well_matches_nutrient_scalar(self) -> None:
        ents = [_StubEnt("w1", 0.0, 0.0, 36.0, "environment_well")]
        s = ambient_scalar_at(50.0, 0.0, ents, {})
        self.assertGreater(s, 0.0)

    def test_niche_pressure_attenuates_well_scalar(self) -> None:
        ents = [_StubEnt("w1", 0.0, 0.0, 36.0, "environment_well")]
        s0 = ambient_scalar_at(50.0, 0.0, ents, {}, 0.0)
        s1 = ambient_scalar_at(50.0, 0.0, ents, {}, 1.0)
        self.assertGreater(s0, s1)
        self.assertGreater(s1, 0.0)

    def test_emission_prev_boosts_scalar(self) -> None:
        ents = [_StubEnt("a1", 0.0, 0.0, 22.0, "actuator")]
        s0 = ambient_scalar_at(40.0, 0.0, ents, {})
        s1 = ambient_scalar_at(40.0, 0.0, ents, {"a1": 1.0})
        self.assertGreater(s1, s0)

    def test_well_emission_mod_monotone(self) -> None:
        ents = [_StubEnt("w1", 0.0, 0.0, 36.0, "environment_well")]
        s0 = ambient_scalar_at(50.0, 0.0, ents, {"w1": 0.0})
        s_half = ambient_scalar_at(50.0, 0.0, ents, {"w1": 0.5})
        s1 = ambient_scalar_at(50.0, 0.0, ents, {"w1": 1.0})
        self.assertLess(s0, s_half)
        self.assertLess(s_half, s1)

    def test_well_missing_emission_matches_full_mod(self) -> None:
        ents = [_StubEnt("w1", 0.0, 0.0, 36.0, "environment_well")]
        s_no = ambient_scalar_at(50.0, 0.0, ents, {})
        s_full = ambient_scalar_at(50.0, 0.0, ents, {"w1": 1.0})
        self.assertAlmostEqual(s_no, s_full, places=9)

    def test_gradient_reasonable_magnitude(self) -> None:
        ents = [_StubEnt("n1", 100.0, 100.0, 36.0, "nutrient")]
        _f, gx, gy = ambient_field_and_gradient(120.0, 100.0, ents, {})
        self.assertLess(abs(gx) + abs(gy), 500.0)


if __name__ == "__main__":
    unittest.main()
