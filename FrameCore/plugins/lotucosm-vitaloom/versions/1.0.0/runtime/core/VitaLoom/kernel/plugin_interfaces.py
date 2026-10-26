"""Legacy editor plugin compatibility interfaces (not new-plugin authority).

Qt-free discovery, lifecycle, dependency ordering, and copied metadata authority
belong to ``core.VitaLoom.core.runtime_plugin_contract`` and
``RuntimePluginHost``. This module keeps established public import paths,
inheritance relationships, and abstract payload shapes for existing PyQt editor
plugins. ``LegacyEditorPluginAdapter`` is the only concrete UI-host consumer.

New plugins must inherit ``IRuntimePlugin`` directly and publish JSON-safe
``editor_contributions``. Concrete QWidget and QSS payloads remain in
Adapter-local factories. These legacy types must not become host discovery,
lifecycle, or contribution-ownership authority.

Compatibility guarantee: importing this module never imports PyQt6. Its public
names, inheritance relationships, and abstract method signatures remain stable.
Except for the deliberate dual adapter MRO of ``IEntityTypeProvider`` and
``IComponentTypeProvider``, legacy UI payloads are recognized in the adapter by
callable shape, not by ``isinstance`` type gates.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict

from core.VitaLoom.core.runtime_plugin_contract import (
    IComponentTypeProvider as IRuntimeComponentTypeProvider,
    ICommandProvider,
    IEntityTypeProvider as IRuntimeEntityTypeProvider,
    IRuntimePlugin,
)

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QDockWidget, QWidget


class IEditorPlugin(IRuntimePlugin):
    """Public legacy base with optional Adapter-local ``on_editor_ready``.

    Required initialization remains in ``on_load`` and explicit runtime
    contracts. The adapter calls ``on_editor_ready`` after UI projection on a
    best-effort basis; it is not a lifecycle gate. New plugins inherit
    ``IRuntimePlugin`` directly.
    """

    def on_editor_ready(self) -> None:
        """Optional best-effort notification after legacy UI composition."""
        return None


class IDockProvider(IEditorPlugin):
    """Public legacy Dock payload interface, not the new authoring contract.

    The structural fallback requires ``provides`` to contain ``"dock"`` and
    callable ``create_dock_widget()`` plus ``get_dock_config()``, only when no
    declarative ``dock_surface`` is present. Declarative copied shell facts win;
    the factory then provides only concrete Qt content.
    """

    @abstractmethod
    def create_dock_widget(self) -> QDockWidget:
        """Return the concrete current-UI-host Dock payload."""
        pass

    @abstractmethod
    def get_dock_config(self) -> Dict[str, Any]:
        """Return the historical fallback layout configuration."""
        pass


class IViewportProvider(IEditorPlugin):
    """Public legacy Viewport payload interface, not the new authoring contract.

    The public abstract surface retains widget/id/name methods. The current
    structural fallback requires only callable ``create_viewport_widget()`` and
    ``get_viewport_id()``, with ``provides`` containing ``"viewport"`` and no
    ``viewport_surface``. ``get_viewport_name()`` remains a stable legacy
    subtype method but is not an ownership gate; declarative shell facts win.
    """

    @abstractmethod
    def create_viewport_widget(self) -> QWidget:
        """Return the concrete current-UI-host Viewport payload."""
        pass

    @abstractmethod
    def get_viewport_id(self) -> str:
        """Return the historical fallback viewport ID."""
        pass

    @abstractmethod
    def get_viewport_name(self) -> str:
        """Return the public historical viewport display name."""
        pass

    def on_viewport_activated(self) -> None:
        """Optional historical viewport activation callback."""
        pass

    def on_viewport_deactivated(self) -> None:
        """Optional historical viewport deactivation callback."""
        pass


class IThemeProvider(IEditorPlugin):
    """Public legacy QSS payload interface, not the new authoring contract.

    The fallback requires ``provides`` to contain ``"theme"``, no declarative
    ``theme_profile``, and callable ``get_theme_name()`` plus ``get_stylesheet()``.
    ``get_color_scheme()`` remains a stable abstract import surface, but does not
    determine Adapter ownership. New plugins use ``theme_profile`` and keep QSS
    as an Adapter-local stylesheet payload.
    """

    @abstractmethod
    def get_theme_name(self) -> str:
        """Return the legacy fallback display name."""
        pass

    @abstractmethod
    def get_stylesheet(self) -> str:
        """Return the concrete QSS payload consumed by the current Adapter."""
        pass

    @abstractmethod
    def get_color_scheme(self) -> Dict[str, str]:
        """Retain the historical public color-token signature."""
        pass


class IEntityTypeProvider(IEditorPlugin, IRuntimeEntityTypeProvider):
    """Deliberate legacy-editor / Qt-free entity-provider dual adapter MRO.

    Do not change this MRO; entity discovery authority belongs to the Qt-free
    runtime provider contract.
    """


class IComponentTypeProvider(IEditorPlugin, IRuntimeComponentTypeProvider):
    """Deliberate legacy-editor / Qt-free component-provider dual adapter MRO.

    Do not change this MRO; component discovery authority belongs to the Qt-free
    runtime provider contract.
    """