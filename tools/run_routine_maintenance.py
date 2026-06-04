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


def _run(cmd: list[str], label: str) -> int:
    print(f"\n=== {label} ===")
    print(" ", " ".join(cmd))
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
