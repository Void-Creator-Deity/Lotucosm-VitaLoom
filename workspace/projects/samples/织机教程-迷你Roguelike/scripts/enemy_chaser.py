# -*- coding: utf-8
"""织机教程 · 史莱姆：追击玩家（ScriptBase.sr_step）。"""
from __future__ import annotations

import math

from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext
from core.Lotucosm.scripts import ScriptBase


class EnemyChaser(ScriptBase):
    def start(self) -> None:
        self._speed = 58.0
        self._max_hp = 30.0
        ent = self.entity
        if ent is not None:
            hud = getattr(ent, "sr_debug_hud", None)
            if not isinstance(hud, dict):
                hud = {}
                ent.sr_debug_hud = hud
            hud.setdefault("hp", self._max_hp)
            hud.setdefault("hp_max", self._max_hp)

    def sr_step(self, ctx: SceneRuntimeTickContext, delta_time: float) -> None:
        ent = self.entity
        if ent is None:
            return
        hud = getattr(ent, "sr_debug_hud", None)
        if isinstance(hud, dict):
            flash = float(hud.get("hit_flash", 0.0))
            if flash > 0.0:
                hud["hit_flash"] = max(0.0, flash - delta_time)
        target = None
        player_id = str((getattr(ctx, "environment", None) or {}).get("game_player_id", "player_rl"))
        for p in ctx.peers:
            if p.id == player_id:
                target = p
                break
        if target is None:
            ent.velocity[0] *= 0.9
            ent.velocity[1] *= 0.9
            return
        dx = float(target.position[0]) - float(ent.position[0])
        dy = float(target.position[1]) - float(ent.position[1])
        mag = math.hypot(dx, dy)
        if mag < 1e-3:
            return
        s = self._speed / mag
        ent.velocity[0] = dx * s
        ent.velocity[1] = dy * s
        vis = self.get_visual()
        if vis is not None:
            vis.flip_x = dx < 0.0
