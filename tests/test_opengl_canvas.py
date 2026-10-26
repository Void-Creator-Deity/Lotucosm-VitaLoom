# -*- coding: utf-8 -*-
from __future__ import annotations

from core.VitaLoom.viewports.opengl_canvas import (
    create_opengl_viewport_canvas_class,
    probe_opengl_canvas_interaction_smoke,
)
from core.VitaLoom.viewports import sr_gpu_canvas


class _FakeOpenGLWidget:
    class UpdateBehavior:
        PartialUpdate = "partial"

    def __init__(self, parent=None):
        self.parent = parent
        self.object_name = ""
        self.minimum_size = None
        self.focus_policy = None
        self.update_behavior = None
        self.update_calls = 0

    def setObjectName(self, name: str) -> None:
        self.object_name = name

    def setMinimumSize(self, width: int, height: int) -> None:
        self.minimum_size = (width, height)

    def setFocusPolicy(self, policy) -> None:
        self.focus_policy = policy

    def setUpdateBehavior(self, behavior) -> None:
        self.update_behavior = behavior

    def update(self) -> None:
        self.update_calls += 1


class _Host:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.pressed: list[str] = []
        self.released: list[str] = []

    def _initialize_sr_opengl_canvas(self, canvas) -> None:
        self.calls.append(("initialize", canvas.object_name))

    def _resize_sr_opengl_canvas(self, canvas, width: int, height: int) -> None:
        self.calls.append(("resize", (width, height)))

    def _paint_sr_opengl_canvas(self, canvas) -> None:
        self.calls.append(("paint", canvas.object_name))

    def _sr_input_press(self, key: str) -> None:
        self.pressed.append(key)

    def _sr_input_release(self, key: str) -> None:
        self.released.append(key)


class _KeyEvent:
    def __init__(self, text: str) -> None:
        self._text = text
        self.accepted = False

    def isAutoRepeat(self) -> bool:
        return False

    def text(self) -> str:
        return self._text

    def key(self) -> int:
        return 0

    def accept(self) -> None:
        self.accepted = True


def test_canvas_factory_routes_qopengl_lifecycle_to_host() -> None:
    Canvas = create_opengl_viewport_canvas_class(_FakeOpenGLWidget)
    host = _Host()
    canvas = Canvas(host)

    canvas.initializeGL()
    canvas.resizeGL(640, 360)
    canvas.paintGL()

    assert canvas.object_name == "gameViewportOpenGLCanvas"
    assert canvas.minimum_size == (400, 300)
    assert canvas.update_behavior == "partial"
    assert host.calls == [
        ("initialize", "gameViewportOpenGLCanvas"),
        ("resize", (640, 360)),
        ("paint", "gameViewportOpenGLCanvas"),
    ]
    assert canvas.opengl_lifecycle_snapshot()["paint_calls"] == 1


def test_canvas_forwards_keyboard_input_to_host() -> None:
    Canvas = create_opengl_viewport_canvas_class(_FakeOpenGLWidget)
    host = _Host()
    canvas = Canvas(host)
    press = _KeyEvent("w")
    release = _KeyEvent("w")

    canvas.keyPressEvent(press)
    canvas.keyReleaseEvent(release)

    assert host.pressed == ["W"]
    assert host.released == ["W"]
    assert press.accepted is True
    assert release.accepted is True


def test_canvas_interaction_smoke_reports_resize_and_keyboard_forwarding() -> None:
    result = probe_opengl_canvas_interaction_smoke()

    assert result["target"] == "qt_opengl_canvas_interaction_smoke"
    assert result["resize_event_count"] >= 2
    assert result["keyboard_event_count"] == 2
    assert result["resize_forwarded"] is True
    assert result["keyboard_forwarded"] is True
    assert result["events_forwarded"] is True
    assert result["interaction_ms"] >= 0.0


class _HostWithFallback(_Host):
    _SrCanvas = object


def test_sr_gpu_canvas_returns_fallback_when_opengl_not_requested(monkeypatch) -> None:
    monkeypatch.delenv("VITALOOM_VIEWPORT_BACKEND", raising=False)
    monkeypatch.delenv("VITALOOM_SR_GPU", raising=False)

    canvas_cls = sr_gpu_canvas.create_sr_canvas_class(_HostWithFallback)

    assert canvas_cls is _HostWithFallback._SrCanvas


def test_sr_gpu_canvas_returns_fallback_when_qopenglwidget_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("VITALOOM_VIEWPORT_BACKEND", "opengl")
    monkeypatch.setattr(sr_gpu_canvas, "_open_gl_probe_done", True)
    monkeypatch.setattr(sr_gpu_canvas, "_OPENGL_WIDGET", None)

    canvas_cls = sr_gpu_canvas.create_sr_canvas_class(_HostWithFallback)

    assert canvas_cls is _HostWithFallback._SrCanvas


def test_sr_gpu_canvas_delegates_explicit_opengl_to_lifecycle_factory(monkeypatch) -> None:
    monkeypatch.setenv("VITALOOM_VIEWPORT_BACKEND", "opengl")
    monkeypatch.setattr(sr_gpu_canvas, "_open_gl_probe_done", True)
    monkeypatch.setattr(sr_gpu_canvas, "_OPENGL_WIDGET", _FakeOpenGLWidget)

    Canvas = sr_gpu_canvas.create_sr_canvas_class(_HostWithFallback)
    host = _HostWithFallback()
    canvas = Canvas(host)
    canvas.initializeGL()
    canvas.paintGL()

    assert canvas.object_name == "gameViewportOpenGLCanvas"
    assert canvas.opengl_lifecycle_snapshot()["initialize_calls"] == 1
    assert canvas.opengl_lifecycle_snapshot()["paint_calls"] == 1
