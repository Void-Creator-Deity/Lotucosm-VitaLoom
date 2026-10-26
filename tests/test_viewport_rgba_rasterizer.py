# -*- coding: utf-8 -*-
from __future__ import annotations

from core.VitaLoom.viewports.opengl_batching import compile_opengl_batches
from core.VitaLoom.viewports.viewport_capture_evidence import analyze_rgba_capture
from core.VitaLoom.viewports.viewport_draw_commands import CircleCommand, LineCommand
from core.VitaLoom.viewports.viewport_rgba_rasterizer import rasterize_opengl_batches


BACKGROUND = (26, 140, 217, 255)


def _evidence(commands: tuple[object, ...], *, width: int = 32, height: int = 24):
    batches = compile_opengl_batches(commands)  # type: ignore[arg-type]
    pixels = rasterize_opengl_batches(
        batches,
        width=width,
        height=height,
        background_rgba=BACKGROUND,
    )
    return analyze_rgba_capture(
        pixels,
        width=width,
        height=height,
        background_rgba=BACKGROUND,
        current_context=True,
        draw_mode="qt_texture_blit",
        gpu_draw_calls=1,
    )


def test_rasterizer_draws_circle_pixels_with_deterministic_bounds() -> None:
    command = CircleCommand(
        kind="circle",
        entity_id="a",
        center=(10.0, 8.0),
        radius=4.0,
        fill=(255, 0, 0, 255),
        stroke=(255, 255, 255, 255),
        stroke_width=1.0,
    )

    evidence = _evidence((command,))
    repeated = _evidence((command,))

    assert evidence.non_background_pixels > 0
    assert evidence.occupied_bounds == (6, 4, 13, 11)
    assert evidence.digest == repeated.digest


def test_rasterizer_draws_line_pixels_and_clips_to_frame() -> None:
    command = LineCommand(
        kind="line",
        edge_id="a:b",
        start=(-10.0, 2.0),
        end=(40.0, 20.0),
        color=(255, 255, 255, 255),
        width=2.0,
    )

    evidence = _evidence((command,))

    assert evidence.non_background_pixels > 0
    assert evidence.occupied_bounds is not None
    assert evidence.occupied_bounds[0] == 0
    assert evidence.occupied_bounds[2] == 31


def test_transparent_fill_selected_ring_does_not_paint_circle_center() -> None:
    command = CircleCommand(
        kind="circle",
        entity_id="a:selected",
        center=(10.0, 8.0),
        radius=5.0,
        fill=(0, 0, 0, 0),
        stroke=(255, 230, 110, 255),
        stroke_width=2.0,
    )
    batches = compile_opengl_batches((command,))
    pixels = rasterize_opengl_batches(
        batches,
        width=24,
        height=20,
        background_rgba=BACKGROUND,
    )

    center = (8 * 24 + 10) * 4
    assert tuple(pixels[center : center + 4]) == BACKGROUND
    evidence = analyze_rgba_capture(
        pixels,
        width=24,
        height=20,
        background_rgba=BACKGROUND,
        current_context=True,
        draw_mode="qt_texture_blit",
        gpu_draw_calls=1,
    )
    assert evidence.non_background_pixels > 0