# -*- coding: utf-8 -*-
"""Capture the QPainter viewport Adapter into Qt-free RGBA evidence."""

from __future__ import annotations

from core.VitaLoom.viewports.qpainter_backend import QPainterViewportBackend
from core.VitaLoom.viewports.viewport_pixel_capture import ViewportPixelCapture
from core.VitaLoom.viewports.viewport_snapshot import ViewportFrameSnapshot


def capture_qpainter_viewport(
    frame: ViewportFrameSnapshot,
    *,
    background_rgba: tuple[int, int, int, int] = (26, 140, 217, 255),
) -> ViewportPixelCapture:
    """Render one immutable frame into a QImage and return plain RGBA bytes."""

    if not isinstance(frame, ViewportFrameSnapshot):
        raise TypeError("capture_qpainter_viewport expects ViewportFrameSnapshot")
    if frame.width < 0 or frame.height < 0:
        raise ValueError("viewport dimensions must be non-negative")

    from PyQt6.QtGui import QColor, QImage, QPainter

    image = QImage(int(frame.width), int(frame.height), QImage.Format.Format_RGBA8888)
    if image.isNull() and (frame.width > 0 and frame.height > 0):
        raise RuntimeError("QPainter capture image is null")
    image.fill(QColor(*background_rgba))

    painter = QPainter(image)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        QPainterViewportBackend().render(painter, frame)
    finally:
        painter.end()

    raw = _tightly_packed_rgba(image)
    return ViewportPixelCapture.from_rgba(
        raw,
        width=int(image.width()),
        height=int(image.height()),
        background_rgba=background_rgba,
        current_context=False,
        fallback_used=False,
        draw_mode="qpainter_qimage",
        gpu_draw_calls=0,
    )


def _tightly_packed_rgba(image: object) -> bytes:
    width = int(image.width())  # type: ignore[attr-defined]
    height = int(image.height())  # type: ignore[attr-defined]
    stride = int(image.bytesPerLine())  # type: ignore[attr-defined]
    pointer = image.constBits()  # type: ignore[attr-defined]
    pointer.setsize(int(image.sizeInBytes()))
    storage = bytes(pointer)
    row_size = width * 4
    if stride == row_size:
        return storage[: row_size * height]
    return b"".join(storage[row * stride : row * stride + row_size] for row in range(height))


__all__ = ["capture_qpainter_viewport"]
