# -*- coding: utf-8 -*-
"""Viewport package exports without eager viewport construction imports."""
from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "SceneViewport": ("core.VitaLoom.viewports.scene_viewport", "SceneViewport"),
    "GameViewport": ("core.VitaLoom.viewports.game_viewport", "GameViewport"),
    "ViewportManager": ("core.VitaLoom.viewports.viewport_manager", "ViewportManager"),
    "ViewportType": ("core.VitaLoom.viewports.viewport_manager", "ViewportType"),
    "get_viewport_manager": (
        "core.VitaLoom.viewports.viewport_manager",
        "get_viewport_manager",
    ),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    try:
        module_name, attr_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
