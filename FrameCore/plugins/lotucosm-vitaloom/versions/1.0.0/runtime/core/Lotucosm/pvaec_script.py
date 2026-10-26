# -*- coding: utf-8 -*-
"""PVAEC 脚本骨架：perceive → think → act；由 GameViewport 经 pvaec_step(ctx, dt) 驱动。

职责: 定义 ScriptBase 之上的三阶段钩子；SR 用 SceneRuntimeTickContext。
时机: _run_script_tick_batch 每实体调用 pvaec_step；spawn/removal 在 act 登记、帧末统一处理。
不变量: perceive 只读 ctx；子类勿在 think 中改拓扑。
排错: 膜无输出 → 查 tick 批次顺序；见 game_viewport 与 scene_runtime_context。
"""

from __future__ import annotations

import math
from typing import Any, Dict, Mapping, Optional

from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext
from core.Lotucosm.scripts import ScriptBase
from core.Lotucosm.sr_developmental_ladder import (
    MAX_DEVELOPMENTAL_STAGE,
    VERIFY_SUCCESS_THRESHOLD,
    can_advance_stage,
    clamp_stage,
    filter_observation_for_stage,
    perception_keys_for_stage,
)


class PvaecScript(ScriptBase):
    """PVAEC 可选基类：子类实现 perceive/think/act；宿主每帧调用 pvaec_step。

    扩展（内稳态六步）:
        设 homeostatic_pvaec_enabled=True 时，act 后执行 verify → remember，
        用内感受（intero_*）评估行动是否改善内稳态。

    扩展（个体发育阶梯 ADR-0004）:
        developmental_ladder_enabled=True 时，perceive 后经 filter_observation 门控；
        remember 后按 S0–S4 条件尝试 developmental_stage 进阶。
    """

    homeostatic_pvaec_enabled: bool = False
    developmental_ladder_enabled: bool = False
    developmental_stage: int = 0
    social_learning_enabled: bool = False
    developmental_plasticity_window: int = 0
    developmental_plasticity_penalty: bool = False

    def __init__(self) -> None:
        super().__init__()
        self._developmental_stage_ticks: int = 0
        self._developmental_explore_act_count: int = 0
        self._developmental_verify_success_count: int = 0
        self._developmental_remember_event_count: int = 0
        self._developmental_reproduced: bool = False
        self._pvaec_pre_act_velocity: Optional[tuple[float, float]] = None
        self._pvaec_last_decision: Dict[str, Any] = {}
        self._pvaec_last_delta_time: float = 0.0
        self._pvaec_verify_components: Dict[str, float] = {}

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
            exafference_predictability,
            homeostatic_success,
            interoception_for_entity,
            pvaec_verify_triple,
            reafference_consistency,
        )

        ent = self.entity
        if ent is None:
            return 0.5
        after = interoception_for_entity(ent)
        homeo = homeostatic_success(intero_before, after)
        dec = getattr(self, "_pvaec_last_decision", None) or {}
        dt = float(getattr(self, "_pvaec_last_delta_time", 0.0) or 0.0)
        pre = self._pvaec_pre_act_velocity
        post: tuple[float, float] | None = None
        vel = getattr(ent, "velocity", None)
        if isinstance(vel, (list, tuple)) and len(vel) >= 2:
            post = (float(vel[0]), float(vel[1]))
        motor_ax = float(dec.get("ax", 0.0))
        motor_ay = float(dec.get("ay", 0.0))
        reaff = reafference_consistency(pre, post, motor_ax, motor_ay, dt)
        obs_after = self.filter_observation(self.perceive(ctx))
        exaff = exafference_predictability(observation, obs_after, motor_ax, motor_ay, dt)
        self._pvaec_verify_components = {
            "homeo": homeo,
            "reaff": reaff,
            "exaff": exaff,
        }
        hud = getattr(ent, "sr_debug_hud", None)
        if isinstance(hud, dict):
            hud["verify_homeo"] = float(homeo)
            hud["verify_reaff"] = float(reaff)
            hud["verify_exaff"] = float(exaff)
            ent.sr_debug_hud = hud
        return pvaec_verify_triple(homeo, reaff, exaff)

    def remember(
        self,
        ctx: SceneRuntimeTickContext,
        observation: Dict[str, Any],
        decision: Dict[str, Any],
        success: float,
    ) -> None:
        """再记忆阶段：默认无操作；中枢脚本可写入 EMA / 经验表。"""
        return

    def perception_mask(self) -> frozenset[str]:
        """返回当前 stage 允许的 observation 键；ladder 关闭时返回空集（表示不过滤）。"""
        if not self.developmental_ladder_enabled:
            return frozenset()
        return perception_keys_for_stage(self.developmental_stage)

    def filter_observation(self, observation: Mapping[str, Any]) -> Dict[str, Any]:
        """按 perception_mask 过滤 observation；ladder 关闭时原样返回。"""
        if not self.developmental_ladder_enabled:
            return dict(observation)
        return filter_observation_for_stage(observation, self.developmental_stage)

    def apply_developmental_profile(self, profile: Mapping[str, Any] | None) -> None:
        """从 props / project developmental_profile 加载 ladder 开关与初始 stage。"""
        if not profile:
            return
        if "enabled" in profile:
            self.developmental_ladder_enabled = bool(profile.get("enabled"))
        if "initial_stage" in profile:
            self.developmental_stage = clamp_stage(int(profile.get("initial_stage", 0)))
        if "plasticity_window" in profile:
            self.developmental_plasticity_window = max(
                0, int(profile.get("plasticity_window", 0) or 0)
            )
        if "plasticity_penalty" in profile:
            self.developmental_plasticity_penalty = bool(profile.get("plasticity_penalty"))
        self._reset_developmental_counters()

    def apply_social_learning_profile(self, profile: Mapping[str, Any] | None) -> None:
        """从 props.social 加载社会学习开关（S3+ 生效）。"""
        if not profile:
            return
        if "enabled" in profile:
            self.social_learning_enabled = bool(profile.get("enabled"))

    def on_stage_advance(self, new_stage: int) -> None:
        """stage 进阶回调；子类可写 HUD / 日志。"""
        ent = self.entity
        if ent is None:
            return
        hud = getattr(ent, "sr_debug_hud", None)
        if not isinstance(hud, dict):
            hud = {}
        hud["developmental_stage"] = int(new_stage)
        if int(getattr(self, "developmental_plasticity_window", 0) or 0) > 0:
            hud["plasticity_window"] = int(self.developmental_plasticity_window)
        ent.sr_debug_hud = hud

    def notify_developmental_reproduction(self) -> None:
        """SR 繁殖登记后调用，满足 S3→S4 的 reproduced 条件。"""
        self._developmental_reproduced = True

    def _reset_developmental_counters(self) -> None:
        self._developmental_stage_ticks = 0
        self._developmental_explore_act_count = 0
        self._developmental_verify_success_count = 0
        self._developmental_remember_event_count = 0
        self._developmental_reproduced = False

    def _capture_pre_act_velocity(self) -> None:
        ent = self.entity
        if ent is None:
            self._pvaec_pre_act_velocity = None
            return
        vel = getattr(ent, "velocity", None)
        if isinstance(vel, (list, tuple)) and len(vel) >= 2:
            self._pvaec_pre_act_velocity = (float(vel[0]), float(vel[1]))
        else:
            self._pvaec_pre_act_velocity = None

    def _track_developmental_explore_act(self) -> None:
        if not self.developmental_ladder_enabled or self.developmental_stage > 1:
            return
        before = self._pvaec_pre_act_velocity
        ent = self.entity
        if before is None or ent is None:
            return
        vel = getattr(ent, "velocity", None)
        if not isinstance(vel, (list, tuple)) or len(vel) < 2:
            return
        dv = math.hypot(float(vel[0]) - before[0], float(vel[1]) - before[1])
        if dv > 0.5:
            self._developmental_explore_act_count += 1

    def _track_developmental_verify(self, success: float) -> None:
        if not self.developmental_ladder_enabled:
            return
        if float(success) >= VERIFY_SUCCESS_THRESHOLD:
            self._developmental_verify_success_count += 1

    def _track_developmental_remember(self) -> None:
        if self.developmental_ladder_enabled:
            self._developmental_remember_event_count += 1

    def _organism_peer_count(self, ctx: SceneRuntimeTickContext) -> int:
        count = 0
        for p in ctx.peers:
            if getattr(p, "entity_type", "") == "organism":
                count += 1
        return count

    def _maybe_advance_developmental_stage(self, ctx: SceneRuntimeTickContext) -> None:
        if not self.developmental_ladder_enabled:
            return
        if self.developmental_stage >= MAX_DEVELOPMENTAL_STAGE:
            return
        self._developmental_stage_ticks += 1
        if not can_advance_stage(
            self.developmental_stage,
            self._developmental_stage_ticks,
            self._developmental_explore_act_count,
            self._developmental_verify_success_count,
            self._developmental_remember_event_count,
            self._developmental_reproduced,
            self._organism_peer_count(ctx),
            plasticity_window=int(self.developmental_plasticity_window),
            plasticity_penalty=bool(self.developmental_plasticity_penalty),
        ):
            return
        new_stage = clamp_stage(self.developmental_stage + 1)
        self.developmental_stage = new_stage
        self._developmental_stage_ticks = 0
        self.on_stage_advance(new_stage)

    def pvaec_step(self, ctx: SceneRuntimeTickContext, delta_time: float) -> None:
        """编排 perceive→think→act；内稳态模式下追加 verify→remember。"""
        from core.Lotucosm.sr_interoception import interoception_for_entity

        self._pvaec_tick_ctx = ctx
        obs_raw = self.perceive(ctx)
        obs = self.filter_observation(obs_raw)
        self._pvaec_last_observation = obs
        intero_before: Dict[str, float] = {}
        if self.homeostatic_pvaec_enabled and self.entity is not None:
            intero_before = interoception_for_entity(self.entity)
        self._capture_pre_act_velocity()
        dec = self.think(obs, delta_time)
        self._pvaec_last_decision = dec
        self._pvaec_last_delta_time = float(delta_time)
        self.act(dec, delta_time)
        self._track_developmental_explore_act()
        if self.homeostatic_pvaec_enabled:
            success = self.verify(ctx, obs, intero_before)
            self._pvaec_last_success = success
            self._track_developmental_verify(success)
            self.remember(ctx, obs, dec, success)
            self._track_developmental_remember()
            self._maybe_record_social_peer(ctx, dec, success)
            self._maybe_advance_developmental_stage(ctx)
        elif self.developmental_ladder_enabled:
            self._maybe_advance_developmental_stage(ctx)

    def _maybe_record_social_peer(
        self,
        ctx: SceneRuntimeTickContext,
        decision: Dict[str, Any],
        success: float,
    ) -> None:
        if not self.social_learning_enabled:
            return
        from core.Lotucosm.social_memory import maybe_record_peer_from_sr_ctx

        maybe_record_peer_from_sr_ctx(self, ctx, decision, success)
