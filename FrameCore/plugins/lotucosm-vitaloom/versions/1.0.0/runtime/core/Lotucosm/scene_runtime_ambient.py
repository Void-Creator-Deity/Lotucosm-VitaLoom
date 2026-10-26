# -*- coding: utf-8 -*-
"""SR 场域与营养势纯数学（从 GameViewport 拆出，无 Qt 依赖）。

职责:
    ambient_* — 场域锚 + 同伴 emission + 生态位调制井/营养势；
    nutrient_* — 仅 nutrient 实体，供膜 sensor 写 chemo/chemo_dir_* 通道。

时机: _run_script_tick_batch 每实体采样一次，写入 ctx.environment；
sensor 脚本将 nutrient_grad 转为信号边，非中枢 GPS 直驱。

排错: 趋化弱 → 查 nutrient 数量、emissions_prev、sr_chemo_gain_scale（中枢 act 写入）。
"""

from __future__ import annotations

from typing import Any, Mapping

from core.Lotucosm.scene_runtime_world_state import well_scale_from_niche_pressure


def well_emission_mod(emissions_prev: Mapping[str, float], eid: str) -> float:
    """Scale static well/nutrient potential by scripted emission (0..1).

    Missing key uses factor 1.0 (legacy behavior). ``f(q) = 0.55 + 0.45 * clamp(q,0,1)``.
    """
    if eid not in emissions_prev:
        return 1.0
    q = float(emissions_prev[eid])
    q = max(0.0, min(1.0, q))
    return 0.55 + 0.45 * q


def ambient_scalar_at(
    ox: float,
    oy: float,
    entities: list[Any],
    emissions_prev: Mapping[str, float],
    niche_pressure: float = 0.0,
) -> float:
    total = 0.0
    for e in entities:
        px = float(e.position[0])
        py = float(e.position[1])
        ddx = ox - px
        ddy = oy - py
        dist_sq = ddx * ddx + ddy * ddy
        et = str(getattr(e, "entity_type", ""))
        rr = float(getattr(e, "radius", 18.0))
        # environment_well / nutrient
        if et in ("environment_well", "nutrient"):
            scale = (rr / 36.0) ** 2
            well_q = well_scale_from_niche_pressure(niche_pressure)
            mod = well_emission_mod(emissions_prev, str(getattr(e, "id", "")))
            total += mod * well_q * scale * 14000.0 / (dist_sq + 2800.0 + rr * rr)
            continue
        q = float(emissions_prev.get(e.id, 0.0))
        if q > 0:
            scale_a = (max(rr, 1.0) / 22.0) ** 0.5
            total += q * scale_a * 3200.0 / (dist_sq + 420.0 + rr * rr)
    return total


def nutrient_scalar_at(
    ox: float,
    oy: float,
    entities: list[Any],
    emissions_prev: Mapping[str, float],
    *,
    field_grid: Any | None = None,
) -> float:
    """仅营养颗粒贡献的标量势（趋化物理层，不含场域锚）。"""
    if field_grid is not None and getattr(field_grid, "enabled", False):
        pot, _gx, _gy = field_grid.nutrient_gradient_at(ox, oy)
        return pot
    total = 0.0
    for e in entities:
        if str(getattr(e, "entity_type", "")) != "nutrient":
            continue
        px = float(e.position[0])
        py = float(e.position[1])
        ddx = ox - px
        ddy = oy - py
        dist_sq = ddx * ddx + ddy * ddy
        rr = float(getattr(e, "radius", 18.0))
        scale = (rr / 36.0) ** 2
        mod = well_emission_mod(emissions_prev, str(getattr(e, "id", "")))
        depl = float(getattr(e, "_sr_field_depletion", 0.0))
        mod *= max(0.08, 1.0 - depl * 0.9)
        total += mod * scale * 14000.0 / (dist_sq + 2800.0 + rr * rr)
    return total


def nutrient_gradient_at(
    ox: float,
    oy: float,
    entities: list[Any],
    emissions_prev: Mapping[str, float],
    *,
    eps: float = 20.0,
    field_grid: Any | None = None,
) -> tuple[float, float, float]:
    """营养势标量 + 梯度 (gx, gy)，供膜受体采样。"""
    if field_grid is not None and getattr(field_grid, "enabled", False):
        return field_grid.nutrient_gradient_at(ox, oy)
    c0 = nutrient_scalar_at(ox, oy, entities, emissions_prev)
    gx = (
        nutrient_scalar_at(ox + eps, oy, entities, emissions_prev)
        - nutrient_scalar_at(ox - eps, oy, entities, emissions_prev)
    ) / (2 * eps)
    gy = (
        nutrient_scalar_at(ox, oy + eps, entities, emissions_prev)
        - nutrient_scalar_at(ox, oy - eps, entities, emissions_prev)
    ) / (2 * eps)
    return c0, gx, gy


def ambient_field_and_gradient(
    ox: float,
    oy: float,
    entities: list[Any],
    emissions_prev: Mapping[str, float],
    *,
    eps: float = 20.0,
    niche_pressure: float = 0.0,
) -> tuple[float, float, float]:
    """环境场标量 + 梯度 (gx, gy)；中枢应激/逃离用，与 nutrient 通道分离。"""
    c0 = ambient_scalar_at(ox, oy, entities, emissions_prev, niche_pressure)
    gx = (
        ambient_scalar_at(ox + eps, oy, entities, emissions_prev, niche_pressure)
        - ambient_scalar_at(ox - eps, oy, entities, emissions_prev, niche_pressure)
    ) / (2 * eps)
    gy = (
        ambient_scalar_at(ox, oy + eps, entities, emissions_prev, niche_pressure)
        - ambient_scalar_at(ox, oy - eps, entities, emissions_prev, niche_pressure)
    ) / (2 * eps)
    return c0, gx, gy
