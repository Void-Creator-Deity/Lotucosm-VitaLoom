# -*- coding: utf-8 -*-
"""Viewport rendering backend contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from core.VitaLoom.viewports.viewport_snapshot import ViewportFrameSnapshot


@dataclass(frozen=True)
class ViewportBackendInfo:
    name: str
    supports_gpu: bool = False
    supports_batching: bool = False
    fallback_reason: str = ""


@runtime_checkable
class ViewportBackend(Protocol):
    info: ViewportBackendInfo

    def render(self, target: Any, frame: ViewportFrameSnapshot) -> None:
        """Render one immutable viewport frame into the backend target."""

    def resize(self, width: int, height: int) -> None:
        """Notify the backend that its target size changed."""

    def set_quality(self, quality: dict[str, Any]) -> None:
        """Apply render quality options expressed as plain data."""

    def stats(self) -> dict[str, Any]:
        """Return backend diagnostics as plain data."""


__all__ = [
    "ViewportBackend",
    "ViewportBackendInfo",
]
