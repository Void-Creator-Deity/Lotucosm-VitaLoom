# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError, is_dataclass
from typing import Any

import pytest

from core.VitaLoom.viewports.viewport_backend import (
    ViewportBackend,
    ViewportBackendInfo,
)
from core.VitaLoom.viewports.viewport_snapshot import build_viewport_frame_snapshot


class _NoopBackend:
    info = ViewportBackendInfo(
        name="noop",
        supports_gpu=False,
        supports_batching=False,
        fallback_reason="contract test",
    )

    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []
        self.size = (0, 0)
        self.quality: dict[str, Any] = {}

    def render(self, target: Any, frame: Any) -> None:
        self.calls.append(("render", frame))

    def resize(self, width: int, height: int) -> None:
        self.size = (width, height)

    def set_quality(self, quality: dict[str, Any]) -> None:
        self.quality = dict(quality)

    def stats(self) -> dict[str, Any]:
        return {
            "backend": self.info.name,
            "render_calls": len([call for call in self.calls if call[0] == "render"]),
            "width": self.size[0],
            "height": self.size[1],
        }


def test_backend_info_is_frozen_plain_metadata() -> None:
    info = ViewportBackendInfo(name="qpainter")

    assert is_dataclass(info)
    assert info.name == "qpainter"
    assert info.supports_gpu is False
    assert info.supports_batching is False
    assert info.fallback_reason == ""

    with pytest.raises(FrozenInstanceError):
        info.name = "mutated"


def test_noop_backend_satisfies_runtime_protocol() -> None:
    backend = _NoopBackend()
    frame = build_viewport_frame_snapshot([], width=320, height=180)

    assert isinstance(backend, ViewportBackend)
    backend.resize(320, 180)
    backend.set_quality({"antialias": True})
    backend.render(target=None, frame=frame)

    assert backend.quality == {"antialias": True}
    assert backend.stats() == {
        "backend": "noop",
        "render_calls": 1,
        "width": 320,
        "height": 180,
    }


def test_viewport_backend_module_stays_independent_from_live_runtime_types() -> None:
    import core.VitaLoom.viewports.viewport_backend as module

    source = inspect.getsource(module)

    assert ".pond" not in source
    assert "game_viewport" not in source
    assert "GameViewport" not in source
    assert "SceneRuntimeEntity" not in source
