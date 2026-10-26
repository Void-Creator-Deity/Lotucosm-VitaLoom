# -*- coding: utf-8
"""PS PVAEC verify 三分：与 SR `pvaec_verify_triple` 语义对齐。

职责: homeo（intero dict）+ reaff（velocity vs motor）+ exaff（component sense 变化）。
时机: `PVAECCycle.validate_action` 在 `use_ps_verify_triple=True` 时调用。
排错: 见 docs/pvaec_comparability_research.md §2。
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from core.Lotucosm.sr_interoception import (
    homeostatic_success,
    interoception_from_environment,
    pvaec_verify_triple,
    reafference_consistency,
)


def ps_use_verify_triple(organism: Any) -> bool:
    return bool(getattr(organism, "use_ps_verify_triple", False))


def snapshot_pre_act_motion(organism: Any) -> None:
    """act 前缓存速度，供 reafference 使用。"""
    vel = organism_velocity(organism)
    organism._ps_pre_act_velocity = vel


def organism_velocity(organism: Any) -> tuple[float, float] | None:
    vel = getattr(organism, "velocity", None)
    if vel is None:
        return None
    try:
        if hasattr(vel, "x") and hasattr(vel, "y"):
            return float(vel.x), float(vel.y)
        if hasattr(vel, "__getitem__"):
            return float(vel[0]), float(vel[1])
    except (TypeError, ValueError, IndexError):
        return None
    return None


def _sense_scalar(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("value", "signal", "reading", "level"):
            if key in value:
                try:
                    return float(value[key])
                except (TypeError, ValueError):
                    continue
    return 0.0


def motor_from_ps_action(action: Mapping[str, Any]) -> tuple[float, float]:
    for details in action.values():
        if not isinstance(details, dict):
            continue
        params = details.get("params")
        if isinstance(params, dict):
            ax = float(params.get("ax", params.get("force_x", 0.0)) or 0.0)
            ay = float(params.get("ay", params.get("force_y", 0.0)) or 0.0)
            if abs(ax) > 1e-9 or abs(ay) > 1e-9:
                return ax, ay
        try:
            sig = float(details.get("signal", 0.0) or 0.0)
        except (TypeError, ValueError):
            sig = 0.0
        cmd = str(details.get("command", "")).lower()
        if cmd == "explore" and sig != 0.0:
            return sig * 0.4, sig * 0.25
        if cmd == "explore":
            return 0.15, 0.1
    return 0.0, 0.0


def ps_exafference_predictability(
    obs_before: Mapping[str, Any],
    obs_after: Mapping[str, Any],
    motor_ax: float,
    motor_ay: float,
    delta_time: float,
) -> float:
    """PS 外场可预测性：component sense 标量 + intero 变化 vs motor 预期。"""
    if delta_time <= 0:
        return 0.5
    motor_mag = math.hypot(float(motor_ax), float(motor_ay))
    coupling = motor_mag * float(delta_time)
    surprises: list[float] = []

    e0 = float(obs_before.get("intero_energy_norm", 0.5))
    e1 = float(obs_after.get("intero_energy_norm", e0))
    expected_e = coupling * 0.03
    err_e = abs((e1 - e0) - expected_e) / max(0.05, expected_e + 0.1)
    surprises.append(min(1.0, err_e))

    for key, val in obs_before.items():
        if str(key).startswith("intero_") or str(key).startswith("_"):
            continue
        if key not in obs_after:
            continue
        s0 = _sense_scalar(val)
        s1 = _sense_scalar(obs_after.get(key, val))
        delta = abs(s1 - s0)
        expected = coupling * (0.04 + 0.02 * min(1.0, abs(s0)))
        if coupling < 1e-6 and delta < 1e-6:
            continue
        err = abs(delta - expected) / max(0.05, expected + 0.08)
        surprises.append(min(1.0, err))

    if not surprises:
        return 0.75
    avg = sum(surprises) / len(surprises)
    return max(0.0, min(1.0, 1.0 - avg * 0.55))


def validate_action_legacy(
    organism: Any,
    *,
    prev_energy: float | None = None,
    prev_health: float | None = None,
) -> float:
    """原 energy/health 启发式 verify（向后兼容）。"""
    success: float = 0.5
    prev_e = float(
        prev_energy
        if prev_energy is not None
        else getattr(organism, "_previous_energy", getattr(organism, "energy", 0.0))
    )
    prev_h = float(
        prev_health
        if prev_health is not None
        else getattr(organism, "_previous_health", getattr(organism, "health", 0.0))
    )
    cur_e = float(getattr(organism, "energy", prev_e))
    cur_h = float(getattr(organism, "health", prev_h))
    max_e = max(1.0, float(getattr(organism, "max_energy", 200.0)))
    max_h = max(1.0, float(getattr(organism, "max_health", 100.0)))

    if cur_e > prev_e:
        success += 0.2
    elif cur_e < prev_e:
        success -= 0.2
    success += 0.15 * (cur_e / max_e - 0.5)

    if cur_h > prev_h:
        success += 0.15
    elif cur_h < prev_h:
        success -= 0.15
    success += 0.1 * (cur_h / max_h - 0.5)

    _store_energy_health_baseline(organism, cur_e, cur_h)
    return max(0.0, min(1.0, success))


def validate_action_triple(
    organism: Any,
    old_perception: Mapping[str, Any],
    new_perception: Mapping[str, Any],
    action: Mapping[str, Any],
    *,
    delta_time: float = 1.0,
) -> float:
    """PS verify 三分，与 SR `PvaecScript.verify` 权重一致。"""
    intero_before = interoception_from_environment(old_perception)
    intero_after = interoception_from_environment(new_perception)
    if not any(intero_before.values()) and hasattr(organism, "energy"):
        from core.Lotucosm.sr_interoception import interoception_for_entity

        intero_before = interoception_for_entity(organism)
        intero_after = interoception_for_entity(organism)

    homeo = homeostatic_success(intero_before, intero_after)
    motor_ax, motor_ay = motor_from_ps_action(action)
    pre = getattr(organism, "_ps_pre_act_velocity", None)
    post = organism_velocity(organism)
    reaff = reafference_consistency(pre, post, motor_ax, motor_ay, float(delta_time))
    exaff = ps_exafference_predictability(
        old_perception, new_perception, motor_ax, motor_ay, float(delta_time)
    )
    organism._ps_verify_components = {"homeo": homeo, "reaff": reaff, "exaff": exaff}
    score = pvaec_verify_triple(homeo, reaff, exaff)
    organism._ps_last_verify_success = float(score)
    _store_energy_health_baseline(organism)
    return score


def _store_energy_health_baseline(
    organism: Any,
    cur_e: float | None = None,
    cur_h: float | None = None,
) -> None:
    if cur_e is None:
        cur_e = float(getattr(organism, "energy", 0.0))
    if cur_h is None:
        cur_h = float(getattr(organism, "health", 0.0))
    if hasattr(organism, "energy"):
        organism._previous_energy = cur_e
    if hasattr(organism, "health"):
        organism._previous_health = cur_h


def developmental_stage_from_entity(entity: Any) -> int | None:
    """SR 实体发育 stage：HUD 或 PvaecScript 脚本。"""
    hud = getattr(entity, "sr_debug_hud", None)
    if isinstance(hud, dict) and "developmental_stage" in hud:
        try:
            return int(hud["developmental_stage"])
        except (TypeError, ValueError):
            pass
    scripts = getattr(entity, "scripts", None)
    if isinstance(scripts, list):
        for script in scripts:
            if not bool(getattr(script, "developmental_ladder_enabled", False)):
                continue
            try:
                return int(getattr(script, "developmental_stage", 0))
            except (TypeError, ValueError):
                continue
    return None
