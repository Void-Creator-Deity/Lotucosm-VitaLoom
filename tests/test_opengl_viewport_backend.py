# -*- coding: utf-8 -*-
from __future__ import annotations

from core.VitaLoom.viewports.opengl_backend import OpenGLViewportBackend
from core.VitaLoom.viewports.viewport_snapshot import (
    ViewportEdgeSnapshot,
    ViewportEntitySnapshot,
    ViewportFrameSnapshot,
)


def _frame() -> ViewportFrameSnapshot:
    return ViewportFrameSnapshot(
        width=320,
        height=240,
        entities=(
            ViewportEntitySnapshot(id="a", entity_type="organism", position=(10.0, 20.0), radius=5.0),
            ViewportEntitySnapshot(id="b", entity_type="nutrient", position=(30.0, 40.0), radius=6.0),
        ),
        edges=(ViewportEdgeSnapshot(source_id="a", target_id="b", kind="hard"),),
    )


def test_opengl_backend_compiles_commands_and_batches_without_gl_context() -> None:
    backend = OpenGLViewportBackend()

    backend.render(object(), _frame())

    stats = backend.stats()
    assert stats["backend"] == "opengl"
    assert stats["supports_gpu"] is True
    assert stats["supports_batching"] is True
    assert stats["last_command_count"] == 3
    assert stats["last_batch_count"] == 3
    assert stats["last_instance_count"] == 3
    assert stats["render_calls"] == 1


def test_opengl_backend_sends_batches_to_explicit_target() -> None:
    class _Target:
        def __init__(self) -> None:
            self.batches = None

        def draw_opengl_batches(self, batches: object) -> None:
            self.batches = batches

    target = _Target()
    backend = OpenGLViewportBackend()

    backend.render(target, _frame())

    assert target.batches is not None
    assert backend.stats()["last_batch_count"] == len(target.batches)
