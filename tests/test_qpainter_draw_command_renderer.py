# -*- coding: utf-8 -*-
from __future__ import annotations

from core.VitaLoom.viewports.qpainter_backend import (
    QPainterDrawCommandRenderer,
    QPainterViewportBackend,
)
from core.VitaLoom.viewports.viewport_draw_commands import CircleCommand
from core.VitaLoom.viewports.viewport_snapshot import (
    ViewportEdgeSnapshot,
    ViewportEntitySnapshot,
    ViewportFrameSnapshot,
)


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


def test_qpainter_draw_command_renderer_records_expected_primitives() -> None:
    painter = _Painter()
    renderer = QPainterDrawCommandRenderer()
    frame = ViewportFrameSnapshot(
        width=200,
        height=120,
        entities=(
            ViewportEntitySnapshot(id="a", entity_type="organism", position=(10.0, 20.0), radius=5.0),
            ViewportEntitySnapshot(id="b", entity_type="nutrient", position=(30.0, 40.0), radius=6.0),
        ),
        edges=(ViewportEdgeSnapshot(source_id="a", target_id="b", kind="hard"),),
    )

    renderer.render_frame(painter, frame)

    names = [name for name, _args in painter.calls]
    assert names.count("drawLine") == 1
    assert names.count("drawEllipse") == 2
    assert ("drawLine", (10, 20, 30, 40)) in painter.calls


def test_qpainter_backend_accepts_snapshot_command_path() -> None:
    painter = _Painter()
    backend = QPainterViewportBackend()
    frame = ViewportFrameSnapshot(
        width=200,
        height=120,
        entities=(
            ViewportEntitySnapshot(id="a", entity_type="organism", position=(10.0, 20.0), radius=5.0),
        ),
    )

    backend.render(painter, frame)

    assert any(name == "drawEllipse" for name, _args in painter.calls)
    assert backend.stats()["render_calls"] == 1
    assert backend.stats()["command_render_calls"] == 1


def test_qpainter_renderer_reuses_style_objects_for_matching_commands() -> None:
    painter = _Painter()
    renderer = QPainterDrawCommandRenderer()
    commands = (
        CircleCommand(
            kind="circle",
            entity_id="a",
            center=(10.0, 20.0),
            radius=5.0,
            fill=(120, 160, 220, 255),
            stroke=(20, 30, 40, 255),
            stroke_width=1.5,
        ),
        CircleCommand(
            kind="circle",
            entity_id="b",
            center=(30.0, 40.0),
            radius=6.0,
            fill=(120, 160, 220, 255),
            stroke=(20, 30, 40, 255),
            stroke_width=1.5,
        ),
    )

    renderer.render_commands(painter, commands)

    pens = [args[0] for name, args in painter.calls if name == "setPen"]
    brushes = [args[0] for name, args in painter.calls if name == "setBrush"]
    assert pens[0] is pens[1]
    assert brushes[0] is brushes[1]
