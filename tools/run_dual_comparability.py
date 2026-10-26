#!/usr/bin/env python3
# -*- coding: utf-8
"""Run PS batch vs unified_bridge headless comparability (ADR-0005)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools._runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from builtin.systems.ps_experiment_runner import PsExperimentRunner
from core.Lotucosm.experiment_config import PsExperimentConfig, load_experiment_config
from core.Lotucosm.runtime.dual_comparability_runner import (
    comparability_report_lines,
    matrix_report_lines,
    run_comparability_matrix,
    run_dual_comparability,
)
from core.VitaLoom.project.evolution_context import (
    apply_evolution_defaults_to_ps_config,
    load_project_evolution_context,
)

DEFAULT_CONFIG = ROOT / "workspace" / "experiments" / "dual_comparability_smoke.json"
DEFAULT_MATRIX = ROOT / "workspace" / "experiments" / "dual_comparability_matrix.json"


def _apply_overrides(cfg: PsExperimentConfig, overrides: dict[str, Any]) -> None:
    for key, value in overrides.items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)


def _load_case_config(case: dict[str, Any], *, seed: int, ticks: int | None) -> PsExperimentConfig:
    rel = str(case.get("config") or DEFAULT_CONFIG)
    cfg_path = Path(rel)
    if not cfg_path.is_file():
        cfg_path = ROOT / rel
    cfg = load_experiment_config(cfg_path)
    overrides = case.get("overrides")
    if isinstance(overrides, dict):
        _apply_overrides(cfg, overrides)
    cfg.seed = int(case.get("seed", seed))
    if ticks is not None:
        cfg.ticks = max(1, ticks)
    elif case.get("ticks") is not None:
        cfg.ticks = max(1, int(case["ticks"]))
    if case.get("name"):
        cfg.name = str(case["name"])
    return cfg


def _run_matrix(matrix_path: Path, *, seed: int, ticks: int | None, report_json: str | None) -> int:
    data = json.loads(matrix_path.read_text(encoding="utf-8"))
    matrix_seed = int(data.get("seed", seed))
    checkpoints = tuple(sorted(set(int(t) for t in (data.get("checkpoint_ticks") or [50]))))
    cases = data.get("cases") or []
    if not cases:
        print("matrix has no cases", file=sys.stderr)
        return 1

    def factory(case: dict[str, Any]) -> PsExperimentRunner:
        cfg = _load_case_config(case, seed=matrix_seed, ticks=ticks)
        return PsExperimentRunner(cfg)

    matrix_result = run_comparability_matrix(
        list(cases),
        base_runner_factory=factory,
        checkpoint_ticks=checkpoints,
    )
    for line in matrix_report_lines(matrix_result):
        print(line)
    if report_json:
        out = Path(report_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        slim = {
            "all_passed": matrix_result.get("all_passed"),
            "cases": [
                {
                    "name": entry.get("name"),
                    "all_passed": (entry.get("result") or {}).get("all_passed"),
                    "final": (entry.get("result") or {}).get("final"),
                    "checkpoints": (entry.get("result") or {}).get("checkpoints"),
                }
                for entry in matrix_result.get("cases") or []
            ],
        }
        out.write_text(json.dumps(slim, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"matrix report written: {out}")
    return 0 if matrix_result.get("all_passed") else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare PS batch vs unified_bridge under the same seed (ADR-0005)."
    )
    parser.add_argument(
        "config",
        nargs="?",
        default=str(DEFAULT_CONFIG),
        help="Experiment JSON config path.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default 42).")
    parser.add_argument("--ticks", type=int, help="Override configured ticks.")
    parser.add_argument(
        "--checkpoint",
        type=int,
        action="append",
        help="Checkpoint tick(s); repeatable (default 20,50; must match sampled ticks).",
    )
    parser.add_argument(
        "--matrix",
        type=str,
        help="Run comparability matrix JSON (e.g. dual_comparability_matrix.json).",
    )
    parser.add_argument("--report-json", type=str, help="Write JSON summary report.")
    parser.add_argument("--project", type=str, help="Project dir for evolution defaults.")
    args = parser.parse_args(argv)

    if args.matrix:
        matrix_path = Path(args.matrix)
        if not matrix_path.is_file():
            matrix_path = ROOT / args.matrix
        if not matrix_path.is_file():
            print(f"matrix does not exist: {args.matrix}", file=sys.stderr)
            return 1
        return _run_matrix(matrix_path, seed=args.seed, ticks=args.ticks, report_json=args.report_json)

    cfg_path = Path(args.config)
    if not cfg_path.is_file():
        print(f"config does not exist: {cfg_path}", file=sys.stderr)
        return 1

    cfg = load_experiment_config(cfg_path)
    if args.project:
        project_json = Path(args.project) / "project.json"
        if project_json.is_file():
            meta = json.loads(project_json.read_text(encoding="utf-8"))
            apply_evolution_defaults_to_ps_config(
                cfg,
                load_project_evolution_context(meta),
            )
    cfg.seed = args.seed
    if args.ticks is not None:
        cfg.ticks = max(1, args.ticks)

    checkpoints = args.checkpoint if args.checkpoint else [20, 50]
    runner = PsExperimentRunner(cfg)
    result = run_dual_comparability(
        runner,
        checkpoint_ticks=tuple(sorted(set(checkpoints))),
    )

    for line in comparability_report_lines(result):
        print(line)

    if args.report_json:
        out = Path(args.report_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        slim = {k: v for k, v in result.items() if k not in ("ps_summary", "unified_bridge_summary")}
        out.write_text(json.dumps(slim, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"report written: {out}")

    return 0 if result.get("all_passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
