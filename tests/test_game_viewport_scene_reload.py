# -*- coding: utf-8 -*-
"""
切换项目/场景：丢弃旧 SR 运行时、播放中不写错误会话、resume 重载。

契约: _on_external_scene_context_changed；write_session=False 时禁止用新 scene_name 写旧 t。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from core.VitaLoom.viewports.game_viewport import GameViewport


class GameViewportSceneReloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def test_needs_reload_when_scene_path_changes(self) -> None:
        gv = GameViewport()
        gv._sr_runtime_dirty = False
        gv._sr_runtime_project_path = "/proj/a"
        gv._sr_runtime_scene_path = "/proj/a/scenes/main.pond"
        gv.editor_context.current_project_path = "/proj/b"
        self.assertTrue(gv._scene_runtime_needs_reload())

    def test_external_change_stops_paused_session(self) -> None:
        gv = GameViewport()
        gv._using_scene_runtime = True
        gv.is_playing = True
        gv.is_paused = True
        gv._scene_runtime_time = 99.0
        gv.scene_runtime_entities = [
            gv._SceneRuntimeEntity("o1", "organism", (0.0, 0.0), 10.0),
        ]
        gv._on_external_scene_context_changed("/other/scene.pond")
        self.assertFalse(gv.is_playing)
        self.assertEqual(len(gv.scene_runtime_entities), 0)
        self.assertTrue(gv._sr_runtime_dirty)

    # 契约: 换场景时 write_session=False，不产生 stopped 摘要

    def test_external_change_skips_session_log(self) -> None:
        gv = GameViewport()
        gv._sr_session_log_enabled = True
        gv._using_scene_runtime = True
        gv.is_playing = True
        gv._sr_session_stamp = "stamp_a"
        gv.scene_runtime_entities = [
            gv._SceneRuntimeEntity("o1", "organism", (0.0, 0.0), 10.0),
        ]
        with patch.object(gv, "_write_sr_session_summary") as mock_write:
            gv._on_external_scene_context_changed("/other/scene.pond")
        mock_write.assert_not_called()

    # 契约: goals_complete 后手动 stop 不再写第二份 stopped

    def test_stop_skips_duplicate_after_goals_complete(self) -> None:
        gv = GameViewport()
        gv._sr_session_log_enabled = True
        gv._using_scene_runtime = True
        gv._sr_last_session_end_reason = "goals_complete"
        gv.scene_runtime_entities = [
            gv._SceneRuntimeEntity("o1", "organism", (0.0, 0.0), 10.0),
        ]
        with patch.object(gv, "_write_sr_session_summary") as mock_write:
            gv._stop_simulation()
        mock_write.assert_not_called()

    def test_scene_change_discards_old_epoch_and_first_tick_uses_new_lifetime(self) -> None:
        from types import SimpleNamespace

        from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
            create_worldbridge_deterministic_randomness_context,
        )
        from core.Lotucosm.runtime.world_bridge_input_sequence import WorldBridgeInputSequence
        from core.Lotucosm.runtime.world_bridge_tick_authority import WorldBridgeTickAuthority
        from core.VitaLoom.viewports.sr_input_state import SrInputState

        gv = GameViewport()
        authority = WorldBridgeTickAuthority(input_sequence=WorldBridgeInputSequence())
        authority.bind_randomness_context(
            create_worldbridge_deterministic_randomness_context("scene-reload", "seed")
        )
        gv._worldbridge_tick_authority = authority
        gv._worldbridge_input_sequence = authority.input_sequence
        gv._worldbridge_input_events_last_tick = []
        gv._sr_input = SrInputState()
        gv._unified_pond = None
        gv.is_playing = False
        gv._using_scene_runtime = True

        authority.input_sequence.append("key_down", {"key": "W"})
        authority.begin_tick(0.05)
        old_epoch = authority.input_sequence.pause_reset_epoch

        gv._on_external_scene_context_changed("/new/scene.pond")
        self.assertEqual(authority.current_tick(), None)
        self.assertEqual(authority.input_sequence.pause_reset_epoch, old_epoch + 1)

        authority.input_sequence.append("key_down", {"key": "D"})
        context = authority.begin_tick(0.05, lifecycle_action="tick")
        self.assertEqual(context["pause_reset_epoch"], old_epoch + 1)
        self.assertEqual(
            [event["payload"]["key"] for event in context["input_events"]],
            ["D"],
        )

    def test_capture_session_context_independent_of_later_scene(self) -> None:
        gv = GameViewport()
        gv.editor_context.current_project_path = "/proj/main"
        with patch.object(gv, "_runtime_context_key", return_value=("/proj/main", "/proj/main/scenes/main_scene.pond")):
            with patch(
                "core.VitaLoom.scene.scene_manager.get_scene_manager"
            ) as mock_sm:
                mock_sm.return_value.get_scene_data.return_value = {
                    "name": "主场景（细胞演化演示）",
                }
                gv._capture_sr_session_context()
        self.assertEqual(gv._sr_session_scene_name, "主场景（细胞演化演示）")
        self.assertEqual(gv._sr_session_project_path, "/proj/main")


if __name__ == "__main__":
    unittest.main()
