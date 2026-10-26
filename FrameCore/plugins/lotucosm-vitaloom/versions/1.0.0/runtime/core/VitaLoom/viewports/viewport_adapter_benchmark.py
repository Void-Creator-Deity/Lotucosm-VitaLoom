# -*- coding: utf-8 -*-
"""Comparable end-to-end evidence for concrete viewport Host Adapters.

The public Interface accepts only immutable viewport snapshots and plain numeric
options. Native Qt/OpenGL objects are created and consumed inside the concrete
capture functions and never appear in the returned report.
"""

from __future__ import annotations

import statistics
import time
from collections.abc import Iterable, Mapping
from typing import Any

from core.VitaLoom.viewports.opengl_batching import compile_opengl_batches
from core.VitaLoom.viewports.viewport_draw_commands import compile_viewport_draw_commands
from core.VitaLoom.viewports.viewport_pixel_capture import ViewportPixelCapture
from core.VitaLoom.viewports.viewport_pixel_parity import (
    ViewportParityTolerance,
    compare_viewport_pixel_captures,
)
from core.VitaLoom.viewports.viewport_snapshot import ViewportFrameSnapshot


BENCHMARK_PARITY_TOLERANCE = ViewportParityTolerance(
    max_bounds_delta=2,
    max_non_background_ratio_delta=0.03,
    max_alpha_coverage_delta=0.0,
    pixel_channel_tolerance=32,
    max_pixel_mismatch_ratio=0.14,
    max_mean_absolute_channel_error=8.5,
)
MINIMUM_OPENGL_SPEEDUP = 1.10


def benchmark_viewport_adapters(
    frames: Iterable[ViewportFrameSnapshot],
    warmup: int = 1,
    iterations: int = 3,
    process_events: int = 8,
) -> dict[str, Any]:
    """Benchmark QPainter and current-context OpenGL under one capture policy."""

    frame_tuple = tuple(frames)
    if not frame_tuple:
        raise ValueError("frames must contain at least one ViewportFrameSnapshot")
    if any(not isinstance(frame, ViewportFrameSnapshot) for frame in frame_tuple):
        raise TypeError("frames must contain only immutable ViewportFrameSnapshot values")
    if int(warmup) < 0:
        raise ValueError("warmup must be non-negative")
    if int(iterations) <= 0:
        raise ValueError("iterations must be positive")
    if int(process_events) <= 0:
        raise ValueError("process_events must be positive")

    warmup_count = int(warmup)
    iteration_count = int(iterations)
    event_count = int(process_events)
    workload = tuple(_workload_record(frame) for frame in frame_tuple)
    states = {
        "qpainter": _new_adapter_state(),
        "opengl": _new_adapter_state(),
    }

    for round_index in range(warmup_count + iteration_count):
        is_warmup = round_index < warmup_count
        measured_index = round_index - warmup_count
        order = ("qpainter", "opengl") if round_index % 2 == 0 else ("opengl", "qpainter")
        for adapter_name in order:
            capture_one = (
                _capture_qpainter_frame if adapter_name == "qpainter" else _capture_opengl_frame
            )
            started = time.perf_counter_ns()
            records = tuple(
                _safe_capture(capture_one, frame, event_count) for frame in frame_tuple
            )
            elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000.0
            if is_warmup:
                states[adapter_name]["warmup_runs"].append(records)
            else:
                states[adapter_name]["timed_runs"].append(records)
                states[adapter_name]["samples_ms"].append(elapsed_ms)
                states[adapter_name]["measured_order"].append(
                    0 if order[0] == adapter_name else 1
                )
                states[adapter_name]["measured_indices"].append(measured_index)

    adapters = {
        name: _summarize_adapter(name, state, len(frame_tuple), warmup_count)
        for name, state in states.items()
    }
    parity = _compare_last_runs(states, frame_tuple)
    parity_ready = bool(parity) and all(item["ready"] for item in parity)
    comparable = (
        adapters["qpainter"]["ready"]
        and adapters["opengl"]["ready"]
        and parity_ready
        and adapters["qpainter"]["samples"] == iteration_count
        and adapters["opengl"]["samples"] == iteration_count
        and adapters["qpainter"]["capture_count"]
        == adapters["opengl"]["capture_count"]
        == len(frame_tuple) * iteration_count
        and adapters["qpainter"]["logical_dimensions"]
        == adapters["opengl"]["logical_dimensions"]
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "benchmark": "viewport_adapter_end_to_end",
        "policy": {
            "warmup": warmup_count,
            "iterations": iteration_count,
            "process_events": event_count,
            "lifecycle": "recreate_render_capture_teardown_per_frame",
            "capture": "logical_rgba_every_frame_with_opengl_framebuffer_readback",
        },
        "workload": list(workload),
        "adapters": adapters,
        "parity": parity,
        "parity_ready": parity_ready,
        "comparable": comparable,
    }
    report["decision"] = decide_viewport_default_policy(report)
    return report


