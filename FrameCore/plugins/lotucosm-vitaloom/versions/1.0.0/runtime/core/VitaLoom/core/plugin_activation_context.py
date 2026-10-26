# -*- coding: utf-8 -*-
"""Qt-free activation projection for runtime-only nested engine plugins.

The projection belongs to one composed L1 VitaLoom Host. It intentionally
exposes only the capability registry and Host-scoped runtime event bus. Legacy
UI plugins continue to receive the concrete EditorContext Adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .runtime_capability_registry import (
    RuntimeCapabilityRegistry,
    require_runtime_capability_registry,
)
from .runtime_event_bus import RuntimeEventBus, require_runtime_event_bus


RUNTIME_PLUGIN_ACTIVATION_CONTEXT = "runtime"
LEGACY_UI_PLUGIN_ACTIVATION_CONTEXT = "legacy_ui"


@runtime_checkable
class RuntimePluginActivationContext(Protocol):
    """Narrow Interface available to runtime-only plugin activation."""

    @property
    def services(self) -> RuntimeCapabilityRegistry: ...

    @property
    def event_bus(self) -> RuntimeEventBus: ...


@dataclass(frozen=True, slots=True)
class RuntimePluginActivationProjection:
    """Immutable view of the two L1 runtime seams shared by non-UI plugins."""

    services: RuntimeCapabilityRegistry
    event_bus: RuntimeEventBus

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "services",
            require_runtime_capability_registry(self.services),
        )
        object.__setattr__(
            self,
            "event_bus",
            require_runtime_event_bus(self.event_bus),
        )


def project_runtime_plugin_activation_context(
    host_context: object,
) -> RuntimePluginActivationProjection:
    """Project a legacy Host Adapter into the narrow runtime plugin Interface."""

    registry = getattr(host_context, "services", None)
    try:
        registry = require_runtime_capability_registry(registry)
    except TypeError as exc:
        raise TypeError(
            "plugin Host context must expose a runtime capability registry"
        ) from exc

    event_bus = getattr(host_context, "event_bus", None)
    try:
        event_bus = require_runtime_event_bus(event_bus)
    except TypeError as exc:
        raise TypeError("plugin Host context must expose a runtime event bus") from exc

    return RuntimePluginActivationProjection(
        services=registry,
        event_bus=event_bus,
    )


__all__ = [
    "LEGACY_UI_PLUGIN_ACTIVATION_CONTEXT",
    "RUNTIME_PLUGIN_ACTIVATION_CONTEXT",
    "RuntimePluginActivationContext",
    "RuntimePluginActivationProjection",
    "project_runtime_plugin_activation_context",
]
