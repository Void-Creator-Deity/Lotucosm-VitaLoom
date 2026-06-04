#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""运行 PS 莲池无头实验（PVAEC + 世代编排），导出 metrics 供分析。

用法:
  python tools/run_ps_experiment.py
  python tools/run_ps_experiment.py data/experiments/pvaec_homeostasis_loop.json
  python tools/run_ps_experiment.py --ticks 200 --name quick_test

排错: docs/experiment_guide.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.Lotucosm.experiment_config import PsExperimentConfig, load_experiment_config
from builtin.systems.ps_experiment_runner import PsExperimentRunner

DEFAULT_CONFIG = ROOT / "data" / "experiments" / "pvaec_homeostasis_loop.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lotucosm PS 莲池无头实验")
    parser.add_argument(
        "config",
        nargs="?",
        default=str(DEFAULT_CONFIG),
        help="实验 JSON 配置路径",
    )
    parser.add_argument("--ticks", type=int, help="覆盖配置中的 ticks")
    parser.add_argument("--name", type=str, help="覆盖配置中的 name")
    parser.add_argument("--seed", type=int, help="随机种子（可复现）")
    parser.add_argument("--no-export", action="store_true", help="不写入 output_dir")
    args = parser.parse_args(argv)

    cfg_path = Path(args.config)
    if not cfg_path.is_file():
        print(f"配置不存在: {cfg_path}", file=sys.stderr)
        return 1

    cfg = load_experiment_config(cfg_path)
    if args.ticks is not None:
        cfg.ticks = max(1, args.ticks)
    if args.name:
        cfg.name = args.name
    if args.seed is not None:
        cfg.seed = args.seed

    runner = PsExperimentRunner(cfg)
    summary = runner.run()
    final = summary["final"]
    print(
        f"[{cfg.name}] ticks={cfg.ticks} pop={final['population']} "
        f"iteration={final['iteration']} avg_energy={final['avg_energy']:.2f} "
        f"avg_fitness={final['avg_fitness']:.2f} avg_mem={final['avg_memory_count']:.1f}"
    )

    if not args.no_export:
        out = runner.export(summary)
        print(f"结果已写入: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
