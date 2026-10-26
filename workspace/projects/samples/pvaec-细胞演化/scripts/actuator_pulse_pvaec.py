# -*- coding: utf-8 -*-
"""主世界 · 膜纤毛：径向脉冲 + inbound chemo 推力。

职责:
    读 ctx.inbound_signals（宿主 actuator 批 use_prev=False，当帧 sensor 输出）；
    叠加相对场景中心的径向脉冲（全局几何，非营养 GPS）。

排错:
    趋化弱 → 查 signal_edges 权重与 sensor chemo；过强 → 另有宿主 _apply_actuator_coupling 推 hub。
    membrane_locked 未阻止本脚本改 velocity，位置仍由宿主每 tick 同步。
"""
from __future__ import annotations

import math
from typing import Any, Dict

from core.Lotucosm.pvaec_script import PvaecScript
from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext

_OMEGA = 2.15
_RADIAL_AMP = 72.0
_MAX_SPD = 130.0
_EPS = 1e-6

SR_INSPECTOR_SCHEMA = [
    {"group": "脉冲", "label": "角频率 ω", "path": "pulse.omega", "type": "float", "min": 0.2, "max": 8.0, "step": 0.05},
    {"group": "脉冲", "label": "径向冲量幅度", "path": "pulse.radial_amp", "type": "float", "min": 0.0, "max": 200.0, "step": 1.0},
    {"group": "脉冲", "label": "最大速度", "path": "pulse.max_spd", "type": "float", "min": 20.0, "max": 400.0, "step": 5.0},
]


class ActuatorPulsePvaec(PvaecScript):
    def __init__(self) -> None:
        """ActuatorPulsePvaec.__init__。

        
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
        self._omega = _OMEGA
        self._radial_amp = _RADIAL_AMP
        self._max_spd = _MAX_SPD

    def start(self) -> None:
        """ActuatorPulsePvaec.start。

        
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
        raw = props.get("pulse")
        if isinstance(raw, dict):
            if "omega" in raw:
                try:
                    self._omega = float(raw["omega"])
                except (TypeError, ValueError):
                    pass
            if "radial_amp" in raw:
                try:
                    self._radial_amp = float(raw["radial_amp"])
                except (TypeError, ValueError):
                    pass
            if "max_spd" in raw:
                try:
                    self._max_spd = float(raw["max_spd"])
                except (TypeError, ValueError):
                    pass

    def perceive(self, ctx: SceneRuntimeTickContext) -> Dict[str, Any]:
        """ActuatorPulsePvaec.perceive。

        
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
        inbound = ctx.inbound_signals
        chemo_in = 0.0
        dir_x = dir_y = 0.0
        if inbound:
            try:
                chemo_in = float(inbound.get("chemo", 0.0))
            except (TypeError, ValueError):
                chemo_in = 0.0
            try:
                dir_x = float(inbound.get("chemo_dir_x", 0.0))
                dir_y = float(inbound.get("chemo_dir_y", 0.0))
            except (TypeError, ValueError):
                pass
        return {
            "ox": float(ctx.owner_position[0]),
            "oy": float(ctx.owner_position[1]),
            "cx": w * 0.5,
            "cy": h * 0.5,
            "t": float(ctx.simulation_time),
            "inbound_chemo": chemo_in,
            "chemo_dir_x": dir_x,
            "chemo_dir_y": dir_y,
        }

    def think(self, observation: Dict[str, Any], delta_time: float) -> Dict[str, Any]:
        """ActuatorPulsePvaec.think。

        
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
        dx, dy = ox - cx, oy - cy
        d = math.hypot(dx, dy) + _EPS
        phase = math.sin(float(observation["t"]) * self._omega)
        chemo_in = float(observation.get("inbound_chemo", 0.0))
        drive = 0.35 + 0.65 * min(1.0, max(0.0, chemo_in))
        amp = self._radial_amp * phase * drive
        cdx = float(observation.get("chemo_dir_x", 0.0))
        cdy = float(observation.get("chemo_dir_y", 0.0))
        cg = math.hypot(cdx, cdy) + _EPS
        chemo_ax = cdx / cg * chemo_in * 28.0 if chemo_in > 0.01 else 0.0
        chemo_ay = cdy / cg * chemo_in * 28.0 if chemo_in > 0.01 else 0.0
        emission = min(1.0, abs(phase) * drive)
        return {
            "ax": amp * dx / d + chemo_ax,
            "ay": amp * dy / d + chemo_ay,
            "emission": emission,
        }

    def act(self, decision: Dict[str, Any], delta_time: float) -> None:
        """ActuatorPulsePvaec.act。

        
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
        ent.emission_strength = float(decision.get("emission", 0.0))
