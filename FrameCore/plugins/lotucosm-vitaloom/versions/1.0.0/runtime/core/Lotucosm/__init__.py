# -*- coding: utf-8 -*-
"""Lotucosm runtime domain package.

The package root preserves its historical public exports without importing
heavy implementations eagerly.  Capability packages such as ``sr_physics2d``
therefore remain importable in clean/headless processes, while callers of
``EntityBase``, ``Pond`` or ``Cosmos`` keep the same public Interface.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS: dict[str, tuple[str, str]] = {
    "EntityBase": (".entity", "EntityBase"),
    "Pond": (".pond", "Pond"),
    "Cosmos": (".cosmos", "Cosmos"),
    "get_cosmos": (".cosmos", "get_cosmos"),
    "Component": (".component", "Component"),
    "System": (".system", "System"),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    value = getattr(import_module(module_name, __name__), attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))