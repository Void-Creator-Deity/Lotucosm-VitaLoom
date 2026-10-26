# -*- coding: utf-8 -*-
"""Select the viewport rendering backend without changing default behavior."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from core.VitaLoom.viewports.opengl_backend import OpenGLViewportBackend
from core.VitaLoom.viewports.qpainter_backend import QPainterViewportBackend
from core.VitaLoom.viewports.viewport_backend import ViewportBackendInfo


VALID_VIEWPORT_BACKENDS = ("qpainter", "opengl", "rhi", "auto")


@dataclass(frozen=True)
class ViewportBackendSelection:
    requested: str
    backend: Any
    info: ViewportBackendInfo


class UnavailableViewportBackend:
    def __init__(self, info: ViewportBackendInfo) -> None:
        self.info = info

    def render(self, target: Any, frame: Any) -> None:
        raise RuntimeError(self.info.fallback_reason)

    def resize(self, width: int, height: int) -> None:
        return None

    def set_quality(self, quality: dict[str, Any]) -> None:
        return None

    def stats(self) -> dict[str, Any]:
        return {
            "backend": self.info.name,
            "available": False,
            "supports_gpu": self.info.supports_gpu,
            "supports_batching": self.info.supports_batching,
            "fallback_reason": self.info.fallback_reason,
        }


def select_viewport_backend(
    requested: str | None = None,
    *,
    renderer: Any | None = None,
    environ: dict[str, str] | None = None,
) -> ViewportBackendSelection:
    env = environ if environ is not None else os.environ
    mode = (requested or env.get("VITALOOM_VIEWPORT_BACKEND") or "auto").strip().lower()
    if mode not in VALID_VIEWPORT_BACKENDS:
        raise ValueError("VITALOOM_VIEWPORT_BACKEND must be qpainter|opengl|rhi|auto")

    if mode == "auto":
        backend = QPainterViewportBackend(renderer=renderer)
        return ViewportBackendSelection(
            requested="auto",
            backend=backend,
            info=ViewportBackendInfo(
                name="qpainter",
                supports_gpu=False,
                supports_batching=False,
                fallback_reason=(
                    "auto keeps QPainter until comparable end-to-end benchmark evidence "
                    "and native geometry readiness satisfy the default-switch policy"
                ),
            ),
        )

    if mode == "qpainter":
        backend = QPainterViewportBackend(renderer=renderer)
        return ViewportBackendSelection("qpainter", backend, backend.info)

    if mode == "opengl":
        if not is_opengl_viewport_available():
            info = ViewportBackendInfo(
                name="opengl",
                supports_gpu=False,
                supports_batching=False,
                fallback_reason="QtOpenGLWidgets is unavailable; use QPainter fallback",
            )
            return ViewportBackendSelection("opengl", UnavailableViewportBackend(info), info)
        backend = OpenGLViewportBackend()
        return ViewportBackendSelection("opengl", backend, backend.info)

    info = ViewportBackendInfo(
        name="rhi",
        supports_gpu=False,
        supports_batching=False,
        fallback_reason="future RHI/native backend target; no runtime implementation yet",
    )
    return ViewportBackendSelection("rhi", UnavailableViewportBackend(info), info)


def is_opengl_viewport_available() -> bool:
    try:
        from core.VitaLoom.viewports.sr_gpu_canvas import _probe_opengl_widget

        return _probe_opengl_widget() is not None
    except Exception:
        return False


__all__ = [
    "UnavailableViewportBackend",
    "VALID_VIEWPORT_BACKENDS",
    "ViewportBackendSelection",
    "is_opengl_viewport_available",
    "select_viewport_backend",
]

