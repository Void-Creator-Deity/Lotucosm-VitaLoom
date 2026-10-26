# -*- coding: utf-8 -*-
"""Qt-free runtime capability registry for the versioned VitaLoom engine plugin.

This L1 Module is intentionally separate from ``FrameCore.service_registry``.
The L0 registry discovers Frame/Suite-level services; this registry belongs to
one composed VitaLoom runtime Host (Editor, Player, or headless command run).
It does not own publication lifecycles: ``CapabilityPublicationLease`` remains
the sole exact-unpublication authority.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable


RUNTIME_CAPABILITY_REGISTRY_CONTEXT_KEY = "runtime_capability_registry"


@runtime_checkable
class RuntimeCapabilityRegistry(Protocol):
    """Minimal L1 Interface shared by runtime capability publishers/consumers."""

    def register(self, key: str, capability: object) -> None: ...

    def unregister(self, key: str) -> None: ...

    def get(self, key: str, default: Any = None) -> Any: ...

    def has(self, key: str) -> bool: ...


def _normalize_key(key: object) -> str:
    if not isinstance(key, str):
        raise TypeError("runtime capability key must be a string")
    normalized = key.strip()
    if not normalized:
        raise ValueError("runtime capability key must not be empty")
    return normalized


class InMemoryRuntimeCapabilityRegistry:
    """Process-local registry Implementation with last-writer-wins lookup."""

    def __init__(self) -> None:
        self._capabilities: dict[str, object] = {}

    def register(self, key: str, capability: object) -> None:
        normalized = _normalize_key(key)
        if capability is None:
            raise ValueError("runtime capability must not be None")
        self._capabilities[normalized] = capability

    def unregister(self, key: str) -> None:
        self._capabilities.pop(_normalize_key(key), None)

    def get(self, key: str, default: Any = None) -> Any:
        return self._capabilities.get(_normalize_key(key), default)

    def has(self, key: str) -> bool:
        return _normalize_key(key) in self._capabilities


def require_runtime_capability_registry(source: object) -> RuntimeCapabilityRegistry:
    """Validate an explicitly composed L1 registry or fail at the seam."""

    if not isinstance(source, RuntimeCapabilityRegistry):
        raise TypeError(
            "runtime capability registry must provide "
            "register/unregister/get/has"
        )
    return source


def resolve_runtime_capability_registry(
    source: object | None,
) -> RuntimeCapabilityRegistry | None:
    """Resolve a registry from an explicit registry, command context, or Adapter.

    Accepted compatibility shapes are deliberately narrow:

    - the L1 registry itself;
    - a command context containing ``runtime_capability_registry``;
    - a legacy command context containing ``editor_context``;
    - a legacy Host Adapter exposing ``.services``.

    This function never creates a registry and never imports Qt. Composition
    roots own construction and lifetime.
    """

    if source is None:
        return None
    if isinstance(source, RuntimeCapabilityRegistry):
        return source
    if isinstance(source, Mapping):
        if RUNTIME_CAPABILITY_REGISTRY_CONTEXT_KEY in source:
            explicit = source[RUNTIME_CAPABILITY_REGISTRY_CONTEXT_KEY]
            return require_runtime_capability_registry(explicit)
        if "editor_context" in source:
            return resolve_runtime_capability_registry(source["editor_context"])
        return None
    services = getattr(source, "services", None)
    if services is None:
        return None
    return require_runtime_capability_registry(services)


# Compatibility name for legacy plugin imports. New code should use the
# domain-specific name above.
ServiceRegistry = InMemoryRuntimeCapabilityRegistry


__all__ = [
    "InMemoryRuntimeCapabilityRegistry",
    "RUNTIME_CAPABILITY_REGISTRY_CONTEXT_KEY",
    "RuntimeCapabilityRegistry",
    "ServiceRegistry",
    "require_runtime_capability_registry",
    "resolve_runtime_capability_registry",
]
