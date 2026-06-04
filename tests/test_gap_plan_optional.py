# -*- coding: utf-8 -*-
"""
计划 D 类可选能力：感知后处理与体外获取策略（默认关闭 / 兼容旧 acquire）。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import unittest

from builtin.components.components_base import ComponentBase
from builtin.entity_types.component_acquisition import (
    try_acquire_best_floating_near,
    evaluate_floating_value,
)
from builtin.entity_types.organism import Organism
from core.Lotucosm.pond import Pond
from core.Lotucosm.pvaec_cycle import PVAECCycle
from core.Lotucosm.perception import PerceptionSystem


class _StubSensor(ComponentBase):
    def __init__(self, component_id: str, value: float) -> None:
        super().__init__(component_id=component_id, position=(0.0, 0.0))
        self._value = value

    def sense(self, environment):  # noqa: ARG002
        return self._value


class PerceptionPipelineTests(unittest.TestCase):
    def test_legacy_pipeline_clips_scalar(self) -> None:
        org = Organism("p1", (0.0, 0.0))
        org.components = {"s1": _StubSensor("s1", 2.0)}
        cycle = PVAECCycle()
        raw = cycle.perceive(org, None)
        self.assertAlmostEqual(float(raw["s1"]), 2.0)
        org.use_legacy_perception_pipeline = True
        org.perception_noise_level = 0.0
        fused = cycle.perceive(org, None)
        self.assertAlmostEqual(float(fused["s1"]), 1.0)

    def test_perception_system_weights(self) -> None:
        ps = PerceptionSystem(noise_level=0.0)
        ps.sensor_weights = {"a": 2.0}
        out = ps.fuse_flat_sensor_dict({"a": 0.5})
        self.assertAlmostEqual(float(out["a"]), 1.0)


class AcquisitionPolicyTests(unittest.TestCase):
    def test_evaluate_uses_preferences(self) -> None:
        org = Organism("o1", (0.0, 0.0))
        org.component_preferences = {"T": 0.8}
        c = ComponentBase(component_id="c1", position=(0.0, 0.0), component_type="T")
        self.assertAlmostEqual(evaluate_floating_value(org, c), 0.8)

    def test_try_acquire_best_prefers_high_value_and_cost(self) -> None:
        pond = Pond()
        low = ComponentBase(component_id="low", position=(0.0, 0.0), component_type="L")
        high = ComponentBase(component_id="high", position=(0.0, 0.0), component_type="H")
        pond.floating_components = [low, high]
        org = Organism("o2", (0.0, 0.0), energy=100.0)
        org.component_preferences = {"L": 0.1, "H": 0.9}
        ok = try_acquire_best_floating_near(
            org, pond, radius=48.0, min_value=0.5, capture_cost=10.0, max_components=32
        )
        self.assertTrue(ok)
        self.assertAlmostEqual(org.energy, 90.0)
        self.assertIn("high", org.components)
        self.assertEqual(len(pond.floating_components), 1)
        self.assertEqual(pond.floating_components[0].id, "low")

    def test_insufficient_energy_skips_acquire(self) -> None:
        pond = Pond()
        c = ComponentBase(component_id="only", position=(0.0, 0.0), component_type="H")
        pond.floating_components = [c]
        org = Organism("o3", (0.0, 0.0), energy=5.0)
        org.component_preferences = {"H": 1.0}
        ok = try_acquire_best_floating_near(
            org, pond, radius=48.0, min_value=0.0, capture_cost=10.0
        )
        self.assertFalse(ok)
        self.assertAlmostEqual(org.energy, 5.0)
        self.assertEqual(len(pond.floating_components), 1)


if __name__ == "__main__":
    unittest.main()
