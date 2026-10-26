# -*- coding: utf-8 -*-
"""
SR mind_dict_mutate：GENE_KEYS 子集遗传。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

from __future__ import annotations

import random
import unittest

from core.Lotucosm.sr_mind_gene import GENE_KEYS, mind_dict_mutate


class MindGeneTests(unittest.TestCase):
    def test_optional_rng_does_not_touch_process_global(self):
        parent = {k: 10.0 for k in GENE_KEYS}
        before = random.getstate()
        child, _ = mind_dict_mutate(parent, 0.5)
        self.assertEqual(random.getstate(), before)
        self.assertEqual(child, mind_dict_mutate(parent, 0.5)[0])

    def test_mutate_changes_within_bounds(self):
        parent = {k: 10.0 for k in GENE_KEYS}
        parent["wander_amp"] = 18.0
        parent["gain_high_stress"] = 32.0
        parent["mem_alpha"] = 0.2
        rng = random.Random(42)
        child, deltas = mind_dict_mutate(parent, 0.5, rng)
        for k in GENE_KEYS:
            self.assertIn(k, child)
            self.assertIn(k, deltas)
        self.assertNotEqual(sum(abs(deltas[k]) for k in GENE_KEYS), 0.0)

    def test_custom_gene_keys_from_profile(self):
        parent = {"wander_amp": 20.0, "max_speed": 300.0, "gain_high_stress": 40.0}
        child, deltas = mind_dict_mutate(
            parent,
            0.4,
            random.Random(7),
            gene_keys=("wander_amp", "max_speed"),
        )
        self.assertIn("wander_amp", child)
        self.assertIn("max_speed", child)
        self.assertNotIn("gain_high_stress", child)
        self.assertLessEqual(child["max_speed"], 600.0)


if __name__ == "__main__":
    unittest.main()
