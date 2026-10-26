# -*- coding: utf-8 -*-
"""SR 战争期互攻竞技场配置（与 sr_war_recovery 三幕配合）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from core.Lotucosm.sr_war_recovery import WarPhase, WarRecoveryProfile, phase_at_time


@dataclass(frozen=True)
class WarCombatProfile:
    combat_enabled_in_war: bool = True
    disable_feeding_in_war: bool = True
    base_hp: float = 100.0
    melee_damage: float = 18.0
    melee_reach: float = 52.0
    melee_arc_half: float = 0.85
    attack_cooldown: float = 0.45
    kill_score: int = 10
    respawn_delay: float = 2.5
    max_respawns_per_lineage: int = 12
    death_mutation_base_prob: float = 0.15
    death_mutation_per_death: float = 0.08
    death_mutation_cap: float = 0.92
    death_mutation_sigma: float = 0.35
    online_train_on_kill: float = 0.04
    war_base_metabolism: float = 0.8

    def to_dict(self) -> dict[str, Any]:
        return {
            "combat_enabled_in_war": self.combat_enabled_in_war,
            "disable_feeding_in_war": self.disable_feeding_in_war,
            "base_hp": self.base_hp,
            "melee_damage": self.melee_damage,
            "melee_reach": self.melee_reach,
            "melee_arc_half": self.melee_arc_half,
            "attack_cooldown": self.attack_cooldown,
            "kill_score": self.kill_score,
            "respawn_delay": self.respawn_delay,
            "max_respawns_per_lineage": self.max_respawns_per_lineage,
            "death_mutation_base_prob": self.death_mutation_base_prob,
            "death_mutation_per_death": self.death_mutation_per_death,
            "death_mutation_cap": self.death_mutation_cap,
            "death_mutation_sigma": self.death_mutation_sigma,
            "online_train_on_kill": self.online_train_on_kill,
            "war_base_metabolism": self.war_base_metabolism,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> WarCombatProfile:
        return resolve_war_combat({"sr_war_recovery": {"combat": dict(data or {})}})


def _coerce_mapping(raw: Any) -> dict[str, Any]:
    return dict(raw) if isinstance(raw, dict) else {}


def resolve_war_combat(scene_data: Mapping[str, Any] | None) -> WarCombatProfile:
    """从场景 sr_war_recovery.combat 解析互攻配置。"""
    wr = _coerce_mapping((scene_data or {}).get("sr_war_recovery"))
    merged = _coerce_mapping(wr.get("combat"))

    def _float(key: str, default: float) -> float:
        if key not in merged:
            return default
        try:
            return float(merged[key])
        except (TypeError, ValueError):
            return default

    def _int(key: str, default: int) -> int:
        if key not in merged:
            return default
        try:
            return int(merged[key])
        except (TypeError, ValueError):
            return default

    def _bool(key: str, default: bool) -> bool:
        if key not in merged:
            return default
        return bool(merged[key])

    return WarCombatProfile(
        combat_enabled_in_war=_bool("combat_enabled_in_war", True),
        disable_feeding_in_war=_bool("disable_feeding_in_war", True),
        base_hp=_float("base_hp", 100.0),
        melee_damage=_float("melee_damage", 18.0),
        melee_reach=_float("melee_reach", 52.0),
        melee_arc_half=_float("melee_arc_half", 0.85),
        attack_cooldown=_float("attack_cooldown", 0.45),
        kill_score=_int("kill_score", 10),
        respawn_delay=_float("respawn_delay", 2.5),
        max_respawns_per_lineage=_int("max_respawns_per_lineage", 12),
        death_mutation_base_prob=_float("death_mutation_base_prob", 0.15),
        death_mutation_per_death=_float("death_mutation_per_death", 0.08),
        death_mutation_cap=_float("death_mutation_cap", 0.92),
        death_mutation_sigma=_float("death_mutation_sigma", 0.35),
        online_train_on_kill=_float("online_train_on_kill", 0.04),
        war_base_metabolism=_float("war_base_metabolism", 0.8),
    )


def combat_active(
    phase: WarPhase,
    combat: WarCombatProfile,
) -> bool:
    return phase == "war" and bool(combat.combat_enabled_in_war)


def feeding_disabled(
    phase: WarPhase,
    combat: WarCombatProfile,
) -> bool:
    return phase == "war" and bool(combat.disable_feeding_in_war)


def death_mutation_probability(death_count: int, combat: WarCombatProfile) -> float:
    dc = max(0, int(death_count))
    p = combat.death_mutation_base_prob + combat.death_mutation_per_death * dc
    return min(combat.death_mutation_cap, max(0.0, p))


def combat_active_at_time(
    sim_t: float,
    recovery: WarRecoveryProfile,
    combat: WarCombatProfile,
    *,
    war_override_until: float = 0.0,
) -> bool:
    phase = phase_at_time(sim_t, recovery, war_override_until=war_override_until)
    return combat_active(phase, combat)
