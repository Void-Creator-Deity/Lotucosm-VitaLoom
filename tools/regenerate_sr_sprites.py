#!/usr/bin/env python3
"""重新生成主世界 SR 贴图（128×128 多层发光）。"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap, QRadialGradient
from PyQt6.QtWidgets import QApplication

from core.VitaLoom.viewports.sr_sprite_assets import SrSpriteCatalog


def glow_disc(p: QPainter, c1: QColor, c2: QColor, r: float = 52) -> None:
    g = QRadialGradient(QPointF(64, 64), r)
    g.setColorAt(0.0, c1)
    g.setColorAt(0.55, c2)
    g.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))
    p.drawEllipse(8, 8, 112, 112)


def save_sprite(out: Path, name: str, painter_fn) -> None:
    pix = QPixmap(128, 128)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter_fn(p)
    p.end()
    pix.save(str(out / name))


def paint_organism(p: QPainter) -> None:
    glow_disc(p, QColor(220, 250, 255, 240), QColor(100, 180, 240, 130))
    p.setPen(QPen(QColor(180, 230, 255, 200), 2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(24, 24, 80, 80)
    p.setBrush(QBrush(QColor(240, 250, 255, 220)))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(48, 48, 32, 32)


def paint_central_brain(p: QPainter) -> None:
    glow_disc(p, QColor(255, 160, 210, 230), QColor(200, 80, 140, 110))
    p.setPen(QPen(QColor(255, 200, 230, 180), 2))
    for i in range(6):
        a = i * (math.tau / 6.0)
        p.drawLine(64, 64, int(64 + 42 * math.cos(a)), int(64 + 42 * math.sin(a)))


def paint_sensor(p: QPainter) -> None:
    glow_disc(p, QColor(160, 255, 200, 230), QColor(60, 180, 120, 100))
    p.setPen(QPen(QColor(200, 255, 220, 200), 2))
    p.drawLine(64, 64, 104, 64)


def paint_actuator(p: QPainter) -> None:
    glow_disc(p, QColor(255, 200, 120, 230), QColor(200, 120, 40, 100))
    p.setPen(QPen(QColor(255, 220, 160, 180), 2))
    for a in (0.0, 2.1, 4.2):
        p.drawLine(64, 64, int(64 + 38 * math.cos(a)), int(64 + 38 * math.sin(a)))


def paint_nutrient(p: QPainter) -> None:
    glow_disc(p, QColor(255, 245, 180, 250), QColor(210, 230, 90, 140), 46)


def paint_well(p: QPainter) -> None:
    p.setPen(QPen(QColor(120, 190, 255, 160), 2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(22, 22, 84, 84)
    glow_disc(p, QColor(140, 200, 255, 180), QColor(60, 120, 220, 70), 38)


def main() -> None:
    _ = QApplication(sys.argv)
    root = Path(__file__).resolve().parents[1]
    out = root / "projects" / "pvaec-细胞演化" / "assets" / "sprites"
    out.mkdir(parents=True, exist_ok=True)
    save_sprite(out, "organism.png", paint_organism)
    save_sprite(out, "central_brain.png", paint_central_brain)
    save_sprite(out, "sensor.png", paint_sensor)
    save_sprite(out, "actuator.png", paint_actuator)
    save_sprite(out, "nutrient.png", paint_nutrient)
    save_sprite(out, "well.png", paint_well)
    SrSpriteCatalog.invalidate_cache()
    print("Regenerated sprites in", out)


if __name__ == "__main__":
    main()
