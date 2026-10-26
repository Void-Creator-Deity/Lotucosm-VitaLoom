# -*- coding: utf-8 -*-
"""sr_war_recovery 配置解析与营养目标单元测试。"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from core.Lotucosm.sr_war_recovery import (
    WAR_NUTRIENT_PURGE_INTERVAL,
    WarRecoveryProfile,
    nutrient_target_for_phase,
    phase_at_time,
    phase_countdown_hud,
    resolve_war_recovery,
    seconds_until_phase_boundary,
)

_ROOT = Path(__file__).resolve().parents[1]
_SCENE = _ROOT / "workspace" / "projects" / "samples" / "pvaec-战争后进化" / "scenes" / "war_recovery_scene.pond"


class SrWarRecoveryTests(unittest.TestCase):
    def test_resolve_scene_overrides_script(self) -> None:
        scene = {"sr_war_recovery": {"peace_until": 40.0, "war_until": 70.0}}
        props = {"war_recovery": {"peace_until": 10.0, "war_until": 20.0}}
        p = resolve_war_recovery(scene, props)
        self.assertEqual(p.peace_until, 40.0)
        self.assertEqual(p.war_until, 70.0)

    def test_phase_at_time_and_override(self) -> None:
        p = WarRecoveryProfile(peace_until=50.0, war_until=85.0)
        self.assertEqual(phase_at_time(10.0, p), "peace")
        self.assertEqual(phase_at_time(60.0, p), "war")
        self.assertEqual(phase_at_time(90.0, p), "recovery")
        self.assertEqual(phase_at_time(10.0, p, war_override_until=100.0), "war")

    def test_recovery_nutrient_boost(self) -> None:
        p = WarRecoveryProfile(
            nutrient_target_peace=8,
            recovery_nutrient_boost=3,
        )
        self.assertEqual(nutrient_target_for_phase("peace", p), 8)
        self.assertEqual(nutrient_target_for_phase("recovery", p), 11)
        self.assertEqual(nutrient_target_for_phase("war", p), 1)

    def test_scene_nutrient_count_matches_peace_target(self) -> None:
        data = json.loads(_SCENE.read_text(encoding="utf-8"))
        wr = data.get("sr_war_recovery") or {}
        nutrients = [e for e in data["entities"] if e.get("type") == "nutrient"]
        self.assertEqual(len(nutrients), int(wr.get("nutrient_target_peace", 8)))

    def test_effective_sr_nutrient_target_via_viewport(self) -> None:
        from core.VitaLoom.viewports.game_viewport import GameViewport

        host = MagicMock(spec=GameViewport)
        host._sr_war_profile = WarRecoveryProfile(
            peace_until=50.0,
            war_until=85.0,
            nutrient_target_peace=8,
            nutrient_target_war=1,
            recovery_nutrient_boost=3,
        )
        host._sr_nutrient_target_count = 8
        host._sr_war_recovery_override_until = 0.0

        def _phase(t: float) -> str:
            from core.Lotucosm.sr_war_recovery import phase_at_time

            return phase_at_time(
                t,
                host._sr_war_profile,
                war_override_until=float(host._sr_war_recovery_override_until or 0.0),
            )

        from core.Lotucosm.sr_war_recovery import nutrient_target_for_phase

        def effective(t: float) -> int:
            return nutrient_target_for_phase(_phase(t), host._sr_war_profile)

        host._scene_runtime_time = 20.0
        self.assertEqual(effective(20.0), 8)
        host._scene_runtime_time = 60.0
        self.assertEqual(effective(60.0), 1)
        host._scene_runtime_time = 100.0
        self.assertEqual(effective(100.0), 11)

    def test_preflush_war_nutrients_before_organism_batch(self) -> None:
        from core.VitaLoom.viewports.game_viewport import GameViewport

        host = MagicMock(spec=GameViewport)
        host._sr_war_profile = WarRecoveryProfile(peace_until=50.0, war_until=85.0)
        host._sr_war_recovery_override_until = 0.0
        host._scene_runtime_time = 60.0
        host._sr_war_nutrient_purge_acc = 0.0

        def _current_war_phase() -> str:
            from core.Lotucosm.sr_war_recovery import phase_at_time

            return phase_at_time(
                float(host._scene_runtime_time),
                host._sr_war_profile,
                war_override_until=float(host._sr_war_recovery_override_until or 0.0),
            )

        host._current_war_phase = _current_war_phase
        host._war_combat_mode_active = lambda: False

        class _Nut:
            def __init__(self, eid: str) -> None:
                self.id = eid
                self.entity_type = "nutrient"

        remove_ids: list[str] = []
        all_e = [_Nut("n1"), _Nut("n2")]
        GameViewport._preflush_war_nutrients(host, remove_ids, all_e, WAR_NUTRIENT_PURGE_INTERVAL)
        self.assertIn("n1", remove_ids)
        self.assertIn("n2", remove_ids)

    def test_phase_countdown_hud(self) -> None:
        p = WarRecoveryProfile(peace_until=50.0, war_until=85.0)
        self.assertAlmostEqual(seconds_until_phase_boundary(10.0, p), 40.0)
        self.assertAlmostEqual(seconds_until_phase_boundary(60.0, p), 25.0)
        self.assertEqual(seconds_until_phase_boundary(100.0, p), -1.0)
        hud = phase_countdown_hud(10.0, p, chinese=True)
        self.assertIn("40", hud)
        self.assertIn("战争", hud)

    def test_session_summary_markdown_includes_war_fields(self) -> None:
        from core.VitaLoom.viewports.game_viewport import (
            build_sr_session_summary_payload,
            format_sr_session_summary_markdown,
        )

        payload = build_sr_session_summary_payload(
            session_stamp="t1",
            end_reason="stopped",
            sim_time=90.0,
            organism_count=5,
            organism_peak=12,
            entity_count=20,
            play_goals={},
            victory_pause_done=False,
            extinction_pause_done=False,
            war_phase="recovery",
            population_at_war_end=7,
            war_population_min=3,
        )
        md = format_sr_session_summary_markdown(payload, chinese=True)
        self.assertIn("战争后进化", md)
        self.assertIn("恢复", md)
        self.assertIn("7", md)
        self.assertIn("3", md)


if __name__ == "__main__":
    unittest.main()
