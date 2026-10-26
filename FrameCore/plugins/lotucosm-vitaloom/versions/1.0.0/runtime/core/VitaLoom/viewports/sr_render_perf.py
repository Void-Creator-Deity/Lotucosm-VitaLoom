# -*- coding: utf-8 -*-
"""SR 渲染性能：背景缓存、质量档位、Cosmos 跳过开关。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap


@dataclass(frozen=True)
class SrRenderQuality:
    membrane_segments: int = 44
    cilia_count: int = 5
    lipid_dots: int = 14
    signal_dots_max: int = 4
    antialiasing: bool = True
    cache_background: bool = True
    skip_cosmos_in_sr: bool = True


def sr_render_quality() -> SrRenderQuality:
    raw = os.environ.get("VITALOOM_SR_QUALITY", "med").strip().lower()
    if raw in ("low", "fast", "lite"):
        return SrRenderQuality(
            membrane_segments=20,
            cilia_count=3,
            lipid_dots=0,
            signal_dots_max=2,
            antialiasing=False,
            cache_background=True,
            skip_cosmos_in_sr=True,
        )
    if raw in ("high", "hq"):
        return SrRenderQuality(
            membrane_segments=40,
            cilia_count=5,
            lipid_dots=12,
            signal_dots_max=5,
            antialiasing=True,
            cache_background=True,
            skip_cosmos_in_sr=True,
        )
    return SrRenderQuality(
        membrane_segments=44,
        cilia_count=5,
        lipid_dots=14,
        signal_dots_max=4,
        antialiasing=True,
        cache_background=True,
        skip_cosmos_in_sr=True,
    )


def sr_skip_cosmos_update() -> bool:
    return sr_render_quality().skip_cosmos_in_sr


class SrBackgroundCache:
    """深空背景缓存（尺寸变化或 scene_time 整秒变化时刷新）。"""

    def __init__(self) -> None:
        self._pixmap: Optional[QPixmap] = None
        self._w = 0
        self._h = 0
        self._time_bucket = -1

    def invalidate(self) -> None:
        self._pixmap = None
        self._time_bucket = -1

    def paint(
        self,
        painter: QPainter,
        width: int,
        height: int,
        scene_time: float,
        paint_fn,
        *,
        enabled: bool = True,
    ) -> None:
        if not enabled or width <= 0 or height <= 0:
            paint_fn(painter, width, height, scene_time)
            return
        bucket = int(scene_time * 0.5)
        if (
            self._pixmap is None
            or self._w != width
            or self._h != height
            or self._time_bucket != bucket
        ):
            self._pixmap = QPixmap(width, height)
            self._pixmap.fill(Qt.GlobalColor.transparent)
            p = QPainter(self._pixmap)
            try:
                if not sr_render_quality().antialiasing:
                    p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
                paint_fn(p, width, height, scene_time)
            finally:
                p.end()
            self._w, self._h, self._time_bucket = width, height, bucket
        painter.drawPixmap(0, 0, self._pixmap)
