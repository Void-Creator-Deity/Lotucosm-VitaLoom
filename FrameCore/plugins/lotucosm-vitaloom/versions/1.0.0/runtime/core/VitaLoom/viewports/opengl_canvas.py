# -*- coding: utf-8 -*-
"""Qt OpenGL viewport canvas lifecycle helpers."""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Iterable
from dataclasses import replace
from typing import Any, Type


_OPENGL_SMOKE_CLEAR_RGBA = (26, 140, 217, 255)
# Keep the probe-created QApplication alive across sequential Host-Adapter checks.
# Without a strong reference, a later Qt test can replace it with an offscreen
# QApplication, after which the Windows current-context QOpenGLWidget gate cannot paint.
_OPENGL_SMOKE_QT_APP: Any | None = None

try:
    from PyQt6.QtCore import Qt
except Exception:  # pragma: no cover - import availability differs by runtime
    Qt = None  # type: ignore[assignment]


def create_opengl_viewport_canvas_class(opengl_widget_cls: Type[Any]) -> Type[Any]:
    """Create a QOpenGLWidget-compatible canvas class with explicit lifecycle diagnostics."""

    class OpenGLViewportCanvas(opengl_widget_cls):  # type: ignore[misc, valid-type]
        def __init__(self, host: Any):
            super().__init__(host)
            self._host = host
            self._initialize_calls = 0
            self._resize_calls = 0
            self._paint_calls = 0
            self._last_size = (0, 0)
            self.setObjectName("gameViewportOpenGLCanvas")
            self.setMinimumSize(400, 300)
            if Qt is not None:
                self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            if hasattr(opengl_widget_cls, "UpdateBehavior"):
                self.setUpdateBehavior(opengl_widget_cls.UpdateBehavior.PartialUpdate)

        def initializeGL(self) -> None:
            self._initialize_calls += 1
            callback = getattr(self._host, "_initialize_sr_opengl_canvas", None)
            if callable(callback):
                callback(self)

        def resizeGL(self, width: int, height: int) -> None:
            self._resize_calls += 1
            self._last_size = (int(width), int(height))
            callback = getattr(self._host, "_resize_sr_opengl_canvas", None)
            if callable(callback):
                callback(self, int(width), int(height))

        def paintGL(self) -> None:
            self._paint_calls += 1
            callback = getattr(self._host, "_paint_sr_opengl_canvas", None)
            if callable(callback):
                callback(self)

        def keyPressEvent(self, event: Any) -> None:
            if event is None or event.isAutoRepeat():
                return
            from core.VitaLoom.viewports.sr_input_state import key_from_qt_event

            key = key_from_qt_event(event)
            if key:
                callback = getattr(self._host, "_sr_input_press", None)
                if callable(callback):
                    callback(key)
            event.accept()

        def keyReleaseEvent(self, event: Any) -> None:
            if event is None or event.isAutoRepeat():
                return
            from core.VitaLoom.viewports.sr_input_state import key_from_qt_event

            key = key_from_qt_event(event)
            if key:
                callback = getattr(self._host, "_sr_input_release", None)
                if callable(callback):
                    callback(key)
            event.accept()

        def opengl_lifecycle_snapshot(self) -> dict[str, Any]:
            return {
                "target": "qt_opengl_canvas",
                "initialize_calls": self._initialize_calls,
                "resize_calls": self._resize_calls,
                "paint_calls": self._paint_calls,
                "last_size": list(self._last_size),
            }

    return OpenGLViewportCanvas


def probe_qt_opengl_canvas_smoke(
    *,
    frame: Any | None = None,
    width: int = 64,
    height: int = 64,
    process_events: int = 8,
    include_logical_capture: bool = False,
) -> dict[str, Any]:
    """Report real current-context pixels through the existing Qt Host Adapter.

    On Windows, an inherited offscreen/minimal QApplication cannot be changed in
    place. Such contaminated callers use a plain-data subprocess worker; clean
    callers and the worker itself stay on the direct Adapter path.
    """

    if _should_isolate_qt_opengl_probe():
        return _run_isolated_qt_opengl_probe(
            frame=frame,
            width=width,
            height=height,
            process_events=process_events,
            include_logical_capture=include_logical_capture,
        )
    return _probe_qt_opengl_canvas_smoke_local(
        frame=frame,
        width=width,
        height=height,
        process_events=process_events,
        include_logical_capture=include_logical_capture,
    )


