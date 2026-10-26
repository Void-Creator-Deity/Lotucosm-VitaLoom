# -*- coding: utf-8 -*-
"""SR/PS 内感受（interoception）：本质变量快照与内稳态验证分数。

借鉴（非归类）: EVAAA 本质变量、Active Inference 偏好验证等文献思路，用于 PVAEC verify 阶段。

职责: 从实体/ctx 抽取 energy/health/stress 等，计算 homeostatic_success。
时机: GameViewport 注入 environment；PvaecScript.verify 读取。
排错: 见 docs/pvaec_cell_evolution.md。
"""
from __future__ import annotations

import math
from typing import Any, Mapping


def interoception_for_entity(entity: Any) -> dict[str, float]:
    """从场景实体抽取内感受 dict（写入 SceneRuntimeTickContext.environment）。"""
    energy = float(getattr(entity, "energy", 0.0) or 0.0)
    max_energy = max(1.0, float(getattr(entity, "max_energy", 200.0) or 200.0))
    health = float(getattr(entity, "health", energy) or energy)
    max_health = max(1.0, float(getattr(entity, "max_health", max_energy) or max_energy))
    stress = float(getattr(entity, "sr_stress_norm", 0.0) or 0.0)
    if stress <= 0.0:
        hud = getattr(entity, "sr_debug_hud", None)
        if isinstance(hud, dict) and "stress_norm" in hud:
            try:
                stress = float(hud["stress_norm"])
            except (TypeError, ValueError):
                pass
    emit = float(getattr(entity, "emission_strength", 0.0) or 0.0)
    return {
        "intero_energy": energy,
        "intero_max_energy": max_energy,
        "intero_energy_norm": energy / max_energy,
        "intero_health": health,
        "intero_max_health": max_health,
        "intero_health_norm": health / max_health,
        "intero_stress": stress,
        "intero_emission": emit,
    }


def interoception_from_environment(env: Mapping[str, Any]) -> dict[str, float]:
    """从 ctx.environment 读取已注入的内感受（缺键则 0）。"""
    keys = (
        "intero_energy",
        "intero_max_energy",
        "intero_energy_norm",
        "intero_health",
        "intero_max_health",
        "intero_health_norm",
        "intero_stress",
        "intero_emission",
    )
    out: dict[str, float] = {}
    for k in keys:
        try:
            out[k] = float(env.get(k, 0.0) or 0.0)
        except (TypeError, ValueError):
            out[k] = 0.0
    return out


def homeostatic_success(before: Mapping[str, float], after: Mapping[str, float]) -> float:
    """内稳态验证分数 [0,1]：energy/health 上升加分，stress 下降加分。"""
    score = 0.5
    e0 = float(before.get("intero_energy_norm", 0.5))
    e1 = float(after.get("intero_energy_norm", e0))
    h0 = float(before.get("intero_health_norm", e0))
    h1 = float(after.get("intero_health_norm", h0))
    s0 = float(before.get("intero_stress", 0.0))
    s1 = float(after.get("intero_stress", s0))

    if e1 > e0 + 1e-6:
        score += 0.22
    elif e1 < e0 - 1e-6:
        score -= 0.22
    score += 0.12 * (e1 - 0.5)

    if h1 > h0 + 1e-6:
        score += 0.12
    elif h1 < h0 - 1e-6:
        score -= 0.12

    if s1 < s0 - 1e-6:
        score += 0.08
    elif s1 > s0 + 1e-6:
        score -= 0.08

    return max(0.0, min(1.0, score))


def reafference_consistency(
    pre_velocity: tuple[float, float] | None,
    post_velocity: tuple[float, float] | None,
    motor_ax: float,
    motor_ay: float,
    delta_time: float,
) -> float:
    """运动一致性分数 [0,1]：实际速度变化与 motor 命令预期是否吻合。"""
    if pre_velocity is None or post_velocity is None or delta_time <= 0:
        return 0.5
    pre_speed = math.hypot(float(pre_velocity[0]), float(pre_velocity[1]))
    post_speed = math.hypot(float(post_velocity[0]), float(post_velocity[1]))
    predicted_delta = math.hypot(float(motor_ax), float(motor_ay)) * float(delta_time)
    actual_delta = abs(post_speed - pre_speed)
    if predicted_delta < 1e-6 and actual_delta < 1e-6:
        return 0.75
    denom = max(0.25, predicted_delta + 0.15)
    err = abs(actual_delta - predicted_delta) / denom
    return max(0.0, min(1.0, 1.0 - err))


def combined_verify_success(homeostatic: float, reafference: float, *, homeo_weight: float = 0.65) -> float:
    """合并内稳态与 reafference 验证分数（兼容旧双分路径）。"""
    w = max(0.0, min(1.0, float(homeo_weight)))
    return max(0.0, min(1.0, w * float(homeostatic) + (1.0 - w) * float(reafference)))


EXAFFERENCE_OBS_KEYS: tuple[str, ...] = (
    "sensor_pull",
    "actuator_pull",
    "ambient_field",
    "ambient_grad_x",
    "ambient_grad_y",
    "niche_pressure",
    "world_load",
    "world_load_derivative",
)


def exafference_predictability(
    obs_before: Mapping[str, Any],
    obs_after: Mapping[str, Any],
    motor_ax: float,
    motor_ay: float,
    delta_time: float,
) -> float:
    """外场可预测性 [0,1]：obs 变化与 motor 预期一致 → 高分；突发的不可预测外场变化 → 低分。"""
    if delta_time <= 0:
        return 0.5
    motor_mag = math.hypot(float(motor_ax), float(motor_ay))
    coupling = motor_mag * float(delta_time)
    surprises: list[float] = []

    sp0 = float(obs_before.get("intrinsic_speed", 0.0))
    sp1 = float(obs_after.get("intrinsic_speed", sp0))
    predicted_sp_delta = coupling * 0.85
    sp_err = abs((sp1 - sp0) - predicted_sp_delta) / max(0.2, predicted_sp_delta + abs(sp0) * 0.05 + 0.1)
    surprises.append(min(1.0, sp_err))

    for key in EXAFFERENCE_OBS_KEYS:
        v0 = float(obs_before.get(key, 0.0))
        v1 = float(obs_after.get(key, v0))
        delta = abs(v1 - v0)
        expected = coupling * (0.015 + 0.01 * min(1.0, abs(v0)))
        if coupling < 1e-6 and delta < 1e-6:
            continue
        err = abs(delta - expected) / max(0.05, expected + 0.08)
        surprises.append(min(1.0, err))

    if not surprises:
        return 0.75
    avg = sum(surprises) / len(surprises)
    return max(0.0, min(1.0, 1.0 - avg * 0.55))


def pvaec_verify_triple(
    homeostatic: float,
    reafference: float,
    exafference: float,
    *,
    homeo_weight: float = 0.50,
    reaff_weight: float = 0.25,
    exaff_weight: float = 0.25,
) -> float:
    """PVAEC verify 三分：intero + reafference + exafference。"""
    w0 = max(0.0, float(homeo_weight))
    w1 = max(0.0, float(reaff_weight))
    w2 = max(0.0, float(exaff_weight))
    total = w0 + w1 + w2
    if total <= 1e-9:
        return 0.5
    score = (
        w0 * float(homeostatic) + w1 * float(reafference) + w2 * float(exafference)
    ) / total
    return max(0.0, min(1.0, score))
