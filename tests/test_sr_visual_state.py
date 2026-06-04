"""SR 视觉状态：从 PVAEC 实体抽取当帧指标。"""

from __future__ import annotations

import unittest

from core.VitaLoom.viewports.sr_visual_state import (
    extract_cell_visual_state,
    extract_entity_visual_state,
)


class _Ent:
    def __init__(self, eid: str, etype: str, **kw):
        self.id = eid
        self.entity_type = etype
        self.position = kw.get("position", [0.0, 0.0])
        self.velocity = kw.get("velocity", [0.0, 0.0])
        self.radius = kw.get("radius", 12.0)
        self.energy = kw.get("energy", None)
        self.emission_strength = kw.get("emission_strength", 0.0)
        self.sr_channel_out = kw.get("sr_channel_out", {})
        self.sr_debug_hud = kw.get("sr_debug_hud", {})


class SrVisualStateTests(unittest.TestCase):
    def test_low_energy_dims_vitality(self) -> None:
        hub = _Ent("o1", "organism", energy=15.0, emission_strength=0.1)
        cell = extract_cell_visual_state(hub, {"o1"}, {"o1": hub}, {"o1": "organism"}, [], [hub])
        self.assertLess(cell.vitality, 0.35)
        self.assertLess(cell.energy, 0.2)

    def test_chemo_drives_signal_flow(self) -> None:
        hub = _Ent("o1", "organism", energy=100.0, emission_strength=0.5)
        sensor = _Ent("s1", "sensor", sr_channel_out={"chemo": 0.9, "chemo_dir_x": 1.0, "chemo_dir_y": 0.0})
        actuator = _Ent("a1", "actuator")
        entities = [hub, sensor, actuator]
        id_to_ent = {"o1": hub, "s1": sensor, "a1": actuator}
        id_to_type = {k: v.entity_type for k, v in id_to_ent.items()}
        edges = [{"start": "s1", "end": "a1", "channel": "chemo", "weight": 1.0}]
        cell = extract_cell_visual_state(hub, {"o1", "s1", "a1"}, id_to_ent, id_to_type, edges, entities)
        self.assertGreater(cell.chemo_activity, 0.5)
        self.assertGreater(cell.by_entity["a1"].chemo_in, 0.3)

    def test_entity_stress(self) -> None:
        ent = _Ent("o1", "organism", sr_debug_hud={"stress": 0.8})
        st = extract_entity_visual_state(ent)
        self.assertAlmostEqual(st.stress, 0.8)


if __name__ == "__main__":
    unittest.main()
