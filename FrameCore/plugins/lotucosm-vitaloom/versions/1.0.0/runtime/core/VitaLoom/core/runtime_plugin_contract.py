# -*- coding: utf-8 -*-
"""Qt-free lifecycle and domain-provider Interfaces for nested engine plugins.

This Module belongs to the versioned runtime of the sole L1
`lotucosm-vitaloom` engine/product plugin.  It is the lifecycle authority for
L2 capability packages, L3 engine extensions, and L4 Project World addons.
It intentionally knows nothing about PyQt, widgets, the EditorKernel, or a
concrete Host Adapter.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Protocol, Type, runtime_checkable


if TYPE_CHECKING:
    from core.VitaLoom.commands.registry import CommandSpec


class IRuntimePlugin(ABC):
    """Minimal lifecycle Interface shared by nested VitaLoom plugins.

    The Host chooses the activation projection from validated plugin metadata.
    Implementations must treat the supplied object as the declared activation
    Interface and release every owned publication/subscription in on_unload().
    """

    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]:
        """Return stable plugin metadata used for identity and lifecycle planning."""
        raise NotImplementedError

    @abstractmethod
    def on_load(self, runtime_context: object) -> None:
        """Activate against the Host-provided runtime Interface."""
        raise NotImplementedError

    @abstractmethod
    def on_unload(self) -> None:
        """Release resources acquired by on_load()."""
        raise NotImplementedError


@runtime_checkable
class IRuntimePluginTeardown(Protocol):
    """Optional staged teardown Interface for concrete Host contribution owners.

    A plugin implements this Interface when runtime resources must be released
    before a concrete Host Adapter removes or destroys projected contributions.
    The method must be retryable and idempotent. It must not remove the Host
    contribution itself; that remains the Adapter's authority.
    """

    def prepare_host_teardown(self) -> None:
        """Release resources that must not outlive concrete Host contributions."""
        ...


class ICommandProvider(ABC):
    """Qt-free provider for commands shared by UI, CLI, MCP, and agents."""

    @abstractmethod
    def get_command_specs(self) -> List["CommandSpec"]:
        """Return the complete command batch contributed by this plugin."""
        raise NotImplementedError


class IEntityTypeProvider(IRuntimePlugin):
    """Runtime/domain provider for constructible entity types."""

    @abstractmethod
    def get_entity_types(self) -> List[Type]:
        """Return entity classes contributed by this plugin."""
        raise NotImplementedError

    @abstractmethod
    def create_entity(self, entity_type: str, **kwargs):
        """Create one entity instance for the requested type identifier."""
        raise NotImplementedError


class IComponentTypeProvider(IRuntimePlugin):
    """Runtime/domain provider for constructible component types."""

    @abstractmethod
    def get_component_types(self) -> List[Type]:
        """Return component classes contributed by this plugin."""
        raise NotImplementedError

    @abstractmethod
    def create_component(self, component_type: str, **kwargs):
        """Create one component instance for the requested type identifier."""
        raise NotImplementedError


__all__ = [
    "IComponentTypeProvider",
    "IEntityTypeProvider",
    "ICommandProvider",
    "IRuntimePlugin",
    "IRuntimePluginTeardown",
]
