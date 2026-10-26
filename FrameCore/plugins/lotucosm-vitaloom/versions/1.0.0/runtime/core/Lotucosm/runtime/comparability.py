# -*- coding: utf-8
"""SR ↔ PS 可比性评估（ADR-0005 / pvaec_comparability_research §4.4）。

供 Ecology Dock、实验报告与自动化测试消费；不合并 tick。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

# ADR-0005 验收阈值
POPULATION_REL_ERROR_MAX = 0.15
DEVELOPMENTAL_STAGE_REL_ERROR_MAX = 0.25
REPRODUCTION_ABS_DIFF_MAX = 1


def relative_error(a: float, b: float, *, floor: float = 1e-9) -> float:
    """|a-b| / max(|a|, |b|, floor)。"""
    denom = max(abs(float(a)), abs(float(b)), floor)
    return abs(float(a) - float(b)) / denom


@dataclass(frozen=True)
class ComparabilityCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ComparabilityReport:
    checks: tuple[ComparabilityCheck, ...]

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_display_lines(self) -> list[str]:
        if not self.checks:
            return ["— [可比性] —", "双轨数据不足", "—"]
        status = "通过" if self.all_passed else "未达阈值"
        lines = ["— [可比性] —", f"ADR 阈值检查: {status}"]
        for c in self.checks:
            mark = "✓" if c.passed else "✗"
            lines.append(f"  {mark} {c.name}: {c.detail}")
        return lines


def evaluate_adr_comparability(
    sr_metrics: Mapping[str, Any],
    ps_metrics: Mapping[str, Any],
    *,
    reproduction_events_sr: Optional[int] = None,
    reproduction_events_ps: Optional[int] = None,
) -> ComparabilityReport:
    """对比 SR 与 PS 指标字典（population / developmental / 可选繁殖计数）。"""
    checks: list[ComparabilityCheck] = []

    sr_pop = float(sr_metrics.get("population", 0) or 0)
    ps_pop = float(ps_metrics.get("population", 0) or 0)
    pop_err = relative_error(sr_pop, ps_pop)
    checks.append(
        ComparabilityCheck(
            "population",
            pop_err <= POPULATION_REL_ERROR_MAX,
            f"SR={int(sr_pop)} PS={int(ps_pop)} rel={pop_err:.1%} (≤{POPULATION_REL_ERROR_MAX:.0%})",
        )
    )

    sr_dev = float(sr_metrics.get("avg_developmental_stage", 0) or 0)
    ps_dev = float(ps_metrics.get("avg_developmental_stage", 0) or 0)
    if sr_dev > 0 or ps_dev > 0:
        dev_err = relative_error(sr_dev, ps_dev)
        checks.append(
            ComparabilityCheck(
                "avg_developmental_stage",
                dev_err <= DEVELOPMENTAL_STAGE_REL_ERROR_MAX,
                f"SR={sr_dev:.2f} PS={ps_dev:.2f} rel={dev_err:.1%} "
                f"(≤{DEVELOPMENTAL_STAGE_REL_ERROR_MAX:.0%})",
            )
        )

    if reproduction_events_sr is None:
        reproduction_events_sr = sr_metrics.get("reproduction_events")
    if reproduction_events_ps is None:
        reproduction_events_ps = ps_metrics.get("reproduction_events")
    if reproduction_events_sr is not None and reproduction_events_ps is not None:
        diff = abs(int(reproduction_events_sr) - int(reproduction_events_ps))
        checks.append(
            ComparabilityCheck(
                "reproduction_events",
                diff <= REPRODUCTION_ABS_DIFF_MAX,
                f"SR={reproduction_events_sr} PS={reproduction_events_ps} "
                f"Δ={diff} (≤{REPRODUCTION_ABS_DIFF_MAX})",
            )
        )

    return ComparabilityReport(checks=tuple(checks))


def metrics_dict_from_ecology_snapshot(snapshot: Any) -> dict[str, Any]:
    """从 EcologySnapshot 提取可比性指标。"""
    extras = getattr(snapshot, "extras", None) or {}
    return {
        "population": int(getattr(snapshot, "population", 0) or 0),
        "avg_developmental_stage": float(extras.get("avg_developmental_stage", 0) or 0),
        "avg_social_memory_count": float(extras.get("avg_social_memory_count", 0) or 0),
        "avg_memory_gene_count": float(extras.get("avg_memory_gene_count", 0) or 0),
        "reproduction_events": int(extras.get("reproduction_events", 0) or 0),
    }


def evaluate_snapshots_comparability(
    sr_snapshot: Any,
    ps_snapshot: Any,
    **kwargs: Any,
) -> ComparabilityReport:
    """EcologySnapshot 对 → ADR 可比性报告。"""
    return evaluate_adr_comparability(
        metrics_dict_from_ecology_snapshot(sr_snapshot),
        metrics_dict_from_ecology_snapshot(ps_snapshot),
        **kwargs,
    )


def comparability_dock_lines(sr_snapshot: Any, ps_snapshot: Any) -> list[str]:
    """Ecology Dock 可比性段：双轨摘要 + ADR 阈值检查。"""
    sr_m = metrics_dict_from_ecology_snapshot(sr_snapshot)
    ps_m = metrics_dict_from_ecology_snapshot(ps_snapshot)
    sr_extras = getattr(sr_snapshot, "extras", None) or {}
    lines = [
        "— [可比性] —",
        (
            f"人口 SR={sr_m['population']} · PS={ps_m['population']} · "
            f"繁殖 SR={sr_m['reproduction_events']} · PS={ps_m['reproduction_events']}"
        ),
        (
            f"发育均阶 SR={sr_m['avg_developmental_stage']:.2f} · "
            f"PS={ps_m['avg_developmental_stage']:.2f} · "
            f"社会记忆 SR={sr_m['avg_social_memory_count']:.1f} · "
            f"PS={ps_m['avg_social_memory_count']:.1f}"
        ),
    ]
    if bool(sr_extras.get("unified_bridge_enabled")):
        bridged = int(sr_extras.get("bridged_organism_count", 0) or 0)
        lines.append(f"WorldBridge: 开 · 已桥接 {bridged}/{sr_m['population']}")
    report = evaluate_adr_comparability(sr_m, ps_m)
    lines.append(f"ADR 阈值: {'通过' if report.all_passed else '未达'}")
    for c in report.checks:
        mark = "✓" if c.passed else "✗"
        lines.append(f"  {mark} {c.name}: {c.detail}")
    return lines


def should_show_comparability_dock(sr_snapshot: Any, ps_snapshot: Any) -> bool:
    """双轨均有会话数据且至少一侧有活跃种群时展示可比性。"""
    sr_open = bool(getattr(sr_snapshot, "session_open", False))
    ps_open = bool(getattr(ps_snapshot, "session_open", False)) or bool(
        getattr(ps_snapshot, "active", False)
    )
    if not sr_open or not ps_open:
        return False
    sr_pop = int(getattr(sr_snapshot, "population", 0) or 0)
    ps_pop = int(getattr(ps_snapshot, "population", 0) or 0)
    if sr_pop > 0 and ps_pop > 0:
        return True
    sr_extras = getattr(sr_snapshot, "extras", None) or {}
    ps_extras = getattr(ps_snapshot, "extras", None) or {}
    sr_repro = int(sr_extras.get("reproduction_events", 0) or 0)
    ps_repro = int(ps_extras.get("reproduction_events", 0) or 0)
    return sr_repro > 0 or ps_repro > 0
