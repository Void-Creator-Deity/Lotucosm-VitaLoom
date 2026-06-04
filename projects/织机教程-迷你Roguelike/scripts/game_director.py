# -*- coding: utf-8
"""织机教程 · 导演：程序化障碍 + 清场后抵近出口。"""
from __future__ import annotations

from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext
from core.Lotucosm.scripts import ScriptBase
from core.Lotucosm.sr_game_procedural import generate_wall_spawns


class GameDirector(ScriptBase):
    def start(self) -> None:
        self._saw_enemies = False
        self._proc_spawned = False

    def sr_step(self, ctx: SceneRuntimeTickContext, delta_time: float) -> None:
        ent = self.entity
        if ent is None:
            return

        if not self._proc_spawned:
            self._proc_spawned = True
            env = getattr(ctx, "environment", None) or {}
            seed = int(env.get("game_proc_seed", 12345))
            count = int(env.get("game_proc_obstacles", 5))
            w, h = float(ctx.bounds[0]), float(ctx.bounds[1])
            ox, oy = float(ctx.owner_position[0]), float(ctx.owner_position[1])
            reserved = [(ox, oy, float(ctx.owner_radius) + 90.0)]
            for p in ctx.peers:
                pad = 50.0 if p.id == "exit_gate" else 42.0
                reserved.append(
                    (float(p.position[0]), float(p.position[1]), float(p.radius) + pad)
                )
            for spec in generate_wall_spawns(w, h, count, seed=seed, reserved=reserved):
                ctx.spawn_requests.append(spec)

        enemies = [p for p in ctx.peers if p.id.startswith("enemy_")]
        if enemies:
            self._saw_enemies = True
        at_exit = False
        for p in ctx.peers:
            if p.id == "exit_gate" and p.surface_gap < 26.0:
                at_exit = True
                break
        hud = getattr(ent, "sr_debug_hud", None)
        if not isinstance(hud, dict):
            hud = {}
            ent.sr_debug_hud = hud
        hud["enemies_left"] = len(enemies)
        if getattr(self, "_enemies_start", None) is None:
            self._enemies_start = len(enemies)
        hud["enemies_total"] = int(getattr(self, "_enemies_start", len(enemies)))
        if getattr(self, "_saw_enemies", False) and not enemies and at_exit:
            hud["dungeon_clear"] = 1
