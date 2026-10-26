# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
import sys
from dataclasses import replace

import pytest

from core.VitaLoom.viewports.opengl_canvas import probe_qt_opengl_interaction_sequence
from core.VitaLoom.viewports.viewport_draw_commands import (
    CircleCommand,
    LineCommand,
    compile_viewport_draw_commands,
)
from core.VitaLoom.viewports.viewport_snapshot import (
    ViewportCameraSnapshot,
    ViewportEdgeSnapshot,
    ViewportEntitySnapshot,
    ViewportFrameSnapshot,
)


def _frame(*, selected: bool = False, camera: ViewportCameraSnapshot | None = None, width: int = 160, height: int = 120) -> ViewportFrameSnapshot:
    return ViewportFrameSnapshot(
        width=width,
        height=height,
        camera=camera or ViewportCameraSnapshot(),
        entities=(
            ViewportEntitySnapshot(
                id="a",
                entity_type="organism",
                position=(28.0, 24.0),
                radius=6.0,
                selected=selected,
            ),
            ViewportEntitySnapshot(
                id="b",
                entity_type="nutrient",
                position=(88.0, 72.0),
                radius=8.0,
            ),
        ),
        edges=(ViewportEdgeSnapshot(source_id="a", target_id="b", kind="hard", weight=2.0),),
        metadata={"immutable_probe": True},
    )


def test_camera_pan_zoom_projection_is_compiled_at_the_qt_free_command_seam() -> None:
    frame = ViewportFrameSnapshot(
        width=160,
        height=120,
        camera=ViewportCameraSnapshot(position=(7.0, -3.0), zoom=2.0),
        entities=(
            ViewportEntitySnapshot(id="a", entity_type="organism", position=(20.0, 15.0), radius=5.0),
            ViewportEntitySnapshot(id="b", entity_type="nutrient", position=(30.0, 25.0), radius=4.0),
        ),
        edges=(ViewportEdgeSnapshot(source_id="a", target_id="b", kind="hard", weight=1.5),),
    )

    commands = compile_viewport_draw_commands(frame)

    line = next(command for command in commands if isinstance(command, LineCommand))
    circle = next(
        command
        for command in commands
        if isinstance(command, CircleCommand) and command.entity_id == "a"
    )
    assert line.start == (47.0, 27.0)
    assert line.end == (67.0, 47.0)
    assert line.width == 3.0
    assert circle.center == (47.0, 27.0)
    assert circle.radius == 10.0
    assert circle.stroke_width == 2.0


def test_camera_zoom_rejects_non_positive_values() -> None:
    frame = _frame(camera=ViewportCameraSnapshot(zoom=0.0))

    with pytest.raises(ValueError, match="camera.zoom"):
        compile_viewport_draw_commands(frame)


def test_interaction_probe_only_accepts_immutable_frames_and_plain_options() -> None:
    signature = inspect.signature(probe_qt_opengl_interaction_sequence)

    assert list(signature.parameters) == ["frames", "process_events"]


@pytest.mark.skipif(sys.platform != "win32", reason="controlled current-context interaction proof is a Windows gate")
def test_windows_interaction_sequence_changes_pixels_without_stale_state_and_releases_context() -> None:
    base = _frame()
    panned = replace(base, camera=ViewportCameraSnapshot(position=(18.0, 7.0), zoom=1.0))
    zoomed = replace(base, camera=ViewportCameraSnapshot(position=(18.0, 7.0), zoom=1.35))
    selected = replace(zoomed, entities=(replace(zoomed.entities[0], selected=True), zoomed.entities[1]))
    repeated = selected
    resized = replace(selected, width=211, height=137)
    frames = (base, panned, zoomed, selected, repeated, resized)
    before = tuple(frames)

    result = probe_qt_opengl_interaction_sequence(frames=frames)

    assert tuple(frames) == before
    assert result["completed"] is True, result
    assert result["context_released"] is True
    assert result["teardown_errors"] == []
    assert result["target_recreations"] >= len(frames)
    assert result["project_world_mutations"] == 0
    assert result["plugin_publications"] == 0

    records = result["records"]
    assert len(records) == len(frames)
    assert all(record["context_current"] is True for record in records)
    assert all(record["fallback_required"] is False for record in records)
    assert all(record["errors"] == [] for record in records)
    assert all(record["pending_instances"] == record["instances"] for record in records)
    assert len({record["target_generation"] for record in records}) == len(frames)

    digests = [record["logical_digest"] for record in records]
    assert digests[0] != digests[1]
    assert digests[1] != digests[2]
    assert digests[2] != digests[3]
    assert digests[3] == digests[4]
    assert digests[4] != digests[5]
    assert records[3]["commands"] == records[2]["commands"] + 1
    assert records[4]["commands"] == records[3]["commands"]
    assert records[5]["logical_dimensions"] == [211, 137]
    assert records[5]["framebuffer_dimensions"] != records[4]["framebuffer_dimensions"]
