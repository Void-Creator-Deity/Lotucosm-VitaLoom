#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run a headless PS experiment from the command line."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools._runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from core.Lotucosm.experiment_config import load_experiment_config
from core.VitaLoom.project.evolution_context import (
    apply_evolution_defaults_to_ps_config,
    load_project_evolution_context,
)
from core.VitaLoom.simulation.ps_experiment_service import PsExperimentService


DEFAULT_CONFIG = ROOT / "workspace" / "experiments" / "pvaec_homeostasis_loop.json"


def _write_junit(path: Path, cfg_name: str, summary: dict, ok: bool) -> None:
    final = summary.get("final") or {}
    cases = [
        ("population", int(final.get("population", 0))),
        ("iteration", int(final.get("iteration", 0))),
        ("avg_fitness", float(final.get("avg_fitness", 0.0))),
    ]
    failed = 0 if ok else 1
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<testsuite name="{escape(cfg_name)}" tests="{len(cases)}" failures="{failed}">',
    ]
    for name, _value in cases:
        if ok:
            lines.append(f'  <testcase classname="ps_experiment" name="{escape(name)}"/>')
        else:
            lines.append(
                f'  <testcase classname="ps_experiment" name="{escape(name)}">'
                '<failure message="run failed"/></testcase>'
            )
    lines.append("</testsuite>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_json_report(path: Path, cfg_name: str, summary: dict, out_dir: Path | None) -> None:
    payload = {
        "name": cfg_name,
        "summary": summary,
        "output_dir": str(out_dir) if out_dir else None,
        "cancelled": bool(summary.get("cancelled")),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a Lotucosm PS experiment without opening the editor."
    )
    parser.add_argument(
        "config",
        nargs="?",
        default=str(DEFAULT_CONFIG),
        help="Experiment JSON config path.",
    )
    parser.add_argument("--ticks", type=int, help="Override configured ticks.")
    parser.add_argument("--name", type=str, help="Override configured experiment name.")
    parser.add_argument("--seed", type=int, help="Random seed for reproducible runs.")
    parser.add_argument("--no-export", action="store_true", help="Do not write run output files.")
    parser.add_argument("--project", type=str, help="Project directory for evolution defaults.")
    parser.add_argument("--junit", type=str, help="Write a JUnit XML report.")
    parser.add_argument("--report-json", type=str, help="Write a JSON summary report.")
    args = parser.parse_args(argv)

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
    if args.ticks is not None:
        cfg.ticks = max(1, args.ticks)
    if args.name:
        cfg.name = args.name
    if args.seed is not None:
        cfg.seed = args.seed

    service = PsExperimentService(ROOT)
    service.config = cfg
    try:
        summary, out_dir = service.run_sync(cfg, export=not args.no_export)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    final = summary["final"]
    cancelled = bool(summary.get("cancelled"))
    ok = not cancelled
    print(
        f"[{cfg.name}] ticks={cfg.ticks} pop={final['population']} "
        f"iteration={final['iteration']} avg_energy={final['avg_energy']:.2f} "
        f"avg_fitness={final['avg_fitness']:.2f} avg_mem={final['avg_memory_count']:.1f}"
    )
    if out_dir is not None:
        print(f"results written: {out_dir}")
    if args.junit:
        _write_junit(Path(args.junit), cfg.name, summary, ok)
    if args.report_json:
        _write_json_report(Path(args.report_json), cfg.name, summary, out_dir)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
