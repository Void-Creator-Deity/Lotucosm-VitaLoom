"""SimulationTransport：唯一模拟 transport 编排。"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, call


class SimulationTransportTests(unittest.TestCase):
    def _make_transport(self):
        from core.VitaLoom.simulation.simulation_transport import SimulationTransport

        ctx = MagicMock()
        ctx.event_bus = MagicMock()
        ctx.kernel = MagicMock()
        ctx.kernel.layout_manager = MagicMock()
        return SimulationTransport(ctx), ctx

    def test_request_play_switches_viewport_and_publishes(self):
        transport, ctx = self._make_transport()
        transport.request_play()
        ctx.kernel.layout_manager.switch_viewport.assert_called_once_with("game")
        ctx.event_bus.publish.assert_called_with("simulation_play")

    def test_request_toggle_pause_when_running(self):
        transport, ctx = self._make_transport()
        transport.sync_from_viewport(is_playing=True, is_paused=False, speed=1.0)
        ctx.event_bus.reset_mock()
        transport.request_toggle()
        ctx.event_bus.publish.assert_called_once_with("simulation_pause")

    def test_set_speed_clamps_and_publishes(self):
        transport, ctx = self._make_transport()
        transport.set_speed(9.0)
        ctx.event_bus.publish.assert_has_calls(
            [call("simulation_speed_changed", 5.0), call("simulation_transport_state", transport.state)]
        )
        self.assertEqual(transport.state.speed, 5.0)

    def test_play_toolbar_label_reflects_state(self):
        transport, _ctx = self._make_transport()
        tr = lambda k, d="": d
        self.assertIn("运行", transport.play_toolbar_label(tr))
        transport.sync_from_viewport(is_playing=True, is_paused=False, speed=1.0)
        self.assertIn("暂停", transport.play_toolbar_label(tr))
        transport.sync_from_viewport(is_playing=True, is_paused=True, speed=1.0)
        self.assertIn("继续", transport.play_toolbar_label(tr))


if __name__ == "__main__":
    unittest.main()