def decide_viewport_default_policy(report: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed unless parity, lifecycle, native geometry, and speed all pass."""

    adapters = report.get("adapters", {})
    qpainter = adapters.get("qpainter", {}) if isinstance(adapters, Mapping) else {}
    opengl = adapters.get("opengl", {}) if isinstance(adapters, Mapping) else {}
    reasons: list[str] = []

    if not bool(report.get("comparable")):
        reasons.append("comparable_end_to_end_evidence")
    if not bool(report.get("parity_ready")):
        reasons.append("pixel_parity")
    if not bool(qpainter.get("ready")):
        reasons.append("qpainter_ready")
    if not bool(opengl.get("ready")):
        reasons.append("opengl_ready")
    if bool(opengl.get("fallback_required", True)):
        reasons.append("opengl_fallback")
    if not bool(opengl.get("context_released")):
        reasons.append("opengl_context_teardown")
    if not bool(opengl.get("native_geometry_acceleration")):
        reasons.append("native_geometry_acceleration")
    if qpainter.get("errors"):
        reasons.append("qpainter_errors")
    if opengl.get("errors") or opengl.get("teardown_errors"):
        reasons.append("opengl_errors")

    qpainter_mean = _positive_float(qpainter.get("mean_ms"))
    opengl_mean = _positive_float(opengl.get("mean_ms"))
    measured_speedup = qpainter_mean / opengl_mean if qpainter_mean and opengl_mean else 0.0
    if measured_speedup < MINIMUM_OPENGL_SPEEDUP:
        reasons.append("minimum_measured_speedup")

    normalized_reasons = _unique_strings(reasons)
    switch_allowed = not normalized_reasons
    return {
        "selected": "opengl" if switch_allowed else "qpainter",
        "switch_allowed": switch_allowed,
        "minimum_required_speedup": MINIMUM_OPENGL_SPEEDUP,
        "measured_speedup": measured_speedup,
        "reasons": normalized_reasons,
    }


def _new_adapter_state() -> dict[str, list[Any]]:
    return {
        "warmup_runs": [],
        "timed_runs": [],
        "samples_ms": [],
        "measured_order": [],
        "measured_indices": [],
    }


def _workload_record(frame: ViewportFrameSnapshot) -> dict[str, Any]:
    commands = compile_viewport_draw_commands(frame)
    batches = compile_opengl_batches(commands)
    return {
        "dimensions": [int(frame.width), int(frame.height)],
        "entities": len(frame.entities),
        "edges": len(frame.edges),
        "commands": len(commands),
        "batches": len(batches),
        "instances": sum(batch.instance_count for batch in batches),
    }


def _safe_capture(capture_one: Any, frame: ViewportFrameSnapshot, process_events: int) -> dict[str, Any]:
    try:
        result = capture_one(frame, process_events)
        if not isinstance(result, dict):
            raise TypeError("Adapter capture must return a dict")
        return result
    except Exception as exc:
        return {
            "logical_capture": None,
            "framebuffer_dimensions": [0, 0],
            "context_current": False,
            "context_released": True,
            "fallback_required": True,
            "native_geometry_acceleration": False,
            "gpu_draw_calls": 0,
            "errors": [f"{exc.__class__.__name__}: {exc}"],
            "teardown_errors": [],
            "draw_mode": "capture_failed",
        }


def _capture_qpainter_frame(
    frame: ViewportFrameSnapshot,
    process_events: int,
) -> dict[str, Any]:
    del process_events
    from core.VitaLoom.viewports.qpainter_capture import capture_qpainter_viewport

    capture = capture_qpainter_viewport(frame)
    return {
        "logical_capture": capture,
        "framebuffer_dimensions": [capture.width, capture.height],
        "context_current": False,
        "context_released": True,
        "fallback_required": bool(capture.evidence.fallback_used),
        "native_geometry_acceleration": False,
        "gpu_draw_calls": 0,
        "errors": list(capture.evidence.errors),
        "teardown_errors": [],
        "draw_mode": capture.evidence.draw_mode,
    }


def _capture_opengl_frame(
    frame: ViewportFrameSnapshot,
    process_events: int,
) -> dict[str, Any]:
    from core.VitaLoom.viewports.opengl_canvas import probe_qt_opengl_canvas_smoke

    smoke = probe_qt_opengl_canvas_smoke(
        frame=frame,
        width=int(frame.width),
        height=int(frame.height),
        process_events=int(process_events),
        include_logical_capture=True,
    )
    target = dict(smoke.get("target_snapshot", {}))
    pixel_probe = dict(smoke.get("pixel_probe", {}))
    capture = smoke.get("logical_capture")
    errors = [
        *([str(smoke["clear_error"])] if smoke.get("clear_error") else []),
        *[
            str(value)
            for key, value in dict(target.get("details", {})).items()
            if str(key).endswith("error") and value
        ],
        *[str(value) for value in pixel_probe.get("errors", ()) if value],
    ]
    if not isinstance(capture, ViewportPixelCapture):
        errors.append("logical OpenGL capture is unavailable")
    if not smoke.get("rendered") and smoke.get("skip_reason"):
        errors.append(str(smoke["skip_reason"]))
    return {
        "logical_capture": capture if isinstance(capture, ViewportPixelCapture) else None,
        "framebuffer_dimensions": [
            int(pixel_probe.get("width", 0) or 0),
            int(pixel_probe.get("height", 0) or 0),
        ],
        "context_current": bool(target.get("context_current", smoke.get("context_current"))),
        "context_released": bool(smoke.get("context_released")),
        "fallback_required": bool(target.get("fallback_required", True)),
        "native_geometry_acceleration": bool(target.get("native_geometry_acceleration", False)),
        "gpu_draw_calls": int(target.get("gpu_draw_calls", 0) or 0),
        "errors": _unique_strings(errors),
        "teardown_errors": _unique_strings(smoke.get("teardown_errors", ())),
        "draw_mode": str(target.get("draw_mode", "")),
    }


def _summarize_adapter(
    name: str,
    state: Mapping[str, list[Any]],
    frames_per_iteration: int,
    warmup: int,
) -> dict[str, Any]:
    timed_runs = list(state["timed_runs"])
    warmup_runs = list(state["warmup_runs"])
    samples = [float(value) for value in state["samples_ms"]]
    timed_records = [record for run in timed_runs for record in run]
    all_records = [record for run in (*warmup_runs, *timed_runs) for record in run]
    last_run = timed_runs[-1] if timed_runs else ()
    logical_captures = [
        record.get("logical_capture")
        for record in timed_records
        if isinstance(record.get("logical_capture"), ViewportPixelCapture)
    ]
    errors = _unique_strings(
        value for record in all_records for value in record.get("errors", ()) if value
    )
    teardown_errors = _unique_strings(
        value for record in all_records for value in record.get("teardown_errors", ()) if value
    )
    fallback_required = any(bool(record.get("fallback_required", True)) for record in all_records)
    context_released = bool(all_records) and all(
        bool(record.get("context_released")) for record in all_records
    )
    context_current = (
        bool(all_records)
        and all(bool(record.get("context_current")) for record in all_records)
        if name == "opengl"
        else False
    )
    native_geometry_acceleration = bool(all_records) and all(
        bool(record.get("native_geometry_acceleration")) for record in all_records
    )
    expected_captures = len(timed_runs) * frames_per_iteration
    ready = (
        len(logical_captures) == expected_captures
        and not errors
        and not teardown_errors
        and not fallback_required
        and context_released
        and (context_current if name == "opengl" else True)
    )
    return {
        "ready": ready,
        "samples": len(samples),
        "samples_ms": samples,
        "mean_ms": statistics.fmean(samples),
        "median_ms": statistics.median(samples),
        "min_ms": min(samples),
        "max_ms": max(samples),
        "p95_ms": _percentile_95(samples),
        "frames_per_iteration": frames_per_iteration,
        "warmup_capture_count": warmup * frames_per_iteration,
        "capture_count": len(logical_captures),
        "logical_digests": [
            str(record["logical_capture"].evidence.digest)
            for record in last_run
            if isinstance(record.get("logical_capture"), ViewportPixelCapture)
        ],
        "logical_dimensions": [
            [int(record["logical_capture"].width), int(record["logical_capture"].height)]
            for record in last_run
            if isinstance(record.get("logical_capture"), ViewportPixelCapture)
        ],
        "framebuffer_dimensions": [
            [int(value) for value in record.get("framebuffer_dimensions", (0, 0))]
            for record in last_run
        ],
        "draw_modes": _unique_strings(record.get("draw_mode", "") for record in all_records),
        "gpu_draw_calls": sum(int(record.get("gpu_draw_calls", 0) or 0) for record in timed_records),
        "context_current": context_current,
        "context_released": context_released,
        "fallback_required": fallback_required,
        "native_geometry_acceleration": native_geometry_acceleration,
        "errors": errors,
        "teardown_errors": teardown_errors,
        "measured_order": list(state["measured_order"]),
    }


def _compare_last_runs(
    states: Mapping[str, Mapping[str, list[Any]]],
    frames: tuple[ViewportFrameSnapshot, ...],
) -> list[dict[str, Any]]:
    qpainter_runs = states["qpainter"]["timed_runs"]
    opengl_runs = states["opengl"]["timed_runs"]
    if not qpainter_runs or not opengl_runs:
        return []
    qpainter_last = qpainter_runs[-1]
    opengl_last = opengl_runs[-1]
    results: list[dict[str, Any]] = []
    for index, frame in enumerate(frames):
        reference = qpainter_last[index].get("logical_capture")
        candidate = opengl_last[index].get("logical_capture")
        if not isinstance(reference, ViewportPixelCapture) or not isinstance(
            candidate, ViewportPixelCapture
        ):
            results.append(
                {
                    "frame_index": index,
                    "dimensions": [int(frame.width), int(frame.height)],
                    "ready": False,
                    "failures": ["capture_missing"],
                }
            )
            continue
        parity = compare_viewport_pixel_captures(
            reference,
            candidate,
            tolerance=BENCHMARK_PARITY_TOLERANCE,
        ).to_dict()
        results.append(
            {
                "frame_index": index,
                "dimensions": [int(frame.width), int(frame.height)],
                **parity,
            }
        )
    return results


def _percentile_95(samples: list[float]) -> float:
    ordered = sorted(samples)
    index = max(0, min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))))
    return ordered[index]


def _positive_float(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if number > 0.0 else 0.0


def _unique_strings(values: Iterable[object]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if value))


__all__ = [
    "BENCHMARK_PARITY_TOLERANCE",
    "MINIMUM_OPENGL_SPEEDUP",
    "benchmark_viewport_adapters",
    "decide_viewport_default_policy",
]
