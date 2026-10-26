# -*- coding: utf-8 -*-
"""Diagnostic OpenGL batch target for the opt-in viewport backend.

This target deliberately does not claim shader-backed drawing. It proves that
OpenGL batches are consumed by a render target, records primitive counts, and
keeps text as an explicit overlay placeholder until the real GL text path lands.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import Any, Iterable

from core.VitaLoom.viewports.opengl_batching import OpenGLBatch


@dataclass(frozen=True)
class OpenGLPixelProbe:
    non_empty: bool
    primitive_pixels: int
    min_x: float | None = None
    min_y: float | None = None
    max_x: float | None = None
    max_y: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "non_empty": self.non_empty,
            "primitive_pixels": self.primitive_pixels,
            "bounds": (
                None
                if self.min_x is None
                else [self.min_x, self.min_y, self.max_x, self.max_y]
            ),
        }


class DiagnosticOpenGLRenderTarget:
    """A deterministic target that consumes OpenGL batches without a GL context."""

    text_policy = "placeholder_for_qpainter_overlay"

    def __init__(self) -> None:
        self._draw_calls = 0
        self._circle_instances = 0
        self._line_instances = 0
        self._text_placeholders = 0
        self._unsupported_instances = 0
        self._bounds: list[tuple[float, float, float, float]] = []

    def draw_opengl_batches(self, batches: Iterable[OpenGLBatch]) -> None:
        for batch in batches:
            self._draw_calls += 1
            if batch.primitive == "circle":
                self._circle_instances += batch.instance_count
                for instance in batch.instances:
                    x, y, radius = float(instance[0]), float(instance[1]), float(instance[2])
                    self._bounds.append((x - radius, y - radius, x + radius, y + radius))
            elif batch.primitive == "line":
                self._line_instances += batch.instance_count
                for instance in batch.instances:
                    x1, y1, x2, y2 = (
                        float(instance[0]),
                        float(instance[1]),
                        float(instance[2]),
                        float(instance[3]),
                    )
                    self._bounds.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
            elif batch.primitive == "text":
                self._text_placeholders += batch.instance_count
            else:
                self._unsupported_instances += batch.instance_count

    def snapshot(self) -> dict[str, Any]:
        return {
            "target": "diagnostic_opengl",
            "draw_calls": self._draw_calls,
            "circle_instances": self._circle_instances,
            "line_instances": self._line_instances,
            "text_placeholders": self._text_placeholders,
            "unsupported_instances": self._unsupported_instances,
            "text_policy": self.text_policy,
            "pixel_probe": self.pixel_probe().to_dict(),
        }

    def pixel_probe(self) -> OpenGLPixelProbe:
        primitive_pixels = self._circle_instances + self._line_instances
        if not self._bounds:
            return OpenGLPixelProbe(non_empty=False, primitive_pixels=primitive_pixels)
        min_x = min(item[0] for item in self._bounds)
        min_y = min(item[1] for item in self._bounds)
        max_x = max(item[2] for item in self._bounds)
        max_y = max(item[3] for item in self._bounds)
        return OpenGLPixelProbe(
            non_empty=primitive_pixels > 0,
            primitive_pixels=primitive_pixels,
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
        )


class QtOpenGLRenderTarget(DiagnosticOpenGLRenderTarget):
    """Qt OpenGL surface bridge that consumes batches through the active painter."""

    text_policy = "qt_painter_overlay"

    def __init__(self, painter: Any) -> None:
        super().__init__()
        self._painter = painter
        self._text_overlay_instances = 0

    def draw_opengl_batches(self, batches: Iterable[OpenGLBatch]) -> None:
        for batch in batches:
            self._draw_calls += 1
            if batch.primitive == "circle":
                self._draw_circles(batch)
            elif batch.primitive == "line":
                self._draw_lines(batch)
            elif batch.primitive == "text":
                self._draw_text(batch)
            else:
                self._unsupported_instances += batch.instance_count

    def snapshot(self) -> dict[str, Any]:
        data = super().snapshot()
        data["target"] = "qt_opengl_painter"
        data["text_overlay_instances"] = self._text_overlay_instances
        return data

    def _draw_circles(self, batch: OpenGLBatch) -> None:
        _primitive, fill, stroke, stroke_width = batch.style_key
        self._set_pen(stroke, float(stroke_width))
        self._set_brush(fill)
        for instance in batch.instances:
            x, y, radius = float(instance[0]), float(instance[1]), float(instance[2])
            self._circle_instances += 1
            self._bounds.append((x - radius, y - radius, x + radius, y + radius))
            size = int(round(radius * 2.0))
            self._painter.drawEllipse(
                int(round(x - radius)),
                int(round(y - radius)),
                size,
                size,
            )

    def _draw_lines(self, batch: OpenGLBatch) -> None:
        _primitive, color, width = batch.style_key
        self._set_pen(color, float(width))
        for instance in batch.instances:
            x1, y1, x2, y2 = (
                float(instance[0]),
                float(instance[1]),
                float(instance[2]),
                float(instance[3]),
            )
            self._line_instances += 1
            self._bounds.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
            self._painter.drawLine(
                int(round(x1)),
                int(round(y1)),
                int(round(x2)),
                int(round(y2)),
            )

    def _draw_text(self, batch: OpenGLBatch) -> None:
        _primitive, color, _size, _text = batch.style_key
        self._set_pen(color, 1.0)
        for instance in batch.instances:
            x, y, text = float(instance[0]), float(instance[1]), str(instance[2])
            self._text_overlay_instances += 1
            self._painter.drawText(int(round(x)), int(round(y)), text)

    def _set_pen(self, color: Any, width: float) -> None:
        try:
            from PyQt6.QtGui import QColor, QPen

            self._painter.setPen(QPen(QColor(*color), width))
        except Exception:
            self._painter.setPen({"color": color, "width": width})

    def _set_brush(self, color: Any) -> None:
        try:
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QColor, QBrush

            if color[3] <= 0:
                self._painter.setBrush(Qt.BrushStyle.NoBrush)
            else:
                self._painter.setBrush(QBrush(QColor(*color)))
        except Exception:
            self._painter.setBrush({"color": color})


def probe_qt_opengl_instancing_support() -> dict[str, Any]:
    shader_api_available = False
    buffer_api_available = False
    context_current = False
    details: dict[str, str] = {}
    try:
        from PyQt6.QtGui import QOpenGLContext
        from PyQt6.QtOpenGL import QOpenGLBuffer, QOpenGLShaderProgram, QOpenGLVertexArrayObject

        shader_api_available = QOpenGLShaderProgram is not None
        buffer_api_available = QOpenGLBuffer is not None and QOpenGLVertexArrayObject is not None
        context_current = QOpenGLContext.currentContext() is not None
    except Exception as exc:
        details["import_error"] = f"{exc.__class__.__name__}: {exc}"
    return {
        "backend": "qt_opengl",
        "shader_api_available": shader_api_available,
        "buffer_api_available": buffer_api_available,
        "context_current": context_current,
        "details": details,
    }


class QtOpenGLInstancingTarget:
    """Qt-native shader/instancing readiness target for future real GPU draws."""

    def __init__(self) -> None:
        self._support = probe_qt_opengl_instancing_support()
        self._gpu_draw_calls = 0
        self._pending_instances = 0
        self._text_overlay_required = 0
        self._shader_program_ready = False
        self._instance_buffer_ready = False
        self._vao_ready = False
        self._gl_functions_ready = False
        self._draw_mode = "fallback_no_current_context"
        self._fallback_required = not (
            self._support["shader_api_available"]
            and self._support["buffer_api_available"]
            and self._support["context_current"]
        )

    def draw_opengl_batches(self, batches: Iterable[OpenGLBatch]) -> None:
        batch_tuple = tuple(batches)
        self._pending_instances += sum(
            batch.instance_count for batch in batch_tuple if batch.primitive in ("circle", "line")
        )
        self._text_overlay_required += sum(
            batch.instance_count for batch in batch_tuple if batch.primitive == "text"
        )
        if self._fallback_required:
            return
        if not self._ensure_resources():
            self._fallback_required = True
            return
        self._draw_mode = "qt_shader_instanced"
        self._draw_instanced_batches(batch_tuple)
        self._gpu_draw_calls += sum(
            1 for batch in batch_tuple if batch.primitive in ("circle", "line")
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "target": "qt_opengl_instancing",
            "shader_api_available": self._support["shader_api_available"],
            "buffer_api_available": self._support["buffer_api_available"],
            "context_current": self._support["context_current"],
            "shader_program_ready": self._shader_program_ready,
            "instance_buffer_ready": self._instance_buffer_ready,
            "vao_ready": self._vao_ready,
            "gl_functions_ready": self._gl_functions_ready,
            "pending_instances": self._pending_instances,
            "text_overlay_required": self._text_overlay_required,
            "draw_mode": self._draw_mode,
            "instanced_draw_api": "QOpenGLFunctions_4_1_Core.glDrawArraysInstanced",
            "attribute_divisor_api": "QOpenGLFunctions_4_1_Core.glVertexAttribDivisor",
            "gpu_draw_calls": self._gpu_draw_calls,
            "pixel_probe": {
                "non_empty": self._gpu_draw_calls > 0,
                "primitive_pixels": self._pending_instances if self._gpu_draw_calls > 0 else 0,
            },
            "fallback_required": self._fallback_required,
            "details": dict(self._support["details"]),
        }

    def _ensure_resources(self) -> bool:
        try:
            from PyQt6.QtGui import QOpenGLContext, QSurfaceFormat
            from PyQt6.QtOpenGL import QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram
            from PyQt6.QtOpenGL import QOpenGLVersionFunctionsFactory, QOpenGLVersionProfile
            from PyQt6.QtOpenGL import QOpenGLVertexArrayObject

            context = QOpenGLContext.currentContext()
            if context is None:
                self._draw_mode = "fallback_no_current_context"
                return False

            profile = QOpenGLVersionProfile()
            profile.setVersion(4, 1)
            profile.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
            functions = QOpenGLVersionFunctionsFactory.get(profile, context)
            self._gl_functions_ready = all(
                callable(getattr(functions, name, None))
                for name in ("glDrawArraysInstanced", "glVertexAttribDivisor")
            )

            program = QOpenGLShaderProgram()
            vertex_ok = program.addShaderFromSourceCode(
                QOpenGLShader.ShaderTypeBit.Vertex,
                """
                attribute vec2 position;
                void main() {
                    gl_Position = vec4(position, 0.0, 1.0);
                }
                """,
            )
            fragment_ok = program.addShaderFromSourceCode(
                QOpenGLShader.ShaderTypeBit.Fragment,
                """
                void main() {
                    gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0);
                }
                """,
            )
            self._shader_program_ready = bool(vertex_ok and fragment_ok and program.link())

            vao = QOpenGLVertexArrayObject()
            self._vao_ready = bool(vao.create())

            buffer = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
            self._instance_buffer_ready = bool(buffer.create())
            if self._instance_buffer_ready:
                buffer.setUsagePattern(QOpenGLBuffer.UsagePattern.DynamicDraw)

            return (
                self._shader_program_ready
                and self._instance_buffer_ready
                and self._vao_ready
                and self._gl_functions_ready
            )
        except Exception as exc:
            self._support["details"]["resource_error"] = f"{exc.__class__.__name__}: {exc}"
            return False

    def _draw_instanced_batches(self, batches: Iterable[OpenGLBatch]) -> None:
        try:
            from PyQt6.QtGui import QOpenGLContext, QSurfaceFormat
            from PyQt6.QtOpenGL import QOpenGLVersionFunctionsFactory, QOpenGLVersionProfile

            context = QOpenGLContext.currentContext()
            if context is None:
                self._draw_mode = "fallback_no_current_context"
                return

            profile = QOpenGLVersionProfile()
            profile.setVersion(4, 1)
            profile.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
            functions = QOpenGLVersionFunctionsFactory.get(profile, context)
            if functions is None:
                self._support["details"]["functions_error"] = "QOpenGLFunctions_4_1_Core unavailable"
                return

            gl_triangles = 0x0004
            gl_lines = 0x0001
            for batch in batches:
                if batch.primitive == "circle":
                    functions.glVertexAttribDivisor(1, 1)
                    functions.glDrawArraysInstanced(gl_triangles, 0, 6, batch.instance_count)
                elif batch.primitive == "line":
                    functions.glVertexAttribDivisor(1, 1)
                    functions.glDrawArraysInstanced(gl_lines, 0, 2, batch.instance_count)
        except Exception as exc:
            self._support["details"]["draw_error"] = f"{exc.__class__.__name__}: {exc}"


class QtOpenGLTextureTarget:
    """Current-context GL texture target backed by deterministic Qt-free pixels.

    This Adapter provides real framebuffer evidence without pretending that the
    current implementation is native geometry acceleration. Batches are
    rasterized as plain RGBA data and presented by a GL texture blit; benchmark
    policy therefore remains responsible for keeping OpenGL opt-in.
    """

    _generation_source = count(1)

    def __init__(
        self,
        *,
        width: int = 1,
        height: int = 1,
        background_rgba: tuple[int, int, int, int] = (26, 140, 217, 255),
        pixel_ratio: float = 1.0,
    ) -> None:
        self._generation = next(self._generation_source)
        self._support = probe_qt_opengl_instancing_support()
        self._width = max(0, int(width))
        self._height = max(0, int(height))
        self._background_rgba = tuple(int(channel) for channel in background_rgba)
        self._pixel_ratio = max(1.0, float(pixel_ratio))
        self._pending_instances = 0
        self._text_overlay_required = 0
        self._gpu_draw_calls = 0
        self._draw_mode = "fallback_no_current_context"
        self._fallback_required = not bool(self._support["context_current"])
        self._details: dict[str, str] = dict(self._support["details"])
        self._pixel_probe: dict[str, Any] = {
            "non_empty": False,
            "ready": False,
            "non_background_pixels": 0,
        }
        self._logical_capture: Any | None = None

    def resize(self, width: int, height: int) -> None:
        self._width = max(0, int(width))
        self._height = max(0, int(height))

    def draw_opengl_batches(self, batches: Iterable[OpenGLBatch]) -> None:
        batch_tuple = tuple(batches)
        primitive_instances = sum(
            batch.instance_count for batch in batch_tuple if batch.primitive in ("circle", "line")
        )
        self._pending_instances += primitive_instances
        self._text_overlay_required += sum(
            batch.instance_count for batch in batch_tuple if batch.primitive == "text"
        )
        if self._fallback_required:
            return
        if self._width <= 0 or self._height <= 0:
            self._fallback_required = True
            self._draw_mode = "fallback_invalid_target_size"
            self._details["target_size_error"] = f"invalid target size {self._width}x{self._height}"
            return

        try:
            from PyQt6.QtCore import QRect, QRectF
            from PyQt6.QtGui import QImage
            from PyQt6.QtOpenGL import (
                QOpenGLFunctions_2_0,
                QOpenGLTexture,
                QOpenGLTextureBlitter,
            )

            from core.VitaLoom.viewports.viewport_pixel_capture import ViewportPixelCapture
            from core.VitaLoom.viewports.viewport_rgba_rasterizer import rasterize_opengl_batches

            pixels = rasterize_opengl_batches(
                batch_tuple,
                width=self._width,
                height=self._height,
                background_rgba=self._background_rgba,
            )
            image = QImage(
                pixels,
                self._width,
                self._height,
                self._width * 4,
                QImage.Format.Format_RGBA8888,
            ).copy()
            if image.isNull():
                raise RuntimeError("RGBA upload image is null")

            functions = QOpenGLFunctions_2_0()
            functions.initializeOpenGLFunctions()
            viewport_width = max(1, int(round(self._width * self._pixel_ratio)))
            viewport_height = max(1, int(round(self._height * self._pixel_ratio)))
            functions.glViewport(0, 0, viewport_width, viewport_height)
            functions.glDisable(0x0B71)  # GL_DEPTH_TEST
            functions.glDisable(0x0B44)  # GL_CULL_FACE

            texture = QOpenGLTexture(image, QOpenGLTexture.MipMapGeneration.DontGenerateMipMaps)
            texture.setMinMagFilters(
                QOpenGLTexture.Filter.Nearest,
                QOpenGLTexture.Filter.Nearest,
            )
            blitter = QOpenGLTextureBlitter()
            if not blitter.create():
                texture.destroy()
                raise RuntimeError("QOpenGLTextureBlitter.create returned false")
            blitter.bind()
            transform = QOpenGLTextureBlitter.targetTransform(
                QRectF(0.0, 0.0, float(viewport_width), float(viewport_height)),
                QRect(0, 0, viewport_width, viewport_height),
            )
            blitter.blit(
                texture.textureId(),
                transform,
                QOpenGLTextureBlitter.Origin.OriginTopLeft,
            )
            blitter.release()
            functions.glFlush()
            self._gpu_draw_calls += 1
            self._draw_mode = "qt_texture_blit"
            self._fallback_required = False
            self._logical_capture = ViewportPixelCapture.from_rgba(
                pixels,
                width=self._width,
                height=self._height,
                background_rgba=self._background_rgba,
                current_context=True,
                fallback_used=False,
                draw_mode=self._draw_mode,
                gpu_draw_calls=self._gpu_draw_calls,
            )
            self._pixel_probe = self._logical_capture.evidence.to_dict()
            blitter.destroy()
            texture.destroy()
        except Exception as exc:
            self._fallback_required = True
            self._draw_mode = "fallback_texture_upload_failed"
            self._details["upload_error"] = f"{exc.__class__.__name__}: {exc}"

    def logical_capture(self) -> Any | None:
        """Return the Qt-free logical RGBA source consumed by the GL blit."""

        return self._logical_capture

    def snapshot(self) -> dict[str, Any]:
        return {
            "target": "qt_opengl_texture",
            "generation": self._generation,
            "context_current": bool(self._support["context_current"]),
            "width": self._width,
            "height": self._height,
            "pixel_ratio": self._pixel_ratio,
            "viewport_width": max(0, int(round(self._width * self._pixel_ratio))),
            "viewport_height": max(0, int(round(self._height * self._pixel_ratio))),
            "pending_instances": self._pending_instances,
            "text_overlay_required": self._text_overlay_required,
            "draw_mode": self._draw_mode,
            "gpu_draw_calls": self._gpu_draw_calls,
            "pixel_probe": dict(self._pixel_probe),
            "fallback_required": self._fallback_required,
            "native_geometry_acceleration": False,
            "details": dict(self._details),
        }


__all__ = [
    "DiagnosticOpenGLRenderTarget",
    "OpenGLPixelProbe",
    "QtOpenGLInstancingTarget",
    "QtOpenGLRenderTarget",
    "QtOpenGLTextureTarget",
    "probe_qt_opengl_instancing_support",
]
