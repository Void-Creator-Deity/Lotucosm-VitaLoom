# -*- coding: utf-8 -*-
from __future__ import annotations

import sys

import pytest

from core.VitaLoom.viewports.opengl_canvas import probe_qt_opengl_canvas_smoke
from core.VitaLoom.viewports.qpainter_capture import capture_qpainter_viewport
from core.VitaLoom.viewports.viewport_pixel_capture import ViewportPixelCapture
from core.VitaLoom.viewports.viewport_pixel_parity import (
    ViewportParityTolerance,
    compare_viewport_pixel_captures,
)
from core.VitaLoom.viewports.viewport_snapshot import (
    ViewportEdgeSnapshot,
    ViewportEntitySnapshot,
    ViewportFrameSnapshot,
)


BACKGROUND = (26, 140, 217, 255)
PARITY_TOLERANCE = ViewportParityTolerance(
    max_bounds_delta=2,
    max_non_background_ratio_delta=0.03,
    max_alpha_coverage_delta=0.0,
    pixel_channel_tolerance=32,
    max_pixel_mismatch_ratio=0.08,
    max_mean_absolute_channel_error=4.0,
)
DENSE_PARITY_TOLERANCE = ViewportParityTolerance(
    max_bounds_delta=2,
    max_non_background_ratio_delta=0.03,
    max_alpha_coverage_delta=0.0,
    pixel_channel_tolerance=32,
    max_pixel_mismatch_ratio=0.14,
    max_mean_absolute_channel_error=8.5,
)


def _scene(name: str) -> ViewportFrameSnapshot:
    if name == "empty":
        return ViewportFrameSnapshot(width=96, height=64)
    if name == "single":
        return ViewportFrameSnapshot(
            width=96,
            height=64,
            entities=(
                ViewportEntitySnapshot(
                    id="a",
                    entity_type="organism",
                    position=(24.0, 20.0),
                    radius=6.0,
                ),
            ),
        )
    if name == "selected":
        return ViewportFrameSnapshot(
            width=96,
            height=64,
            entities=(
                ViewportEntitySnapshot(
                    id="a",
                    entity_type="organism",
                    position=(24.0, 20.0),
                    radius=6.0,
                    selected=True,
                ),
            ),
        )
    if name == "edge":
        return ViewportFrameSnapshot(
            width=96,
            height=64,
            entities=(
                ViewportEntitySnapshot(id="a", entity_type="organism", position=(18.0, 18.0), radius=5.0),
                ViewportEntitySnapshot(id="b", entity_type="nutrient", position=(72.0, 46.0), radius=7.0),
            ),
            edges=(ViewportEdgeSnapshot(source_id="a", target_id="b", kind="hard"),),
        )
    if name == "hidden":
        return ViewportFrameSnapshot(
            width=96,
            height=64,
            entities=(
                ViewportEntitySnapshot(id="a", entity_type="organism", position=(24.0, 20.0), radius=6.0),
                ViewportEntitySnapshot(
                    id="hidden",
                    entity_type="nutrient",
                    position=(74.0, 48.0),
                    radius=8.0,
                    visible=False,
                ),
            ),
            edges=(ViewportEdgeSnapshot(source_id="a", target_id="hidden", kind="hard"),),
        )
    if name == "resize":
        return ViewportFrameSnapshot(
            width=137,
            height=83,
            entities=(
                ViewportEntitySnapshot(id="a", entity_type="sensor", position=(118.0, 66.0), radius=9.0),
            ),
        )
    if name == "dense":
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
        return ViewportFrameSnapshot(width=128, height=72, entities=entities, edges=edges)
    raise AssertionError(name)


def _solid_capture(color: tuple[int, int, int, int]) -> ViewportPixelCapture:
    return ViewportPixelCapture.from_rgba(
        bytes(color) * 4,
        width=2,
        height=2,
        background_rgba=BACKGROUND,
        draw_mode="test",
    )


def test_pixel_parity_reports_exact_repeat_as_ready() -> None:
    capture = _solid_capture((255, 255, 255, 255))

    parity = compare_viewport_pixel_captures(capture, capture)

    assert parity.ready is True
    assert parity.pixel_mismatch_ratio == 0.0
    assert parity.mean_absolute_channel_error == 0.0
    assert parity.bounds_delta == (0, 0, 0, 0)


def test_pixel_parity_fails_closed_for_dimension_mismatch() -> None:
    left = _solid_capture((255, 255, 255, 255))
    right = ViewportPixelCapture.from_rgba(
        bytes((255, 255, 255, 255)) * 6,
        width=3,
        height=2,
        background_rgba=BACKGROUND,
        draw_mode="test",
    )

    parity = compare_viewport_pixel_captures(left, right)

    assert parity.ready is False
    assert "dimensions" in parity.failures


@pytest.mark.parametrize("scene_name", ["empty", "single", "selected", "edge", "hidden", "resize", "dense"])
def test_qpainter_capture_is_deterministic_plain_data(scene_name: str) -> None:
    frame = _scene(scene_name)

    capture = capture_qpainter_viewport(frame, background_rgba=BACKGROUND)
    repeated = capture_qpainter_viewport(frame, background_rgba=BACKGROUND)

    assert isinstance(capture, ViewportPixelCapture)
    assert capture.width == frame.width
    assert capture.height == frame.height
    assert capture.format == "RGBA8888"
    assert capture.evidence.digest == repeated.evidence.digest
    assert capture.evidence.fallback_used is False
    assert capture.evidence.draw_mode == "qpainter_qimage"
    if scene_name == "empty":
        assert capture.evidence.non_background_pixels == 0
    else:
        assert capture.evidence.non_background_pixels > 0


@pytest.mark.parametrize("scene_name", ["empty", "single", "selected", "edge", "hidden", "resize", "dense"])
def test_windows_current_context_logical_pixels_match_qpainter(scene_name: str) -> None:
    if sys.platform != "win32":
        pytest.skip("controlled current-context parity proof is a Windows gate")

    frame = _scene(scene_name)
    qpainter_capture = capture_qpainter_viewport(frame, background_rgba=BACKGROUND)
    result = probe_qt_opengl_canvas_smoke(
        frame=frame,
        width=frame.width,
        height=frame.height,
        include_logical_capture=True,
    )

    assert result["context_current"] is True, result["skip_reason"]
    assert result["target_snapshot"]["fallback_required"] is False
    assert result["pixel_probe"]["errors"] == []
    opengl_capture = result["logical_capture"]
    assert isinstance(opengl_capture, ViewportPixelCapture)

    parity = compare_viewport_pixel_captures(
        qpainter_capture,
        opengl_capture,
        tolerance=DENSE_PARITY_TOLERANCE if scene_name == "dense" else PARITY_TOLERANCE,
    )

    assert parity.ready is True, parity.to_dict()
