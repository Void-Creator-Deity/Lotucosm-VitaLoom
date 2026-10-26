# -*- coding: utf-8 -*-
"""Tool package exports without eager manager imports."""
from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "ToolManager": ("core.VitaLoom.tools.tool_manager", "ToolManager"),
    "ToolType": ("core.VitaLoom.tools.tool_manager", "ToolType"),
    "BaseTool": ("core.VitaLoom.tools.tool_manager", "BaseTool"),
    "SelectTool": ("core.VitaLoom.tools.tool_manager", "SelectTool"),
    "MoveTool": ("core.VitaLoom.tools.tool_manager", "MoveTool"),
    "ConnectTool": ("core.VitaLoom.tools.tool_manager", "ConnectTool"),
    "PanTool": ("core.VitaLoom.tools.tool_manager", "PanTool"),
    "ZoomTool": ("core.VitaLoom.tools.tool_manager", "ZoomTool"),
    "get_tool_manager": ("core.VitaLoom.tools.tool_manager", "get_tool_manager"),
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
