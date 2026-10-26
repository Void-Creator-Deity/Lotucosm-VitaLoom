#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""例行维护一键脚本：测试 + 注释/日志审计（每周门禁）。

职责: 聚合 pytest、audit_comment_standard、audit_logging_guard。
时机: 每周或发版前在项目根执行；每两周可加 --prune-config。
不变量: 任一子步骤非零退出码则本脚本退出码为 1。
通过标准: pytest 0 失败；注释审计 0 缺失；日志审计无 except:pass 等。
排错: 见 docs/routine_maintenance.md、docs/stability_validation_checklist.md。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _run(cmd: list[str], label: str) -> int:
    print(f"\n=== {label} ===", flush=True)
    print(" ", " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=ROOT)
    return int(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lotucosm-VitaLoom 例行维护")
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="跳过 pytest（仅跑审计）",
    )
    parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="跳过注释/日志审计",
    )
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="跳过入口 smoke（main/player/tools help）",
    )
    parser.add_argument(
        "--prune-config",
        action="store_true",
        help="运行 editor_config 路径清理",
    )
    args = parser.parse_args()
    failures = 0

    if args.prune_config:
        failures += _run(
            [sys.executable, "tools/prune_editor_config.py"],
            "prune editor_config",
        )

    failures += _run(
        [sys.executable, "tools/check_core_boundaries.py"],
        "core boundaries",
    )
    failures += _run(
        [sys.executable, "tools/check_release_consistency.py"],
        "release consistency",
    )
    failures += _run(
        [sys.executable, "tools/check_project_plugin_model.py"],
        "project plugin model",
    )
    failures += _run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "FrameCore",
            "workspace",
            "tools",
            "main.py",
            "player.py",
        ],
        "compileall",
    )

    if not args.skip_smoke:
        failures += _run([sys.executable, "main.py", "--version"], "main version")
        failures += _run([sys.executable, "main.py", "--smoke-hub"], "hub smoke")
        failures += _run([sys.executable, "main.py", "--smoke-editor"], "editor smoke")
        failures += _run([sys.executable, "player.py", "--help"], "player help")
        failures += _run([sys.executable, "player.py", "--smoke"], "player smoke")
        failures += _run(
            [sys.executable, "tools/run_ps_experiment.py", "--help"],
            "ps experiment help",
        )
        failures += _run(
            [sys.executable, "tools/update_project_lock.py", "--help"],
            "project lock help",
        )
        failures += _run(
            [sys.executable, "tools/export_player.py", "--help"],
            "export player help",
        )
        failures += _run(
            [sys.executable, "tools/benchmark_engine.py", "--help"],
            "engine benchmark help",
        )
        failures += _run(
            [sys.executable, "tools/check_asset_provenance.py"],
            "asset provenance",
        )

    if not args.skip_tests:
        failures += _run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
            "pytest",
        )

    if not args.skip_audit:
        failures += _run(
            [sys.executable, "tools/audit_comment_standard.py"],
            "comment standard",
        )
        failures += _run(
            [sys.executable, "tools/audit_logging_guard.py"],
            "logging guard",
        )

    if failures:
        print(f"\n维护检查未通过（{failures} 项失败）")
        return 1
    print("\n维护检查全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
