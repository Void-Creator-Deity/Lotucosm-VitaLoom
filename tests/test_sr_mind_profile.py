# -*- coding: utf-8 -*-
"""
MindProfile.from_dict 与 default_main_world 缺省键。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

from __future__ import annotations

import unittest

from core.Lotucosm.sr_mind_profile import MindProfile


class MindProfileTests(unittest.TestCase):
    def test_from_dict_empty_uses_default(self):
        d = MindProfile.default_main_world()
        self.assertEqual(MindProfile.from_dict(None), d)
        self.assertEqual(MindProfile.from_dict({}), d)

    def test_from_dict_partial_overrides(self):
        base = MindProfile.default_main_world()
        m = MindProfile.from_dict({"wander_amp": 99.0, "max_speed": 100.0})
        self.assertEqual(m.wander_amp, 99.0)
        self.assertEqual(m.max_speed, 100.0)
        self.assertEqual(m.mem_alpha, base.mem_alpha)

    def test_from_dict_invalid_value_skipped(self):
        m = MindProfile.from_dict({"wander_amp": "not_a_float", "gain_low_stress": 3.0})
        self.assertEqual(m.gain_low_stress, 3.0)
        d = MindProfile.default_main_world()
        self.assertEqual(m.wander_amp, d.wander_amp)


if __name__ == "__main__":
    unittest.main()