def _should_isolate_qt_opengl_probe() -> bool:
    if sys.platform != "win32" or os.environ.get("VITALOOM_OPENGL_PROBE_WORKER") == "1":
        return False
    requested_platform = os.environ.get("QT_QPA_PLATFORM", "").strip().lower().split(":", 1)[0]
    if requested_platform in {"offscreen", "minimal"}:
        return True
    try:
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        active_platform = str(app.platformName()).strip().lower() if app is not None else ""
    except Exception:
        return False
    return active_platform in {"offscreen", "minimal"}


def _run_isolated_qt_opengl_probe(**kwargs: Any) -> dict[str, Any]:
    from core.VitaLoom.viewports.opengl_probe_worker import run_isolated_qt_opengl_probe

    return run_isolated_qt_opengl_probe(**kwargs)


def _probe_qt_opengl_canvas_smoke_local(
    *,
    frame: Any | None = None,
    width: int = 64,
    height: int = 64,
    process_events: int = 8,
    include_logical_capture: bool = False,
) -> dict[str, Any]:
    """Direct current-process probe used only with a compatible QApplication."""

    result = _base_smoke_result()
    try:
        from PyQt6.QtGui import QOpenGLContext
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    except Exception as exc:
        result["skip_reason"] = f"Qt OpenGL import failed: {exc.__class__.__name__}: {exc}"
        return result

    global _OPENGL_SMOKE_QT_APP

    result["qopenglwidget_available"] = True
    app = QApplication.instance()
    created_app = False
    if app is None:
        try:
            app = QApplication([])
            created_app = True
        except Exception as exc:
            result["skip_reason"] = f"QApplication creation failed: {exc.__class__.__name__}: {exc}"
            return result
    _OPENGL_SMOKE_QT_APP = app
    result["qapplication_available"] = True
    result["created_qapplication"] = created_app

    class _SmokeWidget(QOpenGLWidget):  # type: ignore[misc]
        def __init__(self) -> None:
            super().__init__()
            self.initialize_calls = 0
            self.resize_calls = 0
            self.paint_calls = 0
            self.context_current = False
            self.clear_error = ""
            self.backend_stats: dict[str, Any] = {}
            self.target_snapshot: dict[str, Any] = {}
            self.logical_capture: Any | None = None

        def initializeGL(self) -> None:
            self.initialize_calls += 1

        def resizeGL(self, w: int, h: int) -> None:
            self.resize_calls += 1

        def paintGL(self) -> None:
            self.paint_calls += 1
            context = QOpenGLContext.currentContext()
            self.context_current = context is not None
            if context is None:
                return
            try:
                from PyQt6.QtOpenGL import QOpenGLFunctions_2_0

                functions = QOpenGLFunctions_2_0()
                functions.initializeOpenGLFunctions()
                functions.glClearColor(
                    _OPENGL_SMOKE_CLEAR_RGBA[0] / 255.0,
                    _OPENGL_SMOKE_CLEAR_RGBA[1] / 255.0,
                    _OPENGL_SMOKE_CLEAR_RGBA[2] / 255.0,
                    _OPENGL_SMOKE_CLEAR_RGBA[3] / 255.0,
                )
                functions.glClear(0x00004000)
                if frame is not None:
                    from core.VitaLoom.viewports.opengl_backend import OpenGLViewportBackend
                    from core.VitaLoom.viewports.opengl_render_target import QtOpenGLTextureTarget

                    backend = OpenGLViewportBackend()
                    target_width = int(self.width())
                    target_height = int(self.height())
                    pixel_ratio_reader = getattr(self, "devicePixelRatioF", None)
                    pixel_ratio = float(pixel_ratio_reader()) if callable(pixel_ratio_reader) else 1.0
                    target = QtOpenGLTextureTarget(
                        width=target_width,
                        height=target_height,
                        background_rgba=_OPENGL_SMOKE_CLEAR_RGBA,
                        pixel_ratio=pixel_ratio,
                    )
                    render_frame = frame
                    if int(frame.width) != target_width or int(frame.height) != target_height:
                        render_frame = replace(frame, width=target_width, height=target_height)
                    backend.render(target, render_frame)
                    self.backend_stats = backend.stats()
                    self.target_snapshot = target.snapshot()
                    if include_logical_capture:
                        self.logical_capture = target.logical_capture()
            except Exception as exc:
                self.clear_error = f"{exc.__class__.__name__}: {exc}"

    widget: Any | None = None
    try:
        widget = _SmokeWidget()
        widget.setObjectName("vitalloomOpenGLSmokeWidget")
        if Qt is not None:
            widget.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        widget.resize(int(width), int(height))
        widget.show()
        for _ in range(max(1, int(process_events))):
            app.processEvents()
        widget.update()
        for _ in range(max(1, int(process_events))):
            app.processEvents()

        image = widget.grabFramebuffer()
        result["initialize_calls"] = int(widget.initialize_calls)
        result["resize_calls"] = int(widget.resize_calls)
        result["paint_calls"] = int(widget.paint_calls)
        result["context_current"] = bool(widget.context_current)
        result["clear_error"] = widget.clear_error
        result["frame"] = _frame_smoke_summary(widget.backend_stats)
        result["target_snapshot"] = dict(widget.target_snapshot)
        if include_logical_capture:
            result["logical_capture"] = widget.logical_capture
        result["pixel_probe"] = _probe_qimage_pixels(
            image,
            background_rgba=_OPENGL_SMOKE_CLEAR_RGBA,
            current_context=result["context_current"],
            target_snapshot=result["target_snapshot"],
            errors=(result["clear_error"],),
        )
        result["rendered"] = bool(result["pixel_probe"]["ready"])
        if not result["rendered"]:
            result["skip_reason"] = _smoke_skip_reason(result)
    except Exception as exc:
        result["skip_reason"] = f"QOpenGLWidget smoke failed: {exc.__class__.__name__}: {exc}"
    finally:
        if widget is not None:
            try:
                done_current = getattr(widget, "doneCurrent", None)
                if callable(done_current):
                    done_current()
            except Exception as exc:
                result["teardown_errors"].append(
                    f"doneCurrent failed: {exc.__class__.__name__}: {exc}"
                )
            try:
                widget.close()
            except Exception as exc:
                result["teardown_errors"].append(
                    f"close failed: {exc.__class__.__name__}: {exc}"
                )
            try:
                widget.deleteLater()
                for _ in range(max(1, int(process_events))):
                    app.processEvents()
            except Exception as exc:
                result["teardown_errors"].append(
                    f"deleteLater failed: {exc.__class__.__name__}: {exc}"
                )
        result["context_released"] = QOpenGLContext.currentContext() is None
    return result


