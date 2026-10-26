# -*- coding: utf-8
"""EvolutionProfile Phase C 单元测试。"""
from __future__ import annotations

import unittest

from core.Lotucosm.evolution_profile import (
    EvolutionProfile,
    apply_profile_to_evo_props,
    evolution_profile_from_mapping,
    evolution_profile_to_defaults,
    resolve_sr_reproduction_rates,
)
from core.Lotucosm.experiment_config import PsExperimentConfig
from core.VitaLoom.project.evolution_context import (
    apply_evolution_defaults_to_ps_config,
    apply_evolution_defaults_to_sr_props,
    evolution_defaults_from_ps_config,
    load_evolution_profile,
)


class EvolutionProfileTests(unittest.TestCase):
    def test_defaults_include_memory_fields(self) -> None:
        profile = evolution_profile_from_mapping({"mutation_rate": 0.1})
        d = evolution_profile_to_defaults(profile)
        self.assertIn("memory_gene_inheritance_rate", d)
        self.assertIn("mutation_sigma", d)
        self.assertAlmostEqual(d["memory_gene_mutation_rate"], 0.1)

    def test_mutation_sigma_derived(self) -> None:
        p = evolution_profile_from_mapping({"mutation_rate": 0.08})
        self.assertAlmostEqual(p.mutation_sigma, 0.08 * 4.75)

    def test_evo_props_fill_missing_only(self) -> None:
        profile = evolution_profile_from_mapping({"memory_gene_inheritance_rate": 0.7})
        out = apply_profile_to_evo_props({"mutation_sigma": 0.5}, profile, fill_missing_only=True)
        self.assertAlmostEqual(out["mutation_sigma"], 0.5)
        self.assertAlmostEqual(out["memory_gene_inheritance_rate"], 0.7)

    def test_sr_resolve_layers(self) -> None:
        p = resolve_sr_reproduction_rates(
            {"memory_gene_inheritance_rate": 0.6},
            {"memory_gene_inheritance_rate": 0.9, "mutation_rate": 0.05},
        )
        self.assertAlmostEqual(p.memory_gene_inheritance_rate, 0.6)
        self.assertAlmostEqual(p.mutation_rate, 0.05)

    def test_load_from_project(self) -> None:
        p = load_evolution_profile(
            {
                "evolution_defaults": {
                    "memory_gene_inheritance_rate": 0.75,
                    "gene_keys": ["wander_amp"],
                }
            }
        )
        self.assertAlmostEqual(p.memory_gene_inheritance_rate, 0.75)
        self.assertEqual(p.gene_keys[0], "wander_amp")

    def test_ps_config_roundtrip_extended(self) -> None:
        cfg = PsExperimentConfig()
        apply_evolution_defaults_to_ps_config(
            cfg,
            {
                "mutation_rate": 0.2,
                "memory_gene_inheritance_rate": 0.77,
            },
        )
        self.assertAlmostEqual(cfg.mutation_rate, 0.2)
        d = evolution_defaults_from_ps_config(cfg)
        self.assertIn("memory_gene_inheritance_rate", d)

    def test_sr_props_merge_evo(self) -> None:
        props = apply_evolution_defaults_to_sr_props(
            {"evo": {"reproduce_energy": 128.0}},
            {"memory_gene_inheritance_rate": 0.82, "mutation_sigma": 0.4},
        )
        self.assertAlmostEqual(props["evo"]["memory_gene_inheritance_rate"], 0.82)
        self.assertAlmostEqual(props["evo"]["reproduce_energy"], 128.0)


if __name__ == "__main__":
    unittest.main()
