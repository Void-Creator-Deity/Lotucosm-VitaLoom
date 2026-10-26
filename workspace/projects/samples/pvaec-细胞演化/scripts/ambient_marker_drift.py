# -*- coding: utf-8 -*-
"""主世界 · 信标微粒弱漂移（向场心回弹 + 轻噪声）。

职责: 非 pinned 信标的速度扰动；不参与 chemo 膜链。
时机: 每 tick PVAEC；与 well_pulse 场呼吸独立。
不变量: 仅写 entity.velocity。
排错: 静止 → pinned；过快 → _MAX_SPD。
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict

from core.Lotucosm.pvaec_script import PvaecScript
from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext

_SPRING = 5.5
_NOISE_AMP = 22.0
_MAX_SPD = 105.0
_EPS = 1e-6


class AmbientMarkerDrift(PvaecScript):
    """信标微粒：弱向画布中心弹簧 + 噪声速度（非营养趋化）。

    职责: perceive 读 bounds 中心；act 写 velocity。
    时机: 每 tick perceive→think→act。
    不变量: 非 SR 繁殖/代谢脚本。
    排错: pinned 实体不应挂载本脚本。
    """

    def perceive(self, ctx: SceneRuntimeTickContext) -> Dict[str, Any]:
        """AmbientMarkerDrift.perceive。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        w, h = int(ctx.bounds[0]), int(ctx.bounds[1])
        ox, oy = float(ctx.owner_position[0]), float(ctx.owner_position[1])
        env = ctx.environment
        return {
            "cx": w * 0.5,
            "cy": h * 0.5,
            "ox": ox,
            "oy": oy,
            "gfx": float(env.get("ambient_grad_x", 0.0)),
            "gfy": float(env.get("ambient_grad_y", 0.0)),
        }

    def think(self, observation: Dict[str, Any], delta_time: float) -> Dict[str, Any]:
        """AmbientMarkerDrift.think。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        _ = delta_time
        cx = float(observation["cx"])
        cy = float(observation["cy"])
        ox = float(observation["ox"])
        oy = float(observation["oy"])
        dx, dy = cx - ox, cy - oy
        d = math.hypot(dx, dy) + _EPS
        gfx = float(observation.get("gfx", 0.0))
        gfy = float(observation.get("gfy", 0.0))
        gf = math.hypot(gfx, gfy) + _EPS
        drift = 5.5
        ax = _SPRING * dx / d + drift * gfx / gf + random.uniform(-1.0, 1.0) * _NOISE_AMP
        ay = _SPRING * dy / d + drift * gfy / gf + random.uniform(-1.0, 1.0) * _NOISE_AMP
        return {"ax": ax, "ay": ay}

    def act(self, decision: Dict[str, Any], delta_time: float) -> None:
        """AmbientMarkerDrift.act。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        ent = self.entity
        if ent is None or delta_time <= 0:
            return
        vel = ent.velocity
        ax = float(decision.get("ax", 0.0))
        ay = float(decision.get("ay", 0.0))
        vx = float(vel[0]) + ax * delta_time
        vy = float(vel[1]) + ay * delta_time
        s = math.hypot(vx, vy)
        if s > _MAX_SPD and s > 0:
            k = _MAX_SPD / s
            vx *= k
            vy *= k
        vel[0] = vx
        vel[1] = vy
