# -*- coding: utf-8 -*-
"""SR 中枢 PVAEC：MindProfile + 邻域场与短时记忆（引擎内实现，项目脚本可 re-export）。

架构数据流（SceneRuntime tick）::

    SceneRuntimeTickContext
        → perceive（peers + ambient + memory EMA）
        → think（stress_raw_and_norm + memory_step + motion_acceleration）
        → act（速度积分 + emission_strength + sr_debug_hud）

依赖 sr_central_brain_channels、sr_mind_profile；膜拓扑见 sr_membrane_topology。
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, Optional, Tuple

from core.Lotucosm.pvaec_script import PvaecScript
from core.Lotucosm.scene_runtime_context import RuntimePeerSnapshot, SceneRuntimeTickContext
from core.Lotucosm.sr_central_brain_channels import memory_step, motion_acceleration, stress_raw_and_norm
from core.Lotucosm.sr_mind_profile import MindProfile
from core.VitaLoom.core.logger import get_logger

logger = get_logger("Lotucosm.SRCentralBrainPvaec")


def _inverse_distance_pulls_by_type(
    peers: Tuple[RuntimePeerSnapshot, ...],
    topology_neighbor_ids: frozenset[str],
) -> Dict[str, float]:
    """按 entity_type 聚合逆距离拉力；拓扑邻居加权 1.55，否则 0.34。

    排错:
        pulls 全零 → peers 为空或 surface_gap 极大。
    """
    pulls: Dict[str, float] = defaultdict(float)
    for p in peers:
        sep = max(1.0, p.surface_gap + 1.0)
        wired = 1.55 if p.id in topology_neighbor_ids else 0.34
        pulls[p.entity_type] += wired / sep
    return dict(pulls)


class CentralBrainPvaec(PvaecScript):
    """邻域 + 环境场 + 短时记忆 EMA；可调参数来自 MindProfile。

    生命周期:
        start 读 props → 每 tick perceive/think/act → verify/remember（内稳态 PVAEC）→ 周期性日志
    """

    homeostatic_pvaec_enabled = True

    def __init__(self) -> None:
        """CentralBrainPvaec.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        super().__init__()
        self._memory = {"stress_ema": 0.0, "field_ema": 0.0, "speed_ema": 0.0}
        self._mind = MindProfile.default_main_world()
        self._tick_counter = 0
        self._log_every = 60

    def start(self) -> None:
        """从 _scene_script_properties 加载 mind 与 log_every。

        职责:
            解析 MindProfile.from_dict(props['mind']) 并复位 tick 计数。

        时机:
            脚本 on_attach 后、首帧 tick 前。

        不变量:
            log_every >= 1；无效值回退 60。

        排错:
            行为像默认主世界 → .pond 未写 mind 或 props 键名错误。
        """
        props = getattr(self, "_scene_script_properties", None) or {}
        raw_mind = props.get("mind")
        self._mind = MindProfile.from_dict(raw_mind if isinstance(raw_mind, dict) else None)
        le = props.get("log_every", 60)
        try:
            self._log_every = max(1, int(le))
        except (TypeError, ValueError):
            self._log_every = 60
        self._tick_counter = 0
        ent = self.entity
        entity_id = ent.id if ent is not None else "no_entity"
        logger.info("SR central PVAEC started: entity_id=%s", entity_id)

    def perceive(self, ctx: SceneRuntimeTickContext) -> Dict[str, Any]:
        """组装观察 dict：最近邻、分类型拉力、环境场、记忆 EMA、边界。

        职责:
            只读 ctx，不写 entity 运动状态。

        时机:
            宿主 SR tick 管线 perceive 阶段。

        不变量:
            输出键名供 think/act 与 channels 函数使用。

        排错:
            nearest 恒 None → peers 空；环境场为 0 → scene_runtime_ambient 未注入。
        """
        nearest: Optional[RuntimePeerSnapshot] = ctx.peers[0] if ctx.peers else None
        pulls = _inverse_distance_pulls_by_type(ctx.peers, ctx.topology_neighbor_ids)
        env = ctx.environment
        ambient_field = float(env.get("ambient_field", 0.0))
        amb_gx = float(env.get("ambient_grad_x", 0.0))
        amb_gy = float(env.get("ambient_grad_y", 0.0))
        world_load = float(env.get("world_load", 0.0))
        niche_pressure = float(env.get("niche_pressure", 0.0))
        load_deriv = float(env.get("world_load_derivative", 0.0))
        w, h = int(ctx.bounds[0]), int(ctx.bounds[1])
        ent = self.entity
        intrinsic_speed = 0.0
        if ent is not None:
            vel = getattr(ent, "velocity", None)
            if isinstance(vel, (list, tuple)) and len(vel) >= 2:
                intrinsic_speed = math.hypot(float(vel[0]), float(vel[1]))
        return {
            "nearest_id": nearest.id if nearest else None,
            "nearest_dist": nearest.distance if nearest else None,
            "sensor_pull": pulls.get("sensor", 0.0),
            "actuator_pull": pulls.get("actuator", 0.0),
            "peer_organism_pull": pulls.get("organism", 0.0),
            "ambient_field": ambient_field,
            "ambient_grad_x": amb_gx,
            "ambient_grad_y": amb_gy,
            "world_load": world_load,
            "niche_pressure": niche_pressure,
            "world_load_derivative": load_deriv,
            "intrinsic_speed": intrinsic_speed,
            "memory_stress_ema": float(self._memory["stress_ema"]),
            "memory_field_ema": float(self._memory["field_ema"]),
            "memory_speed_ema": float(self._memory["speed_ema"]),
            "world_width": w,
            "world_height": h,
            "bounds": ctx.bounds,
            "simulation_time": ctx.simulation_time,
        }

    def think(self, observation: Dict[str, Any], delta_time: float) -> Dict[str, Any]:
        """计算 stress、更新记忆 EMA、输出加速度建议 ax/ay。

        职责:
            委托 stress_raw_and_norm、memory_step、motion_acceleration。

        时机:
            perceive 之后、act 之前。

        不变量:
            world_w/h <= 0 时返回零加速度决策。

        排错:
            不动 → bounds 无效或 entity 为 None；应力异常 → MindProfile 阈值字段。
        """
        _ = delta_time
        profile = self._mind
        stress_raw, stress_norm = stress_raw_and_norm(observation, profile)
        memory_step(self._memory, observation, profile, stress_norm)

        ww = observation.get("world_width")
        wh = observation.get("world_height")
        if ww is None or wh is None:
            bounds = observation.get("bounds")
            if isinstance(bounds, (list, tuple)) and len(bounds) >= 2:
                ww, wh = bounds[0], bounds[1]
        try:
            world_w = float(ww)
            world_h = float(wh)
        except (TypeError, ValueError):
            return {
                "stress_raw": stress_raw,
                "stress_norm": stress_norm,
                "memory_arousal": float(self._memory["stress_ema"]),
                "ax": 0.0,
                "ay": 0.0,
            }

        if world_w <= 0 or world_h <= 0:
            return {
                "stress_raw": stress_raw,
                "stress_norm": stress_norm,
                "memory_arousal": float(self._memory["stress_ema"]),
                "ax": 0.0,
                "ay": 0.0,
            }

        ent = self.entity
        if ent is None:
            return {
                "stress_raw": stress_raw,
                "stress_norm": stress_norm,
                "memory_arousal": float(self._memory["stress_ema"]),
                "ax": 0.0,
                "ay": 0.0,
            }

        ox, oy = float(ent.position[0]), float(ent.position[1])
        ax, ay = motion_acceleration(observation, self._memory, profile, stress_norm, ox, oy, world_w, world_h)
        return {
            "stress_raw": stress_raw,
            "stress_norm": stress_norm,
            "memory_arousal": float(self._memory["stress_ema"]),
            "ax": ax,
            "ay": ay,
        }

    def act(self, decision: Dict[str, Any], delta_time: float) -> None:
        """积分加速度到 velocity，钳制 max_speed，写 emission 与 sr_debug_hud。

        职责:
            修改 entity.velocity 与 emission_strength；周期性 info 日志。

        时机:
            think 之后同 tick 内。

        不变量:
            delta_time <= 0 或无效 velocity 时早退。

        排错:
            速度封顶 → MindProfile.max_speed；HUD 无更新 → entity 无 velocity 数组。
        """
        ent = self.entity
        if ent is None or delta_time <= 0:
            return
        vel = getattr(ent, "velocity", None)
        if not isinstance(vel, (list, tuple)) or len(vel) < 2:
            return

        ax = float(decision.get("ax", 0.0))
        ay = float(decision.get("ay", 0.0))
        vx = float(vel[0]) + ax * delta_time
        vy = float(vel[1]) + ay * delta_time
        speed = math.hypot(vx, vy)
        cap = self._mind.max_speed
        if speed > cap and speed > 0:
            scale = cap / speed
            vx *= scale
            vy *= scale
        ent.velocity[0] = vx
        ent.velocity[1] = vy

        arousal = abs(float(decision.get("stress_norm", 0.0)))
        mem = float(decision.get("memory_arousal", 0.0))
        m = self._mind
        ent.emission_strength = min(1.0, m.emission_arousal * arousal + m.emission_memory * mem + m.emission_floor)

        self._tick_counter += 1
        ent.sr_debug_hud = {
            "stress_ema": float(self._memory["stress_ema"]),
            "field_ema": float(self._memory["field_ema"]),
            "speed_ema": float(self._memory["speed_ema"]),
            "wander_amp": float(m.wander_amp),
            "gain_high_stress": float(m.gain_high_stress),
            "mem_alpha": float(m.mem_alpha),
            "stress_norm": float(decision.get("stress_norm", 0.0)),
            "speed": float(speed),
            "emit": float(ent.emission_strength),
        }
        if self._log_every > 0 and self._tick_counter % self._log_every == 0:
            logger.info(
                "central mind | stress_ema=%.3f field_ema=%.3f speed_ema=%.3f | wander=%.1f gain_hi=%.1f mem_a=%.2f | "
                "spd=%.1f emit=%.3f sn=%.3f",
                self._memory["stress_ema"],
                self._memory["field_ema"],
                self._memory["speed_ema"],
                m.wander_amp,
                m.gain_high_stress,
                m.mem_alpha,
                speed,
                ent.emission_strength,
                float(decision.get("stress_norm", 0.0)),
            )

    def remember(
        self,
        ctx: SceneRuntimeTickContext,
        observation: Dict[str, Any],
        decision: Dict[str, Any],
        success: float,
    ) -> None:
        """再记忆：用验证分数微调 stress/field EMA（成功则降应激记忆权重）。"""
        alpha = max(0.01, min(0.5, float(self._mind.mem_alpha)))
        boost = (float(success) - 0.5) * 2.0
        self._memory["stress_ema"] = float(self._memory["stress_ema"]) * (1.0 - alpha) + max(
            0.0, float(decision.get("stress_norm", 0.0)) - 0.08 * boost
        ) * alpha
        self._memory["field_ema"] = float(self._memory["field_ema"]) * (1.0 - alpha) + float(
            observation.get("ambient_field", 0.0)
        ) / 5000.0 * alpha
        ent = self.entity
        if ent is not None:
            ent._sr_last_verify_success = float(success)
            hud = getattr(ent, "sr_debug_hud", None)
            if not isinstance(hud, dict):
                hud = {}
            hud["outcome_success"] = float(success)
            ent.sr_debug_hud = hud
