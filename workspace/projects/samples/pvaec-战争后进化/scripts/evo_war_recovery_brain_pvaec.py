# -*- coding: utf-8 -*-
"""战争后进化 · 演化中枢：和平觅食 / 战争互攻 / 恢复重建。"""
from __future__ import annotations

import importlib.util
import random
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext
from core.Lotucosm.sr_mind_gene import bounds_for_gene_key, mind_dict_mutate
from core.Lotucosm.sr_war_combat import (
    WarCombatProfile,
    combat_active,
    feeding_disabled,
    resolve_war_combat,
)
from core.Lotucosm.sr_war_recovery import (
    WarRecoveryProfile,
    phase_at_time,
    resolve_war_recovery,
)

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from _cell_scripts_bootstrap import ensure_cell_evolution_scripts_path

_cell_root = ensure_cell_evolution_scripts_path()
_evo_spec = importlib.util.spec_from_file_location(
    "mw_evo_central_brain_pvaec", _cell_root / "evo_central_brain_pvaec.py"
)
assert _evo_spec and _evo_spec.loader
_evo_mod = importlib.util.module_from_spec(_evo_spec)
_evo_spec.loader.exec_module(_evo_mod)
EvoCentralBrainPvaec = _evo_mod.EvoCentralBrainPvaec

_COMBAT_TRAIN_KEYS = ("max_speed", "gain_high_stress", "wander_amp")


def _profile_from_ctx(ctx: Optional[SceneRuntimeTickContext]) -> WarRecoveryProfile:
    if ctx is not None:
        env = ctx.environment
        raw = env.get("war_recovery_profile") if isinstance(env, Mapping) else None
        if isinstance(raw, dict):
            return WarRecoveryProfile.from_mapping(raw)
    return WarRecoveryProfile()


def _combat_from_ctx(ctx: Optional[SceneRuntimeTickContext]) -> WarCombatProfile:
    if ctx is not None:
        env = ctx.environment
        raw = env.get("war_combat_profile") if isinstance(env, Mapping) else None
        if isinstance(raw, dict):
            return WarCombatProfile.from_mapping(raw)
    return WarCombatProfile()


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


