# -*- coding: utf-8 -*-
from __future__ import annotations

from core.VitaLoom.viewports.opengl_batching import compile_opengl_batches
from core.VitaLoom.viewports.opengl_render_target import (
    DiagnosticOpenGLRenderTarget,
    QtOpenGLInstancingTarget,
    QtOpenGLRenderTarget,
    probe_qt_opengl_instancing_support,
)
from core.VitaLoom.viewports.viewport_draw_commands import (
    CircleCommand,
    LineCommand,
    TextCommand,
)


def test_diagnostic_opengl_render_target_consumes_circle_and_line_batches() -> None:
    commands = (
        CircleCommand(
            kind="circle",
            entity_id="a",
            center=(10.0, 20.0),
            radius=5.0,
            fill=(120, 210, 245, 220),
            stroke=(205, 245, 255, 230),
        ),
        LineCommand(
            kind="line",
            edge_id="a:b",
            start=(10.0, 20.0),
            end=(30.0, 40.0),
            color=(120, 155, 205, 180),
            width=2.0,
        ),
        TextCommand(
            kind="text",
            text_id="label:a",
            position=(10.0, 20.0),
            text="A",
            color=(255, 255, 255, 255),
        ),
    )
    target = DiagnosticOpenGLRenderTarget()

    target.draw_opengl_batches(compile_opengl_batches(commands))

    snapshot = target.snapshot()
    assert snapshot["draw_calls"] == 3
    assert snapshot["circle_instances"] == 1
    assert snapshot["line_instances"] == 1
    assert snapshot["text_placeholders"] == 1
    assert snapshot["unsupported_instances"] == 0
    assert snapshot["pixel_probe"]["non_empty"] is True


def test_diagnostic_opengl_render_target_exposes_clear_placeholder_policy() -> None:
    target = DiagnosticOpenGLRenderTarget()
    batches = compile_opengl_batches(
        [
            TextCommand(
                kind="text",
                text_id="label:a",
                position=(2.0, 3.0),
                text="A",
                color=(255, 255, 255, 255),
            )
        ]
    )

    target.draw_opengl_batches(batches)

    snapshot = target.snapshot()
    assert snapshot["text_policy"] == "placeholder_for_qpainter_overlay"
    assert snapshot["text_placeholders"] == 1


class _Painter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def setPen(self, value: object) -> None:
        self.calls.append(("setPen", (value,)))

    def setBrush(self, value: object) -> None:
        self.calls.append(("setBrush", (value,)))

    def drawEllipse(self, x: int, y: int, width: int, height: int) -> None:
        self.calls.append(("drawEllipse", (x, y, width, height)))

    def drawLine(self, x1: int, y1: int, x2: int, y2: int) -> None:
        self.calls.append(("drawLine", (x1, y1, x2, y2)))

    def drawText(self, x: int, y: int, text: str) -> None:
        self.calls.append(("drawText", (x, y, text)))


def test_qt_opengl_render_target_consumes_batches_with_qpainter_surface() -> None:
    commands = (
        CircleCommand(
            kind="circle",
            entity_id="a",
            center=(10.0, 20.0),
            radius=5.0,
            fill=(120, 210, 245, 220),
            stroke=(205, 245, 255, 230),
        ),
        LineCommand(
            kind="line",
            edge_id="a:b",
            start=(10.0, 20.0),
            end=(30.0, 40.0),
            color=(120, 155, 205, 180),
            width=2.0,
        ),
    )
    painter = _Painter()
    target = QtOpenGLRenderTarget(painter)

    target.draw_opengl_batches(compile_opengl_batches(commands))

    snapshot = target.snapshot()
    assert snapshot["target"] == "qt_opengl_painter"
    assert snapshot["draw_calls"] == 2
    assert snapshot["circle_instances"] == 1
    assert snapshot["line_instances"] == 1
    assert ("drawEllipse", (5, 15, 10, 10)) in painter.calls
    assert ("drawLine", (10, 20, 30, 40)) in painter.calls
    assert snapshot["pixel_probe"]["non_empty"] is True


def test_qt_opengl_render_target_draws_text_as_overlay_not_placeholder() -> None:
    commands = (
        TextCommand(
            kind="text",
            text_id="label:a",
            position=(10.0, 20.0),
            text="A",
            color=(255, 255, 255, 255),
        ),
    )
    painter = _Painter()
    target = QtOpenGLRenderTarget(painter)

    target.draw_opengl_batches(compile_opengl_batches(commands))

    snapshot = target.snapshot()
    assert snapshot["text_policy"] == "qt_painter_overlay"
    assert snapshot["text_placeholders"] == 0
    assert snapshot["text_overlay_instances"] == 1
    assert ("drawText", (10, 20, "A")) in painter.calls


def test_qt_opengl_instancing_probe_reports_shader_api() -> None:
    support = probe_qt_opengl_instancing_support()

    assert support["backend"] == "qt_opengl"
    assert "shader_api_available" in support
    assert "buffer_api_available" in support
    assert "context_current" in support


def test_qt_opengl_instancing_target_reports_unavailable_without_context() -> None:
    target = QtOpenGLInstancingTarget()

    target.draw_opengl_batches(())

    snapshot = target.snapshot()
    assert snapshot["target"] == "qt_opengl_instancing"
    assert snapshot["shader_api_available"] is True
    assert snapshot["context_current"] is False
    assert snapshot["shader_program_ready"] is False
    assert snapshot["instance_buffer_ready"] is False
    assert snapshot["gl_functions_ready"] is False
    assert snapshot["draw_mode"] == "fallback_no_current_context"
    assert snapshot["gpu_draw_calls"] == 0
    assert snapshot["fallback_required"] is True


def test_qt_opengl_instancing_target_counts_pending_instances_without_context() -> None:
    commands = (
        CircleCommand(
            kind="circle",
            entity_id="a",
            center=(10.0, 20.0),
            radius=5.0,
            fill=(120, 210, 245, 220),
            stroke=(205, 245, 255, 230),
        ),
        LineCommand(
            kind="line",
            edge_id="a:b",
            start=(10.0, 20.0),
            end=(30.0, 40.0),
            color=(120, 155, 205, 180),
            width=2.0,
        ),
        TextCommand(
            kind="text",
            text_id="label:a",
            position=(10.0, 20.0),
            text="A",
            color=(255, 255, 255, 255),
        ),
    )
    target = QtOpenGLInstancingTarget()

    target.draw_opengl_batches(compile_opengl_batches(commands))

    snapshot = target.snapshot()
    assert snapshot["pending_instances"] == 2
    assert snapshot["text_overlay_required"] == 1
    assert snapshot["gpu_draw_calls"] == 0
    assert snapshot["pixel_probe"]["non_empty"] is False


def test_qt_opengl_instancing_target_exposes_instanced_draw_seam() -> None:
    target = QtOpenGLInstancingTarget()

    snapshot = target.snapshot()

    assert snapshot["instanced_draw_api"] == "QOpenGLFunctions_4_1_Core.glDrawArraysInstanced"
    assert snapshot["attribute_divisor_api"] == "QOpenGLFunctions_4_1_Core.glVertexAttribDivisor"
