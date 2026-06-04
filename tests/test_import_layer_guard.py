# -*- coding: utf-8 -*-
"""
Ring0：库模块不得修改 sys.path（引导仅 main/launcher）。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import unittest
from pathlib import Path


class ImportLayerGuardTests(unittest.TestCase):
    def test_builtin_has_no_sys_path_insert(self) -> None:
        root = Path(__file__).resolve().parents[1]
        bad: list[str] = []
        for p in (root / "builtin").rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            if "sys.path.insert" in text:
                bad.append(str(p.relative_to(root)))
        self.assertEqual(bad, [], "Remove sys.path hacks from: " + repr(bad))

    def test_core_lotucosm_has_no_sys_path_insert_except_launcher(self) -> None:
        root = Path(__file__).resolve().parents[1]
        bad: list[str] = []
        for p in (root / "core" / "Lotucosm").glob("*.py"):
            if p.name == "launcher.py":
                continue
            text = p.read_text(encoding="utf-8")
            if "sys.path.insert" in text:
                bad.append(str(p.relative_to(root)))
        self.assertEqual(bad, [], repr(bad))


if __name__ == "__main__":
    unittest.main()
