# -*- coding: utf-8
"""【模板】膜受体 PVAEC — 复制到 ../scripts/ 后改名、改类名再在 .pond 挂载。

复制步骤:
    1. 复制本文件为 projects/pvaec-细胞演化/scripts/my_sensor_pvaec.py
    2. 类名 MySensorPvaecTemplate → MySensorPvaec（与 .pond scripts[].type 一致）
    3. 在实体 scripts[].name 填 my_sensor_pvaec
"""
from __future__ import annotations

from typing import Any, Dict

from core.Lotucosm.pvaec_script import PvaecScript
from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext


class MySensorPvaecTemplate(PvaecScript):
    """最小受体：把营养梯度写成 chemo，供 signal_edges 传到 actuator。"""

    def start(self) -> None:
        props = getattr(self.entity, "_scene_script_properties", None) or {}
        patrol = props.get("patrol") if isinstance(props.get("patrol"), dict) else {}
        self._gain = float(patrol.get("chemo_gain", 1.0))

    def perceive(self, ctx: SceneRuntimeTickContext) -> Dict[str, Any]:
        env = ctx.environment
        gx = float(env.get("nutrient_grad_x", 0.0))
        gy = float(env.get("nutrient_grad_y", 0.0))
        return {"grad": (gx, gy)}

    def think(self, observation: Dict[str, Any], delta_time: float) -> Dict[str, Any]:
        gx, gy = observation.get("grad", (0.0, 0.0))
        mag = (gx * gx + gy * gy) ** 0.5
        chemo = min(1.0, mag * self._gain)
        if mag > 1e-6:
            direction = (gx / mag, gy / mag)
        else:
            direction = (0.0, 0.0)
        return {"chemo": chemo, "dir": direction}

    def act(self, decision: Dict[str, Any], delta_time: float) -> None:
        ent = self.entity
        if ent is None:
            return
        chemo = float(decision.get("chemo", 0.0))
        dx, dy = decision.get("dir", (0.0, 0.0))
        out = getattr(ent, "sr_channel_out", None)
        if not isinstance(out, dict):
            ent.sr_channel_out = {}
            out = ent.sr_channel_out
        out["chemo"] = chemo
        out["chemo_dir_x"] = float(dx) * chemo
        out["chemo_dir_y"] = float(dy) * chemo
