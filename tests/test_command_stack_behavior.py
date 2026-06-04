"""
CommandStack：撤销/重做与场景节点命令契约。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest

from core.VitaLoom.commands.command import CommandStack, ModifyNodePropertyCommand


class _DummyNode:
    def __init__(self):
        self.id = "node_1"
        self.x = 10


class CommandStackBehaviorTests(unittest.TestCase):
    def test_execute_undo_redo_consistent(self):
        node = _DummyNode()
        stack = CommandStack()

        cmd = ModifyNodePropertyCommand(node, "x", 10, 20)
        stack.execute(cmd)
        self.assertEqual(node.x, 20)

        stack.undo()
        self.assertEqual(node.x, 10)

        stack.redo()
        self.assertEqual(node.x, 20)


if __name__ == "__main__":
    unittest.main()
