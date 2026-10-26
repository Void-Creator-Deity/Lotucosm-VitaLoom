# -*- coding: utf-8
"""evolution_defaults 工程字段与 SR 合并测试。"""
from __future__ import annotations

import unittest

from core.Lotucosm.experiment_config import PsExperimentConfig
from core.VitaLoom.project.evolution_context import (
    apply_developmental_profile_from_project,
    apply_evolution_defaults_to_ps_config,
    apply_evolution_defaults_to_sr_mind,
    evolution_defaults_from_ps_config,
    merge_evolution_defaults_into_scene_data,
)


class EvolutionContextTests(unittest.TestCase):
    def test_apply_defaults(self):
        cfg = PsExperimentConfig()
        apply_evolution_defaults_to_ps_config(
            cfg, {"mutation_rate": 0.2, "ticks": 100}
        )
        self.assertAlmostEqual(cfg.mutation_rate, 0.2)
        self.assertEqual(cfg.ticks, 100)

    def test_roundtrip_dict(self):
        cfg = PsExperimentConfig(mutation_rate=0.11, ticks=50)
        d = evolution_defaults_from_ps_config(cfg)
        cfg2 = PsExperimentConfig()
        apply_evolution_defaults_to_ps_config(cfg2, d)
        self.assertAlmostEqual(cfg2.mutation_rate, 0.11)
        self.assertEqual(cfg2.ticks, 50)

    def test_pond_mind_not_overwritten(self):
        scene = {
            "entities": [
                {
                    "scripts": [
                        {
                            "properties": {
                                "mind": {"mutation_rate": 0.01, "evo": {"generation_interval": 3}}
                            }
                        }
                    ]
                }
            ]
        }
        out = merge_evolution_defaults_into_scene_data(
            scene, {"evolution_defaults": {"mutation_rate": 0.99, "evolution_generation_interval": 9}}
        )
        mind = out["entities"][0]["scripts"][0]["properties"]["mind"]
        self.assertAlmostEqual(mind["mutation_rate"], 0.01)
        self.assertEqual(mind["evo"]["generation_interval"], 3)

    def test_defaults_fill_missing(self):
        mind = apply_evolution_defaults_to_sr_mind({}, {"mutation_rate": 0.2})
        self.assertAlmostEqual(mind["mutation_rate"], 0.2)


    def test_apply_developmental_profile(self) -> None:
        cfg = PsExperimentConfig()
        apply_developmental_profile_from_project(
            cfg, {"developmental_profile": {"enabled": True, "initial_stage": 2}}
        )
        self.assertTrue(cfg.developmental_ladder_enabled)
        self.assertEqual(cfg.developmental_initial_stage, 2)


if __name__ == "__main__":
    unittest.main()
