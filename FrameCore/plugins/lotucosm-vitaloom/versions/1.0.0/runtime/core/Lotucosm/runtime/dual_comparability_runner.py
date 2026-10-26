# -*- coding: utf-8
"""PS batch vs unified_bridge 无头对照（ADR-0005 验收）。"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from core.Lotucosm.runtime.comparability import ComparabilityReport, evaluate_adr_comparability


def metrics_at_tick(snapshots: list[Mapping[str, Any]], tick: int) -> Optional[dict[str, Any]]:
    for row in snapshots:
        if int(row.get("tick", 0) or 0) == tick:
            return dict(row)
    return None


def _missing_checkpoint_report(
    tick: int,
    ps_summary: Mapping[str, Any],
    unified_summary: Mapping[str, Any],
) -> dict[str, Any]:
    """报告缺失采样点，而不是用 final 冒充 checkpoint。"""
    ps_ticks = [int(row.get("tick", 0) or 0) for row in (ps_summary.get("snapshots") or [])]
    ub_ticks = [
        int(row.get("tick", 0) or 0) for row in (unified_summary.get("snapshots") or [])
    ]
    detail = (
        f"缺少 tick={tick} 的采样；PS snapshots={ps_ticks} "
        f"unified_bridge snapshots={ub_ticks}"
    )
    return {
        "passed": False,
        "checks": [
            {
                "name": "checkpoint_sample",
                "passed": False,
                "detail": detail,
            }
        ],
        "ps_metrics": None,
        "unified_bridge_metrics": None,
    }


def run_dual_comparability(
    runner: Any,
    *,
    checkpoint_ticks: tuple[int, ...] = (50,),
) -> Dict[str, Any]:
    """同 seed 运行 PS batch 与 unified_bridge，返回 ADR 可比性报告。"""
    normalized_ticks = tuple(sorted(set(int(tick) for tick in checkpoint_ticks)))
    if any(tick < 1 or tick > int(runner.config.ticks) for tick in normalized_ticks):
        raise ValueError("checkpoint ticks must be within the configured run")
    ps_summary = runner.run(snapshot_ticks=normalized_ticks)
    unified_summary = runner.run_unified_bridge(snapshot_ticks=normalized_ticks)

    reports: dict[str, Any] = {}
    for tick in checkpoint_ticks:
        ps_m = metrics_at_tick(ps_summary.get("snapshots") or [], tick)
        ub_m = metrics_at_tick(unified_summary.get("snapshots") or [], tick)
        if ps_m is None or ub_m is None:
            reports[f"tick_{tick}"] = _missing_checkpoint_report(
                tick,
                ps_summary,
                unified_summary,
            )
            continue
        report = evaluate_adr_comparability(ps_m, ub_m)
        reports[f"tick_{tick}"] = {
            "passed": report.all_passed,
            "checks": [
                {"name": c.name, "passed": c.passed, "detail": c.detail} for c in report.checks
            ],
            "ps_metrics": ps_m,
            "unified_bridge_metrics": ub_m,
        }

    final_report = evaluate_adr_comparability(
        ps_summary.get("final") or {},
        unified_summary.get("final") or {},
    )
    return {
        "seed": runner.config.seed,
        "ticks": runner.config.ticks,
        "checkpoint_ticks": list(normalized_ticks),
        "checkpoints": reports,
        "final": {
            "passed": final_report.all_passed,
            "checks": [
                {"name": c.name, "passed": c.passed, "detail": c.detail}
                for c in final_report.checks
            ],
            "ps_metrics": ps_summary.get("final"),
            "unified_bridge_metrics": unified_summary.get("final"),
        },
        "all_passed": final_report.all_passed
        and all(r.get("passed") for r in reports.values()),
        "ps_summary": ps_summary,
        "unified_bridge_summary": unified_summary,
    }


def comparability_report_lines(result: Mapping[str, Any]) -> list[str]:
    """CLI / 日志友好输出。"""
    lines = [
        f"seed={result.get('seed')} ticks={result.get('ticks')} "
        f"all_passed={result.get('all_passed')}",
    ]
    checkpoints = result.get("checkpoints") or {}
    for key in sorted(checkpoints.keys()):
        cp = checkpoints[key]
        tag = "PASS" if cp.get("passed") else "FAIL"
        lines.append(f"{key}: {tag}")
        for c in cp.get("checks") or []:
            mark = "OK" if c.get("passed") else "FAIL"
            lines.append(f"  [{mark}] {c.get('name')}: {c.get('detail')}")
    final = result.get("final") or {}
    lines.append(f"final: {'PASS' if final.get('passed') else 'FAIL'}")
    for c in final.get("checks") or []:
        mark = "OK" if c.get("passed") else "FAIL"
        lines.append(f"  [{mark}] {c.get('name')}: {c.get('detail')}")
    return lines


def run_comparability_matrix(
    cases: list[dict[str, Any]],
    *,
    base_runner_factory: Any,
    checkpoint_ticks: tuple[int, ...] = (50,),
) -> dict[str, Any]:
    """多配置矩阵：每项独立 run_dual_comparability。"""
    runs: list[dict[str, Any]] = []
    for case in cases:
        name = str(case.get("name") or f"case_{len(runs) + 1}")
        runner = base_runner_factory(case)
        result = run_dual_comparability(runner, checkpoint_ticks=checkpoint_ticks)
        runs.append({"name": name, "result": result})
    return {
        "cases": runs,
        "all_passed": all(r["result"].get("all_passed") for r in runs),
    }


def matrix_report_lines(matrix_result: Mapping[str, Any]) -> list[str]:
    lines = [f"matrix all_passed={matrix_result.get('all_passed')}"]
    for entry in matrix_result.get("cases") or []:
        name = entry.get("name", "?")
        result = entry.get("result") or {}
        lines.append(f"--- {name} ---")
        lines.extend(comparability_report_lines(result))
    return lines
