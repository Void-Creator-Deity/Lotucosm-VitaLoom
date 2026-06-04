"""
繁殖系统冒烟：子代实体创建。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest

from core.Lotucosm.pond import Pond
from builtin.entity_types.intelligent_organism import IntelligentOrganism
from builtin.entity_types.reproduction import try_simple_reproduction


class ReproductionSmokeTests(unittest.TestCase):
    def test_try_simple_reproduction_when_energy_high(self):
        pond = Pond(name="t", size=(200.0, 200.0), initial_organisms=0, initial_components=0)
        parent = IntelligentOrganism("p1", (50.0, 50.0), energy=150.0, max_energy=200.0)
        pond.add_organism(parent)
        child = try_simple_reproduction(parent, pond, min_energy_ratio=0.5)
        self.assertIsNotNone(child)
        self.assertIn(child.id, pond.organisms)


if __name__ == "__main__":
    unittest.main()
