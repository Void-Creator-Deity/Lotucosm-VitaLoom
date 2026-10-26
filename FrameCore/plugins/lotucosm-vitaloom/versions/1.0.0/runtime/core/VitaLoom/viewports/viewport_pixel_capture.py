# -*- coding: utf-8 -*-
"""Qt-free RGBA pixel capture value used by viewport Adapter evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.VitaLoom.viewports.viewport_capture_evidence import (
    RGBA,
    ViewportCaptureEvidence,
    analyze_rgba_capture,
)


@dataclass(frozen=True)
class ViewportPixelCapture:
    """One tightly packed RGBA frame plus its plain-data evidence."""

    width: int
    height: int
    format: str
    pixels: bytes
    evidence: ViewportCaptureEvidence

    @classmethod
    def from_rgba(
        cls,
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
    ) -> "ViewportPixelCapture":
        raw = bytes(pixels)
        evidence = analyze_rgba_capture(
            raw,
            width=width,
            height=height,
            background_rgba=background_rgba,
            pixel_format=pixel_format,
            color_tolerance=color_tolerance,
            current_context=current_context,
            fallback_used=fallback_used,
            draw_mode=draw_mode,
            gpu_draw_calls=gpu_draw_calls,
            errors=errors,
        )
        return cls(
            width=evidence.width,
            height=evidence.height,
            format=evidence.format,
            pixels=raw,
            evidence=evidence,
        )

    def summary(self) -> dict[str, object]:
        return {
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "byte_length": len(self.pixels),
            "evidence": self.evidence.to_dict(),
        }


__all__ = ["ViewportPixelCapture"]
