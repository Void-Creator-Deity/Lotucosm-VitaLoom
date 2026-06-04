# -*- coding: utf-8
"""游戏模式 tick 不进入 PVAEC 膜/chemo/生物圈管道。"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from core.Lotucosm.scene_runtime.game_tick import step_game_runtime


class GameModeSkipsPvaecIntegratorsTests(unittest.TestCase):
    def test_step_game_runtime_skips_membrane_and_biosphere(self) -> None:
        host = MagicMock()
        host._scene_runtime_time = 0.0
        host._scene_bounds.return_value = (920.0, 620.0)
        host.scene_runtime_entities = []
        host._sr_caps_game.return_value = {}
        host._sr_input_snapshot.return_value = MagicMock()
        host._run_script_tick_batch = MagicMock()
        host._process_sr_damage_requests = MagicMock()
        host._process_sr_removal_requests = MagicMock()
        host._process_sr_spawn_requests = MagicMock()
        host._refresh_sr_hud = MagicMock()
        host._maybe_log_scene_episode = MagicMock()

        with patch(
            "core.Lotucosm.scene_runtime.session_outcome.resolve_session_outcomes"
        ) as outcome:
            step_game_runtime(host, 0.05)

        host._sync_membrane_positions.assert_not_called()
        host._apply_actuator_coupling.assert_not_called()
        host._advance_sr_visual_integrators.assert_not_called()
        outcome.assert_called_once_with(host)

    def test_update_scene_runtime_entities_early_returns_in_game_mode(self) -> None:
        from core.VitaLoom.viewports.game_viewport import GameViewport

        gv = GameViewport.__new__(GameViewport)
        gv._sr_game_mode = True
        gv._sync_membrane_positions = MagicMock()

        with patch("core.Lotucosm.scene_runtime.game_tick.step_game_runtime") as step:
            GameViewport._update_scene_runtime_entities(gv, 0.05)
            step.assert_called_once_with(gv, 0.05)
        gv._sync_membrane_positions.assert_not_called()


if __name__ == "__main__":
    unittest.main()
