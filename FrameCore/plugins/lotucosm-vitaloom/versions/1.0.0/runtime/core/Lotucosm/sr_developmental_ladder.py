# -*- coding: utf-8 -*-
"""SR PVAEC 个体发育阶梯：S0–S4 感知键 unlock 与进阶阈值（ADR-0004）。

职责: 提供 stage→允许 observation 键、进阶 tick 下限、verify/explore 计数阈值。
时机: PvaecScript.perception_mask / _maybe_advance_developmental_stage。
不变量: stage ∈ [0, MAX_DEVELOPMENTAL_STAGE]；键名与 CentralBrainPvaec.perceive 对齐。
排错: 见 docs/adr/0004-pvaec-developmental-ladder.md。
"""
from __future__ import annotations

from typing import Any, Dict, FrozenSet, Mapping

MAX_DEVELOPMENTAL_STAGE = 4

# CentralBrainPvaec.perceive 输出的全部外场键（按 stage 累加解锁）
_STAGE_KEYS: Dict[int, FrozenSet[str]] = {
    0: frozenset(
        {
            "simulation_time",
            "bounds",
            "world_width",
            "world_height",
            "memory_stress_ema",
            "memory_field_ema",
            "memory_speed_ema",
        }
    ),
    1: frozenset(
        {
            "simulation_time",
            "bounds",
            "world_width",
            "world_height",
            "memory_stress_ema",
            "memory_field_ema",
            "memory_speed_ema",
            "intrinsic_speed",
        }
    ),
    2: frozenset(
        {
            "simulation_time",
            "bounds",
            "world_width",
            "world_height",
            "memory_stress_ema",
            "memory_field_ema",
            "memory_speed_ema",
            "intrinsic_speed",
            "sensor_pull",
            "actuator_pull",
            "ambient_field",
            "ambient_grad_x",
            "ambient_grad_y",
        }
    ),
    3: frozenset(
        {
            "simulation_time",
            "bounds",
            "world_width",
            "world_height",
            "memory_stress_ema",
            "memory_field_ema",
            "memory_speed_ema",
            "intrinsic_speed",
            "sensor_pull",
            "actuator_pull",
            "ambient_field",
            "ambient_grad_x",
            "ambient_grad_y",
            "nearest_id",
            "nearest_dist",
            "peer_organism_pull",
            "niche_pressure",
        }
    ),
    4: frozenset(
        {
            "simulation_time",
            "bounds",
            "world_width",
            "world_height",
            "memory_stress_ema",
            "memory_field_ema",
            "memory_speed_ema",
            "intrinsic_speed",
            "sensor_pull",
            "actuator_pull",
            "ambient_field",
            "ambient_grad_x",
            "ambient_grad_y",
            "nearest_id",
            "nearest_dist",
            "peer_organism_pull",
            "niche_pressure",
            "world_load",
            "world_load_derivative",
        }
    ),
}

_STAGE_MIN_TICKS: Dict[int, int] = {0: 0, 1: 30, 2: 100, 3: 300, 4: 500}
_EXPLORE_ACTS_FOR_S1 = 3
_VERIFY_SUCCESSES_FOR_S2 = 5
_VERIFY_SUCCESS_THRESHOLD = 0.55
VERIFY_SUCCESS_THRESHOLD = _VERIFY_SUCCESS_THRESHOLD
_REMEMBER_EVENTS_FOR_S3 = 1
_ORGANISM_PEER_COUNT_FOR_S4 = 2

_NEUTRAL_VALUES: Dict[str, Any] = {
    "nearest_id": None,
    "nearest_dist": None,
    "sensor_pull": 0.0,
    "actuator_pull": 0.0,
    "peer_organism_pull": 0.0,
    "ambient_field": 0.0,
    "ambient_grad_x": 0.0,
    "ambient_grad_y": 0.0,
    "world_load": 0.0,
    "niche_pressure": 0.0,
    "world_load_derivative": 0.0,
    "intrinsic_speed": 0.0,
    "memory_stress_ema": 0.0,
    "memory_field_ema": 0.0,
    "memory_speed_ema": 0.0,
    "world_width": 0,
    "world_height": 0,
    "simulation_time": 0.0,
}


def clamp_stage(stage: int) -> int:
    """将 stage 钳制到 [0, MAX_DEVELOPMENTAL_STAGE]。"""
    try:
        s = int(stage)
    except (TypeError, ValueError):
        return 0
    return max(0, min(MAX_DEVELOPMENTAL_STAGE, s))


