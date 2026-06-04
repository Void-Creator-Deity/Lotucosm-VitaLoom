# -*- coding: utf-8 -*-
"""
SceneViewportPlugin：精灵/节点选择事件。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest
from unittest.mock import MagicMock, patch

from builtin.editor_extensions.scene_viewport_plugin import SceneViewportPlugin
from core.VitaLoom.tools.selection_tool import Node


class SceneViewportSpriteSelectionTests(unittest.TestCase):
    @patch("core.VitaLoom.scene.scene_manager.get_scene_manager")
    def test_set_sprite_calls_set_selection_with_node_when_matched(self, mock_gsm):
        sm = MagicMock()
        sm.get_scene_data.return_value = {"entities": [{"id": "ent_1", "sprite_path": ""}]}
        mock_gsm.return_value = sm

        plugin = SceneViewportPlugin()
        ctx = MagicMock()
        ctx.set_selection = MagicMock()
        ctx.i18n_tr = lambda key, default="": default
        plugin.context = ctx

        node = Node("ent_1", 10.0, 20.0, "organism")
        vp = MagicMock()
        vp.nodes = [node]
        plugin.viewport = vp

        plugin.on_set_entity_sprite_path(
            {"entity": node, "sprite_path": "textures/icon.png"}
        )

        ctx.set_selection.assert_called_once_with([node])
        self.assertEqual(node.sprite_path, "textures/icon.png")
        sm.update_scene_data.assert_called()

    @patch("core.VitaLoom.scene.scene_manager.get_scene_manager")
    def test_set_sprite_falls_back_to_entity_payload_when_no_node(self, mock_gsm):
        sm = MagicMock()
        sm.get_scene_data.return_value = {"entities": [{"id": "ghost", "sprite_path": ""}]}
        mock_gsm.return_value = sm

        plugin = SceneViewportPlugin()
        ctx = MagicMock()
        ctx.set_selection = MagicMock()
        ctx.i18n_tr = lambda key, default="": default
        plugin.context = ctx

        vp = MagicMock()
        vp.nodes = []
        plugin.viewport = vp

        payload = {"type": "entity", "data": {"id": "ghost"}}
        plugin.on_set_entity_sprite_path(
            {"entity": payload, "sprite_path": "art/x.png"}
        )

        ctx.set_selection.assert_called_once_with([payload])


if __name__ == "__main__":
    unittest.main()
