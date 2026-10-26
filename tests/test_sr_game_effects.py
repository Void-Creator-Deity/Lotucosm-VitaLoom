# -*- coding: utf-8
"""游戏战斗特效。

职责: 锁定 Roguelike 战斗 FX 的创建、摄取和生命周期更新。
排错: 失败时检查 sr_game_effects 的请求字段和时间衰减逻辑。
"""
from __future__ import annotations

import unittest

from core.Lotucosm.sr_game_effects import create_fx_state, ingest_fx_requests, update_game_fx


class SrGameEffectsTests(unittest.TestCase):
    def test_float_and_swing_decay(self) -> None:
        state = create_fx_state()
        ingest_fx_requests(
            state,
            [
                {"type": "float", "x": 10, "y": 20, "text": "35"},
                {"type": "swing", "x": 0, "y": 0, "angle": 0, "range": 30},
            ],
        )
        self.assertEqual(len(state.floats), 1)
        self.assertEqual(len(state.swings), 1)
        update_game_fx(state, 0.05)
        self.assertEqual(len(state.swings), 1)
        update_game_fx(state, 0.12)
        self.assertEqual(len(state.swings), 0)


if __name__ == "__main__":
    unittest.main()
