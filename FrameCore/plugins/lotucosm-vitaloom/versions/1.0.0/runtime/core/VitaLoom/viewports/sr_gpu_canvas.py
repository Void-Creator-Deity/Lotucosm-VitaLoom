# -*- coding: utf-8 -*-
"""Compatibility wrapper for the optional SR OpenGL canvas path."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Optional, Type

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.viewports.opengl_canvas import create_opengl_viewport_canvas_class
from core.VitaLoom.viewports.sr_visual_state import sr_gpu_render_requested

logger = get_logger("SrGpuCanvas")

_OPENGL_WIDGET: Optional[Type[Any]] = None
_open_gl_probe_done = False


def _probe_opengl_widget() -> Optional[Type[Any]]:
    global _OPENGL_WIDGET, _open_gl_probe_done
    if _open_gl_probe_done:
        return _OPENGL_WIDGET
    _open_gl_probe_done = True
    try:
        from PyQt6.QtOpenGLWidgets import QOpenGLWidget

        _OPENGL_WIDGET = QOpenGLWidget
    except ImportError:
        _OPENGL_WIDGET = None
    return _OPENGL_WIDGET


def create_sr_canvas_class(host_cls: type) -> type:
    """Return the default SR canvas or the opt-in OpenGL lifecycle canvas."""

    if not _opengl_viewport_requested():
        return host_cls._SrCanvas
    if _probe_opengl_widget() is None:
        logger.warning("VITALOOM OpenGL canvas requested but QtOpenGLWidgets is unavailable; using QWidget canvas")
        return host_cls._SrCanvas

    opengl_widget = _OPENGL_WIDGET
    assert opengl_widget is not None
    logger.info("SR canvas enabled OpenGL backend through QOpenGLWidget")
    return create_opengl_viewport_canvas_class(opengl_widget)


def _opengl_viewport_requested() -> bool:
    mode = os.environ.get("VITALOOM_VIEWPORT_BACKEND", "").strip().lower()
    return mode == "opengl" or sr_gpu_render_requested()
