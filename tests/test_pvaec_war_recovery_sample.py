# -*- coding: utf-8 -*-
"""PVAEC · 战争后进化：脚本冒烟与场景契约。"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

from core.Lotucosm.scene_runtime_context import RuntimePeerSnapshot, SceneRuntimeTickContext

from core.Lotucosm.sr_war_combat import WarCombatProfile
from core.Lotucosm.sr_war_recovery import WarRecoveryProfile

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _ROOT / "workspace" / "projects" / "samples" / "pvaec-战争后进化" / "scripts"
_SCENE = _ROOT / "workspace" / "projects" / "samples" / "pvaec-战争后进化" / "scenes" / "war_recovery_scene.pond"


def _load_cls(module_slug: str, class_name: str):
    if str(_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS))
    path = _SCRIPTS / f"{module_slug}.py"
    spec = importlib.util.spec_from_file_location(f"war_{module_slug}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, class_name)


WarRecoveryDirectorPvaec = _load_cls("war_recovery_director_pvaec", "WarRecoveryDirectorPvaec")
EvoWarRecoveryBrainPvaec = _load_cls("evo_war_recovery_brain_pvaec", "EvoWarRecoveryBrainPvaec")
ActuatorSpikeCombatPvaec = _load_cls("actuator_spike_combat_pvaec", "ActuatorSpikeCombatPvaec")


class _Fake:
    def __init__(self) -> None:
        self.id = "e1"
        self.position = [300.0, 250.0]
        self.velocity = [0.0, 0.0]
        self.radius = 12.0
        self.emission_strength = 0.0


def _ctx(**kwargs):
    base = dict(
        owner_id="dir",
        owner_type="environment_well",
        owner_position=(460.0, 80.0),
        owner_radius=30.0,
        bounds=(920, 620),
        simulation_time=50.0,
        delta_time=0.05,
        peers=(
            RuntimePeerSnapshot("n1", "nutrient", (500.0, 200.0), 11.0, 40.0, 8.0),
        ),
    )
    base.update(kwargs)
    return SceneRuntimeTickContext(**base)


class WarRecoverySmokeTests(unittest.TestCase):
    def test_scene_has_war_recovery_block(self) -> None:
        data = json.loads(_SCENE.read_text(encoding="utf-8"))
        wr = data.get("sr_war_recovery")
        self.assertIsInstance(wr, dict)
        self.assertLess(wr["peace_until"], wr["war_until"])
        combat = wr.get("combat")
        self.assertIsInstance(combat, dict)
        self.assertTrue(combat.get("combat_enabled_in_war"))
        nutrients = [e for e in data["entities"] if e.get("type") == "nutrient"]
        self.assertGreaterEqual(len(nutrients), 8)

    def test_director_war_phase_raises_emission(self) -> None:
        s = WarRecoveryDirectorPvaec()
        fake = _Fake()
        s.entity = fake
        s.start()
        profile = WarRecoveryProfile(peace_until=45.0, war_until=80.0)
        ctx = SceneRuntimeTickContext(
            owner_id="dir",
            owner_type="environment_well",
            owner_position=(460.0, 80.0),
            owner_radius=30.0,
            bounds=(920, 620),
            simulation_time=55.0,
            delta_time=0.05,
            peers=(),
            environment={
                "war_recovery_profile": profile.to_dict(),
                "war_override_until": 0.0,
                "war_phase": "war",
            },
        )
        s.pvaec_step(ctx, 0.05)
        self.assertGreater(float(fake.emission_strength), 0.7)

    def test_evo_war_brain_combat_hud_in_war(self) -> None:
        s = EvoWarRecoveryBrainPvaec()
        ent = _Fake()
        ent.energy = 100.0
        ent.generation = 0
        ent.sr_debug_hud = {}
        s.entity = ent
        s._scene_script_properties = {
            "evo": {"base_metabolism": 2.0, "speed_cost": 0.0, "niche_cost": 0.0, "feed_from_field": 0.0},
        }
        s.start()
        s._pvaec_last_observation = {
            "niche_pressure": 0.0,
            "ambient_field": 0.0,
            "intrinsic_speed": 0.0,
            "simulation_time": 55.0,
        }
        profile = WarRecoveryProfile(peace_until=45.0, war_until=80.0)
        combat = WarCombatProfile()
        s._pvaec_tick_ctx = SceneRuntimeTickContext(
            owner_id="e1",
            owner_type="organism",
            owner_position=(300.0, 250.0),
            owner_radius=12.0,
            bounds=(920, 620),
            simulation_time=55.0,
            delta_time=0.2,
            peers=(),
            environment={
                "war_recovery_profile": profile.to_dict(),
                "war_combat_profile": combat.to_dict(),
                "war_override_until": 0.0,
                "war_phase": "war",
            },
        )
        s.pvaec_step(s._pvaec_tick_ctx, 0.2)
        hud = ent.sr_debug_hud
        self.assertEqual(hud.get("war_phase"), "war")
        self.assertEqual(hud.get("combat_mode"), 1)
        self.assertIn("hp", hud)

    def test_spike_combat_deals_damage_in_war(self) -> None:
        s = ActuatorSpikeCombatPvaec()
        fake = _Fake()
        fake.id = "ai_organism_01_a1"
        s.entity = fake
        s.start()
        combat = WarCombatProfile()
        profile = WarRecoveryProfile(peace_until=45.0, war_until=80.0)
        damage: list = []
        ctx = SceneRuntimeTickContext(
            owner_id=fake.id,
            owner_type="actuator",
            owner_position=(300.0, 250.0),
            owner_radius=12.0,
            bounds=(920, 620),
            simulation_time=55.0,
            delta_time=0.5,
            peers=(
                RuntimePeerSnapshot(
                    "ai_organism_01", "organism", (320.0, 250.0), 28.0, 20.0, 5.0
                ),
                RuntimePeerSnapshot(
                    "ai_organism_02", "organism", (340.0, 255.0), 26.0, 25.0, 8.0
                ),
            ),
            environment={
                "war_recovery_profile": profile.to_dict(),
                "war_combat_profile": combat.to_dict(),
                "war_phase": "war",
                "membrane_attach": {fake.id: ("ai_organism_01", 40.0, 40.0)},
            },
            damage_requests=damage,
        )
        s.pvaec_step(ctx, 0.5)
        self.assertGreaterEqual(len(damage), 1)


if __name__ == "__main__":
    unittest.main()