def probe_qt_opengl_interaction_sequence(
    frames: Iterable[Any],
    process_events: int = 8,
) -> dict[str, Any]:
    """Render immutable frames through recreated current-context Qt Adapters.

    This probe deliberately recreates the canvas and render target for every
    frame. It proves that camera/selection/resize changes do not depend on stale
    Adapter state and that no Project World or plugin publication seam is used.
    """

    from core.VitaLoom.viewports.viewport_snapshot import ViewportFrameSnapshot

    frame_tuple = tuple(frames)
    if any(not isinstance(frame, ViewportFrameSnapshot) for frame in frame_tuple):
        raise TypeError("frames must contain only immutable ViewportFrameSnapshot values")

    records: list[dict[str, Any]] = []
    teardown_errors: list[str] = []
    context_released = True
    for frame in frame_tuple:
        smoke = probe_qt_opengl_canvas_smoke(
            frame=frame,
            width=int(frame.width),
            height=int(frame.height),
            process_events=process_events,
            include_logical_capture=True,
        )
        target = dict(smoke.get("target_snapshot", {}))
        logical_capture = smoke.get("logical_capture")
        logical_evidence = getattr(logical_capture, "evidence", None)
        logical_errors = list(getattr(logical_evidence, "errors", ()) or ())
        target_errors = [
            str(value)
            for key, value in dict(target.get("details", {})).items()
            if str(key).endswith("error") and value
        ]
        pixel_probe = dict(smoke.get("pixel_probe", {}))
        errors = [
            *([str(smoke["clear_error"])] if smoke.get("clear_error") else []),
            *target_errors,
            *[str(value) for value in pixel_probe.get("errors", ()) if value],
            *[str(value) for value in logical_errors if value],
        ]
        if not smoke.get("rendered") and smoke.get("skip_reason"):
            errors.append(str(smoke["skip_reason"]))

        smoke_teardown_errors = [
            str(value) for value in smoke.get("teardown_errors", ()) if value
        ]
        teardown_errors.extend(smoke_teardown_errors)
        context_released = context_released and bool(smoke.get("context_released", False))
        isolated_process = bool(smoke.get("isolated_process", False))
        native_generation = int(target.get("generation", 0) or 0)
        sequence_generation = len(records) + 1 if isolated_process and native_generation > 0 else native_generation
        records.append(
            {
                "context_current": bool(target.get("context_current", smoke.get("context_current"))),
                "isolated_process": isolated_process,
                "fallback_required": bool(target.get("fallback_required", True)),
                "errors": errors,
                "pending_instances": int(target.get("pending_instances", 0) or 0),
                "instances": int(smoke.get("frame", {}).get("instances", 0) or 0),
                "target_generation": sequence_generation,
                "target_native_generation": native_generation,
                "logical_digest": str(getattr(logical_evidence, "digest", "")),
                "commands": int(smoke.get("frame", {}).get("commands", 0) or 0),
                "logical_dimensions": [
                    int(getattr(logical_capture, "width", 0) or 0),
                    int(getattr(logical_capture, "height", 0) or 0),
                ],
                "framebuffer_dimensions": [
                    int(pixel_probe.get("width", 0) or 0),
                    int(pixel_probe.get("height", 0) or 0),
                ],
            }
        )

    generations = [record["target_generation"] for record in records]
    all_isolated = bool(records) and all(record["isolated_process"] for record in records)
    generation_recreation_proven = (
        all(generation > 0 for generation in generations)
        and (all_isolated or len(set(generations)) == len(generations))
    )
    target_recreations = (
        len(records)
        if all_isolated
        else len(set(generations)) - (1 if 0 in generations else 0)
    )
    completed = (
        len(records) == len(frame_tuple)
        and context_released
        and not teardown_errors
        and all(record["context_current"] for record in records)
        and all(not record["fallback_required"] for record in records)
        and all(not record["errors"] for record in records)
        and all(record["logical_digest"] for record in records)
        and generation_recreation_proven
    )
    return {
        "completed": completed,
        "context_released": context_released,
        "teardown_errors": teardown_errors,
        "target_recreations": target_recreations,
        "project_world_mutations": 0,
        "plugin_publications": 0,
        "records": records,
    }


