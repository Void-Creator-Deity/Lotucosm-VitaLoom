# -*- coding: utf-8 -*-
"""OpenGL viewport backend metadata for the QWidget bridge phase."""

from __future__ import annotations

from typing import Any

from core.VitaLoom.viewports.opengl_batching import compile_opengl_batches
from core.VitaLoom.viewports.viewport_draw_commands import compile_viewport_draw_commands
from core.VitaLoom.viewports.viewport_backend import ViewportBackendInfo
from core.VitaLoom.viewports.viewport_snapshot import ViewportFrameSnapshot


class OpenGLViewportBackend:
    info = ViewportBackendInfo(
        name="opengl",
        supports_gpu=True,
        supports_batching=True,
        fallback_reason="OpenGL is opt-in until QPainter/OpenGL default-switch evidence exists.",
    )

    def __init__(self) -> None:
        self._width = 0
        self._height = 0
        self._quality: dict[str, Any] = {}
        self._render_calls = 0
        self._last_command_count = 0
        self._last_batch_count = 0
        self._last_instance_count = 0
        self._last_first_command = ""
        self._last_target_snapshot: dict[str, Any] | None = None

    def render(self, target: Any, frame: Any) -> None:
        if not isinstance(frame, ViewportFrameSnapshot):
            raise TypeError("OpenGLViewportBackend.render expects ViewportFrameSnapshot")
        self._width = int(frame.width)
        self._height = int(frame.height)
        self._render_calls += 1
        commands = compile_viewport_draw_commands(frame)
        batches = compile_opengl_batches(commands)
        self._last_command_count = len(commands)
        self._last_batch_count = len(batches)
        self._last_instance_count = sum(batch.instance_count for batch in batches)
        self._last_first_command = _describe_first_command(commands[0]) if commands else ""
        resize_target = getattr(target, "resize", None)
        if callable(resize_target):
            resize_target(self._width, self._height)
        draw_batches = getattr(target, "draw_opengl_batches", None)
        if callable(draw_batches):
            draw_batches(batches)
            snapshot = getattr(target, "snapshot", None)
            self._last_target_snapshot = snapshot() if callable(snapshot) else None
        else:
            self._last_target_snapshot = None

    def resize(self, width: int, height: int) -> None:
        self._width = int(width)
        self._height = int(height)

    def set_quality(self, quality: dict[str, Any]) -> None:
        self._quality = dict(quality)

    def stats(self) -> dict[str, Any]:
        return {
            "backend": self.info.name,
            "available": True,
            "supports_gpu": self.info.supports_gpu,
            "supports_batching": self.info.supports_batching,
            "selection_only": False,
            "opengl_parity_ready": True,
            "opengl_batching_ready": True,
            "default_switch_allowed": False,
            "width": self._width,
            "height": self._height,
            "quality": dict(self._quality),
            "render_calls": self._render_calls,
            "last_command_count": self._last_command_count,
            "last_batch_count": self._last_batch_count,
            "last_instance_count": self._last_instance_count,
            "last_first_command": self._last_first_command,
            "last_target_snapshot": self._last_target_snapshot,
        }


def _describe_first_command(command: Any) -> str:
    kind = str(getattr(command, "kind", ""))
    if kind == "line":
        return f"line:{getattr(command, 'edge_id', '')}"
    if kind == "circle":
        return f"circle:{getattr(command, 'entity_id', '')}"
    if kind == "text":
        return f"text:{getattr(command, 'text_id', '')}"
    return kind


__all__ = ["OpenGLViewportBackend"]
