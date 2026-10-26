# -*- coding: utf-8 -*-
"""战争期膜刺执行器：扇形近战伤害其它 organism。"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from core.Lotucosm.pvaec_script import PvaecScript
from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext
from core.Lotucosm.sr_organism_combat import hub_id_for_entity, pick_organism_melee_target
from core.Lotucosm.sr_war_combat import WarCombatProfile, combat_active


def _combat_from_ctx(ctx: Optional[SceneRuntimeTickContext]) -> WarCombatProfile:
    if ctx is None:
        return WarCombatProfile()
    env = ctx.environment
    if not isinstance(env, Mapping):
        return WarCombatProfile()
    raw = env.get("war_combat_profile")
    if isinstance(raw, dict):
        return WarCombatProfile.from_mapping(raw)
    return WarCombatProfile()


def _phase_from_ctx(ctx: Optional[SceneRuntimeTickContext]) -> str:
    if ctx is None:
        return "peace"
    env = ctx.environment
    if isinstance(env, Mapping):
        return str(env.get("war_phase", "peace"))
    return "peace"


class ActuatorSpikeCombatPvaec(PvaecScript):
    """纤毛位点渲染为刺；战争期对邻近 organism 造成近战伤害。"""

    def __init__(self) -> None:
        super().__init__()
        self._cooldown = 0.0

    def start(self) -> None:
        return

    def perceive(self, ctx: SceneRuntimeTickContext) -> Dict[str, Any]:
        return {"phase": _phase_from_ctx(ctx)}

    def think(self, observation: Dict[str, Any], delta_time: float) -> Dict[str, Any]:
        _ = delta_time
        return observation

    def act(self, decision: Dict[str, Any], delta_time: float) -> None:
        phase = str(decision.get("phase", "peace"))
        ctx = getattr(self, "_pvaec_tick_ctx", None)
        if not isinstance(ctx, SceneRuntimeTickContext):
            return
        combat = _combat_from_ctx(ctx)
        if not combat_active(phase, combat) or delta_time <= 0:
            return
        self._cooldown = max(0.0, self._cooldown - delta_time)
        if self._cooldown > 0:
            return
        ent = self.entity
        if ent is None:
            return
        attach: dict[str, Any] = {}
        env = ctx.environment
        if isinstance(env, Mapping):
            raw = env.get("membrane_attach")
            if isinstance(raw, dict):
                attach = raw
        hub_id = hub_id_for_entity(str(getattr(ent, "id", "")), attach)
        hub = next((p for p in ctx.peers if str(p.id) == hub_id), None)
        if hub is not None:
            hub_pos = hub.position
            hub_rad = float(getattr(hub, "radius", 18.0))
        else:
            hub_pos = getattr(ent, "position", (0.0, 0.0))
            hub_rad = float(getattr(ent, "radius", 18.0))
        attacker = type(
            "A",
            (),
            {
                "id": hub_id,
                "position": hub_pos,
                "radius": hub_rad,
                "velocity": getattr(ent, "velocity", [0.0, 0.0]),
            },
        )()
        target = pick_organism_melee_target(
            attacker,
            ctx.peers,
            reach=combat.melee_reach,
            arc_half=combat.melee_arc_half,
            exclude_ids=frozenset({hub_id}),
        )
        if target is None:
            return
        removal = getattr(ctx, "damage_requests", None)
        if removal is None or not hasattr(removal, "append"):
            return
        dmg = float(combat.melee_damage)
        removal.append((str(target.id), dmg, hub_id))
        self._cooldown = float(combat.attack_cooldown)
        ent.emission_strength = max(float(getattr(ent, "emission_strength", 0.0)), 0.9)
        fx = getattr(ctx, "fx_requests", None)
        if fx is not None and hasattr(fx, "append"):
            tx, ty = float(target.position[0]), float(target.position[1])
            fx.append({"type": "float", "x": tx, "y": ty - 10.0, "text": str(int(dmg))})