class EvoWarRecoveryBrainPvaec(EvoCentralBrainPvaec):
    """和平 Evo 代谢；战争期互攻 HP、禁觅食、击杀自训练。"""

    def __init__(self) -> None:
        super().__init__()
        self._war_phase_name = "peace"
        self._combat_score_before = 0
        self._lineage_id = ""

    def start(self) -> None:
        super().start()
        props = getattr(self, "_scene_script_properties", None) or {}
        self._war_profile = resolve_war_recovery(None, props if isinstance(props, dict) else None)
        self._combat_profile = resolve_war_combat(
            {"sr_war_recovery": props.get("war_recovery", {}) if isinstance(props, dict) else {}}
        )
        ent = self.entity
        if ent is not None:
            self._lineage_id = str(getattr(ent, "id", ""))

    def _war_phase(self, sim_t: float, ctx: Optional[SceneRuntimeTickContext]) -> Tuple[str, WarRecoveryProfile, WarCombatProfile]:
        profile = _profile_from_ctx(ctx) if ctx is not None else getattr(self, "_war_profile", WarRecoveryProfile())
        combat = _combat_from_ctx(ctx) if ctx is not None else getattr(self, "_combat_profile", WarCombatProfile())
        override = _override_until(ctx)
        phase = phase_at_time(sim_t, profile, war_override_until=override)
        return phase, profile, combat

    def pvaec_step(self, ctx: SceneRuntimeTickContext, delta_time: float) -> None:
        ent = self.entity
        phase: str | None = None
        combat: WarCombatProfile | None = None
        if ent is not None:
            phase, _profile, combat = self._war_phase(float(ctx.simulation_time), ctx)
            self._war_phase_name = phase
            self._ensure_combat_hud(ent, combat, phase)
        super().pvaec_step(ctx, delta_time)
        if ent is not None and phase is not None and combat is not None:
            self._ensure_combat_hud(ent, combat, phase)

    def _ensure_combat_hud(self, ent: Any, combat: WarCombatProfile, phase: str) -> Dict[str, Any]:
        hud = getattr(ent, "sr_debug_hud", None)
        if not isinstance(hud, dict):
            hud = {}
            ent.sr_debug_hud = hud
        hud["war_phase"] = phase
        if combat_active(phase, combat):
            hud["combat_mode"] = 1
            if "hp" not in hud:
                hud["hp"] = float(combat.base_hp)
            if "hp_max" not in hud:
                hud["hp_max"] = float(combat.base_hp)
            hud.setdefault("combat_score", 0)
            hud.setdefault("death_count", 0)
            hud.setdefault("lineage_id", self._lineage_id or str(getattr(ent, "id", "")))
        else:
            hud.pop("combat_mode", None)
        return hud

    def _online_train_on_kill(self, hud: Dict[str, Any], combat: WarCombatProfile) -> None:
        score = int(hud.get("combat_score", 0) or 0)
        if score <= self._combat_score_before:
            return
        self._combat_score_before = score
        step = float(combat.online_train_on_kill)
        if step <= 0:
            return
        props = getattr(self, "_scene_script_properties", None) or {}
        mind = props.get("mind") if isinstance(props, dict) else None
        if not isinstance(mind, dict):
            return
        for key in _COMBAT_TRAIN_KEYS:
            if key not in mind:
                continue
            lo, hi = bounds_for_gene_key(key)
            try:
                old = float(mind[key])
            except (TypeError, ValueError):
                continue
            delta = step * (hi - lo)
            mind[key] = max(lo, min(hi, old + delta))
        hud["combat_trained"] = int(hud.get("combat_trained", 0) or 0) + 1

    def act(self, decision: Dict[str, Any], delta_time: float) -> None:
        ctx = getattr(self, "_pvaec_tick_ctx", None)
        obs = getattr(self, "_pvaec_last_observation", None)
        sim_t = float(obs.get("simulation_time", 0.0)) if isinstance(obs, dict) else 0.0
        phase, profile, combat = self._war_phase(sim_t, ctx if isinstance(ctx, SceneRuntimeTickContext) else None)
        self._war_phase_name = phase

        ent = self.entity
        hud = self._ensure_combat_hud(ent, combat, phase) if ent is not None else {}

        saved_feed = self._feed_from_field
        saved_well = self._well_feed
        saved_base_meta = self._base_metabolism
        if feeding_disabled(phase, combat):
            self._feed_from_field = 0.0
            self._well_feed = 0.0
        well_mult = float(profile.recovery_well_feed_multiplier) if phase == "recovery" else 1.0
        if well_mult != 1.0:
            self._well_feed = saved_well * well_mult
        if combat_active(phase, combat):
            self._base_metabolism = float(combat.war_base_metabolism)

        super().act(decision, delta_time)

        self._feed_from_field = saved_feed
        self._well_feed = saved_well
        self._base_metabolism = saved_base_meta

        if ent is None or delta_time <= 0:
            return
        if isinstance(hud, dict):
            hud["war_phase"] = phase
            if combat_active(phase, combat):
                hud["war_metabolism_scale"] = 1.0
                self._online_train_on_kill(hud, combat)
            else:
                hud["war_metabolism_scale"] = 1.0

    def _try_eat_nutrients(self, ctx: Optional[SceneRuntimeTickContext], ent: Any) -> None:
        sim_t = 0.0
        obs = getattr(self, "_pvaec_last_observation", None)
        if isinstance(obs, dict):
            sim_t = float(obs.get("simulation_time", 0.0))
        phase, _profile, combat = self._war_phase(sim_t, ctx)
        if feeding_disabled(phase, combat):
            return
        super()._try_eat_nutrients(ctx, ent)

    def _try_reproduce(self, ctx, ent) -> None:
        phase = self._war_phase_name
        combat = _combat_from_ctx(ctx if isinstance(ctx, SceneRuntimeTickContext) else None)
        if combat_active(phase, combat):
            return
        before = len(getattr(ctx, "spawn_requests", None) or [])
        super()._try_reproduce(ctx, ent)
        spawn_requests = getattr(ctx, "spawn_requests", None)
        if not spawn_requests or len(spawn_requests) <= before:
            return
        req = spawn_requests[-1]
        if not isinstance(req, dict):
            return
        scripts = req.get("scripts")
        if not isinstance(scripts, list) or not scripts:
            return
        scripts[0]["name"] = "evo_war_recovery_brain_pvaec"
        scripts[0]["type"] = "EvoWarRecoveryBrainPvaec"