def perception_keys_for_stage(stage: int) -> frozenset[str]:
    """返回给定 stage 允许的 observation 键集合。"""
    return _STAGE_KEYS[clamp_stage(stage)]


def filter_observation_for_stage(observation: Mapping[str, Any], stage: int) -> Dict[str, Any]:
    """按 stage mask：允许键保留原值，其余键置中性值（供 think 安全读取）。"""
    allowed = perception_keys_for_stage(stage)
    out: Dict[str, Any] = dict(observation)
    for key in list(out.keys()):
        if key in allowed:
            continue
        if key in _NEUTRAL_VALUES:
            out[key] = _NEUTRAL_VALUES[key]
        elif key == "bounds":
            out[key] = observation.get("bounds", (0, 0))
        else:
            out.pop(key, None)
    for key in allowed:
        if key not in out:
            out[key] = _NEUTRAL_VALUES.get(key, 0.0)
    return out


def stage_min_ticks(stage: int) -> int:
    """进入下一 stage 前，当前 stage 至少经历的 tick 数。"""
    return _STAGE_MIN_TICKS.get(clamp_stage(stage), 0)


def plasticity_window_active(
    stage: int,
    stage_ticks: int,
    plasticity_window: int,
) -> bool:
    """是否处于 min_ticks 之后的可塑窗口内（Q7 critical period 延长）。"""
    window = max(0, int(plasticity_window))
    if window <= 0:
        return False
    stage = clamp_stage(stage)
    min_t = stage_min_ticks(stage)
    return stage_ticks > min_t and stage_ticks <= min_t + window


def plasticity_window_closed(
    stage: int,
    stage_ticks: int,
    plasticity_window: int,
) -> bool:
    """可塑窗口已关闭且仍未进阶（关键期结束）。"""
    window = max(0, int(plasticity_window))
    if window <= 0:
        return False
    stage = clamp_stage(stage)
    return stage_ticks > stage_min_ticks(stage) + window


def _requirement_with_plasticity(
    required: int,
    stage: int,
    stage_ticks: int,
    plasticity_window: int,
    *,
    plasticity_penalty: bool = False,
) -> int:
    """窗口内放宽 1；窗口关闭后可选收紧 1（关键期结束惩罚）。"""
    if plasticity_window_active(stage, stage_ticks, plasticity_window):
        return max(1, int(required) - 1)
    if plasticity_penalty and plasticity_window_closed(stage, stage_ticks, plasticity_window):
        return int(required) + 1
    return int(required)


def can_advance_stage(
    current_stage: int,
    stage_ticks: int,
    explore_act_count: int,
    verify_success_count: int,
    remember_event_count: int,
    reproduced: bool,
    organism_peer_count: int,
    *,
    plasticity_window: int = 0,
    plasticity_penalty: bool = False,
) -> bool:
    """是否满足从 current_stage 升到 current_stage+1 的条件。"""
    stage = clamp_stage(current_stage)
    if stage >= MAX_DEVELOPMENTAL_STAGE:
        return False
    if stage_ticks < stage_min_ticks(stage):
        return False
    kw = {
        "plasticity_penalty": bool(plasticity_penalty),
    }
    need_explore = _requirement_with_plasticity(
        _EXPLORE_ACTS_FOR_S1, stage, stage_ticks, plasticity_window, **kw
    )
    need_verify = _requirement_with_plasticity(
        _VERIFY_SUCCESSES_FOR_S2, stage, stage_ticks, plasticity_window, **kw
    )
    need_remember = _requirement_with_plasticity(
        _REMEMBER_EVENTS_FOR_S3, stage, stage_ticks, plasticity_window, **kw
    )
    if stage == 0 and explore_act_count < need_explore:
        return False
    if stage == 1 and verify_success_count < need_verify:
        return False
    if stage == 2 and remember_event_count < need_remember:
        return False
    if stage == 3 and not reproduced and organism_peer_count < _ORGANISM_PEER_COUNT_FOR_S4:
        return False
    return True


def can_advance_stage_legacy(
    current_stage: int,
    stage_ticks: int,
    explore_act_count: int,
    verify_success_count: int,
    remember_event_count: int,
    reproduced: bool,
    organism_peer_count: int,
) -> bool:
    """兼容旧签名（无 plasticity_window）。"""
    return can_advance_stage(
        current_stage,
        stage_ticks,
        explore_act_count,
        verify_success_count,
        remember_event_count,
        reproduced,
        organism_peer_count,
        plasticity_window=0,
    )
