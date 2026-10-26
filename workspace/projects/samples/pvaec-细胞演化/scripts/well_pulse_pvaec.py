# -*- coding: utf-8 -*-
"""主世界 · 场域锚：正弦调制 emission_strength，经 ambient 卷积形成呼吸场。"""
from __future__ import annotations

import math
from typing import Any, Dict

from core.Lotucosm.pvaec_script import PvaecScript
from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext


class WellPulsePvaec(PvaecScript):
    """场域锚：正弦调制 emission_strength，经 ambient 卷积影响全图场强。

    职责: act 写 entity.emission_strength；非 SR chemo 通道。
    时机: environment_well 实体每 tick；properties.pulse 可覆盖 omega/幅值。
    排错: 场无呼吸 → 查 emissions_prev 与 ambient_scalar_at。
    """

    def __init__(self) -> None:
        """WellPulsePvaec.__init__。

        
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
        self._omega = 0.42
        self._phase = 0.0
        self._emission_min = 0.3
        self._emission_max = 0.7

    def start(self) -> None:
        """WellPulsePvaec.start。

        
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
            if "phase" in raw:
                try:
                    self._phase = float(raw["phase"])
                except (TypeError, ValueError):
                    pass
            for key, attr in (("emission_min", "_emission_min"), ("emission_max", "_emission_max")):
                if key in raw:
                    try:
                        setattr(self, attr, float(raw[key]))
                    except (TypeError, ValueError):
                        pass
        lo, hi = self._emission_min, self._emission_max
        if hi < lo:
            lo, hi = hi, lo
        self._emission_min, self._emission_max = lo, hi

    def perceive(self, ctx: SceneRuntimeTickContext) -> Dict[str, Any]:
        """WellPulsePvaec.perceive。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return {"t": float(ctx.simulation_time)}

    def think(self, observation: Dict[str, Any], delta_time: float) -> Dict[str, Any]:
        """WellPulsePvaec.think。

        
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
        t = float(observation["t"])
        s = math.sin(self._omega * t + self._phase)
        mid = 0.5 * (self._emission_min + self._emission_max)
        half = 0.5 * (self._emission_max - self._emission_min)
        emission = mid + half * s
        return {"emission": max(self._emission_min, min(self._emission_max, emission))}

    def act(self, decision: Dict[str, Any], delta_time: float) -> None:
        """WellPulsePvaec.act。

        
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
        ent = self.entity
        if ent is None:
            return
        ent.emission_strength = float(decision.get("emission", self._emission_min))
