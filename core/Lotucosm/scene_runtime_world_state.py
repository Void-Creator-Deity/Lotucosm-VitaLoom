"""SR 全局标量：生物圈负载与生态位压力（可单测纯函数）。

职责: step_biosphere_load 每 tick 由 GameViewport 调用；niche_pressure 注入 ambient 与脚本 ctx。
排错: 生态位恒为 0 → load_max；井势过弱 → well_scale_from_niche_pressure。
"""

from __future__ import annotations

import math


def niche_pressure_from_load(load: float, *, load_max: float) -> float:
    """将生物圈负载映射到 [0, 1] 生态位压力。

    职责:
        线性归一化 load / load_max 并钳制。

    时机:
        GameViewport 每 tick 注入 ctx.environment 与 ambient_scalar。

    不变量:
        load_max <= 0 时返回 0.0。

    排错:
        生态位恒为 0 → 查 load_max 与 _sr_biosphere_load 是否更新。
    """
    if load_max <= 0:
        return 0.0
    return max(0.0, min(1.0, float(load) / float(load_max)))


def well_scale_from_niche_pressure(niche_pressure: float, *, floor: float = 0.35, strength: float = 0.65) -> float:
    """高生态位压力下衰减场域井/营养势贡献。

    职责:
        返回 [floor, 1] 乘子，压力越高井越弱。

    时机:
        ambient_scalar_at / nutrient_scalar_at 采样时。

    不变量:
        niche_pressure 钳制在 [0, 1]。

    排错:
        井势过弱 → 调 floor/strength 或负载积分参数。
    """
    p = max(0.0, min(1.0, float(niche_pressure)))
    return max(float(floor), 1.0 - float(strength) * p)


def step_biosphere_load(
    load: float,
    organism_emission_sum: float,
    dt: float,
    *,
    intake_gain: float = 3.2,
    decay_per_sec: float = 0.08,
    load_max: float = 50.0,
) -> float:
    """有机体 emission 摄入 + 指数衰减，再钳制到 load_max。

    职责:
        更新全局 _sr_biosphere_load 标量。

    时机:
        GameViewport tick 末（script 批之后）。

    不变量:
        dt <= 0 时不增只钳制；结果 >= 0。

    排错:
        负载不涨 → organism emission_strength 与 intake_gain。
    """
    if dt <= 0:
        return max(0.0, min(float(load_max), float(load)))
    inc = float(intake_gain) * max(0.0, float(organism_emission_sum)) * float(dt)
    decayed = float(load) * math.exp(-float(decay_per_sec) * float(dt))
    new_load = decayed + inc
    return max(0.0, min(float(load_max), new_load))
