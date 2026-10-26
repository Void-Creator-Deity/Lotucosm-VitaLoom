# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
import sys


def _run_case(name: str, *, timeout: float = 60.0) -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/benchmark_engine.py", "--case", name, "--repeats", "1"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_viewport_benchmark_cases_report_counts() -> None:
    for case in (
        "viewport_draw",
        "viewport_draw_dense",
        "viewport_batch_compile",
        "viewport_qpainter_render",
        "viewport_opengl_render",
        "viewport_opengl_canvas",
        "viewport_interaction_smoke",
    ):
        data = _run_case(case)
        last = data["cases"][0]["last_result"]
        assert last["backend"] in {
            "draw_commands",
            "opengl_batching",
            "qpainter_command_render",
            "opengl_qt_render_target",
            "opengl_qt_canvas_smoke",
            "opengl_canvas_interaction_smoke",
        }
        if case == "viewport_interaction_smoke":
            assert last["resize_event_count"] >= 2
            assert last["keyboard_event_count"] == 2
            assert last["resize_forwarded"] is True
            assert last["keyboard_forwarded"] is True
            assert last["events_forwarded"] is True
            assert last["interaction_ms"] >= 0.0
        elif case == "viewport_opengl_canvas":
            assert last["target"] == "qt_opengl_canvas_smoke"
            assert "qopenglwidget_available" in last
            assert "qapplication_available" in last
            if last["rendered"]:
                assert last["entities"] >= 1
                assert last["commands"] >= 1
                assert last["batches"] >= 1
                assert last["instances"] >= 1
                assert isinstance(last["first_command"], str)
                assert last["context_current"] is True
                assert last["pixel_probe"]["non_empty"] is True
                assert last["frame"]["commands"] >= 1
                assert last["frame"]["batches"] >= 1
                assert last["frame"]["instances"] >= 1
                assert last["target_snapshot"]["target"] == "qt_opengl_texture"
                assert last["target_snapshot"]["fallback_required"] is False
            else:
                assert isinstance(last["skip_reason"], str)
                assert last["skip_reason"]
        else:
            assert last["entities"] >= 1
            assert last["commands"] >= 1
            assert last["batches"] >= 1
            assert last["instances"] >= 1
            assert isinstance(last["first_command"], str)
        if case == "viewport_opengl_render":
            assert last["painter_draw_calls"] >= 1
            assert last["pixel_probe"]["non_empty"] is True
            assert "instancing" in last
            assert "context_current" in last["instancing"]
            assert "fallback_required" in last["instancing"]
            assert last["default_switch_allowed"] is False

def test_viewport_frame_loop_dense_reports_timing_buckets() -> None:
    data = _run_case("viewport_frame_loop_dense")
    last = data["cases"][0]["last_result"]

    assert last["backend"] == "viewport_frame_loop"
    assert last["variant"] == "dense"
    assert last["frames"] >= 30
    assert last["entities"] == 360
    assert last["commands_per_frame"] == 630
    assert last["batches_per_frame"] == 46
    assert last["auto_default_backend"] == "qpainter"
    assert last["command_compile_ms"] >= 0.0
    assert last["batch_compile_ms"] >= 0.0
    assert last["qpainter_render_ms"] >= 0.0
    assert last["opengl_canvas_smoke_ms"] >= 0.0
    if last["opengl_canvas"]["rendered"]:
        assert last["opengl_canvas"]["context_current"] is True
        assert last["opengl_canvas"]["gpu_draw_calls"] >= 1
    else:
        assert last["opengl_canvas"]["skip_reason"]
    assert last["profiler"]["frame_count"] >= 30
    assert last["profiler"]["bucket_names"] == [
        "command_compile",
        "batch_compile",
        "qpainter_render",
        "opengl_canvas_smoke",
        "total",
    ]
    assert last["profiler"]["buckets"]["command_compile"]["samples"] == last["frames"]
    assert last["profiler"]["buckets"]["qpainter_render"]["samples"] == last["frames"]


def test_viewport_adapter_end_to_end_is_comparable_policy_evidence() -> None:
    # The real framebuffer-readback path may exceed 60 s on software OpenGL while still producing valid parity evidence.
    data = _run_case("viewport_adapter_end_to_end", timeout=90.0)
    case = data["cases"][0]
    last = case["last_result"]

    assert case["name"] == "viewport_adapter_end_to_end"
    assert last["benchmark"] == "viewport_adapter_end_to_end"
    assert last["policy"] == {
        "warmup": 1,
        "iterations": 3,
        "process_events": 8,
        "lifecycle": "recreate_render_capture_teardown_per_frame",
        "capture": "logical_rgba_every_frame_with_opengl_framebuffer_readback",
    }
    assert len(last["workload"]) == 1
    assert last["workload"][0]["entities"] == 360
    assert last["workload"][0]["commands"] == 630
    assert last["workload"][0]["batches"] == 46

    qpainter = last["adapters"]["qpainter"]
    opengl = last["adapters"]["opengl"]
    assert qpainter["samples"] == opengl["samples"] == 3
    assert qpainter["capture_count"] == opengl["capture_count"] == 3
    assert qpainter["warmup_capture_count"] == opengl["warmup_capture_count"] == 1
    for adapter in (qpainter, opengl):
        assert adapter["ready"] is True
        assert adapter["mean_ms"] >= 0.0
        assert adapter["median_ms"] >= 0.0
        assert adapter["min_ms"] >= 0.0
        assert adapter["max_ms"] >= 0.0
        assert adapter["p95_ms"] >= 0.0
        assert adapter["errors"] == []
        assert adapter["teardown_errors"] == []

    assert last["comparable"] is True
    assert last["parity_ready"] is True
    assert opengl["context_current"] is True
    assert opengl["context_released"] is True
    assert opengl["fallback_required"] is False
    assert opengl["native_geometry_acceleration"] is False
    assert last["decision"]["selected"] == "qpainter"
    assert last["decision"]["switch_allowed"] is False
    assert "native_geometry_acceleration" in last["decision"]["reasons"]
    assert last["current_auto_backend"] == "qpainter"


