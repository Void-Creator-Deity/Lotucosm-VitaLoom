# -*- coding: utf-8 -*-
"""Qt-free viewport framebuffer capture evidence.

The module deliberately accepts only packed RGBA bytes plus plain metadata. UI
Host Adapters may translate their native image objects at the seam, while tests,
benchmarks, and future replacement Hosts can consume the same deterministic
capture facts without importing Qt or OpenGL types.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable


RGBA = tuple[int, int, int, int]
Bounds = tuple[int, int, int, int]


@dataclass(frozen=True)
class ViewportCaptureEvidence:
    width: int
    height: int
    format: str
    sampled_pixels: int
    non_background_pixels: int
    non_background_ratio: float
    alpha_covered_pixels: int
    alpha_coverage: float
    occupied_bounds: Bounds | None
    digest: str
    background_rgba: RGBA
    current_context: bool
    fallback_used: bool
    draw_mode: str
    gpu_draw_calls: int
    errors: tuple[str, ...]

    @property
    def non_empty(self) -> bool:
        return self.non_background_pixels > 0

    @property
    def ready(self) -> bool:
        """Whether this is strict explicit-OpenGL pixel evidence.

        A non-zero clear colour alone is not evidence. The capture must contain
        pixels that differ from the declared background, come from a current
        context, report at least one GPU draw, avoid fallback, and carry no
        Adapter errors.
        """

        return (
            self.width > 0
            and self.height > 0
            and self.non_empty
            and self.current_context
            and not self.fallback_used
            and self.gpu_draw_calls > 0
            and not self.errors
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "sampled_pixels": self.sampled_pixels,
            "non_background_pixels": self.non_background_pixels,
            "non_background_ratio": self.non_background_ratio,
            "alpha_covered_pixels": self.alpha_covered_pixels,
            "alpha_coverage": self.alpha_coverage,
            "occupied_bounds": list(self.occupied_bounds) if self.occupied_bounds is not None else None,
            "digest": self.digest,
            "background_rgba": list(self.background_rgba),
            "current_context": self.current_context,
            "fallback_used": self.fallback_used,
            "draw_mode": self.draw_mode,
            "gpu_draw_calls": self.gpu_draw_calls,
            "errors": list(self.errors),
            "non_empty": self.non_empty,
            "ready": self.ready,
        }


def analyze_rgba_capture(
    pixels: bytes | bytearray | memoryview,
    *,
    width: int,
    height: int,
    background_rgba: RGBA,
    pixel_format: str = "RGBA8888",
    color_tolerance: int = 2,
    current_context: bool = False,
    fallback_used: bool = False,
    draw_mode: str = "",
    gpu_draw_calls: int = 0,
    errors: Iterable[str] = (),
) -> ViewportCaptureEvidence:
    """Analyze one tightly packed RGBA framebuffer using plain data only."""

    normalized_width = int(width)
    normalized_height = int(height)
    if normalized_width < 0 or normalized_height < 0:
        raise ValueError("capture dimensions must be non-negative")

    normalized_background = _rgba(background_rgba)
    tolerance = int(color_tolerance)
    if tolerance < 0 or tolerance > 255:
        raise ValueError("color_tolerance must be in range 0..255")

    raw = bytes(pixels)
    expected_length = normalized_width * normalized_height * 4
    if len(raw) != expected_length:
        raise ValueError(
            f"RGBA payload length {len(raw)} does not match "
            f"{normalized_width}x{normalized_height} ({expected_length} bytes)"
        )

    non_background_pixels = 0
    alpha_covered_pixels = 0
    min_x: int | None = None
    min_y: int | None = None
    max_x: int | None = None
    max_y: int | None = None

    for index in range(normalized_width * normalized_height):
        offset = index * 4
        pixel = (raw[offset], raw[offset + 1], raw[offset + 2], raw[offset + 3])
        if pixel[3] > 0:
            alpha_covered_pixels += 1
        if any(abs(pixel[channel] - normalized_background[channel]) > tolerance for channel in range(4)):
            non_background_pixels += 1
            x = index % normalized_width
            y = index // normalized_width
            min_x = x if min_x is None else min(min_x, x)
            min_y = y if min_y is None else min(min_y, y)
            max_x = x if max_x is None else max(max_x, x)
            max_y = y if max_y is None else max(max_y, y)

    sampled_pixels = normalized_width * normalized_height
    digest_input = (
        f"{normalized_width}x{normalized_height}:{pixel_format}:".encode("utf-8")
        + bytes(normalized_background)
        + raw
    )
    occupied_bounds = (
        None
        if min_x is None
        else (min_x, min_y if min_y is not None else 0, max_x if max_x is not None else min_x, max_y if max_y is not None else 0)
    )
    normalized_errors = tuple(str(item) for item in errors if str(item))

    return ViewportCaptureEvidence(
        width=normalized_width,
        height=normalized_height,
        format=str(pixel_format),
        sampled_pixels=sampled_pixels,
        non_background_pixels=non_background_pixels,
        non_background_ratio=(non_background_pixels / sampled_pixels if sampled_pixels else 0.0),
        alpha_covered_pixels=alpha_covered_pixels,
        alpha_coverage=(alpha_covered_pixels / sampled_pixels if sampled_pixels else 0.0),
        occupied_bounds=occupied_bounds,
        digest=sha256(digest_input).hexdigest(),
        background_rgba=normalized_background,
        current_context=bool(current_context),
        fallback_used=bool(fallback_used),
        draw_mode=str(draw_mode),
        gpu_draw_calls=max(0, int(gpu_draw_calls)),
        errors=normalized_errors,
    )


def _rgba(value: RGBA) -> RGBA:
    if len(value) != 4:
        raise ValueError("background_rgba must contain exactly four channels")
    channels = tuple(int(channel) for channel in value)
    if any(channel < 0 or channel > 255 for channel in channels):
        raise ValueError("RGBA channels must be in range 0..255")
    return channels  # type: ignore[return-value]


__all__ = [
    "ViewportCaptureEvidence",
    "analyze_rgba_capture",
]