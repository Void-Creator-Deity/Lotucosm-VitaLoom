# -*- coding: utf-8
"""PS 个体发育阶梯：与 SR ADR-0004 语义对齐，挂载于 Organism + PVAECCycle。

职责: 感知 enrich/filter、generate/retrieve 门控、stage 进阶、子代 S0 重置。
排错: 见 docs/adr/0004-pvaec-developmental-ladder.md。
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, MutableMapping, Optional, Sequence

from core.Lotucosm.sr_developmental_ladder import (
    MAX_DEVELOPMENTAL_STAGE,
    VERIFY_SUCCESS_THRESHOLD,
    can_advance_stage,
    clamp_stage,
)
from core.Lotucosm.sr_interoception import interoception_for_entity


def load_developmental_profile(project_config: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if not project_config:
        return {}
    raw = project_config.get("developmental_profile")
    return dict(raw) if isinstance(raw, dict) else {}


def apply_developmental_profile_to_organism(
    organism: Any,
    profile: Optional[Mapping[str, Any]],
) -> None:
    if not profile:
        return
    if "enabled" in profile:
        organism.developmental_ladder_enabled = bool(profile.get("enabled"))
    if "initial_stage" in profile:
        organism.developmental_stage = clamp_stage(int(profile.get("initial_stage", 0)))
    if "plasticity_window" in profile:
        organism.developmental_plasticity_window = max(
            0, int(profile.get("plasticity_window", 0) or 0)
        )
    if "plasticity_penalty" in profile:
        organism.developmental_plasticity_penalty = bool(profile.get("plasticity_penalty"))
    reset_ps_developmental_counters(organism)


def apply_developmental_profile_to_ps_config(cfg: Any, profile: Mapping[str, Any]) -> None:
    if not profile:
        return
    if "enabled" in profile:
        cfg.developmental_ladder_enabled = bool(profile.get("enabled"))
    if "initial_stage" in profile:
        cfg.developmental_initial_stage = clamp_stage(int(profile.get("initial_stage", 0)))


def ensure_ps_developmental_state(organism: Any) -> None:
    if not hasattr(organism, "developmental_ladder_enabled"):
        organism.developmental_ladder_enabled = False
    if not hasattr(organism, "developmental_stage"):
        organism.developmental_stage = 0
    if not hasattr(organism, "developmental_plasticity_window"):
        organism.developmental_plasticity_window = 0
    if not hasattr(organism, "developmental_plasticity_penalty"):
        organism.developmental_plasticity_penalty = False
    for attr, default in (
        ("_developmental_stage_ticks", 0),
        ("_developmental_explore_act_count", 0),
        ("_developmental_verify_success_count", 0),
        ("_developmental_remember_event_count", 0),
        ("_developmental_reproduced", False),
        ("_developmental_last_offspring", 0),
    ):
        if not hasattr(organism, attr):
            setattr(organism, attr, default)


def reset_ps_developmental_counters(organism: Any) -> None:
    organism._developmental_stage_ticks = 0
    organism._developmental_explore_act_count = 0
    organism._developmental_verify_success_count = 0
    organism._developmental_remember_event_count = 0
    organism._developmental_reproduced = False


def reset_ps_developmental_for_child(child: Any, parent: Any) -> None:
    ensure_ps_developmental_state(child)
    child.developmental_ladder_enabled = bool(getattr(parent, "developmental_ladder_enabled", False))
    child.developmental_stage = 0
    reset_ps_developmental_counters(child)


def enrich_ps_perception(organism: Any, perception: Mapping[str, Any], tick: int) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(perception)
    out.update(interoception_for_entity(organism))
    out["_pvaec_tick"] = int(tick)
    out["organism_age"] = int(getattr(organism, "age", 0) or 0)
    return out


def component_ids(organism: Any) -> list[str]:
    comps = getattr(organism, "components", None)
    if isinstance(comps, dict):
        return list(comps.keys())
    return []


def _component_ids(organism: Any) -> list[str]:
    return component_ids(organism)


def filter_ps_perception_for_stage(
    perception: Mapping[str, Any],
    stage: int,
    component_ids: Sequence[str],
) -> Dict[str, Any]:
    stage = clamp_stage(stage)
    if stage >= MAX_DEVELOPMENTAL_STAGE:
        return dict(perception)
    allowed: set[str] = {str(k) for k in perception if str(k).startswith("intero_")}
    if stage >= 1:
        allowed.update(k for k in ("_pvaec_tick", "organism_age") if k in perception)
    comp_keys = [cid for cid in component_ids if cid in perception]
    if stage >= 2 and comp_keys:
        allowed.add(comp_keys[0])
    if stage >= 3:
        allowed.update(comp_keys)
    filtered: Dict[str, Any] = {}
    for key, val in perception.items():
        if key in allowed:
            filtered[key] = val
    for key in allowed:
        if key not in filtered and key in perception:
            filtered[key] = perception[key]
    return filtered


def ps_ladder_enabled(organism: Any) -> bool:
    return bool(getattr(organism, "developmental_ladder_enabled", False))


def gate_ps_retrieve(organism: Any, memories: list[Any]) -> list[Any]:
    if ps_ladder_enabled(organism) and int(getattr(organism, "developmental_stage", 0)) < 2:
        return []
    return memories


def gate_ps_generate_action(organism: Any, action: Dict[str, Any]) -> Dict[str, Any]:
    if not ps_ladder_enabled(organism):
        return action
    stage = int(getattr(organism, "developmental_stage", 0))
    if stage >= 2:
        return action
    comps = component_ids(organism)
    if not comps:
        return action
    target = comps[0]
    details = action.get(target, {})
    if not isinstance(details, dict):
        details = {}
    params = details.get("params")
    return {target: {"command": "explore", "params": dict(params) if isinstance(params, dict) else {}}}


def action_is_explore(action: Mapping[str, Any]) -> bool:
    for details in action.values():
        if isinstance(details, dict) and str(details.get("command", "")).lower() == "explore":
            return True
    return False


def ps_organism_peer_count(organism: Any, environment: Any) -> int:
    if environment is None:
        return 0
    orgs = getattr(environment, "organisms", None)
    if isinstance(orgs, dict):
        return max(0, len(orgs) - 1)
    if isinstance(orgs, (list, tuple)):
        return max(0, len(orgs) - 1)
    pond = getattr(environment, "pond", None)
    if pond is not None:
        p_orgs = getattr(pond, "organisms", None)
        if isinstance(p_orgs, dict):
            return max(0, len(p_orgs) - 1)
    return 0


def track_ps_developmental_after_cycle(
    organism: Any,
    *,
    success: float,
    action: Mapping[str, Any],
    remember_written: bool,
    environment: Any,
) -> None:
    if not ps_ladder_enabled(organism):
        return
    ensure_ps_developmental_state(organism)
    if action_is_explore(action) and int(organism.developmental_stage) <= 1:
        organism._developmental_explore_act_count = int(organism._developmental_explore_act_count) + 1
    if float(success) >= VERIFY_SUCCESS_THRESHOLD:
        organism._developmental_verify_success_count = int(organism._developmental_verify_success_count) + 1
    if remember_written:
        organism._developmental_remember_event_count = int(organism._developmental_remember_event_count) + 1
    if int(getattr(organism, "offspring_count", 0) or 0) > int(getattr(organism, "_developmental_last_offspring", 0) or 0):
        organism._developmental_reproduced = True
    organism._developmental_last_offspring = int(getattr(organism, "offspring_count", 0) or 0)
    maybe_advance_ps_developmental_stage(organism, environment)


def maybe_advance_ps_developmental_stage(organism: Any, environment: Any) -> None:
    if not ps_ladder_enabled(organism):
        return
    stage = int(getattr(organism, "developmental_stage", 0))
    if stage >= MAX_DEVELOPMENTAL_STAGE:
        return
    organism._developmental_stage_ticks = int(getattr(organism, "_developmental_stage_ticks", 0)) + 1
    if not can_advance_stage(
        stage,
        int(organism._developmental_stage_ticks),
        int(organism._developmental_explore_act_count),
        int(organism._developmental_verify_success_count),
        int(organism._developmental_remember_event_count),
        bool(organism._developmental_reproduced),
        ps_organism_peer_count(organism, environment),
        plasticity_window=int(getattr(organism, "developmental_plasticity_window", 0) or 0),
        plasticity_penalty=bool(getattr(organism, "developmental_plasticity_penalty", False)),
    ):
        return
    organism.developmental_stage = clamp_stage(stage + 1)
    organism._developmental_stage_ticks = 0
