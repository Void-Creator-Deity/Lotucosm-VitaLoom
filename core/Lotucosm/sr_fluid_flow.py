# -*- coding: utf-8
"""SR 流体场：胞外营养/场域梯度 + 胞内趋化/能量流 → 膜形变与流动粒子（非纯 sin 装饰）。

职责:
    extracellular_flow_at — 营养势 + 环境场 + 邻近游动尾流；
    intracellular_flow_at — 核→执行器能量流 + 受体→核趋化回流；
    compute_membrane_flow_offsets — 按角度采样内外压差驱动质膜径向偏移；
    advect_fluid_particles — tick 推进 hub 上缓存的流动粒子。

时机: PVAEC 轨每帧 extract_cell + advance 视觉积分器；GameViewport 非 game_mode。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from core.Lotucosm.scene_runtime_ambient import (
    ambient_field_and_gradient,
    nutrient_gradient_at,
)


@dataclass(frozen=True)
class SrFluidCouplingConfig:
    """胞外场 → 运动耦合（PVAEC 轨；默认关闭 GPS 漂移，保留摄取/视觉）。"""

    enabled: bool = False
    drift_gain: float = 0.14
    max_drift_accel: float = 38.0
    uptake_rate: float = 1.6
    secretion_gain: float = 0.22
    chemo_suppress: float = 0.82

    @classmethod
    def from_scene(cls, raw: Mapping[str, Any] | None) -> "SrFluidCouplingConfig":
        if not isinstance(raw, dict):
            return cls()
        kwargs: dict[str, Any] = {}

        def _float(key: str, default: float) -> float:
            try:
                return float(raw[key])
            except (KeyError, TypeError, ValueError):
                return default

        if "enabled" in raw:
            kwargs["enabled"] = bool(raw["enabled"])
        kwargs["drift_gain"] = _float("drift_gain", cls.drift_gain)
        kwargs["max_drift_accel"] = _float("max_drift_accel", cls.max_drift_accel)
        kwargs["uptake_rate"] = _float("uptake_rate", cls.uptake_rate)
        kwargs["secretion_gain"] = _float("secretion_gain", cls.secretion_gain)
        kwargs["chemo_suppress"] = _float("chemo_suppress", cls.chemo_suppress)
        return cls(**kwargs)

    @classmethod
    def from_scene_data(cls, scene_data: Mapping[str, Any]) -> "SrFluidCouplingConfig":
        raw = scene_data.get("sr_fluid_coupling")
        if isinstance(raw, dict):
            return cls.from_scene(raw)
        pond = scene_data.get("pond_config")
        if isinstance(pond, dict):
            nested = pond.get("sr_fluid_coupling")
            if isinstance(nested, dict):
                return cls.from_scene(nested)
        return cls()


def extracellular_drift_gradient_at(
    ox: float,
    oy: float,
    entities: Sequence[Any],
    emissions_prev: Mapping[str, float],
    *,
    niche_pressure: float = 0.0,
    field_grid: Any | None = None,
) -> tuple[float, float]:
    """仅营养 + 环境场梯度（用于运动耦合，不含纤毛射流/尾流，避免与 actuator_coupling 重复）。"""
    if field_grid is not None and getattr(field_grid, "enabled", False):
        _pot, ngx, ngy = field_grid.nutrient_gradient_at(ox, oy)
        _pot_a, agx, agy = field_grid.ambient_gradient_at(ox, oy)
    else:
        _pot, ngx, ngy = nutrient_gradient_at(
            ox, oy, list(entities), emissions_prev, field_grid=field_grid
        )
        _pot_a, agx, agy = ambient_field_and_gradient(
            ox, oy, list(entities), emissions_prev, niche_pressure=niche_pressure
        )
    vx = ngx * 0.62 + agx * 0.38
    vy = ngy * 0.62 + agy * 0.38
    return _norm2(vx, vy, cap=1.0)


def apply_extracellular_drift(
    entities: Sequence[Any],
    emissions_prev: Mapping[str, float],
    dt: float,
    config: SrFluidCouplingConfig,
    *,
    niche_pressure: float = 0.0,
    field_grid: Any | None = None,
) -> None:
    """胞外场梯度对 organism 的轻推（辅助项，膜 chemo 强时自动减弱）。

    设计：中枢不读营养 GPS；主路径仍是 sensor→chemo→actuator。
    漂移只在趋化通道弱时补一点场梯度，避免与膜拓扑抢控制权。
    """
    if not config.enabled or dt <= 0.0:
        return
    gain = max(0.0, float(config.drift_gain))
    cap = max(1.0, float(config.max_drift_accel))
    suppress_k = max(0.0, min(1.0, float(config.chemo_suppress)))
    for ent in entities:
        if str(getattr(ent, "entity_type", "")) != "organism":
            continue
        if getattr(ent, "pinned", False) or getattr(ent, "membrane_locked", False):
            continue
        chemo_scale = max(0.0, min(1.2, float(getattr(ent, "sr_chemo_gain_scale", 1.0))))
        hud = getattr(ent, "sr_debug_hud", None)
        if isinstance(hud, dict):
            try:
                chemo_scale = max(chemo_scale, float(hud.get("chemo_gain_scale", 0.0)) * 0.01)
            except (TypeError, ValueError):
                pass
        blend = max(0.08, 1.0 - suppress_k * min(1.0, chemo_scale))
        ox = float(ent.position[0])
        oy = float(ent.position[1])
        gx, gy = extracellular_drift_gradient_at(
            ox,
            oy,
            entities,
            emissions_prev,
            niche_pressure=niche_pressure,
            field_grid=field_grid,
        )
        mag = math.hypot(gx, gy)
        if mag < 1e-6:
            continue
        ax = gx * cap * gain * blend
        ay = gy * cap * gain * blend
        vel = ent.velocity
        if vel is None or not hasattr(vel, "__getitem__"):
            continue
        vel[0] = float(vel[0]) + ax * dt
        vel[1] = float(vel[1]) + ay * dt
        spd = math.hypot(float(vel[0]), float(vel[1]))
        spd_cap = cap * 0.55
        if spd > spd_cap and spd > 0:
            s = spd_cap / spd
            vel[0] = float(vel[0]) * s
            vel[1] = float(vel[1]) * s


def step_nutrient_field_exchange(
    entities: Sequence[Any],
    dt: float,
    config: SrFluidCouplingConfig,
) -> None:
    """重叠摄取降低营养 emission；纤毛 secretion 写入 emission_strength。"""
    if dt <= 0.0:
        return
    uptake = max(0.0, float(config.uptake_rate))
    sec_gain = max(0.0, float(config.secretion_gain))
    nutrients = [e for e in entities if str(getattr(e, "entity_type", "")) == "nutrient"]
    organisms = [e for e in entities if str(getattr(e, "entity_type", "")) == "organism"]
    actuators = [e for e in entities if str(getattr(e, "entity_type", "")) == "actuator"]

    for act in actuators:
        q = float(getattr(act, "emission_strength", 0.0))
        if q > 0.02:
            act.emission_strength = min(1.0, q + sec_gain * dt)

    if uptake <= 0.0 or not nutrients or not organisms:
        return

    for org in organisms:
        ox = float(org.position[0])
        oy = float(org.position[1])
        ro = max(4.0, float(getattr(org, "radius", 18.0)))
        for nut in nutrients:
            nx = float(nut.position[0])
            ny = float(nut.position[1])
            rn = max(2.0, float(getattr(nut, "radius", 10.0)))
            dist = math.hypot(nx - ox, ny - oy)
            touch = dist <= ro + rn + 6.0
            if not touch:
                continue
            overlap = max(0.0, ro + rn + 6.0 - dist)
            frac = min(1.0, overlap / max(1.0, ro + rn))
            depl = float(getattr(nut, "_sr_field_depletion", 0.0))
            depl = min(1.0, depl + uptake * frac * dt)
            nut._sr_field_depletion = depl
            nut._sr_uptake_flux = min(1.0, depl)
            base_q = float(getattr(nut, "emission_strength", 1.0))
            nut.emission_strength = max(0.0, base_q * (1.0 - depl * 0.85))


def _norm2(x: float, y: float, *, cap: float = 1.0) -> tuple[float, float]:
    d = math.hypot(x, y)
    if d < 1e-9:
        return 0.0, 0.0
    s = min(cap, 1.0) / d
    return x * s, y * s


def extracellular_flow_at(
    ox: float,
    oy: float,
    entities: Sequence[Any],
    emissions_prev: Mapping[str, float],
    *,
    niche_pressure: float = 0.0,
    exclude_hub_id: str | None = None,
) -> tuple[float, float, float]:
    """胞外水流速度 (vx, vy) 与合势标量（仅用于可视化强度）。"""
    _pot_n, ngx, ngy = nutrient_gradient_at(ox, oy, list(entities), emissions_prev)
    _pot_a, agx, agy = ambient_field_and_gradient(
        ox, oy, list(entities), emissions_prev, niche_pressure=niche_pressure
    )
    vx = ngx * 0.55 + agx * 0.35
    vy = ngy * 0.55 + agy * 0.35

    for e in entities:
        if exclude_hub_id and str(getattr(e, "id", "")) == exclude_hub_id:
            continue
        et = str(getattr(e, "entity_type", ""))
        if et not in ("organism", "actuator"):
            continue
        px = float(e.position[0])
        py = float(e.position[1])
        ddx, ddy = ox - px, oy - py
        dist_sq = ddx * ddx + ddy * ddy
        rr = max(8.0, float(getattr(e, "radius", 18.0)))
        if dist_sq > (rr * 4.5) ** 2:
            continue
        vel = getattr(e, "velocity", None)
        if vel is None:
            continue
        try:
            evx, evy = float(vel[0]), float(vel[1])
        except (IndexError, TypeError, ValueError):
            continue
        spd = math.hypot(evx, evy)
        if spd < 2.0:
            continue
        wake = spd * rr * rr / (dist_sq + rr * rr * 0.6)
        vx += evx * wake * 0.018
        vy += evy * wake * 0.018

    for e in entities:
        if str(getattr(e, "entity_type", "")) != "actuator":
            continue
        q = float(emissions_prev.get(str(getattr(e, "id", "")), 0.0))
        if q < 0.08:
            continue
        px = float(e.position[0])
        py = float(e.position[1])
        ddx, ddy = ox - px, oy - py
        dist = math.hypot(ddx, ddy) + 1e-6
        rr = max(6.0, float(getattr(e, "radius", 10.0)))
        if dist > rr * 5.0:
            continue
        jet = q * 42.0 / (dist + rr)
        vx += (ddx / dist) * jet
        vy += (ddy / dist) * jet

    potential = math.hypot(ngx, ngy) + math.hypot(agx, agy) * 0.6
    vx, vy = _norm2(vx, vy, cap=120.0)
    return vx, vy, potential


def intracellular_flow_at(
    ox: float,
    oy: float,
    hub: Any,
    *,
    hub_x: float,
    hub_y: float,
    energy: float,
    signal_flow: float,
    actuators: Sequence[tuple[float, float, float]],
    sensors: Sequence[tuple[float, float, float]],
) -> tuple[float, float]:
    """胞内能量/信号水流：核→执行器 + 受体→核。"""
    vx, vy = 0.0, 0.0
    hx, hy = hub_x, hub_y

    for ax, ay, chemo_in in actuators:
        ddx, ddy = ax - ox, ay - oy
        dist = math.hypot(ddx, ddy) + 1e-6
        w = max(0.05, chemo_in) * energy / (dist + 18.0)
        vx += (ddx / dist) * w * 85.0
        vy += (ddy / dist) * w * 85.0

    for sx, sy, chemo_out in sensors:
        ddx, ddy = hx - ox, hy - oy
        dist = math.hypot(ddx, ddy) + 1e-6
        w = max(0.05, chemo_out) * signal_flow / (dist + 14.0)
        vx += (ddx / dist) * w * 65.0
        vy += (ddy / dist) * w * 65.0

    if not actuators and not sensors:
        ddx, ddy = hx - ox, hy - oy
        dist = math.hypot(ddx, ddy) + 1e-6
        vx += (ddx / dist) * energy * 25.0
        vy += (ddy / dist) * energy * 25.0

    return _norm2(vx, vy, cap=95.0)


@dataclass
class SrExchangeSite:
    x: float
    y: float
    strength: float
    direction: str  # "in" | "out"


@dataclass
class SrCellFluidState:
    hub_id: str
    exo_vx: float = 0.0
    exo_vy: float = 0.0
    endo_vx: float = 0.0
    endo_vy: float = 0.0
    pressure_delta: float = 0.0
    membrane_offsets: list[float] = field(default_factory=list)
    exchange_sites: list[SrExchangeSite] = field(default_factory=list)


def compute_membrane_flow_offsets(
    cx: float,
    cy: float,
    *,
    segments: int,
    base_radius: float,
    hub: Any,
    cell_energy: float,
    cell_signal_flow: float,
    cell_speed: float,
    cell_stress: float,
    vel_x: float,
    vel_y: float,
    membrane_phase: float,
    actuators: Sequence[tuple[float, float, float, float]],
    sensors: Sequence[tuple[float, float, float, float]],
    entities: Sequence[Any],
    emissions_prev: Mapping[str, float],
    niche_pressure: float = 0.0,
    metabolic_wobble_scale: float = 0.35,
) -> tuple[list[float], SrCellFluidState]:
    """按膜角度采样内外流，生成径向偏移（驱动质膜形变）。"""
    n = max(16, segments)
    hub_id = str(getattr(hub, "id", ""))
    act_in = [(a[0], a[1], a[3]) for a in actuators]
    sen_out = [(s[0], s[1], s[3]) for s in sensors]
    offsets: list[float] = []
    exo_sum_x = exo_sum_y = 0.0
    endo_sum_x = endo_sum_y = 0.0
    pressure_samples: list[float] = []

    for i in range(n):
        ang = (i / n) * math.tau
        nx, ny = math.cos(ang), math.sin(ang)
        sample_r = base_radius * 0.92
        sx = cx + nx * sample_r
        sy = cy + ny * sample_r
        evx, evy, _pot = extracellular_flow_at(
            sx,
            sy,
            entities,
            emissions_prev,
            niche_pressure=niche_pressure,
            exclude_hub_id=hub_id,
        )
        ivx, ivy = intracellular_flow_at(
            sx,
            sy,
            hub,
            hub_x=cx,
            hub_y=cy,
            energy=cell_energy,
            signal_flow=cell_signal_flow,
            actuators=act_in,
            sensors=sen_out,
        )
        exo_sum_x += evx
        exo_sum_y += evy
        endo_sum_x += ivx
        endo_sum_y += ivy

        exo_n = evx * nx + evy * ny
        endo_n = ivx * nx + ivy * ny
        vel_n = vel_x * nx + vel_y * ny
        pressure = exo_n - endo_n * 0.85
        pressure_samples.append(pressure)

        deform = (
            exo_n * 0.045
            + endo_n * 0.032
            + vel_n * 0.038 * (0.4 + cell_speed)
            - cell_stress * 6.0
        )
        if cell_signal_flow > 0.04:
            deform += (
                metabolic_wobble_scale
                * cell_signal_flow
                * math.sin(ang * 2.0 + membrane_phase)
                * (0.3 + 0.7 * cell_energy)
            )
        offsets.append(deform)

    anchor_vels: Sequence[tuple[float, float, float, float, float]] = getattr(
        hub, "_sr_shape_anchor_vels", ()
    )
    if anchor_vels:
        for i in range(n):
            ang = (i / n) * math.tau
            nx, ny = math.cos(ang), math.sin(ang)
            for ax, ay, _ar, avx, avy in anchor_vels:
                aang = math.atan2(ay - cy, ax - cx)
                da = ang - aang
                while da > math.pi:
                    da -= math.tau
                while da < -math.pi:
                    da += math.tau
                w = math.exp(-(da * da) / 0.35)
                offsets[i] += w * (avx * nx + avy * ny) * 0.028

    exo_vx = exo_sum_x / n
    exo_vy = exo_sum_y / n
    endo_vx = endo_sum_x / n
    endo_vy = endo_sum_y / n
    pressure_delta = sum(pressure_samples) / max(1, len(pressure_samples))

    exchange: list[SrExchangeSite] = []
    for sx, sy, _sr, chemo_out in sensors:
        exchange.append(SrExchangeSite(sx, sy, min(1.0, chemo_out), "in"))
    for ax, ay, thrust, chemo_in in actuators:
        strength = min(1.0, 0.45 * chemo_in + 0.55 * thrust)
        exchange.append(SrExchangeSite(ax, ay, strength, "out"))

    state = SrCellFluidState(
        hub_id=hub_id,
        exo_vx=exo_vx,
        exo_vy=exo_vy,
        endo_vx=endo_vx,
        endo_vy=endo_vy,
        pressure_delta=pressure_delta,
        membrane_offsets=offsets,
        exchange_sites=exchange,
    )
    return offsets, state


def _ensure_particles(hub: Any, kind: str, count: int) -> list[list[float]]:
    key = f"_sr_fluid_{kind}_particles"
    raw = getattr(hub, key, None)
    if not isinstance(raw, list) or len(raw) != count:
        raw = [[0.0, 0.0, float(i) / max(1, count)] for i in range(count)]
        setattr(hub, key, raw)
    return raw


def advect_fluid_particles(
    hub: Any,
    fluid: SrCellFluidState,
    *,
    cx: float,
    cy: float,
    membrane_radius: float,
    dt: float,
    entities: Sequence[Any],
    emissions_prev: Mapping[str, float],
    niche_pressure: float = 0.0,
    exo_count: int = 10,
    endo_count: int = 8,
) -> None:
    """推进胞外/胞内流动粒子（位置相对 hub，渲染时转世界坐标）。"""
    if dt <= 0.0:
        return
    hub_id = str(getattr(hub, "id", ""))
    exo = _ensure_particles(hub, "exo", exo_count)
    endo = _ensure_particles(hub, "endo", endo_count)
    r_mem = max(20.0, membrane_radius)

    for p in exo:
        ang = p[2] * math.tau
        px = cx + math.cos(ang) * (r_mem * 1.08)
        py = cy + math.sin(ang) * (r_mem * 1.08)
        vx, vy, _ = extracellular_flow_at(
            px,
            py,
            entities,
            emissions_prev,
            niche_pressure=niche_pressure,
            exclude_hub_id=hub_id,
        )
        p[0] = (p[0] + vx * dt * 0.35) % 1.0
        p[1] = (p[1] + vy * dt * 0.35) % 1.0
        p[2] = (p[2] + dt * 0.12) % 1.0

    for p in endo:
        t = p[2]
        px = cx + (p[0] - 0.5) * r_mem * 0.7 * (1.0 - t * 0.5)
        py = cy + (p[1] - 0.5) * r_mem * 0.7 * (1.0 - t * 0.5)
        ivx, ivy = intracellular_flow_at(
            px,
            py,
            hub,
            hub_x=cx,
            hub_y=cy,
            energy=0.6,
            signal_flow=fluid.pressure_delta * 0.01 + 0.2,
            actuators=[(cx + fluid.endo_vx, cy + fluid.endo_vy, 0.5)],
            sensors=[],
        )
        p[0] = max(0.02, min(0.98, p[0] + ivx * dt * 0.004))
        p[1] = max(0.02, min(0.98, p[1] + ivy * dt * 0.004))
        p[2] = (p[2] + dt * (0.25 + abs(fluid.endo_vx + fluid.endo_vy) * 0.002)) % 1.0


def build_cell_fluid_state(
    hub: Any,
    member_ids: set[str],
    id_to_ent: dict[str, Any],
    id_to_type: dict[str, str],
    *,
    cell_energy: float,
    cell_signal_flow: float,
    cell_speed: float,
    cell_stress: float,
    vel_x: float,
    vel_y: float,
    membrane_phase: float,
    by_entity: Mapping[str, Any],
    entities: Sequence[Any],
    emissions_prev: Mapping[str, float],
    niche_pressure: float = 0.0,
    segments: int = 44,
) -> SrCellFluidState:
    """从当帧 PVAEC 视觉状态构造流体场（膜偏移 + 交换位点）。"""
    cx = float(hub.position[0])
    cy = float(hub.position[1])
    base_r = max(26.0, float(getattr(hub, "radius", 22.0)) * 1.35)
    actuators: list[tuple[float, float, float, float]] = []
    sensors: list[tuple[float, float, float, float]] = []
    anchor_vels: list[tuple[float, float, float, float, float]] = []
    for mid in member_ids:
        if mid == str(getattr(hub, "id", "")):
            continue
        ent = id_to_ent.get(mid)
        if ent is None:
            continue
        et = id_to_type.get(mid, "")
        st = by_entity.get(mid)
        px, py = float(ent.position[0]), float(ent.position[1])
        vel = getattr(ent, "velocity", None)
        avx = avy = 0.0
        if vel is not None and hasattr(vel, "__getitem__"):
            try:
                avx, avy = float(vel[0]), float(vel[1])
            except (IndexError, TypeError, ValueError):
                pass
        if et == "actuator":
            chemo_in = float(getattr(st, "chemo_in", 0.0)) if st is not None else 0.0
            thrust = float(getattr(st, "thrust", 0.0)) if st is not None else 0.0
            actuators.append((px, py, thrust, chemo_in))
        elif et == "sensor":
            chemo_out = float(getattr(st, "chemo_out", 0.0)) if st is not None else 0.0
            sensors.append((px, py, float(getattr(ent, "radius", 10.0)), chemo_out))
        if et in ("sensor", "actuator"):
            anchor_vels.append((px, py, float(getattr(ent, "radius", 10.0)), avx, avy))
    hub._sr_shape_anchor_vels = anchor_vels

    _offsets, state = compute_membrane_flow_offsets(
        cx,
        cy,
        segments=segments,
        base_radius=base_r,
        hub=hub,
        cell_energy=cell_energy,
        cell_signal_flow=cell_signal_flow,
        cell_speed=cell_speed,
        cell_stress=cell_stress,
        vel_x=vel_x,
        vel_y=vel_y,
        membrane_phase=membrane_phase,
        actuators=actuators,
        sensors=sensors,
        entities=entities,
        emissions_prev=emissions_prev,
        niche_pressure=niche_pressure,
    )
    use_pbd = bool(getattr(hub, "_sr_membrane_pbd", False))
    if use_pbd:
        from core.Lotucosm.sr_membrane_pbd import refine_membrane_offsets_pbd

        pbd_anchors = [(a[0], a[1], a[2]) for a in anchor_vels]
        state.membrane_offsets = refine_membrane_offsets_pbd(
            state.membrane_offsets,
            hub=hub,
            anchors=pbd_anchors,
            segments=segments,
            base_radius=base_r,
            dt=0.016,
        )
    hub._sr_fluid_state = state
    return state
