# -*- coding: utf-8
"""官方 SR 2D 物理引擎（SrPhysics2DWorld）。"""
from __future__ import annotations

import math
import unittest
from types import SimpleNamespace

from core.Lotucosm.sr_physics2d import Physics2DMode, SrPhysics2DConfig, SrPhysics2DWorld


def _org(x, y, *, vx=0.0, r=20.0):
    return SimpleNamespace(
        entity_type="organism",
        position=[x, y],
        velocity=[vx, 0.0],
        radius=r,
        pinned=False,
        membrane_locked=False,
    )


def _nut(x, y, *, r=14.0):
    return SimpleNamespace(
        entity_type="nutrient",
        position=[x, y],
        velocity=[0.0, 0.0],
        radius=r,
        pinned=True,
        membrane_locked=False,
    )


class SrPhysics2DWorldTests(unittest.TestCase):
    def test_config_from_scene(self) -> None:
        cfg = SrPhysics2DConfig.from_scene_data(
            {"pond_config": {"sr_physics2d": {"restitution": 0.5, "contact_iterations": 6}}}
        )
        self.assertAlmostEqual(cfg.restitution, 0.5)
        self.assertEqual(cfg.contact_iterations, 6)

    def test_pvaec_step_separates_overlap(self) -> None:
        org = _org(50.0, 50.0, r=22.0)
        nut = _nut(50.0, 50.0)
        world = SrPhysics2DWorld(SrPhysics2DConfig(contact_iterations=4))
        world.step([org, nut], 0.016, 400, 400, mode=Physics2DMode.PVAEC)
        dist = ((org.position[0] - nut.position[0]) ** 2 + (org.position[1] - nut.position[1]) ** 2) ** 0.5
        self.assertGreaterEqual(dist, org.radius + nut.radius - 1.0)

    def test_game_mode_wall_mover(self) -> None:
        from core.Lotucosm.sr_game_entity_kind import is_game_wall

        wall = SimpleNamespace(
            id="wall_1",
            entity_type="game_prop",
            position=[100.0, 80.0],
            velocity=[0.0, 0.0],
            radius=28.0,
            pinned=True,
            membrane_locked=False,
            sr_visual=SimpleNamespace(sprite="wall"),
        )
        player = SimpleNamespace(
            id="player_rl",
            entity_type="game_actor",
            position=[100.0, 80.0],
            velocity=[0.0, 0.0],
            radius=22.0,
            pinned=False,
            membrane_locked=False,
        )
        self.assertTrue(is_game_wall(wall))
        world = SrPhysics2DWorld()
        world.step([wall, player], 0.016, 400, 400, mode=Physics2DMode.GAME)
        self.assertGreater(abs(player.position[1] - 80.0), 5.0)


    def test_proc_wall_disk_pushes_mover(self) -> None:
        from core.Lotucosm.sr_physics2d.game_contacts import resolve_game_contacts

        proc = SimpleNamespace(
            id="proc_wall_01",
            entity_type="game_prop",
            position=[200.0, 200.0],
            velocity=[0.0, 0.0],
            radius=24.0,
            pinned=True,
            membrane_locked=False,
            sr_visual=SimpleNamespace(sprite="wall"),
        )
        player = SimpleNamespace(
            id="player_rl",
            entity_type="game_actor",
            position=[200.0, 200.0],
            velocity=[0.0, 0.0],
            radius=22.0,
            pinned=False,
            membrane_locked=False,
        )
        cfg = SrPhysics2DConfig(game_contact_iterations=4)
        resolve_game_contacts([proc, player], config=cfg)
        dist = math.hypot(player.position[0] - 200.0, player.position[1] - 200.0)
        self.assertGreater(dist, 20.0)

    def test_infer_physics2d_mode_both_projects(self) -> None:
        from core.Lotucosm.sr_physics2d import infer_physics2d_mode

        self.assertEqual(
            infer_physics2d_mode({"sr_game_mode": True}),
            Physics2DMode.GAME,
        )
        self.assertEqual(
            infer_physics2d_mode({"pond_config": {}}),
            Physics2DMode.PVAEC,
        )

    def test_step_for_viewport_switches_mode(self) -> None:
        wall = SimpleNamespace(
            id="wall_n1",
            entity_type="game_prop",
            position=[100.0, 80.0],
            velocity=[0.0, 0.0],
            radius=28.0,
            pinned=True,
            membrane_locked=False,
            sr_visual=SimpleNamespace(sprite="wall"),
        )
        player = SimpleNamespace(
            id="player_rl",
            entity_type="game_actor",
            position=[100.0, 80.0],
            velocity=[0.0, 0.0],
            radius=22.0,
            pinned=False,
            membrane_locked=False,
        )
        org = _org(50.0, 50.0, r=22.0)
        nut = _nut(50.0, 50.0)

        game_host = SimpleNamespace(_sr_game_mode=True, _sr_spring_links=())
        pvaec_host = SimpleNamespace(_sr_game_mode=False, _sr_spring_links=())
        world = SrPhysics2DWorld()

        world.step_for_viewport(game_host, [wall, player], 0.016, 400, 400)
        self.assertGreater(abs(player.position[1] - 80.0), 5.0)

        world.step_for_viewport(pvaec_host, [org, nut], 0.016, 400, 400)
        dist = math.hypot(org.position[0] - nut.position[0], org.position[1] - nut.position[1])
        self.assertGreaterEqual(dist, org.radius + nut.radius - 1.0)


if __name__ == "__main__":
    unittest.main()
