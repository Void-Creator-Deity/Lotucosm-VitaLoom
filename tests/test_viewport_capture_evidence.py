# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from core.VitaLoom.viewports.viewport_capture_evidence import analyze_rgba_capture


BACKGROUND = (26, 140, 217, 255)


def _pixels(*rows: tuple[tuple[int, int, int, int], ...]) -> bytes:
    return bytes(channel for row in rows for pixel in row for channel in pixel)


def test_all_background_capture_is_not_render_evidence() -> None:
    evidence = analyze_rgba_capture(
        _pixels((BACKGROUND, BACKGROUND), (BACKGROUND, BACKGROUND)),
        width=2,
        height=2,
        background_rgba=BACKGROUND,
        current_context=True,
        draw_mode="qt_shader_instanced",
        gpu_draw_calls=1,
    )

    data = evidence.to_dict()
    assert data["width"] == 2
    assert data["height"] == 2
    assert data["format"] == "RGBA8888"
    assert data["sampled_pixels"] == 4
    assert data["non_background_pixels"] == 0
    assert data["occupied_bounds"] is None
    assert data["non_empty"] is False
    assert data["ready"] is False


def test_capture_reports_content_bounds_alpha_coverage_and_stable_digest() -> None:
    content = (255, 255, 255, 255)
    raw = _pixels((BACKGROUND, content), (BACKGROUND, BACKGROUND))

    evidence = analyze_rgba_capture(
        raw,
        width=2,
        height=2,
        background_rgba=BACKGROUND,
        current_context=True,
        draw_mode="qt_shader_instanced",
        gpu_draw_calls=1,
    )
    repeated = analyze_rgba_capture(
        raw,
        width=2,
        height=2,
        background_rgba=BACKGROUND,
        current_context=True,
        draw_mode="qt_shader_instanced",
        gpu_draw_calls=1,
    )

    data = evidence.to_dict()
    assert data["non_background_pixels"] == 1
    assert data["non_background_ratio"] == pytest.approx(0.25)
    assert data["alpha_covered_pixels"] == 4
    assert data["alpha_coverage"] == pytest.approx(1.0)
    assert data["occupied_bounds"] == [1, 0, 1, 0]
    assert data["digest"] == repeated.digest
    assert len(data["digest"]) == 64
    assert data["non_empty"] is True
    assert data["ready"] is True


def test_capture_rejects_silent_fallback_even_when_pixels_changed() -> None:
    evidence = analyze_rgba_capture(
        _pixels(((255, 255, 255, 255),)),
        width=1,
        height=1,
        background_rgba=BACKGROUND,
        current_context=True,
        fallback_used=True,
        draw_mode="diagnostic_or_qpainter_fallback",
        gpu_draw_calls=1,
    )

    data = evidence.to_dict()
    assert data["non_background_pixels"] == 1
    assert data["fallback_used"] is True
    assert data["ready"] is False


def test_capture_rejects_missing_context_or_reported_errors() -> None:
    evidence = analyze_rgba_capture(
        _pixels(((255, 255, 255, 255),)),
        width=1,
        height=1,
        background_rgba=BACKGROUND,
        current_context=False,
        draw_mode="qt_shader_instanced",
        gpu_draw_calls=1,
        errors=("context was lost",),
    )

    data = evidence.to_dict()
    assert data["current_context"] is False
    assert data["errors"] == ["context was lost"]
    assert data["ready"] is False


def test_capture_requires_exact_rgba_payload_length() -> None:
    with pytest.raises(ValueError, match="RGBA payload length"):
        analyze_rgba_capture(
            b"\x00\x00\x00\x00",
            width=2,
            height=1,
            background_rgba=BACKGROUND,
        )