# -*- coding: utf-8
"""SR 播放输入状态：键盘/鼠标快照供 ScriptBase.sr_step 读取（非 PVAEC 包）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Set, Tuple


@dataclass(frozen=True)
class SrInputSnapshot:
    keys_down: frozenset[str] = frozenset()
    mouse_scene_xy: Optional[Tuple[float, float]] = None
    mouse_left: bool = False
    mouse_left_clicked: bool = False


_EMPTY_SNAPSHOT = SrInputSnapshot()


def normalize_sr_key(key_text: str) -> str:
    """Qt key text → 脚本可读键名（W/A/S/D/Space/Up 等）。"""
    if not key_text:
        return ""
    t = key_text.strip()
    if len(t) == 1 and t.isalpha():
        return t.upper()
    aliases = {
        "Space": "Space",
        " ": "Space",
        "Up": "Up",
        "Down": "Down",
        "Left": "Left",
        "Right": "Right",
        "Return": "Return",
        "Enter": "Return",
        "Escape": "Escape",
    }
    return aliases.get(t, t)


def key_from_qt_event(event: Any) -> str:
    """PyQt6 QKeyEvent → 脚本键名。"""
    try:
        t = normalize_sr_key(event.text() or "")
        if t:
            return t
    except Exception:
        pass
    try:
        from PyQt6.QtCore import Qt

        mapping = {
            int(Qt.Key.Key_W): "W",
            int(Qt.Key.Key_A): "A",
            int(Qt.Key.Key_S): "S",
            int(Qt.Key.Key_D): "D",
            int(Qt.Key.Key_Up): "Up",
            int(Qt.Key.Key_Down): "Down",
            int(Qt.Key.Key_Left): "Left",
            int(Qt.Key.Key_Right): "Right",
            int(Qt.Key.Key_Space): "Space",
            int(Qt.Key.Key_Return): "Return",
            int(Qt.Key.Key_Enter): "Return",
            int(Qt.Key.Key_Escape): "Escape",
        }
        return mapping.get(int(event.key()), "")
    except Exception:
        return ""


class SrInputState:
    """可变输入缓冲；每帧 tick 前 snapshot() 注入 SceneRuntimeTickContext。"""

    def __init__(self) -> None:
        self._keys: Set[str] = set()
        self._mouse_scene_xy: Optional[Tuple[float, float]] = None
        self._mouse_left = False
        self._mouse_left_clicked = False

    def press(self, key: str) -> None:
        k = normalize_sr_key(key)
        if k:
            self._keys.add(k)

    def release(self, key: str) -> None:
        k = normalize_sr_key(key)
        if k:
            self._keys.discard(k)

    def set_mouse_scene(self, x: float, y: float) -> None:
        self._mouse_scene_xy = (float(x), float(y))

    def mouse_press_left(self) -> None:
        self._mouse_left = True
        self._mouse_left_clicked = True

    def mouse_release_left(self) -> None:
        self._mouse_left = False

    def clear(self) -> None:
        self._keys.clear()
        self._mouse_scene_xy = None
        self._mouse_left = False
        self._mouse_left_clicked = False

    def snapshot(self) -> SrInputSnapshot:
        mouse = self._mouse_scene_xy
        snap = SrInputSnapshot(
            keys_down=frozenset(self._keys),
            mouse_scene_xy=mouse,
            mouse_left=self._mouse_left,
            mouse_left_clicked=self._mouse_left_clicked,
        )
        self._mouse_left_clicked = False
        return snap

    @staticmethod
    def empty_snapshot() -> SrInputSnapshot:
        return _EMPTY_SNAPSHOT
