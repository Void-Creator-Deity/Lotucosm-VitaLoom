# -*- coding: utf-8 -*-
"""SR 视觉状态：从 PVAEC 当帧数据抽取指标（非 sin 循环装饰）。"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from core.Lotucosm.sr_membrane_topology import aggregate_channel_signals


def _f(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _norm01(value: float, *, hi: float = 1.0, lo: float = 0.0) -> float:
    if hi <= lo:
        return 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def _channel_map(entity: Any) -> dict[str, float]:
    raw = getattr(entity, "sr_channel_out", None)
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, float] = {}
    for k, v in raw.items():
        out[str(k)] = _f(v, 0.0)
    return out


@dataclass
class SrEntityVisualState:
    energy: float = 0.5
    arousal: float = 0.0
    chemo_out: float = 0.0
    chemo_in: float = 0.0
    chemo_dir_x: float = 0.0
    chemo_dir_y: float = 0.0
    speed: float = 0.0
    stress: float = 0.0
    thrust: float = 0.0


@dataclass
class SrCellVisualState:
    hub_id: str
    energy: float = 0.5
    arousal: float = 0.0
    chemo_activity: float = 0.0
    signal_flow: float = 0.0
    speed: float = 0.0
    stress: float = 0.0
    vitality: float = 0.5
    signal_phase: float = 0.0
    membrane_phase: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    by_entity: dict[str, SrEntityVisualState] = field(default_factory=dict)
    fluid_pressure_delta: float = 0.0


def extract_entity_visual_state(
    entity: Any,
    *,
    inbound: Mapping[str, float] | None = None,
) -> SrEntityVisualState:
    energy_raw = getattr(entity, "energy", None)
    energy = _norm01(_f(energy_raw, 90.0), hi=180.0, lo=8.0) if energy_raw is not None else 0.5
    arousal = max(0.0, min(1.0, _f(getattr(entity, "emission_strength", 0.0))))
    ch = _channel_map(entity)
    chemo_out = _norm01(max(abs(ch.get("chemo", 0.0)), abs(ch.get("chemo_signal", 0.0))), hi=1.2)
    chemo_in = 0.0
    cdx, cdy = ch.get("chemo_dir_x", 0.0), ch.get("chemo_dir_y", 0.0)
    if inbound:
        chemo_in = _norm01(abs(_f(inbound.get("chemo", 0.0))), hi=1.5)
        cdx = _f(inbound.get("chemo_dir_x", cdx))
        cdy = _f(inbound.get("chemo_dir_y", cdy))
    vx, vy = 0.0, 0.0
    vel = getattr(entity, "velocity", None)
    if vel is not None and hasattr(vel, "__getitem__"):
        try:
            vx, vy = _f(vel[0]), _f(vel[1])
        except (IndexError, TypeError):
            pass
    speed = _norm01(math.hypot(vx, vy), hi=175.0)
    thrust = speed
    hud = getattr(entity, "sr_debug_hud", None)
    stress = 0.0
    if isinstance(hud, Mapping):
        stress = max(0.0, min(1.0, _f(hud.get("stress", hud.get("niche_pressure", 0.0)))))
        thrust = max(thrust, _norm01(abs(_f(hud.get("inbound_chemo", 0.0))), hi=1.2))
    return SrEntityVisualState(
        energy=energy,
        arousal=arousal,
        chemo_out=chemo_out,
        chemo_in=chemo_in,
        chemo_dir_x=cdx,
        chemo_dir_y=cdy,
        speed=speed,
        stress=stress,
        thrust=thrust,
    )


def advance_cell_visual_integrators(
    hub: Any,
    signal_flow: float,
    dt: float,
    *,
    vitality: float = 0.5,
    energy: float = 0.5,
    arousal: float = 0.0,
    speed: float = 0.0,
    stress: float = 0.0,
) -> tuple[float, float]:
    """推进胞内信号相位 + 膜代谢律动相位（均随模拟状态变速，非 scene_time）。"""
    sig_phase = float(getattr(hub, "_sr_vis_signal_phase", 0.0))
    flow = max(0.0, float(signal_flow))
    if flow > 0.02:
        sig_phase += flow * dt * 2.5
    else:
        sig_phase *= 0.85
    hub._sr_vis_signal_phase = sig_phase

    mem_phase = float(getattr(hub, "_sr_vis_membrane_phase", 0.0))
    # 代谢越快（能量/觉醒/游动/趋化）膜律动越快；应激抑制
    beat_rate = (
        0.6
        + 1.4 * max(0.0, energy)
        + 1.0 * max(0.0, arousal)
        + 0.7 * max(0.0, speed)
        + 0.5 * flow
        + 0.35 * max(0.0, vitality)
        - 0.9 * max(0.0, stress)
    )
    beat_rate = max(0.12, beat_rate)
    mem_phase += beat_rate * dt
    hub._sr_vis_membrane_phase = mem_phase
    return sig_phase, mem_phase


def extract_cell_visual_state(
    hub: Any,
    member_ids: set[str],
    id_to_ent: dict[str, Any],
    id_to_type: dict[str, str],
    signal_edges: Iterable[dict[str, Any]],
    all_entities: list[Any],
) -> SrCellVisualState:
    inbound_all = aggregate_channel_signals(signal_edges, all_entities, use_prev=False)
    hub_st = extract_entity_visual_state(hub)
    by_ent: dict[str, SrEntityVisualState] = {str(hub.id): hub_st}
    chemo_peak = 0.0
    flow_peak = 0.0

    vx, vy = 0.0, 0.0
    vel = getattr(hub, "velocity", None)
    if vel is not None and hasattr(vel, "__getitem__"):
        try:
            vx, vy = _f(vel[0]), _f(vel[1])
        except (IndexError, TypeError):
            pass

    for mid in member_ids:
        ent = id_to_ent.get(mid)
        if ent is None or mid == hub.id:
            continue
        et = id_to_type.get(mid, "")
        in_map = inbound_all.get(mid, {})
        st = extract_entity_visual_state(ent, inbound=in_map if et == "actuator" else None)
        if et == "sensor":
            chemo_peak = max(chemo_peak, st.chemo_out)
            flow_peak = max(flow_peak, st.chemo_out)
        if et == "actuator":
            flow_peak = max(flow_peak, st.chemo_in)
        by_ent[mid] = st

    vitality = max(
        0.08,
        min(
            1.0,
            0.4 * hub_st.energy
            + 0.25 * hub_st.arousal
            + 0.2 * chemo_peak
            + 0.15 * hub_st.speed
            - 0.2 * hub_st.stress,
        ),
    )
    return SrCellVisualState(
        hub_id=str(hub.id),
        energy=hub_st.energy,
        arousal=hub_st.arousal,
        chemo_activity=chemo_peak,
        signal_flow=flow_peak,
        speed=hub_st.speed,
        stress=hub_st.stress,
        vitality=vitality,
        signal_phase=float(getattr(hub, "_sr_vis_signal_phase", 0.0)),
        membrane_phase=float(getattr(hub, "_sr_vis_membrane_phase", 0.0)),
        vel_x=vx,
        vel_y=vy,
        by_entity=by_ent,
    )


def sr_gpu_render_requested() -> bool:
    import os

    return os.environ.get("VITALOOM_SR_GPU", "").strip().lower() in ("1", "true", "yes")
