# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Any

from PyQt6.QtWidgets import QApplication

from core.VitaLoom.viewports.viewport_profiler import ViewportFrameProfiler

_QT_APP: QApplication | None = None


def test_profiler_records_fixed_buckets_and_rolling_averages() -> None:
    profiler = ViewportFrameProfiler(window=3)

    profiler.record("script", 1.0)
    profiler.record("script", 2.0)
    profiler.record("script", 3.0)
    profiler.record("script", 100.0)
    profiler.record("render", 4.5)

    snapshot = profiler.snapshot()

    assert set(snapshot) == {"script", "spawn", "fluid", "physics", "render", "total"}
    assert snapshot["script"]["last_ms"] == 100.0
    assert snapshot["script"]["avg_ms"] == 35.0
    assert snapshot["script"]["samples"] == 3
    assert snapshot["render"]["last_ms"] == 4.5
    assert snapshot["render"]["avg_ms"] == 4.5
    assert snapshot["physics"]["samples"] == 0


def test_profiler_measure_context_uses_clock_and_never_raises_from_recording() -> None:
    ticks = iter([10.0, 10.025])
    profiler = ViewportFrameProfiler(clock=lambda: next(ticks))

    with profiler.measure("total"):
        pass

    profiler.record("missing", 1.0)
    profiler.record("render", "not-a-number")

    snapshot = profiler.snapshot()
    assert snapshot["total"]["last_ms"] == 25.0
    assert snapshot["render"]["samples"] == 0


def test_profiler_structured_snapshot_reports_bucket_names_and_frame_count() -> None:
    profiler = ViewportFrameProfiler(
        buckets=("command_compile", "batch_compile", "qpainter_render", "total"),
        window=5,
    )

    profiler.record("command_compile", 1.25)
    profiler.record("command_compile", 1.75)
    profiler.record("batch_compile", 0.5)
    profiler.record("qpainter_render", 3.0)

    snapshot = profiler.structured_snapshot()

    assert snapshot["bucket_names"] == [
        "command_compile",
        "batch_compile",
        "qpainter_render",
        "total",
    ]
    assert snapshot["frame_count"] == 2
    assert snapshot["buckets"]["command_compile"]["samples"] == 2
    assert snapshot["buckets"]["qpainter_render"]["last_ms"] == 3.0
    assert snapshot["window"] == 5


def test_game_viewport_exposes_plain_profiler_snapshot() -> None:
    global _QT_APP
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _QT_APP = QApplication.instance() or QApplication([])

    from core.VitaLoom.viewports.game_viewport import GameViewport

    viewport = GameViewport()
    viewport._viewport_profiler.record("physics", 2.5)

    snapshot = viewport.get_viewport_profiler_snapshot()

    assert isinstance(snapshot, dict)
    assert snapshot["physics"]["last_ms"] == 2.5
    assert snapshot["physics"]["avg_ms"] == 2.5
    assert snapshot["render"]["samples"] == 0
