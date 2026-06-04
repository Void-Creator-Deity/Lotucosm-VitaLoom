# -*- coding: utf-8
"""【模板】纤毛执行器 PVAEC — 复制到 ../scripts/ 后改名、改类名再在 .pond 挂载。"""
from __future__ import annotations

from typing import Any, Dict

from core.Lotucosm.pvaec_script import PvaecScript
from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext


class MyActuatorPvaecTemplate(PvaecScript):
    """最小执行器：用 inbound chemo 方向推 velocity（膜锁定时不改位置）。"""

    def start(self) -> None:
        props = getattr(self.entity, "_scene_script_properties", None) or {}
        pulse = props.get("pulse") if isinstance(props.get("pulse"), dict) else {}
        self._thrust = float(pulse.get("thrust", 80.0))

    def perceive(self, ctx: SceneRuntimeTickContext) -> Dict[str, Any]:
        return {"inbound": dict(ctx.inbound_signals)}

    def think(self, observation: Dict[str, Any], delta_time: float) -> Dict[str, Any]:
        inbound = observation.get("inbound") or {}
        dx = float(inbound.get("chemo_dir_x", 0.0))
        dy = float(inbound.get("chemo_dir_y", 0.0))
        mag = (dx * dx + dy * dy) ** 0.5
        if mag < 1e-6:
            return {"fx": 0.0, "fy": 0.0}
        scale = self._thrust / mag
        return {"fx": dx * scale, "fy": dy * scale}

    def act(self, decision: Dict[str, Any], delta_time: float) -> None:
        ent = self.entity
        if ent is None or getattr(ent, "membrane_locked", False):
            return
        ent.velocity[0] = float(ent.velocity[0]) + float(decision.get("fx", 0.0)) * delta_time
        ent.velocity[1] = float(ent.velocity[1]) + float(decision.get("fy", 0.0)) * delta_time
