# -*- coding: utf-8 -*-
"""SR/PS 内感受（interoception）：本质变量快照与内稳态验证分数。

借鉴（非归类）: EVAAA 本质变量、Active Inference 偏好验证等文献思路，用于 PVAEC verify 阶段。

职责: 从实体/ctx 抽取 energy/health/stress 等，计算 homeostatic_success。
时机: GameViewport 注入 environment；PvaecScript.verify 读取。
排错: 见 docs/pvaec_cell_evolution.md。
"""
from __future__ import annotations

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
