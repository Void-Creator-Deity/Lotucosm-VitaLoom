# -*- coding: utf-8 -*-
"""战争后进化 · 场景导演：按时间窗切换场域脉冲，并在战争期清扫营养颗粒。"""
from __future__ import annotations

import math
from typing import Any, Dict, Mapping, Optional

from core.Lotucosm.pvaec_script import PvaecScript
from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext
from core.Lotucosm.sr_war_recovery import WarRecoveryProfile, phase_at_time, resolve_war_recovery


def _profile_from_ctx(ctx: Optional[SceneRuntimeTickContext]) -> WarRecoveryProfile:
    if ctx is not None:
        env = ctx.environment
        raw = env.get("war_recovery_profile") if isinstance(env, Mapping) else None
        if isinstance(raw, dict):
            return WarRecoveryProfile.from_mapping(raw)
    return WarRecoveryProfile()


def _override_until(ctx: Optional[SceneRuntimeTickContext]) -> float:
    if ctx is None:
        return 0.0
    env = ctx.environment
    if not isinstance(env, Mapping):
        return 0.0
    try:
        return float(env.get("war_override_until", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


class WarRecoveryDirectorPvaec(PvaecScript):
    """挂载于场域锚：和平弱脉冲 / 战争强红脉冲 / 恢复绿脉冲（营养清扫由 viewport 预清扫）。"""

    def __init__(self) -> None:
        super().__init__()
        self._war_profile = WarRecoveryProfile()

    def start(self) -> None:
        props = getattr(self, "_scene_script_properties", None) or {}
        self._war_profile = resolve_war_recovery(None, props if isinstance(props, dict) else None)

    def perceive(self, ctx: SceneRuntimeTickContext) -> Dict[str, Any]:
        profile = _profile_from_ctx(ctx)
        t = float(ctx.simulation_time)
        phase = phase_at_time(t, profile, war_override_until=_override_until(ctx))
        return {"t": t, "phase": phase}

    def think(self, observation: Dict[str, Any], delta_time: float) -> Dict[str, Any]:
        _ = delta_time
        phase = str(observation.get("phase", "peace"))
        t = float(observation.get("t", 0.0))
        if phase == "war":
            pulse = 0.55 + 0.45 * math.sin(t * 2.4)
            emission = 0.85 + 0.15 * pulse
        elif phase == "recovery":
            emission = 0.55 + 0.3 * math.sin(t * 0.6)
        else:
            emission = 0.25 + 0.15 * math.sin(t * 0.35)
        return {"phase": phase, "emission": emission}

    def act(self, decision: Dict[str, Any], delta_time: float) -> None:
        ent = self.entity
        if ent is None:
            return
        ent.emission_strength = float(decision.get("emission", 0.3))
