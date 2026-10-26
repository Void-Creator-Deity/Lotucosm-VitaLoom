# -*- coding: utf-8 -*-
"""sr_war_combat 与 sr_organism_combat 单元测试。"""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from core.Lotucosm.sr_organism_combat import pick_organism_melee_target
from core.Lotucosm.sr_war_combat import (
    WarCombatProfile,
    combat_active,
    death_mutation_probability,
    feeding_disabled,
    resolve_war_combat,
)


class SrWarCombatTests(unittest.TestCase):
    def test_resolve_combat_from_scene(self) -> None:
        scene = {
            "sr_war_recovery": {
                "combat": {
                    "melee_damage": 25.0,
                    "kill_score": 12,
                }
            }
        }
        c = resolve_war_combat(scene)
        self.assertAlmostEqual(c.melee_damage, 25.0)
        self.assertEqual(c.kill_score, 12)

    def test_feeding_disabled_only_in_war(self) -> None:
        c = WarCombatProfile()
        self.assertTrue(feeding_disabled("war", c))
        self.assertFalse(feeding_disabled("peace", c))
        self.assertFalse(feeding_disabled("recovery", c))

    def test_death_mutation_probability_scales(self) -> None:
        c = WarCombatProfile(
            death_mutation_base_prob=0.1,
            death_mutation_per_death=0.1,
            death_mutation_cap=0.8,
        )
        self.assertAlmostEqual(death_mutation_probability(0, c), 0.1)
        self.assertAlmostEqual(death_mutation_probability(3, c), 0.4)
        self.assertAlmostEqual(death_mutation_probability(20, c), 0.8)

    def test_combat_active_flag(self) -> None:
        c = WarCombatProfile(combat_enabled_in_war=True)
        self.assertTrue(combat_active("war", c))
        self.assertFalse(combat_active("peace", c))

    def test_pick_organism_melee_target(self) -> None:
        attacker = SimpleNamespace(
            id="a1",
            position=[100.0, 100.0],
            radius=20.0,
            velocity=[10.0, 0.0],
        )
        peer = SimpleNamespace(
            id="b1",
            entity_type="organism",
            position=[130.0, 100.0],
            radius=18.0,
            surface_gap=8.0,
        )
        far = SimpleNamespace(
            id="c1",
            entity_type="organism",
            position=[400.0, 100.0],
            radius=18.0,
            surface_gap=300.0,
        )
        hit = pick_organism_melee_target(
            attacker,
            (peer, far),
            reach=60.0,
            arc_half=1.2,
        )
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(str(hit.id), "b1")


if __name__ == "__main__":
    unittest.main()
