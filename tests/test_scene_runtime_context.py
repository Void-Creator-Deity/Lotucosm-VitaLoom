# -*- coding: utf-8 -*-
"""
SceneRuntimeTickContext：peers 距离、topology、inbound 只读映射。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
import unittest

from core.Lotucosm.scene_runtime_context import build_scene_runtime_tick_context


class _E:
    def __init__(self, eid, t, x, y, r=10.0):
        self.id = eid
        self.entity_type = t
        self.position = [x, y]
        self.radius = r


class SceneRuntimeContextTests(unittest.TestCase):
    def test_horizon_filters_distant_peer(self):
        owner = _E("o", "organism", 0, 0, r=10.0)
        near = _E("a", "sensor", 30, 0, r=5.0)
        far = _E("b", "sensor", 5000, 0, r=5.0)
        ctx = build_scene_runtime_tick_context(
            owner=owner,
            peers=[owner, near, far],
            bounds=(800, 600),
            simulation_time=1.0,
            delta_time=0.05,
            neighbor_radius_scale=6.0,
        )
        ids = {p.id for p in ctx.peers}
        self.assertIn("a", ids)
        self.assertNotIn("b", ids)

    def test_sorted_by_distance(self):
        owner = _E("o", "organism", 0, 0, r=10.0)
        p1 = _E("1", "actuator", 50, 0, r=5.0)
        p2 = _E("2", "sensor", 20, 0, r=5.0)
        ctx = build_scene_runtime_tick_context(
            owner=owner,
            peers=[p1, p2],
            bounds=(800, 600),
            simulation_time=0.0,
            delta_time=0.05,
        )
        self.assertEqual(ctx.peers[0].id, "2")

    def test_min_horizon_includes_distant_peer(self):
        owner = _E("o", "organism", 0, 0, r=10.0)
        ring = _E("far_sensor", "sensor", 350, 0, r=8.0)
        ctx = build_scene_runtime_tick_context(
            owner=owner,
            peers=[ring],
            bounds=(800, 600),
            simulation_time=0.0,
            delta_time=0.05,
            neighbor_radius_scale=6.0,
            min_horizon=400.0,
        )
        self.assertEqual(len(ctx.peers), 1)
        self.assertEqual(ctx.environment["ambient_field"], 0.0)


if __name__ == "__main__":
    unittest.main()
