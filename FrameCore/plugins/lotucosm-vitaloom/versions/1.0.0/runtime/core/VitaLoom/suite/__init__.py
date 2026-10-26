# -*- coding: utf-8 -*-
"""Suite adapter exports without eager runtime imports."""
from __future__ import annotations

__all__ = ["load_product_registry", "resolve_project_runtime"]


def __getattr__(name: str):
    if name == "load_product_registry":
        from core.VitaLoom.suite.product_registry import load_product_registry

        return load_product_registry
    if name == "resolve_project_runtime":
        from core.VitaLoom.suite.project_lock import resolve_project_runtime

        return resolve_project_runtime
    raise AttributeError(name)