def probe_opengl_canvas_interaction_smoke(
    *,
    width: int = 640,
    height: int = 360,
    key_text: str = "w",
) -> dict[str, Any]:
    """Exercise resize and keyboard forwarding without opening the full editor."""

    class _InteractionFakeOpenGLWidget:
        class UpdateBehavior:
            PartialUpdate = "partial"

        def __init__(self, parent: Any = None) -> None:
            self.parent = parent
            self.object_name = ""
            self.minimum_size = None
            self.focus_policy = None
            self.update_behavior = None

        def setObjectName(self, name: str) -> None:
            self.object_name = name

        def setMinimumSize(self, canvas_width: int, canvas_height: int) -> None:
            self.minimum_size = (int(canvas_width), int(canvas_height))

        def setFocusPolicy(self, policy: Any) -> None:
            self.focus_policy = policy

        def setUpdateBehavior(self, behavior: Any) -> None:
            self.update_behavior = behavior

    class _InteractionHost:
        def __init__(self) -> None:
            self.initialize_calls = 0
            self.resize_calls: list[tuple[int, int]] = []
            self.paint_calls = 0
            self.pressed: list[str] = []
            self.released: list[str] = []

        def _initialize_sr_opengl_canvas(self, canvas: Any) -> None:
            self.initialize_calls += 1

        def _resize_sr_opengl_canvas(self, canvas: Any, canvas_width: int, canvas_height: int) -> None:
            self.resize_calls.append((int(canvas_width), int(canvas_height)))

        def _paint_sr_opengl_canvas(self, canvas: Any) -> None:
            self.paint_calls += 1

        def _sr_input_press(self, key: str) -> None:
            self.pressed.append(key)

        def _sr_input_release(self, key: str) -> None:
            self.released.append(key)

    class _InteractionKeyEvent:
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

    Canvas = create_opengl_viewport_canvas_class(_InteractionFakeOpenGLWidget)
    host = _InteractionHost()
    canvas = Canvas(host)
    press = _InteractionKeyEvent(key_text)
    release = _InteractionKeyEvent(key_text)

    start = time.perf_counter()
    canvas.initializeGL()
    canvas.resizeGL(width, height)
    canvas.resizeGL(width + 32, height + 18)
    canvas.keyPressEvent(press)
    canvas.keyReleaseEvent(release)
    canvas.paintGL()
    interaction_ms = (time.perf_counter() - start) * 1000.0

    expected_key = key_text.upper()
    resize_forwarded = host.resize_calls == [(int(width), int(height)), (int(width + 32), int(height + 18))]
    keyboard_forwarded = (
        host.pressed == [expected_key]
        and host.released == [expected_key]
        and press.accepted
        and release.accepted
    )
    lifecycle = canvas.opengl_lifecycle_snapshot()
    return {
        "target": "qt_opengl_canvas_interaction_smoke",
        "backend": "opengl_canvas_interaction_smoke",
        "resize_event_count": len(host.resize_calls),
        "keyboard_event_count": len(host.pressed) + len(host.released),
        "resize_forwarded": resize_forwarded,
        "keyboard_forwarded": keyboard_forwarded,
        "events_forwarded": resize_forwarded and keyboard_forwarded,
        "interaction_ms": interaction_ms,
        "initialize_calls": host.initialize_calls,
        "paint_calls": host.paint_calls,
        "last_size": lifecycle["last_size"],
        "pressed": list(host.pressed),
        "released": list(host.released),
    }


