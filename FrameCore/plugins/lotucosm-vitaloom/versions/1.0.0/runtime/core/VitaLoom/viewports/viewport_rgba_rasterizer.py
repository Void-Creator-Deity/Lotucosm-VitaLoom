# -*- coding: utf-8 -*-
"""Deterministic Qt-free RGBA rasterization for viewport OpenGL batches.

This is a compatibility Implementation for the current OpenGL Host Adapter: it
turns the existing immutable batch facts into pixels that can be uploaded to a
current GL context. It is intentionally not described as native geometry
acceleration; the benchmark policy remains responsible for keeping it opt-in.
"""

from __future__ import annotations

from math import ceil, floor, hypot
from typing import Iterable

from core.VitaLoom.viewports.opengl_batching import OpenGLBatch


RGBA = tuple[int, int, int, int]


def rasterize_opengl_batches(
    batches: Iterable[OpenGLBatch],
    *,
    width: int,
    height: int,
    background_rgba: RGBA,
) -> bytes:
    """Rasterize batches into tightly packed top-left-origin RGBA8888 bytes."""

    normalized_width = max(0, int(width))
    normalized_height = max(0, int(height))
    background = _rgba(background_rgba)
    pixels = bytearray(bytes(background) * (normalized_width * normalized_height))
    if normalized_width == 0 or normalized_height == 0:
        return bytes(pixels)

    for batch in batches:
        if batch.primitive == "circle":
            _draw_circle_batch(pixels, normalized_width, normalized_height, batch)
        elif batch.primitive == "line":
            _draw_line_batch(pixels, normalized_width, normalized_height, batch)
        # Text remains an explicit overlay requirement. The current draw-command
        # compiler does not emit text for the representative L0-L4 scene seam.
    return bytes(pixels)


def _draw_circle_batch(pixels: bytearray, width: int, height: int, batch: OpenGLBatch) -> None:
    _primitive, fill_value, stroke_value, stroke_width_value = batch.style_key
    fill = _rgba(fill_value)
    stroke = _rgba(stroke_value)
    stroke_width = max(0.0, float(stroke_width_value))

    for instance in batch.instances:
        center_x = float(instance[0])
        center_y = float(instance[1])
        radius = max(0.0, float(instance[2]))
        if radius <= 0.0:
            continue
        min_x = max(0, int(floor(center_x - radius)))
        min_y = max(0, int(floor(center_y - radius)))
        max_x = min(width - 1, int(ceil(center_x + radius) - 1))
        max_y = min(height - 1, int(ceil(center_y + radius) - 1))
        stroke_start = max(0.0, radius - stroke_width)

        for y in range(min_y, max_y + 1):
            sample_y = y + 0.5 - center_y
            for x in range(min_x, max_x + 1):
                distance = hypot(x + 0.5 - center_x, sample_y)
                if distance > radius:
                    continue
                color = stroke if stroke_width > 0.0 and distance >= stroke_start else fill
                if color[3] > 0:
                    _blend_pixel(pixels, width, x, y, color)


def _draw_line_batch(pixels: bytearray, width: int, height: int, batch: OpenGLBatch) -> None:
    _primitive, color_value, line_width_value = batch.style_key
    color = _rgba(color_value)
    if color[3] <= 0:
        return
    radius = max(0.5, float(line_width_value) / 2.0)

    for instance in batch.instances:
        x1 = float(instance[0])
        y1 = float(instance[1])
        x2 = float(instance[2])
        y2 = float(instance[3])
        min_x = max(0, int(floor(min(x1, x2) - radius)))
        min_y = max(0, int(floor(min(y1, y2) - radius)))
        max_x = min(width - 1, int(ceil(max(x1, x2) + radius) - 1))
        max_y = min(height - 1, int(ceil(max(y1, y2) + radius) - 1))

        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if _point_segment_distance(x + 0.5, y + 0.5, x1, y1, x2, y2) <= radius:
                    _blend_pixel(pixels, width, x, y, color)


def _point_segment_distance(
    px: float,
    py: float,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
) -> float:
    dx = x2 - x1
    dy = y2 - y1
    length_squared = dx * dx + dy * dy
    if length_squared <= 0.0:
        return hypot(px - x1, py - y1)
    projection = ((px - x1) * dx + (py - y1) * dy) / length_squared
    clamped = max(0.0, min(1.0, projection))
    closest_x = x1 + clamped * dx
    closest_y = y1 + clamped * dy
    return hypot(px - closest_x, py - closest_y)


def _blend_pixel(pixels: bytearray, width: int, x: int, y: int, source: RGBA) -> None:
    offset = (y * width + x) * 4
    source_alpha = source[3] / 255.0
    inverse_alpha = 1.0 - source_alpha
    destination_alpha = pixels[offset + 3] / 255.0
    output_alpha = source_alpha + destination_alpha * inverse_alpha

    if output_alpha <= 0.0:
        pixels[offset : offset + 4] = b"\x00\x00\x00\x00"
        return

    for channel in range(3):
        source_component = source[channel] / 255.0
        destination_component = pixels[offset + channel] / 255.0
        premultiplied = (
            source_component * source_alpha
            + destination_component * destination_alpha * inverse_alpha
        )
        pixels[offset + channel] = _byte(premultiplied / output_alpha)
    pixels[offset + 3] = _byte(output_alpha)


def _byte(value: float) -> int:
    return max(0, min(255, int(round(value * 255.0))))


def _rgba(value: object) -> RGBA:
    try:
        channels = tuple(int(channel) for channel in value)  # type: ignore[union-attr]
    except (TypeError, ValueError) as exc:
        raise ValueError("RGBA value must be an iterable of four integers") from exc
    if len(channels) != 4 or any(channel < 0 or channel > 255 for channel in channels):
        raise ValueError("RGBA channels must contain four values in range 0..255")
    return channels  # type: ignore[return-value]


__all__ = ["rasterize_opengl_batches"]