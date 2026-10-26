# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
import sys
from dataclasses import replace

import pytest

from core.VitaLoom.viewports.viewport_adapter_benchmark import (
    benchmark_viewport_adapters,
    decide_viewport_default_policy,
)
from core.VitaLoom.viewports.viewport_pixel_capture import ViewportPixelCapture
from core.VitaLoom.viewports.viewport_snapshot import (
    ViewportEdgeSnapshot,
    ViewportEntitySnapshot,
    ViewportFrameSnapshot,
)


BACKGROUND = (26, 140, 217, 255)


def _frame(*, width: int = 128, height: int = 72) -> ViewportFrameSnapshot:
    entities = tuple(
        ViewportEntitySnapshot(
            id=f"entity-{index:02d}",
            entity_type=("organism", "sensor", "actuator", "nutrient")[index % 4],
            position=(10.0 + (index % 8) * 14.0, 10.0 + (index // 8) * 14.0),
            radius=4.0 + float(index % 3),
            selected=index in {5, 19},
        )
        for index in range(32)
    )
    edges = tuple(
        ViewportEdgeSnapshot(
            source_id=entities[index].id,
            target_id=entities[index + 1].id,
            kind="hard" if index % 2 == 0 else "signal",
        )
        for index in range(len(entities) - 1)
    )
    return ViewportFrameSnapshot(
        width=width,
        height=height,
        entities=entities,
        edges=edges,
        metadata={"immutable_benchmark": True},
    )


def _capture(frame: ViewportFrameSnapshot, *, draw_mode: str) -> ViewportPixelCapture:
    pixels = bytearray(bytes(BACKGROUND) * (frame.width * frame.height))
    if frame.width > 0 and frame.height > 0:
        offset = ((frame.height // 2) * frame.width + (frame.width // 2)) * 4
        pixels[offset : offset + 4] = bytes((255, 255, 255, 255))
    return ViewportPixelCapture.from_rgba(
        pixels,
        width=frame.width,
        height=frame.height,
        background_rgba=BACKGROUND,
        draw_mode=draw_mode,
    )


def _adapter_result(
    frame: ViewportFrameSnapshot,
    *,
    name: str,
    current_context: bool,
    native_geometry_acceleration: bool,
) -> dict[str, object]:
    return {
        "logical_capture": _capture(frame, draw_mode=name),
        "framebuffer_dimensions": [frame.width, frame.height],
        "context_current": current_context,
        "context_released": True,
        "fallback_required": False,
        "native_geometry_acceleration": native_geometry_acceleration,
        "gpu_draw_calls": 1 if current_context else 0,
        "errors": [],
        "teardown_errors": [],
        "draw_mode": name,
    }


def test_benchmark_interface_only_accepts_frames_and_plain_options() -> None:
    assert list(inspect.signature(benchmark_viewport_adapters).parameters) == [
        "frames",
        "warmup",
        "iterations",
        "process_events",
    ]


def test_benchmark_uses_identical_workload_warmup_iterations_and_capture_policy(monkeypatch) -> None:
    from core.VitaLoom.viewports import viewport_adapter_benchmark as benchmark_module

    frames = (_frame(), replace(_frame(), width=137, height=83))
    before = tuple(frames)
    calls: list[tuple[str, int, int]] = []

    def fake_qpainter(frame: ViewportFrameSnapshot, process_events: int) -> dict[str, object]:
        calls.append(("qpainter", frame.width, process_events))
        return _adapter_result(
            frame,
            name="fake_qpainter",
            current_context=False,
            native_geometry_acceleration=False,
        )

    def fake_opengl(frame: ViewportFrameSnapshot, process_events: int) -> dict[str, object]:
        calls.append(("opengl", frame.width, process_events))
        return _adapter_result(
            frame,
            name="fake_opengl",
            current_context=True,
            native_geometry_acceleration=False,
        )

    monkeypatch.setattr(benchmark_module, "_capture_qpainter_frame", fake_qpainter)
    monkeypatch.setattr(benchmark_module, "_capture_opengl_frame", fake_opengl)

    report = benchmark_viewport_adapters(
        frames,
        warmup=2,
        iterations=3,
        process_events=5,
    )

    assert tuple(frames) == before
    assert calls.count(("qpainter", 128, 5)) == 5
    assert calls.count(("qpainter", 137, 5)) == 5
    assert calls.count(("opengl", 128, 5)) == 5
    assert calls.count(("opengl", 137, 5)) == 5
    assert report["policy"] == {
        "warmup": 2,
        "iterations": 3,
        "process_events": 5,
        "lifecycle": "recreate_render_capture_teardown_per_frame",
        "capture": "logical_rgba_every_frame_with_opengl_framebuffer_readback",
    }
    assert report["workload"][0]["dimensions"] == [128, 72]
    assert report["workload"][1]["dimensions"] == [137, 83]
    assert report["adapters"]["qpainter"]["samples"] == 3
    assert report["adapters"]["opengl"]["samples"] == 3
    assert report["adapters"]["qpainter"]["capture_count"] == 6
    assert report["adapters"]["opengl"]["capture_count"] == 6
    assert report["parity_ready"] is True
    assert report["comparable"] is True
    assert report["decision"]["selected"] == "qpainter"
    assert "native_geometry_acceleration" in report["decision"]["reasons"]


def test_default_policy_requires_comparability_parity_native_geometry_and_speedup() -> None:
    base = {
        "comparable": True,
        "parity_ready": True,
        "adapters": {
            "qpainter": {"ready": True, "mean_ms": 20.0, "errors": []},
            "opengl": {
                "ready": True,
                "mean_ms": 10.0,
                "errors": [],
                "fallback_required": False,
                "context_released": True,
                "native_geometry_acceleration": False,
            },
        },
    }

    blocked = decide_viewport_default_policy(base)
    assert blocked["selected"] == "qpainter"
    assert blocked["switch_allowed"] is False
    assert "native_geometry_acceleration" in blocked["reasons"]

    allowed_report = {
        **base,
        "adapters": {
            **base["adapters"],
            "opengl": {
                **base["adapters"]["opengl"],
                "native_geometry_acceleration": True,
            },
        },
    }
    allowed = decide_viewport_default_policy(allowed_report)
    assert allowed["selected"] == "opengl"
    assert allowed["switch_allowed"] is True
    assert allowed["measured_speedup"] == pytest.approx(2.0)


@pytest.mark.skipif(sys.platform != "win32", reason="real current-context benchmark is a Windows gate")
def test_windows_end_to_end_benchmark_is_comparable_and_keeps_qpainter_policy() -> None:
    frame = _frame()

    report = benchmark_viewport_adapters((frame,), warmup=1, iterations=2, process_events=6)

    assert report["comparable"] is True, report
    assert report["parity_ready"] is True, report["parity"]
    assert report["adapters"]["qpainter"]["ready"] is True
    assert report["adapters"]["opengl"]["ready"] is True
    assert report["adapters"]["qpainter"]["capture_count"] == 2
    assert report["adapters"]["opengl"]["capture_count"] == 2
    assert report["adapters"]["opengl"]["context_current"] is True
    assert report["adapters"]["opengl"]["context_released"] is True
    assert report["adapters"]["opengl"]["fallback_required"] is False
    assert report["adapters"]["opengl"]["errors"] == []
    assert report["adapters"]["opengl"]["teardown_errors"] == []
    assert report["adapters"]["opengl"]["native_geometry_acceleration"] is False
    assert report["decision"]["selected"] == "qpainter"
    assert report["decision"]["switch_allowed"] is False
    assert "native_geometry_acceleration" in report["decision"]["reasons"]
