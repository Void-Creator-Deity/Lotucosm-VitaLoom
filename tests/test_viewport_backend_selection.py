# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_viewport_backend_selection_import_stays_qt_free_in_a_fresh_interpreter() -> None:
    runtime_root = (
        Path(__file__).resolve().parents[1]
        / "FrameCore"
        / "plugins"
        / "lotucosm-vitaloom"
        / "versions"
        / "1.0.0"
        / "runtime"
    )
    environ = dict(os.environ)
    environ["PYTHONPATH"] = str(runtime_root)
    probe = subprocess.run(
        [
            sys.executable,
            "-B",
            "-S",
            "-c",
            (
                "import sys; "
                "import core.VitaLoom.viewports.graphics_backend_strategy; "
                "import core.VitaLoom.viewports.sr_gpu_canvas; "
                "print(','.join(sorted(name for name in sys.modules "
                "if name == 'PyQt6' or name.startswith('PyQt6.'))))"
            ),
        ],
        cwd=runtime_root.parents[5],
        env=environ,
        capture_output=True,
        text=True,
        check=False,
    )

    assert probe.returncode == 0, probe.stderr
    assert probe.stdout.strip() == ""


def test_auto_backend_keeps_qpainter_until_benchmark_and_native_readiness(monkeypatch) -> None:
    from core.VitaLoom.viewports.graphics_backend_strategy import select_viewport_backend
    from core.VitaLoom.viewports.qpainter_backend import QPainterViewportBackend

    monkeypatch.delenv("VITALOOM_VIEWPORT_BACKEND", raising=False)

    selection = select_viewport_backend()

    assert selection.requested == "auto"
    assert isinstance(selection.backend, QPainterViewportBackend)
    assert selection.info.name == "qpainter"
    assert "benchmark" in selection.info.fallback_reason
    assert "native geometry" in selection.info.fallback_reason
    assert selection.backend.stats()["default_switch_allowed"] is False


def test_explicit_qpainter_backend_selection(monkeypatch) -> None:
    from core.VitaLoom.viewports.graphics_backend_strategy import select_viewport_backend
    from core.VitaLoom.viewports.qpainter_backend import QPainterViewportBackend

    monkeypatch.setenv("VITALOOM_VIEWPORT_BACKEND", "qpainter")

    selection = select_viewport_backend()

    assert selection.requested == "qpainter"
    assert isinstance(selection.backend, QPainterViewportBackend)
    assert selection.info.name == "qpainter"


def test_rhi_selection_reports_future_backend_not_available() -> None:
    from core.VitaLoom.viewports.graphics_backend_strategy import select_viewport_backend

    selection = select_viewport_backend("rhi")

    assert selection.requested == "rhi"
    assert selection.info.name == "rhi"
    assert selection.info.supports_gpu is False
    assert "future" in selection.info.fallback_reason
    assert selection.backend.stats()["available"] is False


def test_opengl_selection_uses_metadata_backend_when_qt_opengl_is_available(monkeypatch) -> None:
    from core.VitaLoom.viewports import graphics_backend_strategy
    from core.VitaLoom.viewports.opengl_backend import OpenGLViewportBackend

    monkeypatch.setattr(graphics_backend_strategy, "is_opengl_viewport_available", lambda: True)

    selection = graphics_backend_strategy.select_viewport_backend("opengl")

    assert selection.requested == "opengl"
    assert isinstance(selection.backend, OpenGLViewportBackend)
    assert selection.info.name == "opengl"
    assert selection.info.supports_gpu is True
    assert selection.info.supports_batching is True
    assert "opt-in" in selection.info.fallback_reason
    stats = selection.backend.stats()
    assert stats["opengl_parity_ready"] is True
    assert stats["opengl_batching_ready"] is True
    assert stats["default_switch_allowed"] is False


def test_opengl_selection_reports_clear_fallback_when_unavailable(monkeypatch) -> None:
    from core.VitaLoom.viewports import graphics_backend_strategy

    monkeypatch.setattr(graphics_backend_strategy, "is_opengl_viewport_available", lambda: False)

    selection = graphics_backend_strategy.select_viewport_backend("opengl")

    assert selection.requested == "opengl"
    assert selection.info.name == "opengl"
    assert selection.info.supports_gpu is False
    assert "QtOpenGLWidgets" in selection.info.fallback_reason
    assert selection.backend.stats()["available"] is False


def test_backend_selection_rejects_unknown_mode() -> None:
    from core.VitaLoom.viewports.graphics_backend_strategy import select_viewport_backend

    try:
        select_viewport_backend("vulkan")
    except ValueError as exc:
        assert "qpainter|opengl|rhi|auto" in str(exc)
    else:
        raise AssertionError("unknown backend mode should be rejected")


def test_sr_canvas_class_honors_viewport_backend_opengl_env(monkeypatch) -> None:
    from core.VitaLoom.viewports import sr_gpu_canvas

    class _Host:
        class _SrCanvas:
            pass

    class _DummyOpenGL:
        class UpdateBehavior:
            PartialUpdate = object()

    monkeypatch.delenv("VITALOOM_SR_GPU", raising=False)
    monkeypatch.setenv("VITALOOM_VIEWPORT_BACKEND", "opengl")
    monkeypatch.setattr(sr_gpu_canvas, "_OPENGL_WIDGET", _DummyOpenGL)
    monkeypatch.setattr(sr_gpu_canvas, "_probe_opengl_widget", lambda: _DummyOpenGL)

    canvas_cls = sr_gpu_canvas.create_sr_canvas_class(_Host)

    assert issubclass(canvas_cls, _DummyOpenGL)
