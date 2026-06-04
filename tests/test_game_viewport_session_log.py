# -*- coding: utf-8 -*-
"""
SR 会话摘要：build_sr_session_summary_payload / Markdown 落盘。

契约: scene_name 来自开局快照（_capture_sr_session_context），非写盘时 SceneManager；
换场景写盘见 test_game_viewport_scene_reload.py。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import json
import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from core.VitaLoom.viewports.game_viewport import (
    GameViewport,
    build_sr_session_summary_payload,
    format_sr_session_summary_markdown,
    sr_all_play_goals_satisfied,
)


class SrSessionSummaryTests(unittest.TestCase):
    def test_build_payload_goals_satisfied(self) -> None:
        p = build_sr_session_summary_payload(
            session_stamp="20260101_120000",
            end_reason="goals_complete",
            sim_time=120.0,
            organism_count=5,
            organism_peak=5,
            entity_count=12,
            play_goals={"survive_seconds": 100, "peak_population": 5},
            victory_pause_done=True,
            extinction_pause_done=False,
        )
        self.assertTrue(p["sr_play_goals_satisfied"])
        self.assertEqual(p["end_reason_zh"], "演示目标达成")

    def test_markdown_chinese_contains_peak(self) -> None:
        p = build_sr_session_summary_payload(
            session_stamp="x",
            end_reason="extinction",
            sim_time=30.0,
            organism_count=0,
            organism_peak=3,
            entity_count=8,
            play_goals={},
            victory_pause_done=False,
            extinction_pause_done=True,
        )
        md = format_sr_session_summary_markdown(p, chinese=True)
        self.assertIn("种群灭绝", md)
        self.assertIn("峰值 3", md)


class GameViewportSessionLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self._proj = Path(__file__).resolve().parents[1]
        self._log_dir = self._proj / "logs" / "sr_sessions"
        shutil.rmtree(self._log_dir, ignore_errors=True)

    def tearDown(self) -> None:
        shutil.rmtree(self._log_dir, ignore_errors=True)

    def test_write_session_summary_creates_json_and_md(self) -> None:
        gv = GameViewport()
        gv._sr_session_log_enabled = True
        gv._sr_session_stamp = "test_stamp"
        gv._using_scene_runtime = True
        gv._scene_runtime_time = 99.0
        gv._sr_pop_peak = 4
        gv._sr_play_goals = {"survive_seconds": 60, "peak_population": 4, "pause_on_complete": True}
        gv._sr_victory_pause_done = True
        gv._sr_demo_legend = {"title": "图例"}
        gv.scene_runtime_entities = [
            gv._SceneRuntimeEntity("o1", "organism", (10.0, 10.0), 20.0),
        ]
        returned = gv._write_sr_session_summary("stopped")
        files = list(self._log_dir.glob("session_test_stamp_stopped.*"))
        self.assertEqual(len(files), 2)
        jp = self._log_dir / "session_test_stamp_stopped.json"
        mp = self._log_dir / "session_test_stamp_stopped.md"
        self.assertTrue(jp.is_file() and mp.is_file())
        self.assertEqual(returned, mp)
        self.assertEqual(gv._sr_last_session_md_path, mp)
        self.assertEqual(gv._sr_last_session_end_reason, "stopped")
        data = json.loads(jp.read_text(encoding="utf-8"))
        self.assertEqual(data["end_reason"], "stopped")
        self.assertTrue(sr_all_play_goals_satisfied(
            {"survive_seconds": 60, "peak_population": 4}, 99.0, 4
        ))
        self.assertIn("手动停止", mp.read_text(encoding="utf-8"))

    def test_payload_includes_membrane_topology_fields(self) -> None:
        p = build_sr_session_summary_payload(
            session_stamp="m",
            end_reason="stopped",
            sim_time=10.0,
            organism_count=1,
            organism_peak=2,
            entity_count=6,
            play_goals={},
            victory_pause_done=False,
            extinction_pause_done=False,
            membrane_sensor_count=3,
            mean_edge_weight=1.1,
            mean_chemo_channel=0.42,
        )
        md = format_sr_session_summary_markdown(p, chinese=True)
        self.assertIn("膜拓扑", md)
        self.assertIn("膜受体数", md)
        self.assertIn("1.100", md)

    def test_session_log_disabled_by_env(self) -> None:
        with patch.dict(os.environ, {"LOTUCOSM_SR_SESSION_LOG": "0"}, clear=False):
            gv = GameViewport()
        self.assertFalse(gv._sr_session_log_enabled)


if __name__ == "__main__":
    unittest.main()
