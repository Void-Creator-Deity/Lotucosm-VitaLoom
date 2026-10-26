# -*- coding: utf-8 -*-
from __future__ import annotations

import sys

import pytest

from core.VitaLoom.viewports.opengl_canvas import probe_qt_opengl_canvas_smoke
from core.VitaLoom.viewports.viewport_draw_commands import compile_viewport_draw_commands
from core.VitaLoom.viewports.viewport_snapshot import (
    ViewportEdgeSnapshot,
    ViewportEntitySnapshot,
    ViewportFrameSnapshot,
)


def _scene(name: str) -> ViewportFrameSnapshot:
    if name == "empty":
        return ViewportFrameSnapshot(width=320, height=240)
    if name == "single":
        return ViewportFrameSnapshot(
            width=320,
            height=240,
            entities=(
                ViewportEntitySnapshot(id="a", entity_type="organism", position=(10.0, 20.0), radius=5.0),
            ),
        )
    if name == "selected":
        return ViewportFrameSnapshot(
            width=320,
            height=240,
            entities=(
                ViewportEntitySnapshot(
                    id="a",
                    entity_type="organism",
                    position=(10.0, 20.0),
                    radius=5.0,
                    selected=True,
                ),
            ),
        )
    if name == "edge":
        return ViewportFrameSnapshot(
            width=320,
            height=240,
            entities=(
                ViewportEntitySnapshot(id="a", entity_type="organism", position=(10.0, 20.0), radius=5.0),
                ViewportEntitySnapshot(id="b", entity_type="nutrient", position=(30.0, 40.0), radius=6.0),
            ),
            edges=(ViewportEdgeSnapshot(source_id="a", target_id="b", kind="hard"),),
        )
    if name == "hidden":
        return ViewportFrameSnapshot(
            width=320,
            height=240,
            entities=(
                ViewportEntitySnapshot(id="a", entity_type="organism", position=(10.0, 20.0), radius=5.0),
                ViewportEntitySnapshot(id="b", entity_type="nutrient", position=(30.0, 40.0), radius=6.0, visible=False),
            ),
            edges=(ViewportEdgeSnapshot(source_id="a", target_id="b", kind="hard"),),
        )
    raise AssertionError(name)


def test_qt_opengl_canvas_smoke_returns_structured_result() -> None:
    result = probe_qt_opengl_canvas_smoke()

    assert result["target"] == "qt_opengl_canvas_smoke"
    assert "qopenglwidget_available" in result
    assert "qapplication_available" in result
    assert "context_current" in result
    assert "rendered" in result
    assert "skip_reason" in result
    assert "pixel_probe" in result
    assert "non_empty" in result["pixel_probe"]
    if not result["rendered"]:
        assert result["skip_reason"]


def test_qt_opengl_canvas_smoke_renders_pixels_or_skips_with_reason() -> None:
    result = probe_qt_opengl_canvas_smoke()
    if not result["rendered"]:
        pytest.skip(str(result["skip_reason"]))

    assert result["qopenglwidget_available"] is True
    assert result["qapplication_available"] is True
    assert result["context_current"] is True
    assert result["initialize_calls"] >= 1
    assert result["paint_calls"] >= 1
    assert result["pixel_probe"]["non_empty"] is True


def test_windows_current_context_produces_real_scene_pixels_without_fallback() -> None:
    if sys.platform != "win32":
        pytest.skip("controlled current-context proof is a Windows gate")

    result = probe_qt_opengl_canvas_smoke(frame=_scene("edge"), width=160, height=120)

    assert result["rendered"] is True, result["skip_reason"]
    assert result["context_current"] is True
    assert result["pixel_probe"]["ready"] is True
    assert result["pixel_probe"]["non_background_pixels"] > 0
    assert result["pixel_probe"]["occupied_bounds"] is not None
    assert result["pixel_probe"]["fallback_used"] is False
    assert result["pixel_probe"]["gpu_draw_calls"] > 0
    assert result["pixel_probe"]["errors"] == []
    assert len(result["pixel_probe"]["digest"]) == 64


def test_qt_opengl_canvas_smoke_records_representative_frame_target_snapshot() -> None:
    frame = _scene("edge")

    result = probe_qt_opengl_canvas_smoke(frame=frame)
    if not result["rendered"]:
        pytest.skip(str(result["skip_reason"]))

    assert result["frame"]["commands"] == 3
    assert result["frame"]["batches"] == 3
    assert result["frame"]["instances"] == 3
    assert result["frame"]["first_command"] == "line:a:b"
    assert result["target_snapshot"]["target"] == "qt_opengl_texture"
    assert result["target_snapshot"]["context_current"] is True
    assert result["target_snapshot"]["pending_instances"] == 3


@pytest.mark.parametrize("scene_name", ["empty", "single", "selected", "edge", "hidden"])
def test_qt_opengl_canvas_smoke_frame_counts_match_draw_commands(scene_name: str) -> None:
    frame = _scene(scene_name)
    expected_commands = compile_viewport_draw_commands(frame)

    result = probe_qt_opengl_canvas_smoke(frame=frame)
    if not result["rendered"]:
        pytest.skip(str(result["skip_reason"]))

    assert result["frame"]["commands"] == len(expected_commands)
    assert result["frame"]["instances"] == len(expected_commands)
    assert result["target_snapshot"]["context_current"] is True
    assert result["target_snapshot"]["pending_instances"] == len(expected_commands)
    assert result["target_snapshot"]["fallback_required"] is False
