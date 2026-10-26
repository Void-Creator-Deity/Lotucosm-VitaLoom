#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理 workspace/state/system/editor_config.json 中的无效/临时项目路径。

职责: 调用 ProjectManager 内置消毒逻辑并打印结果。
时机: 最近列表含 pytest 临时目录或 last_opened 指向已删工程时手动运行。
排错: 见 docs/routine_maintenance.md。
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main() -> int:
    from core.VitaLoom.project.project_manager import get_project_manager

    pm = get_project_manager()
    before = pm._read_editor_config()
    pm._sanitize_recent_projects()
    pm._sanitize_editor_config()
    after = pm._read_editor_config()

    cfg_path = pm._get_config_file()
    print(f"配置文件: {cfg_path}")
    print("清理前:", json.dumps(before, ensure_ascii=False, indent=2))
    print("清理后:", json.dumps(after, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