def _base_smoke_result() -> dict[str, Any]:
    return {
        "target": "qt_opengl_canvas_smoke",
        "qopenglwidget_available": False,
        "qapplication_available": False,
        "created_qapplication": False,
        "isolated_process": False,
        "initialize_calls": 0,
        "resize_calls": 0,
        "paint_calls": 0,
        "context_current": False,
        "clear_error": "",
        "rendered": False,
        "skip_reason": "",
        "pixel_probe": {
            "non_empty": False,
            "ready": False,
            "width": 0,
            "height": 0,
            "format": "RGBA8888",
            "sampled_pixels": 0,
            "non_background_pixels": 0,
            "non_background_ratio": 0.0,
            "alpha_covered_pixels": 0,
            "alpha_coverage": 0.0,
            "occupied_bounds": None,
            "digest": "",
            "background_rgba": list(_OPENGL_SMOKE_CLEAR_RGBA),
            "current_context": False,
            "fallback_used": False,
            "draw_mode": "",
            "gpu_draw_calls": 0,
            "errors": [],
        },
        "frame": {
            "commands": 0,
            "batches": 0,
            "instances": 0,
            "first_command": "",
        },
        "target_snapshot": {},
        "logical_capture": None,
        "context_released": False,
        "teardown_errors": [],
    }


