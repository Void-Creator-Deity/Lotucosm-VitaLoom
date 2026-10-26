#!/usr/bin/env python3
"""Regenerate the PVAEC sample project's 128x128 SR sprite assets."""

from __future__ import annotations

import math
import sys
from pathlib import Path

def _find_repo_root(start: Path) -> Path:
    for path in (start, *start.parents):
        if (path / "FrameCore").is_dir() and (path / "main.py").is_file():
            return path
    raise RuntimeError("could not find repository root from project tool path")


REPO_ROOT = _find_repo_root(Path(__file__).resolve())
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools._runtime_bootstrap import install_runtime_paths

install_runtime_paths(REPO_ROOT)

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPixmap, QRadialGradient
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


def save_canvas(out: Path, name: str, w: int, h: int, painter_fn) -> None:
    pix = QPixmap(w, h)
    pix.fill(QColor(10, 14, 20))
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter_fn(p, w, h)
    p.end()
    out.mkdir(parents=True, exist_ok=True)
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


def paint_logo(p: QPainter, w: int, h: int) -> None:
    gradient = QRadialGradient(QPointF(w * 0.42, h * 0.45), min(w, h) * 0.52)
    gradient.setColorAt(0.0, QColor(145, 230, 255))
    gradient.setColorAt(0.45, QColor(84, 150, 220))
    gradient.setColorAt(1.0, QColor(12, 18, 28))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(gradient))
    p.drawEllipse(int(w * 0.12), int(h * 0.12), int(w * 0.76), int(h * 0.76))
    p.setPen(QPen(QColor(220, 250, 255, 210), max(2, w // 90)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for scale in (0.34, 0.48, 0.62):
        size = int(min(w, h) * scale)
        p.drawEllipse((w - size) // 2, (h - size) // 2, size, size)
    p.setPen(QPen(QColor(255, 220, 130, 230), max(2, w // 100)))
    for i in range(8):
        a = i * (math.tau / 8.0)
        x1 = int(w / 2 + math.cos(a) * w * 0.12)
        y1 = int(h / 2 + math.sin(a) * h * 0.12)
        x2 = int(w / 2 + math.cos(a) * w * 0.32)
        y2 = int(h / 2 + math.sin(a) * h * 0.32)
        p.drawLine(x1, y1, x2, y2)


def paint_brand_sheet(p: QPainter, w: int, h: int) -> None:
    p.fillRect(0, 0, w, h, QColor(9, 12, 18))
    cell_w = w // 3
    cell_h = h // 2
    for row in range(2):
        for col in range(3):
            cx = col * cell_w + cell_w // 2
            cy = row * cell_h + cell_h // 2
            radius = min(cell_w, cell_h) * (0.18 + 0.035 * (row + col))
            g = QRadialGradient(QPointF(cx, cy), radius * 2.4)
            g.setColorAt(0.0, QColor(230, 250, 255, 230))
            g.setColorAt(0.42, QColor(92, 180, 235, 150))
            g.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(g))
            p.drawEllipse(int(cx - radius * 1.7), int(cy - radius * 1.7), int(radius * 3.4), int(radius * 3.4))
            p.setPen(QPen(QColor(190, 240, 255, 170), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2))
    p.setPen(QColor(225, 240, 245))
    font = QFont("Arial", max(18, w // 32))
    font.setBold(True)
    p.setFont(font)
    p.drawText(36, h - 58, "PVAEC CELL EVOLUTION")
    p.setPen(QColor(135, 170, 185))
    p.setFont(QFont("Arial", max(10, w // 70)))
    p.drawText(38, h - 30, "project-generated visual identity")


def main() -> None:
    _ = QApplication(sys.argv)
    project_root = Path(__file__).resolve().parents[1]
    out = project_root / "assets" / "sprites"
    out.mkdir(parents=True, exist_ok=True)
    save_sprite(out, "organism.png", paint_organism)
    save_sprite(out, "central_brain.png", paint_central_brain)
    save_sprite(out, "sensor.png", paint_sensor)
    save_sprite(out, "actuator.png", paint_actuator)
    save_sprite(out, "nutrient.png", paint_nutrient)
    save_sprite(out, "well.png", paint_well)
    save_canvas(project_root / "assets" / "branding", "logo.png", 512, 512, paint_logo)
    save_canvas(project_root / "assets", "未标题-1.png", 1024, 768, paint_brand_sheet)
    SrSpriteCatalog.invalidate_cache()
    print("Regenerated sprites in", out)


if __name__ == "__main__":
    main()
