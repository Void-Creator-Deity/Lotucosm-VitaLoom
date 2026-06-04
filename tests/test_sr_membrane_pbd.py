# -*- coding: utf-8
"""膜 PBD 约束。"""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from core.Lotucosm.sr_membrane_pbd import refine_membrane_offsets_pbd


class SrMembranePbdTests(unittest.TestCase):
    def test_refine_changes_offsets(self) -> None:
        hub = SimpleNamespace(id="o1", position=[50.0, 50.0])
        offsets = [2.0] * 24
        out = refine_membrane_offsets_pbd(
            offsets,
            hub=hub,
            anchors=[(70.0, 50.0, 10.0)],
            segments=24,
            base_radius=30.0,
            dt=0.016,
            budget_ms=5.0,
        )
        self.assertEqual(len(out), 24)
        self.assertNotEqual(sum(out), sum(offsets))


if __name__ == "__main__":
    unittest.main()
