"""sr_resolve_session_banner 与场景可配置横幅文案。"""

from __future__ import annotations

import unittest

from core.VitaLoom.viewports.game_viewport import sr_resolve_session_banner


class SrBannerCopyTests(unittest.TestCase):
    def test_victory_uses_scene_keys(self):
        goals = {
            "victory_title_zh": "自定义标题",
            "victory_banner_zh": "自定义正文",
            "hint_zh": "自定义提示",
        }
        title, msg, hint = sr_resolve_session_banner("victory", goals, chinese=True)
        self.assertEqual(title, "自定义标题")
        self.assertEqual(msg, "自定义正文")
        self.assertEqual(hint, "自定义提示")

    def test_extinction_defaults_en(self):
        title, msg, hint = sr_resolve_session_banner("extinction", {}, chinese=False)
        self.assertEqual(title, "Extinction")
        self.assertIn("extinct", msg.lower())

    def test_victory_uses_en_keys(self):
        goals = {
            "victory_title_en": "Custom Title",
            "victory_banner_en": "Custom body",
            "hint_en": "Custom hint",
        }
        title, msg, hint = sr_resolve_session_banner("victory", goals, chinese=False)
        self.assertEqual(title, "Custom Title")
        self.assertEqual(msg, "Custom body")
        self.assertEqual(hint, "Custom hint")


if __name__ == "__main__":
    unittest.main()
