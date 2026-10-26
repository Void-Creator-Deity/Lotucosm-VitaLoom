# -*- coding: utf-8 -*-
"""Scene package exports without eager manager imports."""
from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "SceneManager": ("core.VitaLoom.scene.scene_manager", "SceneManager"),
    "get_scene_manager": ("core.VitaLoom.scene.scene_manager", "get_scene_manager"),
    "SceneSwitcher": ("core.VitaLoom.scene.scene_switcher", "SceneSwitcher"),
    "SceneWizard": ("core.VitaLoom.scene.scene_switcher", "SceneWizard"),
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
