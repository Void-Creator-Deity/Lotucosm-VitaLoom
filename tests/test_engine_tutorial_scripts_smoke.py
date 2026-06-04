# -*- coding: utf-8
"""织机教程 ScriptBase：importlib 加载 + sr_step 冒烟。"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from core.Lotucosm.scene_runtime_context import RuntimePeerSnapshot, SceneRuntimeTickContext
from core.VitaLoom.viewports.sr_input_state import SrInputSnapshot

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _ROOT / "projects" / "织机教程-迷你Roguelike" / "scripts"


def _load_cls(module_slug: str, class_name: str):
    path = _SCRIPTS / f"{module_slug}.py"
    spec = importlib.util.spec_from_file_location(f"tut_{module_slug}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, class_name)


PlayerController = _load_cls("player_controller", "PlayerController")
EnemyChaser = _load_cls("enemy_chaser", "EnemyChaser")
GameDirector = _load_cls("game_director", "GameDirector")


class _Fake:
    def __init__(self):
        self.id = "player_rl"
        self.position = [320.0, 310.0]
        self.velocity = [0.0, 0.0]
        self.radius = 22.0
        self.energy = 100.0
        self.sr_debug_hud = {"hp": 100.0, "hp_max": 100.0}
        self.sr_visual = None


def _ctx(**kwargs):
    base = dict(
        owner_id="player_rl",
        owner_type="game_actor",
        owner_position=(320.0, 310.0),
        owner_radius=22.0,
        bounds=(920, 620),
        simulation_time=1.0,
        delta_time=0.016,
        peers=(
            RuntimePeerSnapshot("enemy_01", "game_actor", (400.0, 300.0), 16.0, 40.0, 30.0),
            RuntimePeerSnapshot("exit_gate", "game_prop", (760.0, 310.0), 20.0, 0.0, 200.0),
        ),
        input=SrInputSnapshot(keys_down=frozenset({"D"})),
        environment={"game_player_id": "player_rl"},
    )
    base.update(kwargs)
    return SceneRuntimeTickContext(**base)


class EngineTutorialScriptsSmokeTests(unittest.TestCase):
    def test_player_controller_wasd_step(self) -> None:
        s = PlayerController()
        ent = _Fake()
        s.entity = ent
        s.start()
        s.sr_step(_ctx(), 0.016)
        self.assertGreater(ent.velocity[0], 0.0)

    def test_enemy_chaser_step(self) -> None:
        s = EnemyChaser()
        ent = _Fake()
        ent.id = "enemy_01"
        s.entity = ent
        s.start()
        s.sr_step(
            _ctx(
                owner_id="enemy_01",
                peers=(RuntimePeerSnapshot("player_rl", "game_actor", (320.0, 310.0), 22.0, 100.0, 50.0),),
                environment={"game_player_id": "player_rl"},
            ),
            0.016,
        )

    def test_game_director_clears_when_no_enemies_at_exit(self) -> None:
        s = GameDirector()
        ent = _Fake()
        s.entity = ent
        s.start()
        s.sr_step(
            _ctx(
                peers=(RuntimePeerSnapshot("exit_gate", "game_prop", (322.0, 310.0), 20.0, 0.0, 18.0),),
            ),
            0.016,
        )
        self.assertNotIn("dungeon_clear", ent.sr_debug_hud)
        s.sr_step(
            _ctx(
                peers=(
                    RuntimePeerSnapshot("enemy_01", "game_actor", (400.0, 300.0), 16.0, 40.0, 30.0),
                    RuntimePeerSnapshot("exit_gate", "game_prop", (322.0, 310.0), 20.0, 0.0, 18.0),
                ),
            ),
            0.016,
        )
        s.sr_step(
            _ctx(
                peers=(RuntimePeerSnapshot("exit_gate", "game_prop", (322.0, 310.0), 20.0, 0.0, 18.0),),
            ),
            0.016,
        )
        self.assertEqual(ent.sr_debug_hud.get("dungeon_clear"), 1)


if __name__ == "__main__":
    unittest.main()
