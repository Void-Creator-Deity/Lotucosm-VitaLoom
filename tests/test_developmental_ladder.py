# -*- coding: utf-8
"""PVAEC 个体发育阶梯（ADR-0004）单元测试。"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from core.Lotucosm.scene_runtime_context import RuntimePeerSnapshot, SceneRuntimeTickContext
from core.Lotucosm.sr_developmental_ladder import (
    MAX_DEVELOPMENTAL_STAGE,
    can_advance_stage,
    filter_observation_for_stage,
    perception_keys_for_stage,
    stage_min_ticks,
)

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化" / "scripts"


def _load_central_brain():
    if str(_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS))
    path = _SCRIPTS / "central_brain_pvaec.py"
    spec = importlib.util.spec_from_file_location("test_developmental_ladder_cb", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CentralBrainPvaec


CentralBrainPvaec = _load_central_brain()


class _FakeEntity:
    def __init__(self, eid: str = "e1"):
        self.id = eid
        self.position = [0.0, 0.0]
        self.velocity = [0.0, 0.0]
        self.energy = 100.0
        self.max_energy = 200.0
        self.health = 100.0
        self.max_health = 200.0
        self.sr_debug_hud = {}


class DevelopmentalLadderModuleTests(unittest.TestCase):
    def test_stage0_masks_peer_pulls(self) -> None:
        raw = {
            "sensor_pull": 0.9,
            "peer_organism_pull": 0.5,
            "world_load": 12.0,
            "simulation_time": 1.0,
            "bounds": (800, 600),
            "world_width": 800,
            "world_height": 600,
        }
        masked = filter_observation_for_stage(raw, 0)
        self.assertEqual(masked["sensor_pull"], 0.0)
        self.assertEqual(masked["peer_organism_pull"], 0.0)
        self.assertEqual(masked["world_load"], 0.0)

    def test_stage2_unlocks_sensor_pull(self) -> None:
        raw = {"sensor_pull": 0.42, "peer_organism_pull": 0.3, "simulation_time": 0.0}
        masked = filter_observation_for_stage(raw, 2)
        self.assertAlmostEqual(masked["sensor_pull"], 0.42)
        self.assertEqual(masked["peer_organism_pull"], 0.0)

    def test_can_advance_s0_to_s1(self) -> None:
        self.assertTrue(
            can_advance_stage(0, stage_min_ticks(0) + 1, explore_act_count=3, verify_success_count=0, remember_event_count=0, reproduced=False, organism_peer_count=0)
        )
        self.assertFalse(
            can_advance_stage(0, stage_min_ticks(0) + 1, explore_act_count=2, verify_success_count=0, remember_event_count=0, reproduced=False, organism_peer_count=0)
        )

    def test_perception_keys_monotonic(self) -> None:
        prev = 0
        for stage in range(MAX_DEVELOPMENTAL_STAGE + 1):
            keys = perception_keys_for_stage(stage)
            self.assertGreaterEqual(len(keys), prev)
            prev = len(keys)


class PvaecScriptDevelopmentalTests(unittest.TestCase):
    def test_pvaec_step_masks_before_think(self) -> None:
        script = CentralBrainPvaec()
        script.developmental_ladder_enabled = True
        script.developmental_stage = 0
        script.entity = _FakeEntity()
        p = RuntimePeerSnapshot("s1", "sensor", (10.0, 0.0), 5.0, 3.0, 0.0)
        ctx = SceneRuntimeTickContext(
            owner_id="e1",
            owner_type="organism",
            owner_position=(0.0, 0.0),
            owner_radius=20.0,
            bounds=(800, 600),
            simulation_time=0.0,
            delta_time=0.05,
            peers=(p,),
        )
        script.pvaec_step(ctx, 0.05)
        obs = script._pvaec_last_observation
        self.assertEqual(obs["sensor_pull"], 0.0)

    def test_on_stage_advance_writes_hud(self) -> None:
        script = CentralBrainPvaec()
        script.entity = _FakeEntity()
        script.on_stage_advance(2)
        self.assertEqual(script.entity.sr_debug_hud["developmental_stage"], 2)


if __name__ == "__main__":
    unittest.main()
