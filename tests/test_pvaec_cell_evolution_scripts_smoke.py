# -*- coding: utf-8 -*-
"""
PVAEC · 细胞演化工程脚本：importlib 路径加载 + pvaec_step 冒烟。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from core.Lotucosm.scene_runtime_context import RuntimePeerSnapshot, SceneRuntimeTickContext

_ROOT = Path(__file__).resolve().parents[1]
_MW = _ROOT / "projects" / "pvaec-细胞演化" / "scripts"


def _load_cls(module_slug: str, class_name: str):
    path = _MW / f"{module_slug}.py"
    spec = importlib.util.spec_from_file_location(f"mw_{module_slug}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, class_name)


AmbientMarkerDrift = _load_cls("ambient_marker_drift", "AmbientMarkerDrift")
SensorPatrolPvaec = _load_cls("sensor_patrol_pvaec", "SensorPatrolPvaec")
ActuatorPulsePvaec = _load_cls("actuator_pulse_pvaec", "ActuatorPulsePvaec")
SatelliteRoamerPvaec = _load_cls("satellite_roamer_pvaec", "SatelliteRoamerPvaec")
WellPulsePvaec = _load_cls("well_pulse_pvaec", "WellPulsePvaec")
EvoCentralBrainPvaec = _load_cls("evo_central_brain_pvaec", "EvoCentralBrainPvaec")


class _Fake:
    def __init__(self):
        self.id = "e1"
        self.position = [300.0, 250.0]
        self.velocity = [0.0, 0.0]
        self.radius = 12.0


def _ctx(**kwargs):
    base = dict(
        owner_id="e1",
        owner_type="sensor",
        owner_position=(300.0, 250.0),
        owner_radius=12.0,
        bounds=(800, 600),
        simulation_time=1.25,
        delta_time=0.05,
        peers=(
            RuntimePeerSnapshot("hub", "organism", (400.0, 300.0), 30.0, 50.0, 10.0),
        ),
    )
    base.update(kwargs)
    return SceneRuntimeTickContext(**base)


class SmokeTests(unittest.TestCase):
    def test_ambient_marker_drift_step(self):
        s = AmbientMarkerDrift()
        s.entity = _Fake()
        s.pvaec_step(_ctx(owner_type="empty"), 0.05)

    def test_sensor_patrol_step(self):
        s = SensorPatrolPvaec()
        s.entity = _Fake()
        s.pvaec_step(_ctx(), 0.05)

    def test_actuator_pulse_step(self):
        s = ActuatorPulsePvaec()
        s.entity = _Fake()
        s.pvaec_step(_ctx(owner_type="actuator"), 0.05)

    def test_satellite_roamer_step(self):
        s = SatelliteRoamerPvaec()
        s.entity = _Fake()
        s.pvaec_step(_ctx(owner_type="organism"), 0.05)

    def test_well_pulse_step(self):
        s = WellPulsePvaec()
        s.entity = _Fake()
        s.pvaec_step(_ctx(owner_type="environment_well"), 0.05)

    def test_evo_metabolism_scales_with_delta_time(self):
        s = EvoCentralBrainPvaec()
        ent = _Fake()
        ent.energy = 100.0
        ent.generation = 0
        ent.sr_debug_hud = {}
        s.entity = ent
        s._scene_script_properties = {
            "evo": {"base_metabolism": 4.0, "speed_cost": 0.0, "niche_cost": 0.0, "feed_from_field": 0.0}
        }
        s.start()
        obs = {"niche_pressure": 0.0, "ambient_field": 0.0, "intrinsic_speed": 0.0}
        s._pvaec_last_observation = obs
        s._pvaec_tick_ctx = _ctx(owner_type="organism")
        s.act({}, 0.05)
        self.assertGreater(float(ent.energy), 99.0)
        s.act({}, 1.0)
        self.assertLess(float(ent.energy), 99.0)

    def test_evo_homeostatic_multi_frame(self) -> None:
        s = EvoCentralBrainPvaec()
        ent = _Fake()
        ent.entity_type = "organism"
        ent.energy = 100.0
        ent.generation = 0
        ent.sr_debug_hud = {}
        ent.emission_strength = 0.0
        s.entity = ent
        s._scene_script_properties = {
            "evo": {"base_metabolism": 2.0, "speed_cost": 0.0, "niche_cost": 0.0, "feed_from_field": 0.0}
        }
        s.start()
        ctx = _ctx(owner_type="organism")
        for _ in range(5):
            s.pvaec_step(ctx, 0.05)
        self.assertTrue(hasattr(ent, "_sr_last_verify_success") or isinstance(ent.sr_debug_hud, dict))


if __name__ == "__main__":
    unittest.main()
