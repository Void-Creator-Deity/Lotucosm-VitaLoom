# -*- coding: utf-8 -*-
"""SrInputState 单元测试。"""
from __future__ import annotations

import unittest

from core.VitaLoom.viewports.sr_input_state import SrInputState, normalize_sr_key


class SrInputStateTests(unittest.TestCase):
    def test_press_release_and_snapshot(self) -> None:
        st = SrInputState()
        st.press("w")
        st.press("D")
        snap = st.snapshot()
        self.assertEqual(snap.keys_down, frozenset({"W", "D"}))
        snap2 = st.snapshot()
        self.assertEqual(snap, snap2)
        st.release("W")
        self.assertEqual(st.snapshot().keys_down, frozenset({"D"}))

    def test_clear(self) -> None:
        st = SrInputState()
        st.press("Space")
        st.set_mouse_scene(10.0, 20.0)
        st.clear()
        snap = st.snapshot()
        self.assertEqual(snap.keys_down, frozenset())
        self.assertIsNone(snap.mouse_scene_xy)

    def test_mouse_click_edge(self) -> None:
        st = SrInputState()
        st.mouse_press_left()
        snap = st.snapshot()
        self.assertTrue(snap.mouse_left)
        self.assertTrue(snap.mouse_left_clicked)
        snap2 = st.snapshot()
        self.assertTrue(snap2.mouse_left)
        self.assertFalse(snap2.mouse_left_clicked)

    def test_normalize_key(self) -> None:
        self.assertEqual(normalize_sr_key("a"), "A")
        self.assertEqual(normalize_sr_key("Space"), "Space")


if __name__ == "__main__":
    unittest.main()
