# -*- coding: utf-8
"""NavigationBody place_code 最小实现测试。"""
from __future__ import annotations

import unittest

from core.Lotucosm.sr_navigation_body import (
    cell_index,
    load_navigation_from_props,
    navigation_acceleration_bias,
    navigation_enabled_for_stage,
    navigation_state_to_props,
    update_place_familiarity,
)


class _Ent:
    position = [100.0, 100.0]


class NavigationBodyTests(unittest.TestCase):
    def test_cell_index(self) -> None:
        self.assertEqual(cell_index(100.0, 50.0, 80.0), (1, 0))

    def test_familiarity_and_bias(self) -> None:
        ent = _Ent()
        update_place_familiarity(ent, 100.0, 100.0, 0.9, cell_size=80.0)
        update_place_familiarity(ent, 180.0, 100.0, 0.9, cell_size=80.0)
        bx, by = navigation_acceleration_bias(ent, 100.0, 100.0, cell_size=80.0, blend=20.0)
        self.assertNotEqual(bx, 0.0)

    def test_spawn_props_roundtrip(self) -> None:
        ent = _Ent()
        update_place_familiarity(ent, 50.0, 50.0, 1.0)
        props = navigation_state_to_props(ent)
        ent2 = _Ent()
        load_navigation_from_props(ent2, {"initial_navigation": props})
        self.assertTrue(ent2.sr_navigation["place_familiarity"])

    def test_stage_gate(self) -> None:
        self.assertFalse(navigation_enabled_for_stage(True, 2))
        self.assertTrue(navigation_enabled_for_stage(True, 3))
        self.assertTrue(navigation_enabled_for_stage(False, 0))


if __name__ == "__main__":
    unittest.main()