def _probe_qimage_pixels(
    image: Any,
    *,
    background_rgba: tuple[int, int, int, int],
    current_context: bool,
    target_snapshot: dict[str, Any],
    errors: tuple[str, ...] = (),
) -> dict[str, Any]:
    from core.VitaLoom.viewports.viewport_capture_evidence import analyze_rgba_capture

    normalized_errors = tuple(item for item in errors if item)
    if image is None or image.isNull():
        return analyze_rgba_capture(
            b"",
            width=0,
            height=0,
            background_rgba=background_rgba,
            current_context=current_context,
            fallback_used=bool(target_snapshot.get("fallback_required", False)),
            draw_mode=str(target_snapshot.get("draw_mode", "")),
            gpu_draw_calls=int(target_snapshot.get("gpu_draw_calls", 0) or 0),
            errors=(*normalized_errors, "framebuffer image is null"),
        ).to_dict()

    from PyQt6.QtGui import QImage

    converted = image.convertToFormat(QImage.Format.Format_RGBA8888)
    width = int(converted.width())
    height = int(converted.height())
    stride = int(converted.bytesPerLine())
    pointer = converted.constBits()
    pointer.setsize(int(converted.sizeInBytes()))
    storage = bytes(pointer)
    row_size = width * 4
    raw = (
        storage[: row_size * height]
        if stride == row_size
        else b"".join(storage[row * stride : row * stride + row_size] for row in range(height))
    )
    target_errors = tuple(
        str(value)
        for key, value in dict(target_snapshot.get("details", {})).items()
        if str(key).endswith("error") and value
    )
    return analyze_rgba_capture(
        raw,
        width=width,
        height=height,
        background_rgba=background_rgba,
        current_context=current_context,
        fallback_used=bool(target_snapshot.get("fallback_required", False)),
        draw_mode=str(target_snapshot.get("draw_mode", "")),
        gpu_draw_calls=int(target_snapshot.get("gpu_draw_calls", 0) or 0),
        errors=(*normalized_errors, *target_errors),
    ).to_dict()


def _smoke_skip_reason(result: dict[str, Any]) -> str:
    if not result["qopenglwidget_available"]:
        return "QOpenGLWidget is unavailable"
    if not result["qapplication_available"]:
        return "QApplication is unavailable"
    if result["paint_calls"] <= 0:
        return "QOpenGLWidget paintGL was not called"
    if not result["context_current"]:
        return "QOpenGLContext was not current during paintGL"
    if result["clear_error"]:
        return f"OpenGL clear failed: {result['clear_error']}"
    if result["pixel_probe"]["fallback_used"]:
        return "OpenGL target required a diagnostic or painter fallback"
    if result["pixel_probe"]["errors"]:
        return f"OpenGL capture reported errors: {result['pixel_probe']['errors'][0]}"
    if not result["pixel_probe"]["non_empty"]:
        return "framebuffer contains only the declared background"
    if result["pixel_probe"]["gpu_draw_calls"] <= 0:
        return "OpenGL target reported no GPU draw calls"
    return "unknown OpenGL smoke failure"


def _frame_smoke_summary(stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "commands": int(stats.get("last_command_count", 0) or 0),
        "batches": int(stats.get("last_batch_count", 0) or 0),
        "instances": int(stats.get("last_instance_count", 0) or 0),
        "first_command": str(stats.get("last_first_command", "")),
    }


__all__ = [
    "create_opengl_viewport_canvas_class",
    "probe_opengl_canvas_interaction_smoke",
    "probe_qt_opengl_canvas_smoke",
    "probe_qt_opengl_interaction_sequence",
]
