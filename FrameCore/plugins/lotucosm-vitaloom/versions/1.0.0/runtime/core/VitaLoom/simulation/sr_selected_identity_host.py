# -*- coding: utf-8 -*-
"""Dedicated Seam for current editor-selection to SR identity resolution."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from core.VitaLoom.core.service_keys import SR_SELECTED_IDENTITY_HOST


@runtime_checkable
class ISrSelectedIdentityHost(Protocol):
    def resolve_selected_sr_runtime_entity(
        self,
        *,
        explicit_identity: object | None = None,
        selection_scene_path: str | None = None,
    ) -> dict[str, Any]: ...


class _NullSrSelectedIdentityHost:
    def resolve_selected_sr_runtime_entity(
        self,
        *,
        explicit_identity: object | None = None,
        selection_scene_path: str | None = None,
    ) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "status": "unavailable",
            "scope": "selected_sr_runtime_entity",
            "authority": "sr_selected_identity_correlation",
            "track": "sr_play",
            "read_only": True,
            "selection_relation": "scene_correlated_not_unified",
            "identity": None,
            "reason": "selected_identity_host_unavailable",
        }


def get_sr_selected_identity_host(source: Any = None) -> ISrSelectedIdentityHost:
    """Resolve selected-identity Host from explicit registry/context or legacy state."""
    from core.VitaLoom.core.runtime_capability_registry import (
        resolve_runtime_capability_registry,
    )

    registry = resolve_runtime_capability_registry(source)
    if registry is None and source is None:
        try:
            from core.VitaLoom.core.editor_context import get_existing_editor_context

            registry = resolve_runtime_capability_registry(get_existing_editor_context())
        except Exception:
            registry = None
    host = registry.get(SR_SELECTED_IDENTITY_HOST) if registry is not None else None
    if isinstance(host, ISrSelectedIdentityHost):
        return host
    return _NullSrSelectedIdentityHost()
