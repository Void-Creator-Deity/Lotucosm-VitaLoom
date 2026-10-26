"""Kernel package exports without eager editor imports."""
from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "EditorKernel": ("core.VitaLoom.kernel.editor_kernel", "EditorKernel"),
    "PluginLoader": ("core.VitaLoom.kernel.plugin_loader", "PluginLoader"),
    "EventBus": ("core.VitaLoom.kernel.event_bus", "EventBus"),
    "LayoutManager": ("core.VitaLoom.kernel.layout_manager", "LayoutManager"),
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
