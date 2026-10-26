# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Any

from PyQt6.QtWidgets import QApplication

from core.VitaLoom.viewports.qpainter_backend import (
    QPainterViewportBackend,
    QPainterViewportFrame,
)

_QT_APP: QApplication | None = None


class _Renderer:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, int, int, dict[str, Any]]] = []

    def paint_frame(self, painter: Any, width: int, height: int, **kwargs: Any) -> None:
        self.calls.append((painter, width, height, kwargs))


class _Entity:
    id = "hub"
    entity_type = "organism"
    position = (1.0, 2.0)
    velocity = (0.0, 0.0)
    radius = 12.0


def test_qpainter_backend_delegates_to_existing_renderer() -> None:
    renderer = _Renderer()
    backend = QPainterViewportBackend(renderer=renderer)
    entity = _Entity()
    frame = QPainterViewportFrame(
        width=640,
        height=360,
        entities=[entity],
        structural_edges=[("hub", "sensor")],
        signal_edges=[{"source": "hub", "target": "sensor"}],
        connection_edges=[{"source": "hub", "target": "sensor", "link_kind": "soft"}],
        spring_links=[("hub", "sensor")],
        scene_time=2.5,
        demo_legend={"title": "demo"},
        show_legend=True,
        session_banner={"kind": "victory"},
        sprite_catalog="catalog",
        game_mode=True,
        game_fx={"sparks": []},
        game_player_id="player",
        emissions_prev={"hub": 0.2},
        niche_pressure=0.4,
    )

    backend.render("painter", frame)

    painter, width, height, kwargs = renderer.calls[0]
    assert painter == "painter"
    assert width == 640
    assert height == 360
    assert kwargs["entities"] == [entity]
    assert kwargs["structural_edges"] == [("hub", "sensor")]
    assert kwargs["signal_edges"] == [{"source": "hub", "target": "sensor"}]
    assert kwargs["connection_edges"] == [{"source": "hub", "target": "sensor", "link_kind": "soft"}]
    assert kwargs["spring_links"] == [("hub", "sensor")]
    assert kwargs["scene_time"] == 2.5
    assert kwargs["demo_legend"] == {"title": "demo"}
    assert kwargs["show_legend"] is True
    assert kwargs["session_banner"] == {"kind": "victory"}
    assert kwargs["sprite_catalog"] == "catalog"
    assert kwargs["game_mode"] is True
    assert kwargs["game_fx"] == {"sparks": []}
    assert kwargs["game_player_id"] == "player"
    assert kwargs["emissions_prev"] == {"hub": 0.2}
    assert kwargs["niche_pressure"] == 0.4
    assert backend.stats()["render_calls"] == 1


def test_game_viewport_delegates_scene_runtime_painting_to_backend(monkeypatch: Any) -> None:
    global _QT_APP
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _QT_APP = QApplication.instance() or QApplication([])

    import core.VitaLoom.viewports.game_viewport as game_viewport

    class _FakePainter:
        class RenderHint:
            Antialiasing = object()

        def __init__(self, canvas: Any) -> None:
            self.canvas = canvas
            self.ended = False

        def setRenderHint(self, *_args: Any, **_kwargs: Any) -> None:
            return None

        def end(self) -> None:
            self.ended = True

    class _Canvas:
        def width(self) -> int:
            return 320

        def height(self) -> int:
            return 180

    class _Backend:
        def __init__(self) -> None:
            self.calls: list[tuple[Any, QPainterViewportFrame]] = []

        def render(self, target: Any, frame: QPainterViewportFrame) -> None:
            self.calls.append((target, frame))

    monkeypatch.setattr(game_viewport, "QPainter", _FakePainter)
    viewport = game_viewport.GameViewport()
    backend = _Backend()
    entity = _Entity()
    viewport._viewport_backend = backend
    viewport._using_scene_runtime = True
    viewport.is_playing = False
    viewport.scene_runtime_entities = [entity]
    viewport._scene_runtime_edges = [("hub", "sensor")]
    viewport._sr_signal_edges = [{"source": "hub", "target": "sensor"}]
    viewport._sr_connection_edges = []
    viewport._sr_spring_links = []

    viewport._paint_sr_canvas(_Canvas(), None)

    painter, frame = backend.calls[0]
    assert isinstance(painter, _FakePainter)
    assert painter.ended is True
    assert frame.width == 320
    assert frame.height == 180
    assert frame.entities == [entity]
    assert frame.structural_edges == [("hub", "sensor")]
    assert frame.signal_edges == [{"source": "hub", "target": "sensor"}]


def test_game_viewport_uses_backend_strategy_for_explicit_opengl(monkeypatch: Any) -> None:
    global _QT_APP
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _QT_APP = QApplication.instance() or QApplication([])

    import core.VitaLoom.viewports.game_viewport as game_viewport

    class _Backend:
        info = type("Info", (), {"name": "opengl"})()

        def stats(self) -> dict[str, object]:
            return {"backend": "opengl"}

    class _Selection:
        requested = "opengl"
        backend = _Backend()
        info = _Backend.info

    monkeypatch.setattr(game_viewport, "select_viewport_backend", lambda **kwargs: _Selection())

    viewport = game_viewport.GameViewport()

    assert viewport._viewport_backend is _Selection.backend


def test_game_viewport_renders_explicit_opengl_backend_with_snapshot_target(monkeypatch: Any) -> None:
    global _QT_APP
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _QT_APP = QApplication.instance() or QApplication([])

    import core.VitaLoom.viewports.game_viewport as game_viewport
    from core.VitaLoom.viewports.opengl_backend import OpenGLViewportBackend

    class _FakePainter:
        class RenderHint:
            Antialiasing = object()

        def __init__(self, canvas: Any) -> None:
            self.canvas = canvas
            self.ended = False

        def setRenderHint(self, *_args: Any, **_kwargs: Any) -> None:
            return None

        def setPen(self, _value: object) -> None:
            return None

        def setBrush(self, _value: object) -> None:
            return None

        def drawEllipse(self, *_args: Any) -> None:
            return None

        def drawLine(self, *_args: Any) -> None:
            return None

        def end(self) -> None:
            self.ended = True

    class _Canvas:
        def width(self) -> int:
            return 320

        def height(self) -> int:
            return 180

    monkeypatch.setattr(game_viewport, "QPainter", _FakePainter)
    viewport = game_viewport.GameViewport()
    viewport._viewport_backend = OpenGLViewportBackend()
    entity = _Entity()
    viewport._using_scene_runtime = True
    viewport.is_playing = False
    viewport.scene_runtime_entities = [entity]
    viewport._scene_runtime_edges = []
    viewport._sr_signal_edges = []
    viewport._sr_connection_edges = []
    viewport._sr_spring_links = []

    viewport._paint_sr_canvas(_Canvas(), None)

    stats = viewport._viewport_backend.stats()
    assert stats["last_command_count"] == 1
    assert stats["last_target_snapshot"]["circle_instances"] == 1
    assert stats["last_target_snapshot"]["pixel_probe"]["non_empty"] is True
