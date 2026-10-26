# -*- coding: utf-8 -*-
"""VitaLoom Player exports."""
from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "PlayerShell": ("core.VitaLoom.player.player_shell", "PlayerShell"),
    "run_player_shell": ("core.VitaLoom.player.player_shell", "run_player_shell"),
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
