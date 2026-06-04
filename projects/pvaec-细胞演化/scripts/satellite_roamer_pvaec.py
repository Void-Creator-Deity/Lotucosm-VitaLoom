# -*- coding: utf-8 -*-
"""主世界 · 从属 organism：弱向心 + 切向漫游，与中枢区分。"""
from __future__ import annotations

import math
from typing import Any, Dict

from core.Lotucosm.pvaec_script import PvaecScript
from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext

_GAIN_CENTER = 15.0
_TANGENT_AMP = 36.0
_MAX_SPD = 210.0
_FLEE_SCALE = 18.0
_NICHE_FLEE = 0.55
_EPS = 1e-6


class SatelliteRoamerPvaec(PvaecScript):
    """从属 organism：弱向心 + 切向漫游 + 场梯度逃离（非膜 chemo 链）。

    职责: 与 EvoCentralBrain 区分，不繁殖、不写 sr_channel_out。
    排错: 与中枢抢控制 → 场景勿对同一 hub 挂本脚本与 evo 中枢。
    """

    def __init__(self) -> None:
        """SatelliteRoamerPvaec.__init__。

        
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
        self._gain_center = _GAIN_CENTER
        self._tangent_amp = _TANGENT_AMP
        self._max_spd = _MAX_SPD
        self._flee_scale = _FLEE_SCALE
        self._niche_flee = _NICHE_FLEE

    def start(self) -> None:
        """SatelliteRoamerPvaec.start。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        props = getattr(self, "_scene_script_properties", None) or {}
        raw = props.get("roam")
        if isinstance(raw, dict):
            for key, attr in (
                ("gain_center", "_gain_center"),
                ("tangent_amp", "_tangent_amp"),
                ("max_spd", "_max_spd"),
                ("flee_scale", "_flee_scale"),
                ("niche_flee", "_niche_flee"),
            ):
                if key in raw:
                    try:
                        setattr(self, attr, float(raw[key]))
                    except (TypeError, ValueError):
                        pass

    def perceive(self, ctx: SceneRuntimeTickContext) -> Dict[str, Any]:
        """SatelliteRoamerPvaec.perceive。

        
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
        env = ctx.environment
        return {
            "ox": float(ctx.owner_position[0]),
            "oy": float(ctx.owner_position[1]),
            "cx": w * 0.5,
            "cy": h * 0.5,
            "t": float(ctx.simulation_time),
            "field": float(env.get("ambient_field", 0.0)),
            "gfx": float(env.get("ambient_grad_x", 0.0)),
            "gfy": float(env.get("ambient_grad_y", 0.0)),
            "niche_pressure": float(env.get("niche_pressure", 0.0)),
            "world_load": float(env.get("world_load", 0.0)),
        }

    def think(self, observation: Dict[str, Any], delta_time: float) -> Dict[str, Any]:
        """SatelliteRoamerPvaec.think。

        
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
        ox = float(observation["ox"])
        oy = float(observation["oy"])
        cx = float(observation["cx"])
        cy = float(observation["cy"])
        tx, ty = cx - ox, cy - oy
        d = math.hypot(tx, ty) + _EPS
        ux, uy = tx / d, ty / d
        px, py = -uy, ux
        t = float(observation["t"])
        wobble = math.sin(t * 1.28)
        ax = self._gain_center * ux + self._tangent_amp * wobble * px
        ay = self._gain_center * uy + self._tangent_amp * math.cos(t * 1.05) * py
        gfx = float(observation.get("gfx", 0.0))
        gfy = float(observation.get("gfy", 0.0))
        gf = math.hypot(gfx, gfy) + _EPS
        flee = min(1.0, float(observation.get("field", 0.0)) / 11000.0)
        niche_p = float(observation.get("niche_pressure", 0.0))
        flee *= 1.0 + self._niche_flee * niche_p
        ax -= flee * self._flee_scale * gfx / gf
        ay -= flee * self._flee_scale * gfy / gf
        return {"ax": ax, "ay": ay}

    def act(self, decision: Dict[str, Any], delta_time: float) -> None:
        """SatelliteRoamerPvaec.act。

        
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
        cap = self._max_spd
        if s > cap and s > 0:
            k = cap / s
            vx *= k
            vy *= k
        vel[0] = vx
        vel[1] = vy
        spd = math.hypot(vx, vy)
        ent.emission_strength = min(1.0, 0.06 + spd / 360.0)
