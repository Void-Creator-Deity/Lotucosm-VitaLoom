"""advance_cell_visual_integrators：chemo 停则相位衰减。"""

from __future__ import annotations

import unittest

from core.VitaLoom.viewports.sr_visual_state import advance_cell_visual_integrators


class _Hub:
    id = "o1"


class SrVisualIntegratorTests(unittest.TestCase):
    def test_phase_advances_with_flow(self) -> None:
        hub = _Hub()
        _sig, mem0 = advance_cell_visual_integrators(hub, 0.8, 0.05, energy=0.7, vitality=0.6)
        _sig, mem1 = advance_cell_visual_integrators(hub, 0.8, 0.05, energy=0.7, vitality=0.6)
        self.assertGreater(mem1, mem0)

    def test_phase_decays_without_flow(self) -> None:
        hub = _Hub()
        hub._sr_vis_signal_phase = 1.0
        sig, _mem = advance_cell_visual_integrators(hub, 0.0, 0.05)
        self.assertLess(sig, 1.0)

    def test_membrane_slower_when_stressed(self) -> None:
        hub = _Hub()
        _, m_low = advance_cell_visual_integrators(hub, 0.2, 0.1, energy=0.8, stress=0.0)
        hub._sr_vis_membrane_phase = 0.0
        _, m_hi = advance_cell_visual_integrators(hub, 0.2, 0.1, energy=0.8, stress=0.9)
        self.assertGreater(m_low, m_hi)


if __name__ == "__main__":
    unittest.main()
