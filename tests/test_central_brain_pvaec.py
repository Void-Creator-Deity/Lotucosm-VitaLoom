# -*- coding: utf-8 -*-
"""
中枢体脚本：单元测试（从引擎包导入）。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import math
import unittest

from core.Lotucosm.scene_runtime_context import RuntimePeerSnapshot, SceneRuntimeTickContext
from core.Lotucosm.sr_central_brain_pvaec import CentralBrainPvaec


class _FakeEntity:
    def __init__(self, eid: str, x: float, y: float):
        self.id = eid
        self.position = [x, y]
        self.velocity = [0.0, 0.0]


class CentralBrainPvaecTests(unittest.TestCase):
    def test_perceive_empty_peers(self):
        script = CentralBrainPvaec()
        ctx = SceneRuntimeTickContext(
            owner_id="ai",
            owner_type="organism",
            owner_position=(100.0, 100.0),
            owner_radius=20.0,
            bounds=(800, 600),
            simulation_time=0.0,
            delta_time=0.05,
            peers=(),
        )
        obs = script.perceive(ctx)
        self.assertEqual(obs["sensor_pull"], 0.0)
        self.assertEqual(obs["actuator_pull"], 0.0)
        self.assertEqual(obs["world_width"], 800)
        self.assertEqual(obs["world_height"], 600)

    def test_perceive_pulls_one_sensor(self):
        script = CentralBrainPvaec()
        p = RuntimePeerSnapshot("s1", "sensor", (10.0, 0.0), 5.0, 3.0, 0.0)
        ctx = SceneRuntimeTickContext(
            owner_id="ai",
            owner_type="organism",
            owner_position=(0.0, 0.0),
            owner_radius=20.0,
            bounds=(800, 600),
            simulation_time=1.0,
            delta_time=0.05,
            peers=(p,),
        )
        obs = script.perceive(ctx)
        self.assertAlmostEqual(obs["sensor_pull"], 0.34)
        self.assertEqual(obs["actuator_pull"], 0.0)

    def test_think_invalid_world_size_returns_zero_accel(self):
        script = CentralBrainPvaec()
        script.entity = _FakeEntity("ai", 100.0, 100.0)
        dec = script.think({"sensor_pull": 1.0, "actuator_pull": 0.0, "world_width": -1, "world_height": 600}, 0.05)
        self.assertEqual(dec["ax"], 0.0)
        self.assertEqual(dec["ay"], 0.0)

    def test_act_clamps_speed(self):
        script = CentralBrainPvaec()
        script.entity = _FakeEntity("ai", 0.0, 0.0)
        script.entity.velocity = [1000.0, 1000.0]
        script.act({"ax": 0.0, "ay": 0.0}, 0.05)
        spd = math.hypot(script.entity.velocity[0], script.entity.velocity[1])
        self.assertLessEqual(spd, 420.0 + 1e-6)

    def test_start_without_entity_no_crash(self):
        script = CentralBrainPvaec()
        script.entity = None
        script.start()

    def test_think_two_mind_profiles_change_accel(self):
        from core.Lotucosm.sr_mind_profile import MindProfile

        obs = {
            "sensor_pull": 0.5,
            "actuator_pull": 0.1,
            "peer_organism_pull": 0.2,
            "ambient_field": 2000.0,
            "ambient_grad_x": 0.3,
            "ambient_grad_y": -0.4,
            "niche_pressure": 0.3,
            "world_load_derivative": 0.0,
            "intrinsic_speed": 50.0,
            "world_width": 800.0,
            "world_height": 600.0,
        }
        ent = _FakeEntity("a", 100.0, 150.0)
        s1 = CentralBrainPvaec()
        s1.entity = ent
        s1._memory = {"stress_ema": 0.1, "field_ema": 0.2, "speed_ema": 0.3}
        s1._mind = MindProfile.default_main_world()
        s2 = CentralBrainPvaec()
        s2.entity = _FakeEntity("b", 100.0, 150.0)
        s2._memory = {"stress_ema": 0.1, "field_ema": 0.2, "speed_ema": 0.3}
        s2._mind = MindProfile.from_dict({"gain_high_stress": 60.0, "wander_amp": 40.0})
        d1 = s1.think(dict(obs), 0.05)
        d2 = s2.think(dict(obs), 0.05)
        self.assertGreater(abs(d2["ax"] - d1["ax"]) + abs(d2["ay"] - d1["ay"]), 1e-6)


if __name__ == "__main__":
    unittest.main()
