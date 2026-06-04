# -*- coding: utf-8 -*-
"""SR 画布 GPU 可选后端：VITALOOM_SR_GPU=1 时尝试 OpenGL 合成，失败回退 QWidget。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Type

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.viewports.sr_visual_state import sr_gpu_render_requested

if TYPE_CHECKING:
    from core.VitaLoom.viewports.game_viewport import GameViewport

logger = get_logger("SrGpuCanvas")

_OPENGL_WIDGET: Optional[Type[QWidget]] = None
_open_gl_probe_done = False


def _probe_opengl_widget() -> Optional[Type[QWidget]]:
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
    """按环境变量返回 _SrCanvas 或 _SrGpuCanvas 类。"""
    if not sr_gpu_render_requested():
        return host_cls._SrCanvas
    if _probe_opengl_widget() is None:
        logger.warning("VITALOOM_SR_GPU=1 但未找到 QtOpenGLWidgets，回退 CPU 画布")
        return host_cls._SrCanvas

    OGL = _OPENGL_WIDGET
    assert OGL is not None

    class _SrGpuCanvas(OGL):  # type: ignore[misc, valid-type]
        """OpenGL 画布：paintGL 内 QPainter（Qt GPU 合成）；后续可在此加 shader 粒子。"""

        def __init__(self, host: "GameViewport"):
            super().__init__(host)
            self._host = host
            self.setObjectName("gameViewportCanvas")
            self.setMinimumSize(400, 300)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setUpdateBehavior(OGL.UpdateBehavior.PartialUpdate)

        def paintGL(self) -> None:
            from PyQt6.QtGui import QPainter

            painter = QPainter(self)
            try:
                self._host._paint_sr_canvas(self, None)
            finally:
                painter.end()

        def keyPressEvent(self, event) -> None:
            if event is None or event.isAutoRepeat():
                return
            from core.VitaLoom.viewports.sr_input_state import key_from_qt_event

            k = key_from_qt_event(event)
            if k:
                self._host._sr_input_press(k)
            event.accept()

        def keyReleaseEvent(self, event) -> None:
            if event is None or event.isAutoRepeat():
                return
            from core.VitaLoom.viewports.sr_input_state import key_from_qt_event

            k = key_from_qt_event(event)
            if k:
                self._host._sr_input_release(k)
            event.accept()

    logger.info("SR 画布已启用 OpenGL 后端（VITALOOM_SR_GPU=1）")
    return _SrGpuCanvas
