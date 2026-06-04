# -*- coding: utf-8 -*-
"""
Ring0：仓库根目录下 PS 内核符号可导入（无路径 hack）。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import unittest


class PsKernelImportSmoke(unittest.TestCase):
    def test_pond_organism_pvaec_import(self) -> None:
        from core.Lotucosm.pond import Pond
        from builtin.entity_types.organism import Organism
        from core.Lotucosm.pvaec_cycle import PVAECCycle

        self.assertTrue(callable(Pond))
        self.assertTrue(callable(PVAECCycle))
        o = Organism("x", (0.0, 0.0))
        self.assertEqual(o.id, "x")


if __name__ == "__main__":
    unittest.main()
