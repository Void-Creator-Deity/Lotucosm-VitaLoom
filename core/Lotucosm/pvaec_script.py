# -*- coding: utf-8 -*-
"""PVAEC 脚本骨架：perceive → think → act；由 GameViewport 经 pvaec_step(ctx, dt) 驱动。

职责: 定义 ScriptBase 之上的三阶段钩子；SR 用 SceneRuntimeTickContext。
时机: _run_script_tick_batch 每实体调用 pvaec_step；spawn/removal 在 act 登记、帧末统一处理。
不变量: perceive 只读 ctx；子类勿在 think 中改拓扑。
排错: 膜无输出 → 查 tick 批次顺序；见 game_viewport 与 scene_runtime_context。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext
from core.Lotucosm.scripts import ScriptBase


class PvaecScript(ScriptBase):
    """PVAEC 可选基类：子类实现 perceive/think/act；宿主每帧调用 pvaec_step。

    扩展（内稳态六步）:
        设 homeostatic_pvaec_enabled=True 时，act 后执行 verify → remember，
        用内感受（intero_*）评估行动是否改善内稳态。
    """

    homeostatic_pvaec_enabled: bool = False

    def perceive(self, ctx: SceneRuntimeTickContext) -> Dict[str, Any]:
        """感知阶段：只读 ctx，返回 observation dict（子类覆盖）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return {}

    def think(self, observation: Dict[str, Any], delta_time: float) -> Dict[str, Any]:
        """思考阶段：由 observation 产出 decision dict（子类覆盖）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return {}

    def act(self, decision: Dict[str, Any], delta_time: float) -> None:
        """行动阶段：可写 self.entity（速度、通道、spawn 请求等）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return

    def verify(
        self,
        ctx: SceneRuntimeTickContext,
        observation: Dict[str, Any],
        intero_before: Dict[str, float],
    ) -> float:
        """验证阶段：比较 act 前后内稳态，返回 success_rate [0,1]（子类可覆盖）。"""
        from core.Lotucosm.sr_interoception import (
            homeostatic_success,
            interoception_for_entity,
        )

        ent = self.entity
        if ent is None:
            return 0.5
        after = interoception_for_entity(ent)
        return homeostatic_success(intero_before, after)

    def remember(
        self,
        ctx: SceneRuntimeTickContext,
        observation: Dict[str, Any],
        decision: Dict[str, Any],
        success: float,
    ) -> None:
        """再记忆阶段：默认无操作；中枢脚本可写入 EMA / 经验表。"""
        return

    def pvaec_step(self, ctx: SceneRuntimeTickContext, delta_time: float) -> None:
        """编排 perceive→think→act；内稳态模式下追加 verify→remember。"""
        from core.Lotucosm.sr_interoception import interoception_for_entity

        self._pvaec_tick_ctx = ctx
        obs = self.perceive(ctx)
        self._pvaec_last_observation = obs
        intero_before: Dict[str, float] = {}
        if self.homeostatic_pvaec_enabled and self.entity is not None:
            intero_before = interoception_for_entity(self.entity)
        dec = self.think(obs, delta_time)
        self.act(dec, delta_time)
        if self.homeostatic_pvaec_enabled:
            success = self.verify(ctx, obs, intero_before)
            self._pvaec_last_success = success
            self.remember(ctx, obs, dec, success)
