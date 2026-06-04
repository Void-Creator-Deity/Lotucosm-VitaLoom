# -*- coding: utf-8 -*-
"""重新生成教程贴图：像素风、无中心圆点；墙为横条。"""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication


def _save(path: Path, w: int, h: int, draw) -> None:
    pix = QPixmap(w, h)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    draw(p, w, h)
    p.end()
    path.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(path))


def _draw_wall(p: QPainter, w: int, h: int) -> None:
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(72, 80, 96))
    p.drawRect(0, 0, w, h)
    p.setBrush(QColor(108, 116, 128))
    p.drawRect(0, 0, w, max(2, h // 3))


def _draw_slime(p: QPainter, w: int, h: int) -> None:
    p.setPen(QPen(QColor(24, 96, 48), 2))
    p.setBrush(QColor(76, 196, 100))
    p.drawRoundedRect(3, 6, w - 6, h - 8, 6, 6)
    p.setBrush(QColor(24, 48, 24))
    p.drawRect(9, 13, 4, 4)
    p.drawRect(w - 13, 13, 4, 4)


def _draw_player(p: QPainter, w: int, h: int, frame: int) -> None:
    p.setPen(QPen(QColor(32, 72, 128), 2))
    p.setBrush(QColor(72, 168, 248))
    p.drawRect(11, 4, 10, 10)
    p.drawRect(9, 14, 14, 12)
    leg = frame % 2
    p.drawRect(9, 26, 5, 5 + leg)
    p.drawRect(18, 26, 5, 5 + (1 - leg))


def _draw_exit(p: QPainter, w: int, h: int) -> None:
    p.setPen(QPen(QColor(128, 96, 24), 2))
    p.setBrush(QColor(248, 204, 56))
    p.drawRect(4, 4, w - 8, h - 8)
    p.setBrush(QColor(176, 132, 40))
    p.drawRect(w // 2 - 3, h // 2 - 5, 6, 10)


def main() -> int:
    app = QApplication(sys.argv)
    root = Path(__file__).resolve().parents[1] / "assets" / "sprites"
    _save(root / "wall.png", 64, 16, _draw_wall)
    _save(root / "slime.png", 32, 28, _draw_slime)
    _save(root / "exit.png", 32, 32, _draw_exit)
    _save(root / "player_0.png", 32, 32, lambda p, w, h: _draw_player(p, w, h, 0))
    _save(root / "player_1.png", 32, 32, lambda p, w, h: _draw_player(p, w, h, 1))
    print("wrote sprites to", root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
