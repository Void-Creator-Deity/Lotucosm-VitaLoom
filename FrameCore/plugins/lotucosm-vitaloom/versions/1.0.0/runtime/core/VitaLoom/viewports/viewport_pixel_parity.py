# -*- coding: utf-8 -*-
"""Qt-free tolerance metrics for viewport Adapter pixel parity."""

from __future__ import annotations

from dataclasses import dataclass

from core.VitaLoom.viewports.viewport_pixel_capture import ViewportPixelCapture


@dataclass(frozen=True)
class ViewportParityTolerance:
    max_bounds_delta: int = 0
    max_non_background_ratio_delta: float = 0.0
    max_alpha_coverage_delta: float = 0.0
    pixel_channel_tolerance: int = 0
    max_pixel_mismatch_ratio: float = 0.0
    max_mean_absolute_channel_error: float = 0.0

    def __post_init__(self) -> None:
        if self.max_bounds_delta < 0:
            raise ValueError("max_bounds_delta must be non-negative")
        if not 0.0 <= self.max_non_background_ratio_delta <= 1.0:
            raise ValueError("max_non_background_ratio_delta must be in range 0..1")
        if not 0.0 <= self.max_alpha_coverage_delta <= 1.0:
            raise ValueError("max_alpha_coverage_delta must be in range 0..1")
        if not 0 <= self.pixel_channel_tolerance <= 255:
            raise ValueError("pixel_channel_tolerance must be in range 0..255")
        if not 0.0 <= self.max_pixel_mismatch_ratio <= 1.0:
            raise ValueError("max_pixel_mismatch_ratio must be in range 0..1")
        if self.max_mean_absolute_channel_error < 0.0:
            raise ValueError("max_mean_absolute_channel_error must be non-negative")


@dataclass(frozen=True)
class ViewportPixelParity:
    dimensions_match: bool
    format_match: bool
    bounds_delta: tuple[int, int, int, int] | None
    non_background_ratio_delta: float
    alpha_coverage_delta: float
    pixel_mismatch_count: int
    pixel_mismatch_ratio: float
    mean_absolute_channel_error: float
    max_channel_error: int
    tolerance: ViewportParityTolerance
    failures: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.failures

    def to_dict(self) -> dict[str, object]:
        return {
            "dimensions_match": self.dimensions_match,
            "format_match": self.format_match,
            "bounds_delta": list(self.bounds_delta) if self.bounds_delta is not None else None,
            "non_background_ratio_delta": self.non_background_ratio_delta,
            "alpha_coverage_delta": self.alpha_coverage_delta,
            "pixel_mismatch_count": self.pixel_mismatch_count,
            "pixel_mismatch_ratio": self.pixel_mismatch_ratio,
            "mean_absolute_channel_error": self.mean_absolute_channel_error,
            "max_channel_error": self.max_channel_error,
            "failures": list(self.failures),
            "ready": self.ready,
        }


def compare_viewport_pixel_captures(
    reference: ViewportPixelCapture,
    candidate: ViewportPixelCapture,
    *,
    tolerance: ViewportParityTolerance | None = None,
) -> ViewportPixelParity:
    limits = tolerance or ViewportParityTolerance()
    dimensions_match = (reference.width, reference.height) == (candidate.width, candidate.height)
    format_match = reference.format == candidate.format
    failures: list[str] = []
    if not dimensions_match:
        failures.append("dimensions")
    if not format_match:
        failures.append("format")

    bounds_delta = _bounds_delta(
        reference.evidence.occupied_bounds,
        candidate.evidence.occupied_bounds,
    )
    if bounds_delta is None:
        failures.append("occupied_bounds")
    elif max(bounds_delta, default=0) > limits.max_bounds_delta:
        failures.append("occupied_bounds")

    non_background_ratio_delta = abs(
        reference.evidence.non_background_ratio - candidate.evidence.non_background_ratio
    )
    if non_background_ratio_delta > limits.max_non_background_ratio_delta:
        failures.append("non_background_ratio")

    alpha_coverage_delta = abs(reference.evidence.alpha_coverage - candidate.evidence.alpha_coverage)
    if alpha_coverage_delta > limits.max_alpha_coverage_delta:
        failures.append("alpha_coverage")

    mismatch_count = 0
    mismatch_ratio = 1.0 if not dimensions_match else 0.0
    mean_error = 255.0 if not dimensions_match else 0.0
    max_error = 255 if not dimensions_match else 0
    if dimensions_match:
        sampled_pixels = reference.width * reference.height
        absolute_error_sum = 0
        for offset in range(0, len(reference.pixels), 4):
            channel_errors = tuple(
                abs(reference.pixels[offset + channel] - candidate.pixels[offset + channel])
                for channel in range(4)
            )
            absolute_error_sum += sum(channel_errors)
            max_error = max(max_error, *channel_errors)
            if any(error > limits.pixel_channel_tolerance for error in channel_errors):
                mismatch_count += 1
        mismatch_ratio = mismatch_count / sampled_pixels if sampled_pixels else 0.0
        channel_count = sampled_pixels * 4
        mean_error = absolute_error_sum / channel_count if channel_count else 0.0

    if mismatch_ratio > limits.max_pixel_mismatch_ratio:
        failures.append("pixel_mismatch_ratio")
    if mean_error > limits.max_mean_absolute_channel_error:
        failures.append("mean_absolute_channel_error")

    return ViewportPixelParity(
        dimensions_match=dimensions_match,
        format_match=format_match,
        bounds_delta=bounds_delta,
        non_background_ratio_delta=non_background_ratio_delta,
        alpha_coverage_delta=alpha_coverage_delta,
        pixel_mismatch_count=mismatch_count,
        pixel_mismatch_ratio=mismatch_ratio,
        mean_absolute_channel_error=mean_error,
        max_channel_error=max_error,
        tolerance=limits,
        failures=tuple(dict.fromkeys(failures)),
    )


def _bounds_delta(
    reference: tuple[int, int, int, int] | None,
    candidate: tuple[int, int, int, int] | None,
) -> tuple[int, int, int, int] | None:
    if reference is None and candidate is None:
        return (0, 0, 0, 0)
    if reference is None or candidate is None:
        return None
    return tuple(abs(left - right) for left, right in zip(reference, candidate))  # type: ignore[return-value]


__all__ = [
    "ViewportParityTolerance",
    "ViewportPixelParity",
    "compare_viewport_pixel_captures",
]
