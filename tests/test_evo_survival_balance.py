# -*- coding: utf-8 -*-
"""
主世界演化脚本：无摄食时应在合理时间内仍存活（代谢按 dt 积分）。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import importlib.util
import json
import math
import unittest
from pathlib import Path

from core.Lotucosm.scene_runtime_context import RuntimePeerSnapshot, SceneRuntimeTickContext

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "projects" / "pvaec-细胞演化" / "scripts" / "evo_central_brain_pvaec.py"
_SCENE = _ROOT / "projects" / "pvaec-细胞演化" / "scenes" / "main_scene.pond"


def _load_evo():
    spec = importlib.util.spec_from_file_location("evo_brain", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.EvoCentralBrainPvaec


class _Ent:
    def __init__(self):
        self.id = "ai_organism_01"
        self.position = [460.0, 310.0]
        self.velocity = [0.0, 0.0]
        self.radius = 32.0
        self.energy = 125.0
        self.generation = 0
        self.emission_strength = 0.0
        self.sr_debug_hud = {}


class EvoSurvivalBalanceTests(unittest.TestCase):
    def setUp(self) -> None:
        scene = json.loads(_SCENE.read_text(encoding="utf-8"))
        org = next(e for e in scene["entities"] if e.get("type") == "organism")
        self._props = org["scripts"][0]["properties"]
        self._evo = _load_evo()

    def test_no_food_20_sim_seconds_still_alive(self) -> None:
        s = self._evo()
        ent = _Ent()
        s.entity = ent
        s._scene_script_properties = self._props
        s.start()
        dt = 0.05
        sim_t = 0.0
        for _ in range(int(20.0 / dt)):
            sim_t += dt
            ctx = SceneRuntimeTickContext(
                owner_id=ent.id,
                owner_type="organism",
                owner_position=(ent.position[0], ent.position[1]),
                owner_radius=ent.radius,
                bounds=(920, 620),
                simulation_time=sim_t,
                delta_time=dt,
                peers=(),
                spawn_requests=[],
                removal_requests=[],
                capabilities={"dynamic_spawn": True, "dynamic_despawn": True},
            )
            obs = s.perceive(ctx)
            dec = s.think(obs, dt)
            s._pvaec_tick_ctx = ctx
            s._pvaec_last_observation = obs
            s.act(dec, dt)
        self.assertGreater(
            float(ent.energy),
            30.0,
            "20 模拟秒内无食物时不应耗尽（检查代谢是否按 delta_time 积分）",
        )

    def test_starter_grace_reduces_early_drain(self) -> None:
        s = self._evo()
        ent = _Ent()
        s.entity = ent
        evo = dict(self._props.get("evo", {}))
        evo["feed_from_field"] = 0.0
        evo["well_proximity_feed"] = 0.0
        s._scene_script_properties = {**self._props, "evo": evo}
        s.start()

        def one_step(sim_t: float) -> float:
            ent.energy = 100.0
            dt = 0.05
            ctx = SceneRuntimeTickContext(
                owner_id=ent.id,
                owner_type="organism",
                owner_position=(460.0, 310.0),
                owner_radius=32.0,
                bounds=(920, 620),
                simulation_time=sim_t,
                delta_time=dt,
                peers=(),
                spawn_requests=[],
                removal_requests=[],
                capabilities={"dynamic_spawn": True},
            )
            obs = s.perceive(ctx)
            dec = s.think(obs, dt)
            s._pvaec_tick_ctx = ctx
            s._pvaec_last_observation = obs
            s.act(dec, dt)
            return float(ent.energy)

        early = one_step(5.0)
        late = one_step(25.0)
        self.assertGreater(early, late, "开局缓冲期应比 18s 后扣能更慢")


if __name__ == "__main__":
    unittest.main()
