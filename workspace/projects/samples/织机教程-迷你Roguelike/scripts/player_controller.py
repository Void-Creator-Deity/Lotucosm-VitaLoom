# -*- coding: utf-8
"""织机教程 · 玩家：WASD + 鼠标瞄准挥砍、Space 攻击、HP。"""
from __future__ import annotations

import math

from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext
from core.Lotucosm.scripts import ScriptBase
from core.Lotucosm.sr_game_combat import pick_melee_target_in_arc


class PlayerController(ScriptBase):
    def start(self) -> None:
        self._move_speed = 165.0
        self._attack_gap = 28.0
        self._attack_arc = 0.72
        self._attack_damage = 35.0
        self._hurt_dps = 32.0
        self._attack_cooldown = 0.0
        self._max_hp = 100.0
        ent = self.entity
        if ent is not None:
            hud = getattr(ent, "sr_debug_hud", None)
            if not isinstance(hud, dict):
                hud = {}
                ent.sr_debug_hud = hud
            hud.setdefault("hp", self._max_hp)
            hud.setdefault("hp_max", self._max_hp)

    def _aim_angle(self, ctx: SceneRuntimeTickContext, px: float, py: float, dx: float, dy: float) -> float:
        inp = getattr(ctx, "input", None)
        mouse = getattr(inp, "mouse_scene_xy", None) if inp is not None else None
        if mouse is not None:
            mx, my = float(mouse[0]), float(mouse[1])
            return math.atan2(my - py, mx - px)
        if abs(dx) + abs(dy) > 1e-3:
            return math.atan2(dy, dx)
        return 0.0

    def sr_step(self, ctx: SceneRuntimeTickContext, delta_time: float) -> None:
        ent = self.entity
        if ent is None:
            return
        hud = getattr(ent, "sr_debug_hud", None)
        if not isinstance(hud, dict):
            hud = {}
            ent.sr_debug_hud = hud
        hp = float(hud.get("hp", self._max_hp))
        if hud.get("player_dead") == 1:
            ent.velocity[0] = 0.0
            ent.velocity[1] = 0.0
            return

        keys = getattr(getattr(ctx, "input", None), "keys_down", frozenset()) or frozenset()
        inp = getattr(ctx, "input", None)
        mouse_click = bool(getattr(inp, "mouse_left_clicked", False)) if inp is not None else False

        dx = dy = 0.0
        if "W" in keys or "Up" in keys:
            dy -= 1.0
        if "S" in keys or "Down" in keys:
            dy += 1.0
        if "A" in keys or "Left" in keys:
            dx -= 1.0
        if "D" in keys or "Right" in keys:
            dx += 1.0
        mag = math.hypot(dx, dy)
        moving = mag > 1e-3
        if moving:
            s = self._move_speed / mag
            ent.velocity[0] = dx * s
            ent.velocity[1] = dy * s
        else:
            ent.velocity[0] *= 0.85
            ent.velocity[1] *= 0.85

        px = float(ent.position[0])
        py = float(ent.position[1])
        aim = self._aim_angle(ctx, px, py, dx, dy)
        hud["aim_angle"] = aim

        vis = self.get_visual()
        if vis is not None:
            mouse = getattr(inp, "mouse_scene_xy", None) if inp is not None else None
            if mouse is not None:
                vis.flip_x = float(mouse[0]) < px
            elif moving and dx < -0.01:
                vis.flip_x = True
            elif moving and dx > 0.01:
                vis.flip_x = False
            vis.anim = "player_walk" if moving else ""
            if moving:
                vis.frame = int(ctx.simulation_time * 8.0) % 2

        self._attack_cooldown = max(0.0, self._attack_cooldown - delta_time)
        want_attack = "Space" in keys or mouse_click
        if not want_attack:
            for p in ctx.peers:
                if p.id.startswith("enemy_") and p.surface_gap < self._attack_gap:
                    want_attack = True
                    break
        if want_attack and self._attack_cooldown <= 0.0:
            target = pick_melee_target_in_arc(
                px, py, aim, self._attack_gap, self._attack_arc, ctx.peers
            )
            if target is not None:
                ex, ey = float(target.position[0]), float(target.position[1])
                ctx.damage_requests.append((target.id, self._attack_damage))
                ctx.fx_requests.append(
                    {
                        "type": "swing",
                        "x": px,
                        "y": py,
                        "angle": aim,
                        "range": self._attack_gap,
                        "arc_half": self._attack_arc,
                    }
                )
                ctx.fx_requests.append(
                    {
                        "type": "float",
                        "x": ex,
                        "y": ey - 8.0,
                        "text": str(int(self._attack_damage)),
                    }
                )
                self._attack_cooldown = 0.35

        for p in ctx.peers:
            if not p.id.startswith("enemy_"):
                continue
            if p.surface_gap < 8.0:
                hp = max(0.0, hp - self._hurt_dps * delta_time)
        hud["hp"] = hp
        if hp <= 0.05:
            hud["player_dead"] = 1
            ent.velocity[0] = 0.0
            ent.velocity[1] = 0.0
