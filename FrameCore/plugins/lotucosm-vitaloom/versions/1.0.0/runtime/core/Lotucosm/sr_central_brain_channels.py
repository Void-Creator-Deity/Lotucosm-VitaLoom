# -*- coding: utf-8 -*-
"""SR 中枢纯函数通道数学（无实体引用；MindProfile 参数化）。

motion_acceleration 含世界几何中心牵引，与膜 chemo 趋化独立（勿与 GPS 趋食混淆）。

职责: stress_raw_and_norm / memory_step / motion_acceleration 纯函数。
时机: CentralBrainPvaec.think/act 每 tick。
不变量: 营养趋化不在此模块（走膜通道）。
排错: 总往中心漂 → motion_acceleration；见 docs/sr_mind_profile_fields.md P2。
"""

from __future__ import annotations

import math
from typing import Any, Dict, Tuple

from core.Lotucosm.sr_mind_profile import MindProfile

_EPS_NORM = 1e-6


def stress_raw_and_norm(observation: Dict[str, Any], profile: MindProfile) -> Tuple[float, float]:
    """合成应激 raw 与 tanh 归一化值。

    职责:
        聚合 sensor/actuator/场/生态位/负载导数项。

    时机:
        CentralBrainPvaec.think 每 tick。

    不变量:
        纯函数，不写 observation。

    排错:
        应激恒为 0 → 查 observation 键名与 MindProfile 系数。
    """
    sensor_pull = float(observation.get("sensor_pull", 0.0))
    actuator_pull = float(observation.get("actuator_pull", 0.0))
    org_pull = float(observation.get("peer_organism_pull", 0.0))
    ambient_field = float(observation.get("ambient_field", 0.0))
    niche_p = float(observation.get("niche_pressure", 0.0))
    w_load_deriv = float(observation.get("world_load_derivative", 0.0))

    wave_risk = math.tanh((ambient_field / profile.wave_field_div) * profile.wave_tanh_scale)
    stress_raw = (
        sensor_pull
        - profile.actuator_damping * actuator_pull
        + profile.wave_risk_coeff * wave_risk
        - profile.org_pull_coeff * org_pull
        + profile.niche_stress_coeff * niche_p
        - profile.load_deriv_penalty * max(0.0, w_load_deriv)
    )
    stress_norm = math.tanh(stress_raw * profile.stress_tanh_scale)
    return stress_raw, stress_norm


def memory_step(
    memory: Dict[str, float],
    observation: Dict[str, Any],
    profile: MindProfile,
    stress_norm: float,
) -> None:
    """更新 stress/field/speed 的 EMA 记忆。

    职责:
        就地写 memory dict 三个 EMA 键。

    时机:
        think 在 stress_norm 计算之后。

    不变量:
        memory 须预初始化键（中枢 start 负责）。

    排错:
        记忆不更新 → mem_alpha 为 0 或 memory 缺键。
    """
    a = profile.mem_alpha
    ambient_field = float(observation.get("ambient_field", 0.0))
    intrinsic_speed = float(observation.get("intrinsic_speed", 0.0))
    memory["stress_ema"] = (1 - a) * memory["stress_ema"] + a * abs(stress_norm)
    memory["field_ema"] = (1 - a) * memory["field_ema"] + a * min(ambient_field / profile.field_flee_div, 1.0)
    spd_n = min(1.0, intrinsic_speed / profile.intrinsic_speed_div)
    memory["speed_ema"] = (1 - a) * memory["speed_ema"] + a * spd_n


def motion_acceleration(
    observation: Dict[str, Any],
    memory: Dict[str, float],
    profile: MindProfile,
    stress_norm: float,
    ox: float,
    oy: float,
    world_w: float,
    world_h: float,
) -> Tuple[float, float]:
    """合成加速度：世界中心牵引 + 沿 ambient 梯度逃离 + 切向漫游。

    职责:
        返回 (ax, ay) 供中枢写入 organism.velocity。

    时机:
        CentralBrainPvaec.think 在 stress_norm 与 memory_step 之后。

    不变量:
        非营养 GPS；与膜 chemo 通道独立（见模块顶 P2）。

    排错:
        总往中心漂 → gain_high/low_stress；逃离弱 → field_flee_gain。
    """
    ambient_field = float(observation.get("ambient_field", 0.0))
    gxf = float(observation.get("ambient_grad_x", 0.0))
    gyf = float(observation.get("ambient_grad_y", 0.0))
    niche_p = float(observation.get("niche_pressure", 0.0))

    center_x = world_w * 0.5
    center_y = world_h * 0.5
    toward_cx = center_x - ox
    toward_cy = center_y - oy
    norm = math.hypot(toward_cx, toward_cy) + _EPS_NORM
    dir_x = toward_cx / norm
    dir_y = toward_cy / norm

    gain = (
        profile.gain_high_stress
        if stress_norm > profile.stress_norm_threshold
        else profile.gain_low_stress
    )
    gn = math.hypot(gxf, gyf) + _EPS_NORM
    flee_x, flee_y = -gxf / gn, -gyf / gn
    flee_w = min(1.0, ambient_field / profile.field_flee_div) * profile.field_flee_gain
    mem_boost = float(memory["stress_ema"])
    flee_w *= 1.0 + profile.mem_flee_boost * mem_boost
    flee_w *= 1.0 + profile.niche_flee_boost * niche_p

    tangent_x, tangent_y = -flee_y, flee_x
    wander = profile.wander_amp * float(memory["speed_ema"])

    ax = dir_x * gain + flee_x * flee_w + tangent_x * wander
    ay = dir_y * gain + flee_y * flee_w + tangent_y * wander
    return ax, ay