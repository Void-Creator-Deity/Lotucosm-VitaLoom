# -*- coding: utf-8 -*-
"""Core host exports without eager singleton imports."""
from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "EditorContext": ("core.VitaLoom.core.editor_context", "EditorContext"),
    "EditorMode": ("core.VitaLoom.core.editor_context", "EditorMode"),
    "get_editor_context": ("core.VitaLoom.core.editor_context", "get_editor_context"),
    "SignalBus": ("core.VitaLoom.core.signal_bus", "SignalBus"),
    "SignalType": ("core.VitaLoom.core.signal_bus", "SignalType"),
    "get_signal_bus": ("core.VitaLoom.core.signal_bus", "get_signal_bus"),
    "ErrorHandler": ("core.VitaLoom.core.error_handler", "ErrorHandler"),
    "get_error_handler": ("core.VitaLoom.core.error_handler", "get_error_handler"),
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
