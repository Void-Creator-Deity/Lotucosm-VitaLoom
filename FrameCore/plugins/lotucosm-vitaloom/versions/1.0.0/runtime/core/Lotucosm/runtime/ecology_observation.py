# -*- coding: utf-8
"""生态观测接缝：SR 播放与 PS 批处理输出同一只读结构。

Phase C.0：不合并 tick，先统一「读模型」供生态 Dock、状态栏、社区插件消费。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, Optional


class EcologyLane(str, Enum):
    """模拟轨道标识（与 docs/runtime_unification_roadmap.md 一致）。"""

    SR_PLAY = "sr_play"
    PS_BATCH = "ps_batch"
    PS_REPLAY = "ps_replay"  # Phase C.2：快照回放叠加层（规划）


@dataclass(frozen=True)
class EcologySnapshot:
    """单轨生态只读快照。"""

    lane: EcologyLane
    active: bool
    session_open: bool
    label: str
    population: int = 0
    population_peak: int = 0
    generation: float = 0.0
    avg_fitness: float = 0.0
    total_energy: float = 0.0
    sim_time: float = 0.0
    tick: int = 0
    tick_total: int = 0
    cancelled: bool = False
    play_goals_satisfied: Optional[bool] = None
    extras: Dict[str, Any] = field(default_factory=dict)

    def to_display_lines(self) -> list[str]:
        """生态 Dock 等 UI 用的简短行（中文默认文案）。"""
        if self.lane == EcologyLane.SR_PLAY:
            if not self.session_open:
                return ["— [SR 段] —", "SR 播放: 未开始", "—"]
            state = "运行" if self.active else "暂停/停止"
            paused = bool(self.extras.get("paused"))
            lines = [
                "— [SR 段] —",
                f"模拟会话: 进行中（tick: {state}）",
                f"暂停中: {'是' if paused else '否'}",
                f"模拟时间: {self.sim_time:.1f} s",
                f"总人口（细胞）: {self.population}",
                f"种群峰值: {self.population_peak}",
                f"平均世代: {self.generation:.2f}",
                f"wander_amp 方差: {float(self.extras.get('wander_amp_variance', 0)):.3f}",
                f"总生物能量: {self.total_energy:.1f}",
            ]
            if self.play_goals_satisfied is None:
                lines.append("演示目标: 无")
            else:
                lines.append(
                    f"演示目标: {'已达' if self.play_goals_satisfied else '未达'}"
                )
            dev = float(self.extras.get("avg_developmental_stage", 0) or 0)
            s4 = float(self.extras.get("pct_at_stage_s4", 0) or 0)
            mem_g = float(self.extras.get("avg_memory_gene_count", 0) or 0)
            soc = float(self.extras.get("avg_social_memory_count", 0) or 0)
            if bool(self.extras.get("developmental_ladder_enabled")) or dev > 0:
                lines.append(f"发育均阶: {dev:.2f} · S4 占比: {s4:.0%}")
            lines.append(f"MemoryGene: {mem_g:.1f} · 社会记忆: {soc:.1f}")
            if bool(self.extras.get("unified_bridge_enabled")):
                bridged = int(self.extras.get("bridged_organism_count", 0) or 0)
                lines.append(f"WorldBridge: 开 · 已桥接 {bridged}/{self.population}")
            repro = int(self.extras.get("reproduction_events", 0) or 0)
            if repro > 0:
                lines.append(f"繁殖事件（累计）: {repro}")
            return lines
        # PS 轨
        if self.extras.get("service_missing"):
            return ["— [PS 段] —", "PS 实验: 服务未加载", "—"]
        if not self.session_open and not self.active:
            return ["— [PS 段] —", "PS 实验: 未运行", "—"]
        if self.active:
            dev = float(self.extras.get("avg_developmental_stage", 0) or 0)
            s4 = float(self.extras.get("pct_at_stage_s4", 0) or 0)
            mem_g = float(self.extras.get("avg_memory_gene_count", 0) or 0)
            soc = float(self.extras.get("avg_social_memory_count", 0) or 0)
            verify = float(self.extras.get("avg_verify_success", 0) or 0)
            lines = [
                "— [PS 段] —",
                f"PS 实验: 运行中 {self.tick}/{self.tick_total}",
                f"pop={self.population} · gen={int(self.generation)} · fit={self.avg_fitness:.3f}",
            ]
            if bool(self.extras.get("developmental_ladder_enabled")) or dev > 0:
                lines.append(f"发育均阶: {dev:.2f} · S4: {s4:.0%} · verify: {verify:.2f}")
            lines.append(f"MemoryGene: {mem_g:.1f} · 社会记忆: {soc:.1f}")
            repro = int(self.extras.get("reproduction_events", 0) or 0)
            if repro > 0:
                lines.append(f"繁殖事件（累计）: {repro}")
            return lines
        tag = "已取消" if self.cancelled else "已完成"
        dev = float(self.extras.get("avg_developmental_stage", 0) or 0)
        mem_g = float(self.extras.get("avg_memory_gene_count", 0) or 0)
        soc = float(self.extras.get("avg_social_memory_count", 0) or 0)
        return [
            "— [PS 段] —",
            f"PS 实验: {tag}",
            f"pop={self.population} · gen={int(self.generation)} · "
            f"fit={self.avg_fitness:.3f} · mem={self.extras.get('avg_memory_count', 0):.1f}",
            f"MemoryGene: {mem_g:.1f} · 社会记忆: {soc:.1f} · 发育: {dev:.2f}",
            f"繁殖事件: {int(self.extras.get('reproduction_events', 0) or 0)}",
        ]


def snapshot_from_sr(raw: Mapping[str, Any]) -> EcologySnapshot:
    """将 GameViewport.get_sr_ecology_snapshot() 转为统一结构。"""
    sim_running = bool(raw.get("sim_running"))
    return EcologySnapshot(
        lane=EcologyLane.SR_PLAY,
        active=bool(raw.get("active")),
        session_open=sim_running,
        label="SR 场景播放",
        population=int(raw.get("population", 0)),
        population_peak=int(raw.get("population_peak", 0)),
        generation=float(raw.get("avg_generation", 0.0)),
        total_energy=float(raw.get("total_energy", 0.0)),
        sim_time=float(raw.get("sim_time", 0.0)),
        play_goals_satisfied=raw.get("play_goals_satisfied"),
        extras={
            "paused": bool(raw.get("paused")),
            "wander_amp_variance": float(raw.get("wander_amp_variance", 0.0)),
            "membrane_sensor_count": int(raw.get("membrane_sensor_count", 0)),
            "avg_memory_gene_count": float(raw.get("avg_memory_gene_count", 0.0)),
            "avg_social_memory_count": float(raw.get("avg_social_memory_count", 0.0)),
            "avg_developmental_stage": float(raw.get("avg_developmental_stage", 0.0)),
            "pct_at_stage_s4": float(raw.get("pct_at_stage_s4", 0.0)),
            "developmental_ladder_enabled": bool(raw.get("developmental_ladder_enabled", False)),
            "unified_bridge_enabled": bool(raw.get("unified_bridge_enabled", False)),
            "bridged_organism_count": int(raw.get("bridged_organism_count", 0)),
            "reproduction_events": int(raw.get("reproduction_events", 0) or 0),
            "war_phase": raw.get("war_phase"),
            "population_at_war_end": raw.get("population_at_war_end"),
            "war_population_min": raw.get("war_population_min"),
        },
    )


def snapshot_from_ps(raw: Mapping[str, Any]) -> EcologySnapshot:
    """将 PsExperimentService.get_ecology_snapshot() 转为统一结构。"""
    active = bool(raw.get("ps_active"))
    session_open = active or "ps_population" in raw
    if not session_open and raw.get("ps_service_missing"):
        return EcologySnapshot(
            lane=EcologyLane.PS_BATCH,
            active=False,
            session_open=False,
            label="PS 批实验",
            extras={"service_missing": True},
        )
    return EcologySnapshot(
        lane=EcologyLane.PS_BATCH,
        active=active,
        session_open=session_open,
        label=str(raw.get("ps_name", "PS 批实验")),
        population=int(raw.get("ps_population", 0)),
        generation=float(raw.get("ps_iteration", 0)),
        avg_fitness=float(raw.get("ps_avg_fitness", 0.0)),
        tick=int(raw.get("ps_tick", 0)),
        tick_total=int(raw.get("ps_total_ticks", 0)),
        cancelled=bool(raw.get("ps_cancelled", False)),
        extras={
            "avg_memory_count": float(raw.get("ps_avg_memory_count", 0.0)),
            "avg_memory_gene_count": float(raw.get("ps_avg_memory_gene_count", 0.0)),
            "avg_social_memory_count": float(raw.get("ps_avg_social_memory_count", 0.0)),
            "avg_developmental_stage": float(raw.get("ps_avg_developmental_stage", 0.0)),
            "pct_at_stage_s4": float(raw.get("ps_pct_at_stage_s4", 0.0)),
            "developmental_ladder_enabled": bool(raw.get("ps_developmental_ladder_enabled", False)),
            "avg_verify_success": float(raw.get("ps_avg_verify_success", 0.0)),
            "reproduction_events": int(raw.get("ps_reproduction_events", 0) or 0),
            "war_phase": raw.get("ps_war_phase"),
            "population_at_war_end": raw.get("ps_population_at_war_end"),
            "war_population_min": raw.get("ps_war_population_min"),
        },
    )
