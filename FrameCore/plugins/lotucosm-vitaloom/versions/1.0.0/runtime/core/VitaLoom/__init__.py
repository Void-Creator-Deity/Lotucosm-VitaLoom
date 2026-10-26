"""VitaLoom package exports without eager editor host imports."""
from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "EditorKernel": ("core.VitaLoom.kernel", "EditorKernel"),
    "PluginLoader": ("core.VitaLoom.kernel", "PluginLoader"),
    "EventBus": ("core.VitaLoom.kernel", "EventBus"),
    "LayoutManager": ("core.VitaLoom.kernel", "LayoutManager"),
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
