# -*- coding: utf-8 -*-
"""主世界 · 膜受体：营养场梯度 → sr_channel_out（chemo 通道）。

职责:
    从 environment 读 nutrient_grad_* / nutrient_potential，写入 chemo、chemo_dir_*。
    供 sr_membrane_topology.aggregate_channel_signals 沿 signal_edges 传到 actuator。

膜锁定:
    membrane_locked 为 True 时不改 velocity（位置由宿主 _sync_membrane_positions 跟随 hub）。

排错:
    纤毛无趋化 → 查 chemo 是否写出、边是否重复双倍、宿主 tick 是否 sensor 在 actuator 前；
    org_pull 取 peers 中第一个 organism，非最近距离（弱牵引示意）。
"""
from __future__ import annotations

import math
from typing import Any, Dict, Optional

from core.Lotucosm.pvaec_script import PvaecScript
from core.Lotucosm.scene_runtime_context import RuntimePeerSnapshot, SceneRuntimeTickContext

_ORG_PULL = 26.0
_PATROL_AMP = 14.0
_MAX_SPD = 115.0
_EPS = 1e-6

SR_INSPECTOR_SCHEMA = [
    {"group": "巡逻与牵引", "label": "巡逻幅度", "path": "patrol.patrol_amp", "type": "float", "min": 0.0, "max": 40.0, "step": 0.5},
    {"group": "巡逻与牵引", "label": "趋向机体拉力", "path": "patrol.org_pull", "type": "float", "min": 0.0, "max": 60.0, "step": 0.5},
    {"group": "巡逻与牵引", "label": "最大速度", "path": "patrol.max_spd", "type": "float", "min": 20.0, "max": 300.0, "step": 5.0},
]


class SensorPatrolPvaec(PvaecScript):
    def __init__(self) -> None:
        """SensorPatrolPvaec.__init__。

        
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
        self._org_pull = _ORG_PULL
        self._patrol_amp = _PATROL_AMP
        self._max_spd = _MAX_SPD
        self._last_chemo_signal = 0.0
        self._last_chemo_dir = (0.0, 0.0)

    def start(self) -> None:
        """SensorPatrolPvaec.start。

        
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
        raw = props.get("patrol")
        if isinstance(raw, dict):
            if "org_pull" in raw:
                try:
                    self._org_pull = float(raw["org_pull"])
                except (TypeError, ValueError):
                    pass
            if "patrol_amp" in raw:
                try:
                    self._patrol_amp = float(raw["patrol_amp"])
                except (TypeError, ValueError):
                    pass
            if "max_spd" in raw:
                try:
                    self._max_spd = float(raw["max_spd"])
                except (TypeError, ValueError):
                    pass

    def perceive(self, ctx: SceneRuntimeTickContext) -> Dict[str, Any]:
        """SensorPatrolPvaec.perceive。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        linked = ctx.topology_neighbor_ids
        nearest_org: Optional[RuntimePeerSnapshot] = None
        for p in ctx.peers:
            if p.entity_type == "organism" and p.id in linked:
                nearest_org = p
                break
        if nearest_org is None:
            for p in ctx.peers:
                if p.entity_type == "organism":
                    nearest_org = p
                    break
        env = ctx.environment
        return {
            "org": nearest_org,
            "ox": float(ctx.owner_position[0]),
            "oy": float(ctx.owner_position[1]),
            "t": float(ctx.simulation_time),
            "field": float(env.get("ambient_field", 0.0)),
            "gfx": float(env.get("ambient_grad_x", 0.0)),
            "gfy": float(env.get("ambient_grad_y", 0.0)),
            "nutrient_potential": float(env.get("nutrient_potential", 0.0)),
            "nutrient_grad_x": float(env.get("nutrient_grad_x", 0.0)),
            "nutrient_grad_y": float(env.get("nutrient_grad_y", 0.0)),
            "chemo_gain_scale": float(env.get("chemo_gain_scale", 1.0)),
        }

    def think(self, observation: Dict[str, Any], delta_time: float) -> Dict[str, Any]:
        """SensorPatrolPvaec.think。

        
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
        ax = self._patrol_amp * math.cos(float(observation["t"]) * 0.65)
        ay = self._patrol_amp * math.sin(float(observation["t"]) * 0.52)
        org = observation.get("org")
        if org is not None:
            px, py = float(org.position[0]), float(org.position[1])
            dx, dy = px - ox, py - oy
            d = math.hypot(dx, dy) + _EPS
            ax += self._org_pull * dx / d
            ay += self._org_pull * dy / d
        gfx = float(observation.get("gfx", 0.0))
        gfy = float(observation.get("gfy", 0.0))
        gf = math.hypot(gfx, gfy) + _EPS
        trace = min(1.0, float(observation.get("field", 0.0)) / 9000.0)
        ax += trace * 10.0 * gfx / gf
        ay += trace * 10.0 * gfy / gf
        ngx = float(observation.get("nutrient_grad_x", 0.0))
        ngy = float(observation.get("nutrient_grad_y", 0.0))
        ng = math.hypot(ngx, ngy) + _EPS
        chemo_strength = min(
            1.0,
            math.sqrt(max(0.0, float(observation.get("nutrient_potential", 0.0))) / 120.0),
        ) * float(observation.get("chemo_gain_scale", 1.0))
        self._last_chemo_signal = chemo_strength
        self._last_chemo_dir = (ngx / ng, ngy / ng) if ng > _EPS else (0.0, 0.0)
        return {"ax": ax, "ay": ay, "chemo_signal": chemo_strength}

    def act(self, decision: Dict[str, Any], delta_time: float) -> None:
        """SensorPatrolPvaec.act。

        
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
        if not getattr(ent, "membrane_locked", False):
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
        # 通道契约: aggregate 读 chemo，兼容别名 chemo_signal
        ent.sr_channel_out = {
            "chemo": float(getattr(self, "_last_chemo_signal", 0.0)),
            "chemo_signal": float(getattr(self, "_last_chemo_signal", 0.0)),
            "chemo_dir_x": float(self._last_chemo_dir[0]),
            "chemo_dir_y": float(self._last_chemo_dir[1]),
        }
