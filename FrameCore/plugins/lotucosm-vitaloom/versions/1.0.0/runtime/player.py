"""VitaLoom Player：运行已导出或开发中的工程（无 Hub、无完整编辑器）。"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

project_root = os.path.dirname(os.path.abspath(__file__))
RUNTIME_ROOT = Path(project_root)
VERSION_ROOT = RUNTIME_ROOT.parent
SUITE_ROOT = VERSION_ROOT.parents[3]
APP_ROOT = SUITE_ROOT.parents[2]

os.environ.setdefault("VITALOOM_PRODUCT_VERSION_ROOT", str(VERSION_ROOT))
os.environ.setdefault("VITALOOM_SUITE_ROOT", str(SUITE_ROOT))
os.environ.setdefault("FRAMECORE_ROOT", str(APP_ROOT / "FrameCore"))
os.environ.setdefault("VITALOOM_APP_ROOT", str(APP_ROOT))

for path in (str(RUNTIME_ROOT), str(APP_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault("VITALOOM_PLAYER_MODE", "1")
os.environ.setdefault("VITALOOM_SKIP_HUB", "1")
os.environ.setdefault("VITALOOM_SKIP_AUTO_OPEN", "1")

from core.VitaLoom.core.bundle_paths import resource_root  # noqa: E402
from core.VitaLoom.suite.runtime_bootstrap import bootstrap_suite_runtime  # noqa: E402


def _default_smoke_project() -> str:
    from core.VitaLoom.core.bundle_paths import iter_discovered_project_dirs

    for project in iter_discovered_project_dirs():
        if os.path.isfile(os.path.join(project, "project.json")):
            return str(project)
    raise FileNotFoundError("未找到可用于 Player smoke 的示范工程")


def main() -> None:
    parser = argparse.ArgumentParser(description="VitaLoom Player — 运行莲池工程")
    parser.add_argument(
        "--project",
        default=None,
        help="含 project.json 的工程目录",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="offscreen 构造 PlayerShell 并打开工程后立即退出",
    )
    args = parser.parse_args()
    if args.smoke and not args.project:
        project_path = os.path.abspath(_default_smoke_project())
    elif args.project:
        project_path = os.path.abspath(args.project)
    else:
        parser.error("--project is required unless --smoke is used")
    if not os.path.isfile(os.path.join(project_path, "project.json")):
        print(f"错误: 无效工程目录（缺少 project.json）: {project_path}")
        sys.exit(1)

    try:
        bootstrap_suite_runtime(resource_root())
    except Exception as exc:
        print(f"错误: Suite runtime invalid: {exc}")
        sys.exit(1)

    from PyQt6.QtWidgets import QApplication
    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
    )
    from core.VitaLoom.player.player_shell import run_player_shell, run_player_smoke

    app = QApplication(sys.argv)
    capability_registry = InMemoryRuntimeCapabilityRegistry()
    if args.smoke:
        try:
            code = run_player_smoke(
                app,
                project_root,
                project_path,
                capability_registry=capability_registry,
            )
        except Exception as exc:
            print(f"错误: Player smoke failed: {exc}")
            sys.exit(1)
        sys.exit(code)
    print(f"▶ VitaLoom Player 启动: {project_path}")
    code = run_player_shell(
        app,
        project_root,
        project_path,
        capability_registry=capability_registry,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
