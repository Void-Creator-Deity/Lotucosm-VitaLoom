# -*- coding: utf-8 -*-
"""SR 战争后进化三幕配置：场景 sr_war_recovery 为真源，脚本 props 可覆盖缺省。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Optional

WarPhase = Literal["peace", "war", "recovery"]

# 战争窗营养清扫间隔（秒）；viewport 预清扫与导演脉冲共用。
WAR_NUTRIENT_PURGE_INTERVAL = 0.35


@dataclass(frozen=True)
class WarRecoveryProfile:
    peace_until: float = 45.0
    war_until: float = 80.0
    nutrient_target_peace: int = 8
    nutrient_target_war: int = 1
    metabolism_multiplier_war: float = 2.15
    war_shock_drain: float = 5.5
    manual_trigger: bool = False
    manual_war_duration: float = 35.0
    recovery_nutrient_boost: int = 0
    recovery_well_feed_multiplier: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "peace_until": self.peace_until,
            "war_until": self.war_until,
            "nutrient_target_peace": self.nutrient_target_peace,
            "nutrient_target_war": self.nutrient_target_war,
            "metabolism_multiplier_war": self.metabolism_multiplier_war,
            "war_shock_drain": self.war_shock_drain,
            "manual_trigger": self.manual_trigger,
            "manual_war_duration": self.manual_war_duration,
            "recovery_nutrient_boost": self.recovery_nutrient_boost,
            "recovery_well_feed_multiplier": self.recovery_well_feed_multiplier,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> WarRecoveryProfile:
        return resolve_war_recovery({"sr_war_recovery": data or {}}, None)


def _coerce_mapping(raw: Any) -> dict[str, Any]:
    return dict(raw) if isinstance(raw, dict) else {}


def resolve_war_recovery(
    scene_data: Mapping[str, Any] | None,
    script_props: Mapping[str, Any] | None = None,
) -> WarRecoveryProfile:
    """合并场景 sr_war_recovery 与脚本 properties.war_recovery（场景优先）。"""
    scene_wr = _coerce_mapping((scene_data or {}).get("sr_war_recovery"))
    props_wr = _coerce_mapping((script_props or {}).get("war_recovery"))
    merged = {**props_wr, **scene_wr}

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

    peace = _float("peace_until", 45.0)
    war_end = _float("war_until", 80.0)
    if war_end < peace:
        war_end = peace

    return WarRecoveryProfile(
        peace_until=peace,
        war_until=war_end,
        nutrient_target_peace=_int("nutrient_target_peace", 8),
        nutrient_target_war=_int("nutrient_target_war", 1),
        metabolism_multiplier_war=_float("metabolism_multiplier_war", 2.15),
        war_shock_drain=_float("war_shock_drain", 5.5),
        manual_trigger=bool(merged.get("manual_trigger", False)),
        manual_war_duration=_float("manual_war_duration", 35.0),
        recovery_nutrient_boost=_int("recovery_nutrient_boost", 0),
        recovery_well_feed_multiplier=_float("recovery_well_feed_multiplier", 1.0),
    )


def phase_at_time(
    sim_t: float,
    profile: WarRecoveryProfile,
    *,
    war_override_until: float = 0.0,
) -> WarPhase:
    """当前仿真时刻所属三幕；war_override_until>sim_t 时强制战争窗。"""
    t = float(sim_t)
    if war_override_until > t:
        return "war"
    if t < profile.peace_until:
        return "peace"
    if t < profile.war_until:
        return "war"
    return "recovery"


def metabolism_scale_for_phase(phase: WarPhase, profile: WarRecoveryProfile) -> float:
    if phase == "war":
        return float(profile.metabolism_multiplier_war)
    return 1.0


def nutrient_target_for_phase(phase: WarPhase, profile: WarRecoveryProfile) -> int:
    if phase == "war":
        return max(0, profile.nutrient_target_war)
    base = max(0, profile.nutrient_target_peace)
    if phase == "recovery" and profile.recovery_nutrient_boost > 0:
        return base + profile.recovery_nutrient_boost
    return base


def phase_label_zh(phase: WarPhase) -> str:
    return {"peace": "和平", "war": "战争", "recovery": "恢复"}.get(phase, phase)


def phase_label_en(phase: WarPhase) -> str:
    return phase


def seconds_until_phase_boundary(
    sim_t: float,
    profile: WarRecoveryProfile,
    *,
    war_override_until: float = 0.0,
) -> float:
    """距当前阶段结束还剩多少仿真秒；恢复期返回 -1（无内置结束）。"""
    t = float(sim_t)
    if war_override_until > t:
        return max(0.0, war_override_until - t)
    phase = phase_at_time(t, profile, war_override_until=war_override_until)
    if phase == "peace":
        return max(0.0, profile.peace_until - t)
    if phase == "war":
        return max(0.0, profile.war_until - t)
    return -1.0


def phase_countdown_hud(
    sim_t: float,
    profile: WarRecoveryProfile,
    *,
    war_override_until: float = 0.0,
    chinese: bool = True,
) -> str:
    """HUD 用阶段倒计时片段（空串表示不显示）。"""
    phase = phase_at_time(sim_t, profile, war_override_until=war_override_until)
    remain = seconds_until_phase_boundary(sim_t, profile, war_override_until=war_override_until)
    if remain < 0:
        return ""
    if phase == "peace":
        return f"距战争{remain:.0f}s" if chinese else f"war in {remain:.0f}s"
    if phase == "war":
        if war_override_until > float(sim_t):
            return f"手动战争{remain:.0f}s" if chinese else f"manual war {remain:.0f}s"
        return f"战争剩余{remain:.0f}s" if chinese else f"war {remain:.0f}s left"
    return ""
