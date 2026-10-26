# -*- coding: utf-8
"""运动积分：速度阻尼 + 位置更新 + 画布边界反弹。"""

from __future__ import annotations

import math
from typing import Any

from core.Lotucosm.sr_physics2d.config import SrPhysics2DConfig


def is_kinematic_integrable(entity: Any) -> bool:
    if getattr(entity, "pinned", False) or getattr(entity, "membrane_locked", False):
        return False
    return True


def integrate_entity(
    entity: Any,
    dt: float,
    width: float,
    height: float,
    config: SrPhysics2DConfig,
) -> None:
    """单实体欧拉积分（与旧 ``_SceneRuntimeEntity.step_physics`` 语义一致）。"""
    if not is_kinematic_integrable(entity):
        entity.velocity[0] = 0.0
        entity.velocity[1] = 0.0
        return

    damp = max(0.0, min(1.0, config.linear_damping))
    entity.velocity[0] *= damp
    entity.velocity[1] *= damp

    max_spd = max(1.0, float(config.max_speed))
    vx, vy = float(entity.velocity[0]), float(entity.velocity[1])
    spd = math.sqrt(vx * vx + vy * vy)
    if spd > max_spd:
        scale = max_spd / spd
        entity.velocity[0] = vx * scale
        entity.velocity[1] = vy * scale

    entity.position[0] += float(entity.velocity[0]) * dt
    entity.position[1] += float(entity.velocity[1]) * dt

    w, h = float(width), float(height)
    r = float(getattr(entity, "radius", 18.0))
    bounce = max(0.0, min(1.0, config.boundary_bounce))

    if entity.position[0] < r:
        entity.position[0] = r
        entity.velocity[0] = abs(float(entity.velocity[0])) * bounce
    elif entity.position[0] > w - r:
        entity.position[0] = w - r
        entity.velocity[0] = -abs(float(entity.velocity[0])) * bounce

    if entity.position[1] < r:
        entity.position[1] = r
        entity.velocity[1] = abs(float(entity.velocity[1])) * bounce
    elif entity.position[1] > h - r:
        entity.position[1] = h - r
        entity.velocity[1] = -abs(float(entity.velocity[1])) * bounce


def integrate_all(
    entities: list[Any],
    dt: float,
    width: float,
    height: float,
    config: SrPhysics2DConfig,
) -> None:
    for entity in entities:
        integrate_entity(entity, dt, width, height, config)
