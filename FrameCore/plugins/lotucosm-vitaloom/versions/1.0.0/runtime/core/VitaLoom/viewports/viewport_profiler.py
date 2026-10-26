# -*- coding: utf-8 -*-
"""Small rolling profiler for viewport frame phases."""

from __future__ import annotations

import time
from collections import deque
from contextlib import contextmanager
from typing import Callable, Iterator


DEFAULT_VIEWPORT_PROFILE_BUCKETS = ("script", "spawn", "fluid", "physics", "render", "total")


class ViewportFrameProfiler:
    def __init__(
        self,
        *,
        buckets: tuple[str, ...] = DEFAULT_VIEWPORT_PROFILE_BUCKETS,
        window: int = 90,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._clock = clock
        self._window = max(1, int(window))
        self._samples = {name: deque(maxlen=self._window) for name in buckets}

    def record(self, bucket: str, elapsed_ms: object) -> None:
        try:
            samples = self._samples.get(str(bucket))
            if samples is None:
                return
            value = float(elapsed_ms)
            if value < 0.0:
                return
            samples.append(value)
        except Exception:
            return

    @contextmanager
    def measure(self, bucket: str) -> Iterator[None]:
        try:
            start = self._clock()
        except Exception:
            start = None
        try:
            yield
        finally:
            if start is None:
                return
            try:
                self.record(bucket, (self._clock() - start) * 1000.0)
            except Exception:
                return

    def snapshot(self) -> dict[str, dict[str, float | int]]:
        out: dict[str, dict[str, float | int]] = {}
        for name, samples in self._samples.items():
            values = list(samples)
            last = values[-1] if values else 0.0
            avg = (sum(values) / len(values)) if values else 0.0
            out[name] = {
                "last_ms": round(float(last), 3),
                "avg_ms": round(float(avg), 3),
                "samples": len(values),
            }
        return out

    def structured_snapshot(self) -> dict[str, object]:
        buckets = self.snapshot()
        frame_count = 0
        for data in buckets.values():
            frame_count = max(frame_count, int(data.get("samples", 0)))
        return {
            "bucket_names": list(self._samples.keys()),
            "frame_count": frame_count,
            "window": self._window,
            "buckets": buckets,
        }


__all__ = [
    "DEFAULT_VIEWPORT_PROFILE_BUCKETS",
    "ViewportFrameProfiler",
]
