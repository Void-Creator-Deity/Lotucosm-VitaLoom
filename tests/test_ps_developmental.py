# -*- coding: utf-8
"""PS 个体发育阶梯（ADR-0004）单元测试。"""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from builtin.entity_types.organism import Organism
from builtin.systems.inheritance import InheritanceSystem
from core.Lotucosm.experiment_config import PsExperimentConfig
from core.Lotucosm.ps_developmental import (
    filter_ps_perception_for_stage,
    gate_ps_generate_action,
    gate_ps_retrieve,
    maybe_advance_ps_developmental_stage,
    reset_ps_developmental_for_child,
)
from core.Lotucosm.sr_developmental_ladder import stage_min_ticks
from core.VitaLoom.project.evolution_context import apply_developmental_profile_from_project


class _FakeOrganism:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", "o1")
        self.organism_id = self.id
        self.age = kwargs.get("age", 0)
        self.energy = kwargs.get("energy", 100.0)
        self.max_energy = kwargs.get("max_energy", 200.0)
        self.health = kwargs.get("health", 100.0)
        self.max_health = kwargs.get("max_health", 100.0)
        self.components = kwargs.get("components", {"sensor_a": object(), "motor_b": object()})
        self.developmental_ladder_enabled = kwargs.get("developmental_ladder_enabled", False)
        self.developmental_stage = kwargs.get("developmental_stage", 0)
        self._developmental_stage_ticks = 0
        self._developmental_explore_act_count = 0
        self._developmental_verify_success_count = 0
        self._developmental_remember_event_count = 0
        self._developmental_reproduced = False
        self._developmental_last_offspring = 0
        self.offspring_count = 0


class PsDevelopmentalModuleTests(unittest.TestCase):
    def test_stage0_filters_component_sense(self) -> None:
        perception = {
            "intero_energy": 0.8,
            "sensor_a": {"value": 1.0},
            "motor_b": {"value": 2.0},
        }
        filtered = filter_ps_perception_for_stage(
            perception,
            0,
            ["sensor_a", "motor_b"],
        )
        self.assertIn("intero_energy", filtered)
        self.assertNotIn("sensor_a", filtered)
        self.assertNotIn("motor_b", filtered)

    def test_stage2_unlocks_first_component(self) -> None:
        perception = {
            "intero_energy": 0.8,
            "_pvaec_tick": 3,
            "sensor_a": {"value": 1.0},
            "motor_b": {"value": 2.0},
        }
        filtered = filter_ps_perception_for_stage(
            perception,
            2,
            ["sensor_a", "motor_b"],
        )
        self.assertIn("sensor_a", filtered)
        self.assertNotIn("motor_b", filtered)

    def test_gate_retrieve_empty_before_s2(self) -> None:
        org = _FakeOrganism(developmental_ladder_enabled=True, developmental_stage=1)
        self.assertEqual(gate_ps_retrieve(org, [{"x": 1}]), [])

    def test_gate_generate_explore_only_before_s2(self) -> None:
        org = _FakeOrganism(developmental_ladder_enabled=True, developmental_stage=0)
        action = gate_ps_generate_action(
            org,
            {"sensor_a": {"command": "move"}, "motor_b": {"command": "push"}},
        )
        self.assertEqual(action["sensor_a"]["command"], "explore")
        self.assertNotIn("motor_b", action)

    def test_child_resets_to_s0(self) -> None:
        parent = _FakeOrganism(
            developmental_ladder_enabled=True,
            developmental_stage=3,
        )
        parent._developmental_explore_act_count = 9
        child = _FakeOrganism(developmental_ladder_enabled=False, developmental_stage=2)
        reset_ps_developmental_for_child(child, parent)
        self.assertTrue(child.developmental_ladder_enabled)
        self.assertEqual(child.developmental_stage, 0)
        self.assertEqual(child._developmental_explore_act_count, 0)

    def test_inheritance_system_resets_child_stage(self) -> None:
        parent = Organism("p1", (0.0, 0.0))
        parent.developmental_ladder_enabled = True
        parent.developmental_stage = 2
        parent._developmental_verify_success_count = 5
        child = InheritanceSystem().inherit(parent, (1.0, 1.0))
        self.assertTrue(child.developmental_ladder_enabled)
        self.assertEqual(child.developmental_stage, 0)
        self.assertEqual(child._developmental_verify_success_count, 0)

    def test_apply_profile_from_project_json(self) -> None:
        cfg = PsExperimentConfig()
        apply_developmental_profile_from_project(
            cfg,
            {"developmental_profile": {"enabled": True, "initial_stage": 1}},
        )
        self.assertTrue(cfg.developmental_ladder_enabled)
        self.assertEqual(cfg.developmental_initial_stage, 1)

    def test_organism_init_has_developmental_defaults(self) -> None:
        org = Organism("x1", (0.0, 0.0))
        self.assertFalse(org.developmental_ladder_enabled)
        self.assertEqual(org.developmental_stage, 0)
        self.assertTrue(hasattr(org, "_developmental_stage_ticks"))

    def test_maybe_advance_s0_to_s1(self) -> None:
        org = _FakeOrganism(developmental_ladder_enabled=True, developmental_stage=0)
        org._developmental_stage_ticks = stage_min_ticks(0) + 1
        org._developmental_explore_act_count = 3
        env = SimpleNamespace(organisms={"a": org, "b": object()})
        maybe_advance_ps_developmental_stage(org, env)
        self.assertEqual(org.developmental_stage, 1)


if __name__ == "__main__":
    unittest.main()
