# -*- coding: utf-8 -*-
"""SrInputState 单元测试。"""
from __future__ import annotations

import unittest

from core.VitaLoom.viewports.sr_input_state import SrInputState, normalize_sr_key


class SrInputStateTests(unittest.TestCase):

    def test_capture_and_restore_preserves_unconsumed_local_buffer(self) -> None:
        state = SrInputState()
        state.press("w")
        state.set_mouse_scene(12.5, 8.0)
        state.mouse_press_left()
        captured = state.capture_state()
        state.clear()

        state.restore_state(captured)
        assert state.capture_state() == {
            "keys_down": ["W"],
            "mouse_scene_xy": [12.5, 8.0],
            "mouse_left": True,
            "mouse_left_clicked": True,
        }
        assert state.snapshot().mouse_left_clicked is True
        assert state.snapshot().mouse_left_clicked is False

    def test_restore_rejects_invalid_state_without_mutation(self) -> None:
        state = SrInputState()
        state.press("A")
        state.mouse_press_left()
        before = state.capture_state()
        invalid = (
            {"keys_down": ["W"], "mouse_left": "yes"},
            {**before, "mouse_scene_xy": [float("nan"), 1.0]},
            {**before, "mouse_scene_xy": [1.0, float("inf")]},
            {**before, "mouse_scene_xy": [True, 1.0]},
            {**before, "unexpected": 1},
        )
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                state.restore_state(payload)
            self.assertEqual(state.capture_state(), before)
        self.assertTrue(state.snapshot().mouse_left_clicked)

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
