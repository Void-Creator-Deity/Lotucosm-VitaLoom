# -*- coding: utf-8
"""SR 内外流体场：营养梯度驱动膜形变。"""
from __future__ import annotations

import math
import unittest
from types import SimpleNamespace

from core.Lotucosm.sr_fluid_flow import (
    build_cell_fluid_state,
    compute_membrane_flow_offsets,
    extracellular_flow_at,
    intracellular_flow_at,
)


def _nut(x, y, *, r=12.0, eid="n1"):
    return SimpleNamespace(
        id=eid,
        entity_type="nutrient",
        position=[x, y],
        velocity=[0.0, 0.0],
        radius=r,
        pinned=True,
    )


class SrFluidFlowTests(unittest.TestCase):
    def test_extracellular_flow_points_toward_nutrient(self) -> None:
        entities = [_nut(200.0, 100.0)]
        vx, vy, pot = extracellular_flow_at(100.0, 100.0, entities, {})
        self.assertGreater(vx, 0.0)
        self.assertAlmostEqual(vy, 0.0, delta=0.5)
        self.assertGreater(pot, 0.0)

    def test_intracellular_flow_toward_actuator(self) -> None:
        vx, vy = intracellular_flow_at(
            100.0,
            100.0,
            SimpleNamespace(id="o1"),
            hub_x=100.0,
            hub_y=100.0,
            energy=0.8,
            signal_flow=0.6,
            actuators=[(140.0, 100.0, 0.9)],
            sensors=[],
        )
        self.assertGreater(vx, 0.0)

    def test_membrane_offsets_vary_with_velocity(self) -> None:
        hub = SimpleNamespace(id="o1", position=[100.0, 100.0], radius=22.0, velocity=[80.0, 0.0])
        off_still, _ = compute_membrane_flow_offsets(
            100.0,
            100.0,
            segments=24,
            base_radius=40.0,
            hub=hub,
            cell_energy=0.7,
            cell_signal_flow=0.5,
            cell_speed=0.0,
            cell_stress=0.0,
            vel_x=0.0,
            vel_y=0.0,
            membrane_phase=0.0,
            actuators=[],
            sensors=[],
            entities=[],
            emissions_prev={},
        )
        off_move, _ = compute_membrane_flow_offsets(
            100.0,
            100.0,
            segments=24,
            base_radius=40.0,
            hub=hub,
            cell_energy=0.7,
            cell_signal_flow=0.5,
            cell_speed=0.8,
            cell_stress=0.0,
            vel_x=80.0,
            vel_y=0.0,
            membrane_phase=0.0,
            actuators=[],
            sensors=[],
            entities=[],
            emissions_prev={},
        )
        self.assertNotAlmostEqual(off_still[0], off_move[0], delta=0.05)
        self.assertGreater(max(off_move) - min(off_move), max(off_still) - min(off_still))

    def test_build_cell_fluid_state_exchange_sites(self) -> None:
        hub = SimpleNamespace(id="o1", position=[100.0, 100.0], radius=24.0, velocity=[0.0, 0.0])
        sensor = SimpleNamespace(
            id="s1",
            entity_type="sensor",
            position=[130.0, 100.0],
            radius=10.0,
            sr_channel_out={"chemo": 0.8},
        )
        actuator = SimpleNamespace(
            id="a1",
            entity_type="actuator",
            position=[70.0, 100.0],
            radius=10.0,
            velocity=[0.0, 0.0],
        )
        id_to_ent = {"o1": hub, "s1": sensor, "a1": actuator}
        id_to_type = {"o1": "organism", "s1": "sensor", "a1": "actuator"}
        from core.VitaLoom.viewports.sr_visual_state import SrEntityVisualState

        by_ent = {
            "s1": SrEntityVisualState(chemo_out=0.7),
            "a1": SrEntityVisualState(chemo_in=0.5, thrust=0.4),
        }
        state = build_cell_fluid_state(
            hub,
            {"o1", "s1", "a1"},
            id_to_ent,
            id_to_type,
            cell_energy=0.6,
            cell_signal_flow=0.5,
            cell_speed=0.2,
            cell_stress=0.0,
            vel_x=0.0,
            vel_y=0.0,
            membrane_phase=0.0,
            by_entity=by_ent,
            entities=[hub, sensor, actuator, _nut(200.0, 100.0)],
            emissions_prev={},
        )
        self.assertGreater(len(state.membrane_offsets), 16)
        dirs = {s.direction for s in state.exchange_sites}
        self.assertIn("in", dirs)
        self.assertIn("out", dirs)
        self.assertGreater(math.hypot(state.exo_vx, state.exo_vy), 0.0)

    def test_advect_fluid_particles_moves(self) -> None:
        from core.Lotucosm.sr_fluid_flow import SrCellFluidState, advect_fluid_particles

        hub = SimpleNamespace(id="o1", position=[100.0, 100.0], radius=24.0)
        fluid = SrCellFluidState(hub_id="o1", endo_vx=12.0, endo_vy=3.0, pressure_delta=0.5)
        nut = _nut(200.0, 100.0)
        advect_fluid_particles(
            hub,
            fluid,
            cx=100.0,
            cy=100.0,
            membrane_radius=40.0,
            dt=0.05,
            entities=[hub, nut],
            emissions_prev={},
        )
        exo = getattr(hub, "_sr_fluid_exo_particles", None)
        endo = getattr(hub, "_sr_fluid_endo_particles", None)
        self.assertIsInstance(exo, list)
        self.assertIsInstance(endo, list)
        self.assertEqual(len(exo), 10)
        self.assertEqual(len(endo), 8)


if __name__ == "__main__":
    unittest.main()
