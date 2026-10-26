# -*- coding: utf-8 -*-
"""Concrete legacy Editor Adapter for nested runtime plugin contributions.

This Module belongs to the current PyQt-era Editor Host inside the versioned
runtime of the sole L1 ``lotucosm-vitaloom`` engine plugin.  It satisfies the
Qt-free ``RuntimePluginHostAdapter`` seam without becoming plugin-framework
or lifecycle authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from core.VitaLoom.core.editor_contribution_contract import (
    EditorContribution,
    EditorDockSurfaceContribution,
    EditorMenuCommandContribution,
    EditorMenuSeparatorContribution,
    EditorToolbarCommandContribution,
    EditorToolbarSeparatorContribution,
    EditorThemeProfileContribution,
    EditorViewportSurfaceContribution,
    parse_editor_contributions,
)
from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.plugin_activation_contract import (
    parse_plugin_activation_metadata,
)
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHostAdapter


logger = get_logger("LegacyEditorPluginAdapter")

ActivePluginItemsResolver = Callable[
    [], Iterable[tuple[str, IRuntimePlugin]]
]
ActivePluginMetadataResolver = Callable[
    [], Iterable[tuple[str, Mapping[str, Any]]]
]


@dataclass(frozen=True, slots=True)
class _LegacyThemeProjection:
    """Concrete stylesheet payload attached to one Host-owned theme identity."""

    owner_plugin_id: str
    theme_id: str
    contribution_id: str
    display_name: str
    appearance: str
    stylesheet: str
    order: int
    declarative: bool

    @property
    def sort_key(self) -> tuple[int, str, str]:
        return (self.order, self.theme_id, self.owner_plugin_id)


class LegacyEditorPluginAdapter(RuntimePluginHostAdapter):
    """Publish and remove concrete legacy Editor plugin contributions.

    Runtime discovery, registry ownership, dependency order, lifecycle plans,
    Project World orchestration, and reload planning stay in the Qt-free Host
    Modules.  This Adapter only projects the concrete Editor context and applies
    legacy command/UI/signal side effects around runtime callbacks.
    """

    def __init__(self, editor_kernel: object) -> None:
        self.kernel = editor_kernel
        self.runtime_activation_context: object | None = None
        self._active_plugin_items_resolver: ActivePluginItemsResolver | None = None
        self._active_plugin_metadata_resolver: (
            ActivePluginMetadataResolver | None
        ) = None
        self._contribution_refresh_events_by_owner: dict[str, frozenset[str]] = {}
        self._contribution_refresh_callbacks: dict[str, Callable[..., None]] = {}
        self._declarative_dock_owner_by_id: dict[str, str] = {}
        self._declarative_viewport_owner_by_id: dict[str, str] = {}
        self._theme_owner_by_id: dict[str, str] = {}
        self._theme_projection_by_owner: dict[str, _LegacyThemeProjection] = {}
        self._theme_baseline_state: Mapping[str, Any] | None = None

    def bind_active_plugin_items_resolver(
        self,
        resolver: ActivePluginItemsResolver,
    ) -> None:
        """Bind the exact Host-owned active plugin view used by UI refreshes."""
        if not callable(resolver):
            raise TypeError("active plugin items resolver must be callable")
        self._active_plugin_items_resolver = resolver

    def bind_active_plugin_metadata_resolver(
        self,
        resolver: ActivePluginMetadataResolver,
    ) -> None:
        """Bind the exact Host-owned copied metadata view used by refreshes."""
        if not callable(resolver):
            raise TypeError("active plugin metadata resolver must be callable")
        self._active_plugin_metadata_resolver = resolver

    def activation_context_for(self, plugin_info: Mapping[str, Any]) -> object:
        """Return the explicit runtime projection or exact legacy UI context."""
        from core.VitaLoom.core.plugin_activation_context import (
            LEGACY_UI_PLUGIN_ACTIVATION_CONTEXT,
            RUNTIME_PLUGIN_ACTIVATION_CONTEXT,
            project_runtime_plugin_activation_context,
        )

        activation_metadata = parse_plugin_activation_metadata(
            plugin_info,
            plugin_id=str(plugin_info.get("name", "") or ""),
        )
        kind = activation_metadata.kind
        if kind == LEGACY_UI_PLUGIN_ACTIVATION_CONTEXT:
            return self.kernel.get_context()
        if kind != RUNTIME_PLUGIN_ACTIVATION_CONTEXT:
            plugin_name = plugin_info.get("name", "<unknown>")
            raise ValueError(
                f"plugin {plugin_name!r} has unsupported activation_context {kind!r}"
            )
        if self.runtime_activation_context is None:
            self.runtime_activation_context = project_runtime_plugin_activation_context(
                self.kernel.get_context()
            )
        return self.runtime_activation_context

    def after_lifecycle_transition(self, _report: Mapping[str, Any]) -> None:
        """Settle legacy layout only after a concrete runtime transition."""
        layout_manager = getattr(self.kernel, "layout_manager", None)
        if layout_manager and hasattr(layout_manager, "process_pending_dock_tabify"):
            layout_manager.process_pending_dock_tabify()

    def after_plugin_load(
        self,
        plugin: IRuntimePlugin,
        plugin_id: str,
        plugin_info: Mapping[str, Any],
    ) -> None:
        """Attach concrete Editor contributions after runtime ``on_load``."""
        legacy_plugin_name = str(
            plugin_info.get("declared_name", plugin_info.get("name", plugin_id))
            or plugin_id
        )
        logger.info("Loading plugin: %s", legacy_plugin_name)
        provides = plugin_info.get("provides", [])
        contributions: tuple[EditorContribution, ...] = ()
        if plugin_info.get("editor_contributions"):
            contributions = self._copied_editor_contributions(plugin_id, plugin_info)
        has_declarative_dock = any(
            isinstance(item, EditorDockSurfaceContribution)
            for item in contributions
        )
        has_declarative_viewport = any(
            isinstance(item, EditorViewportSurfaceContribution)
            for item in contributions
        )
        theme_profiles = tuple(
            item
            for item in contributions
            if isinstance(item, EditorThemeProfileContribution)
        )
        if "dock" in provides and not has_declarative_dock:
            self.register_dock(plugin)
        if "viewport" in provides and not has_declarative_viewport:
            self.register_viewport(plugin)
        if contributions:
            self.register_editor_contributions(
                plugin_id,
                plugin_info,
                plugin=plugin,
                contributions=contributions,
                fail_closed=True,
            )
        if theme_profiles:
            if len(theme_profiles) != 1:
                raise RuntimeError(
                    "legacy theme Adapter requires exactly one theme profile "
                    f"per provider: {plugin_id}"
                )
            self.register_theme(
                plugin,
                plugin_id,
                theme_profile=theme_profiles[0],
            )
        elif "theme" in provides and self._supports_legacy_theme_payload(plugin):
            try:
                self.register_theme(plugin, plugin_id)
            except Exception:
                logger.exception(
                    "Failed to register legacy plugin theme: %s", plugin_id
                )
        editor_ready = getattr(plugin, "on_editor_ready", None)
        if callable(editor_ready):
            try:
                editor_ready()
            except Exception:
                logger.exception(
                    "Plugin on_editor_ready failed: %s", legacy_plugin_name
                )
        self.kernel.plugin_loaded.emit(legacy_plugin_name)

    def before_plugin_unload(
        self,
        plugin: IRuntimePlugin,
        plugin_id: str,
        plugin_info: Mapping[str, Any],
    ) -> None:
        """Fail closed before dynamic unload so Host state stays retryable."""
        self.cleanup_plugin_ui(
            plugin, plugin_id, plugin_info=plugin_info, fail_closed=True
        )

    def before_plugin_shutdown(
        self,
        plugin: IRuntimePlugin,
        plugin_id: str,
        plugin_info: Mapping[str, Any],
    ) -> None:
        """Make shutdown-critical contribution cleanup observable to the Host."""
        self.cleanup_plugin_ui(
            plugin, plugin_id, plugin_info=plugin_info, fail_closed=True
        )

    def after_plugin_deactivated(
        self,
        plugin: IRuntimePlugin,
        plugin_id: str,
        plugin_info: Mapping[str, Any],
    ) -> None:
        """Emit the legacy kernel signal after Host registry removal."""
        self.kernel.plugin_unloaded.emit(plugin_id)
        logger.info("Plugin unloaded: %s", plugin_id)

    def register_dock(self, plugin: object) -> None:
        """Best-effort fallback for a pre-declarative community dock plugin."""
        factory = getattr(plugin, "create_dock_widget", None)
        config_factory = getattr(plugin, "get_dock_config", None)
        if not callable(factory) or not callable(config_factory):
            logger.warning(
                "Skipping legacy dock projection; plugin lacks callable "
                "create_dock_widget/get_dock_config"
            )
            return
        try:
            self.kernel.layout_manager.add_dock(factory(), config_factory())
        except Exception:
            logger.exception("Failed to register legacy community dock")

    @staticmethod
    def _qt_dock_area(area: str):
        """Map one portable dock area token inside the concrete Qt Adapter."""
        from PyQt6.QtCore import Qt

        mapping = {
            "left": Qt.DockWidgetArea.LeftDockWidgetArea,
            "right": Qt.DockWidgetArea.RightDockWidgetArea,
            "top": Qt.DockWidgetArea.TopDockWidgetArea,
            "bottom": Qt.DockWidgetArea.BottomDockWidgetArea,
        }
        try:
            return mapping[area]
        except KeyError as error:
            raise ValueError(f"unsupported portable dock area: {area!r}") from error

    def _project_dock_surface(
        self,
        contribution: EditorDockSurfaceContribution,
        plugin: object | None,
    ) -> None:
        """Project stable shell facts while keeping Qt content in this Adapter."""
        layout_manager = getattr(self.kernel, "layout_manager", None)
        if layout_manager is None:
            raise RuntimeError("layout manager is unavailable")

        docks = getattr(layout_manager, "docks", {})
        existing = docks.get(contribution.dock_id) if isinstance(docks, Mapping) else None
        current_owner = self._declarative_dock_owner_by_id.get(
            contribution.dock_id
        )
        if current_owner not in (None, contribution.owner_plugin_id):
            raise RuntimeError(
                "dock surface id is already owned by another plugin: "
                f"{contribution.dock_id!r}"
            )
        if existing is not None and current_owner is None:
            raise RuntimeError(
                "dock surface id collides with an existing legacy dock: "
                f"{contribution.dock_id!r}"
            )

        title = self._translate_contribution_label(
            contribution.title_key, contribution.default_title
        )
        if existing is not None:
            if hasattr(existing, "setObjectName"):
                existing.setObjectName(contribution.dock_id)
            if hasattr(existing, "setWindowTitle"):
                existing.setWindowTitle(title)
            return

        factory = getattr(plugin, "create_dock_widget", None)
        if not callable(factory):
            raise TypeError(
                "current legacy dock projection requires the active plugin's "
                "existing create_dock_widget implementation"
            )
        dock_widget = factory()
        if hasattr(dock_widget, "setObjectName"):
            dock_widget.setObjectName(contribution.dock_id)
        if hasattr(dock_widget, "setWindowTitle"):
            dock_widget.setWindowTitle(title)
        config = {
            "title": contribution.dock_id,
            "area": self._qt_dock_area(contribution.area),
            "default_visible": contribution.default_visible,
            "can_close": contribution.can_close,
            "can_float": contribution.can_float,
            "can_move": contribution.can_move,
            "tabbed_with": contribution.tabbed_with,
        }
        layout_manager.add_dock(dock_widget, config)
        self._declarative_dock_owner_by_id[contribution.dock_id] = (
            contribution.owner_plugin_id
        )


    def _project_viewport_surface(
        self,
        contribution: EditorViewportSurfaceContribution,
        plugin: object | None,
    ) -> None:
        """Project stable viewport shell facts through the legacy content bridge."""
        layout_manager = getattr(self.kernel, "layout_manager", None)
        if layout_manager is None:
            raise RuntimeError("layout manager is unavailable")

        viewports = getattr(layout_manager, "viewports", {})
        existing = (
            viewports.get(contribution.viewport_id)
            if isinstance(viewports, Mapping)
            else None
        )
        current_owner = self._declarative_viewport_owner_by_id.get(
            contribution.viewport_id
        )
        if current_owner not in (None, contribution.owner_plugin_id):
            raise RuntimeError(
                "viewport surface id is already owned by another plugin: "
                f"{contribution.viewport_id!r}"
            )
        if existing is not None and current_owner is None:
            raise RuntimeError(
                "viewport surface id collides with an existing legacy viewport: "
                f"{contribution.viewport_id!r}"
            )

        display_name = self._translate_contribution_label(
            contribution.name_key, contribution.default_name
        )
        if existing is not None:
            rename = getattr(layout_manager, "set_viewport_display_name", None)
            if not callable(rename):
                raise RuntimeError(
                    "layout manager cannot refresh declarative viewport names"
                )
            rename(contribution.viewport_id, display_name)
            return

        factory = getattr(plugin, "create_viewport_widget", None)
        if not callable(factory):
            raise TypeError(
                "current legacy viewport projection requires the active plugin's "
                "existing create_viewport_widget implementation"
            )
        viewport_widget = factory()
        try:
            layout_manager.add_viewport(
                contribution.viewport_id,
                viewport_widget,
                plugin,
                display_name=display_name,
            )
        except BaseException:
            discard = getattr(viewport_widget, "deleteLater", None)
            if callable(discard):
                discard()
            raise
        self._declarative_viewport_owner_by_id[contribution.viewport_id] = (
            contribution.owner_plugin_id
        )


    def register_viewport(self, plugin: object) -> None:
        """Best-effort fallback for a pre-declarative community viewport plugin."""
        factory = getattr(plugin, "create_viewport_widget", None)
        viewport_id_factory = getattr(plugin, "get_viewport_id", None)
        if not callable(factory) or not callable(viewport_id_factory):
            logger.warning(
                "Skipping legacy viewport projection; plugin lacks callable "
                "create_viewport_widget/get_viewport_id"
            )
            return
        try:
            viewport_widget = factory()
            viewport_id = viewport_id_factory()
            self.kernel.layout_manager.add_viewport(viewport_id, viewport_widget, plugin)
        except Exception:
            logger.exception("Failed to register legacy community viewport")
    def refresh_editor_contributions(self) -> None:
        """Refresh copied Editor contributions once in exact Host metadata order.

        Menu and toolbar structure is derived only from immutable Host-copied
        metadata. Active plugin objects are looked up solely for concrete Dock,
        viewport, and theme Adapter payloads that remain outside the portable
        contribution facts; no live menu/toolbar callback Interface is queried.
        """
        metadata_resolver = self._active_plugin_metadata_resolver
        if metadata_resolver is None:
            logger.warning(
                "Active plugin metadata resolver is unavailable; skipping Editor contribution refresh"
            )
            return
        try:
            metadata_items = tuple(metadata_resolver())
        except Exception:
            logger.exception("Failed to resolve copied editor contribution metadata")
            return

        active_items: tuple[tuple[str, IRuntimePlugin], ...] = ()
        resolver = self._active_plugin_items_resolver
        if resolver is not None:
            try:
                active_items = tuple(resolver())
            except Exception:
                logger.exception(
                    "Failed to resolve active plugins for concrete Editor contribution refresh"
                )
        plugins_by_id = {
            str(plugin_id or "").strip(): plugin
            for plugin_id, plugin in active_items
            if str(plugin_id or "").strip()
        }

        layout_manager = getattr(self.kernel, "layout_manager", None)
        if not layout_manager:
            logger.warning(
                "Layout manager is unavailable; skipping Editor contribution refresh"
            )
            return

        seen: set[str] = set()
        for plugin_id, plugin_info in metadata_items:
            canonical_id = str(plugin_id or "").strip()
            if not canonical_id or canonical_id in seen:
                continue
            seen.add(canonical_id)
            if not plugin_info.get("editor_contributions"):
                continue
            try:
                if hasattr(layout_manager, "remove_plugin_ui"):
                    layout_manager.remove_plugin_ui(canonical_id)
                self.register_editor_contributions(
                    canonical_id,
                    plugin_info,
                    replace_existing=False,
                    plugin=plugins_by_id.get(canonical_id),
                )
            except Exception:
                logger.exception(
                    "Failed to refresh Editor contributions: %s", canonical_id
                )
    def _copied_editor_contributions(
        self,
        plugin_id: str,
        plugin_info: Mapping[str, Any],
    ) -> tuple[EditorContribution, ...]:
        raw_items = plugin_info.get("editor_contributions", [])
        declarations: list[dict[str, Any]] = []
        for raw_item in raw_items:
            if not isinstance(raw_item, Mapping):
                raise TypeError("copied editor contribution must be an object")
            owner = str(raw_item.get("owner_plugin_id", "") or "").strip()
            if owner != plugin_id:
                raise ValueError(
                    "copied editor contribution owner does not match Host plugin id"
                )
            declarations.append(
                {
                    str(key): value
                    for key, value in raw_item.items()
                    if key != "owner_plugin_id"
                }
            )
        return parse_editor_contributions(plugin_id, declarations)

    def _translate_contribution_label(self, key: str, default: str) -> str:
        context = self.kernel.get_context()
        translate = getattr(context, "i18n_tr", None)
        if callable(translate):
            return str(translate(key, default))
        return str(default or key)

    def _command_action(
        self,
        contribution: EditorMenuCommandContribution | EditorToolbarCommandContribution,
    ) -> Callable[..., Mapping[str, Any]]:
        def invoke(*_args) -> Mapping[str, Any]:
            from core.VitaLoom.commands.registry import get_command_registry

            # `to_dict()` thaws a fresh JSON-safe payload. A command handler must
            # not be able to mutate the metadata snapshot captured by a previous
            # QAction trigger.
            payload = contribution.to_dict()["command_payload"]
            result = get_command_registry().run(
                contribution.command_id,
                payload,
                context={
                    "source": "legacy_editor_contribution",
                    "owner_plugin_id": contribution.owner_plugin_id,
                    "contribution_id": contribution.id,
                },
            )
            if not result.get("ok", False):
                logger.error(
                    "Editor contribution command failed: owner=%s contribution=%s command=%s error=%s",
                    contribution.owner_plugin_id,
                    contribution.id,
                    contribution.command_id,
                    result.get("error"),
                )
            return result

        return invoke

    def _toolbar_label(
        self, contribution: EditorToolbarCommandContribution
    ) -> str:
        label_key = contribution.label_key
        default_label = contribution.default_label
        state = contribution.state
        if state is not None:
            try:
                from core.VitaLoom.commands.registry import get_command_registry

                registry = get_command_registry()
                description = registry.describe(state.command_id)
                if description.get("mutates", False):
                    raise ValueError(
                        "toolbar state command must be read-only"
                    )
                result = registry.run(
                    state.command_id,
                    {},
                    context={
                        "source": "legacy_editor_contribution_state",
                        "owner_plugin_id": contribution.owner_plugin_id,
                        "contribution_id": contribution.id,
                    },
                )
                if result.get("ok", False):
                    facts = result.get("result", {})
                    value = (
                        facts.get(state.result_field)
                        if isinstance(facts, Mapping)
                        else None
                    )
                    variant = state.label_variants.get(str(value))
                    if variant is not None:
                        label_key = variant.label_key
                        default_label = variant.default_label
            except Exception:
                logger.exception(
                    "Failed to resolve toolbar contribution state: owner=%s contribution=%s",
                    contribution.owner_plugin_id,
                    contribution.id,
                )
        return self._translate_contribution_label(label_key, default_label)

    def _set_contribution_refresh_events(
        self,
        plugin_id: str,
        event_names: Iterable[str],
        *,
        fail_closed: bool = False,
    ) -> None:
        owner = str(plugin_id or "").strip()
        desired_owner_events = frozenset(str(name) for name in event_names)
        if desired_owner_events:
            self._contribution_refresh_events_by_owner[owner] = desired_owner_events
        else:
            self._contribution_refresh_events_by_owner.pop(owner, None)
        desired_events = set().union(
            *self._contribution_refresh_events_by_owner.values()
        ) if self._contribution_refresh_events_by_owner else set()
        context = self.kernel.get_context()
        event_bus = getattr(context, "event_bus", None)
        if event_bus is None:
            if desired_events and fail_closed:
                raise RuntimeError("editor contribution event bus is unavailable")
            return

        for event_name in sorted(
            set(self._contribution_refresh_callbacks) - desired_events
        ):
            callback = self._contribution_refresh_callbacks[event_name]
            try:
                event_bus.unsubscribe(event_name, callback)
                self._contribution_refresh_callbacks.pop(event_name, None)
            except Exception:
                logger.exception(
                    "Failed to unsubscribe editor contribution refresh event: %s",
                    event_name,
                )
                if fail_closed:
                    raise

        for event_name in sorted(
            desired_events - set(self._contribution_refresh_callbacks)
        ):
            def refresh(_data=None, *, _event_name=event_name) -> None:
                self.refresh_editor_contributions()

            try:
                event_bus.subscribe(event_name, refresh)
                self._contribution_refresh_callbacks[event_name] = refresh
            except Exception:
                logger.exception(
                    "Failed to subscribe editor contribution refresh event: %s",
                    event_name,
                )
                if fail_closed:
                    raise

    def register_editor_contributions(
        self,
        plugin_id: str,
        plugin_info: Mapping[str, Any],
        *,
        replace_existing: bool = False,
        plugin: object | None = None,
        contributions: tuple[EditorContribution, ...] | None = None,
        fail_closed: bool = False,
    ) -> None:
        """Project copied Qt-free contribution facts into the legacy layout."""
        try:
            if contributions is None:
                contributions = self._copied_editor_contributions(
                    plugin_id, plugin_info
                )
            layout_manager = getattr(self.kernel, "layout_manager", None)
            if not layout_manager:
                raise RuntimeError("layout manager is unavailable")
            if replace_existing and hasattr(layout_manager, "remove_plugin_ui"):
                layout_manager.remove_plugin_ui(plugin_id)
            menu_items = []
            toolbar_items = []
            refresh_events: set[str] = set()
            for contribution in contributions:
                if isinstance(contribution, EditorMenuCommandContribution):
                    path = [
                        self._translate_contribution_label(
                            segment.label_key, segment.default_label
                        )
                        for segment in contribution.menu_path
                    ]
                    path.append(
                        self._translate_contribution_label(
                            contribution.label_key, contribution.default_label
                        )
                    )
                    menu_items.append(
                        {
                            "path": "/".join(path),
                            "action": self._command_action(contribution),
                            "shortcut": contribution.shortcut,
                        }
                    )
                elif isinstance(contribution, EditorMenuSeparatorContribution):
                    path = [
                        self._translate_contribution_label(
                            segment.label_key, segment.default_label
                        )
                        for segment in contribution.menu_path
                    ]
                    menu_items.append(
                        {
                            "path": f"{'/'.join(path)}/",
                            "separator": True,
                        }
                    )
                elif isinstance(contribution, EditorDockSurfaceContribution):
                    self._project_dock_surface(contribution, plugin)
                    refresh_events.update(contribution.refresh_events)
                elif isinstance(contribution, EditorViewportSurfaceContribution):
                    self._project_viewport_surface(contribution, plugin)
                    refresh_events.update(contribution.refresh_events)
                elif isinstance(contribution, EditorToolbarCommandContribution):
                    toolbar_items.append(
                        {
                            "text": self._toolbar_label(contribution),
                            "action": self._command_action(contribution),
                            "icon": contribution.icon,
                        }
                    )
                    if contribution.state is not None:
                        refresh_events.update(contribution.state.refresh_events)
                elif isinstance(contribution, EditorToolbarSeparatorContribution):
                    toolbar_items.append({"separator": True})
            if menu_items:
                layout_manager.add_menu_items(menu_items, plugin_id)
            if toolbar_items:
                layout_manager.add_toolbar_items(toolbar_items, plugin_id)
            self._set_contribution_refresh_events(plugin_id, refresh_events)
        except Exception:
            logger.exception(
                "Failed to project editor contributions: %s", plugin_id
            )
            if fail_closed:
                raise

    @staticmethod
    def _active_theme_projection(
        projections: Mapping[str, _LegacyThemeProjection],
    ) -> _LegacyThemeProjection | None:
        if not projections:
            return None
        return max(projections.values(), key=lambda item: item.sort_key)

    @staticmethod
    def _legacy_theme_id(plugin_id: str) -> str:
        return f"legacy.{plugin_id}"

    @staticmethod
    def _supports_legacy_theme_payload(plugin: IRuntimePlugin) -> bool:
        """Recognize only the bounded community fallback payload shape.

        Built-in themes are activated from copied ``theme_profile`` facts. This
        compatibility check is intentionally local to the PyQt adapter, so the
        obsolete legacy provider interface is not runtime authority.
        """
        return callable(getattr(plugin, "get_theme_name", None)) and callable(
            getattr(plugin, "get_stylesheet", None)
        )
    def _compose_theme_stylesheet(
        self,
        appearance: str,
        payload: str,
        *,
        include_modern_overlay: bool,
    ) -> str:
        from core.VitaLoom.ui.theme_manager import get_theme_manager

        theme_manager = get_theme_manager()
        base = (
            theme_manager.LIGHT_THEME
            if appearance == "light"
            else theme_manager.DARK_THEME
        )
        layers = [str(base)]
        if include_modern_overlay:
            from core.VitaLoom.ui.design_tokens import modern_editor_overlay

            layers.append(str(modern_editor_overlay()))
        layers.append(payload)
        return "\n".join(layers)

    def register_theme(
        self,
        plugin: IRuntimePlugin,
        plugin_id: str,
        *,
        theme_profile: EditorThemeProfileContribution | None = None,
    ) -> None:
        """Project one copied theme identity with a concrete legacy payload."""
        owner = str(plugin_id or "").strip()
        if not owner:
            raise ValueError("theme owner plugin id is empty")
        if owner in self._theme_projection_by_owner:
            raise RuntimeError(f"theme owner {owner!r} is already projected")

        if theme_profile is not None:
            if theme_profile.owner_plugin_id != owner:
                raise ValueError(
                    "copied theme profile owner does not match Host plugin id"
                )
            theme_id = theme_profile.theme_id
            existing_owner = self._theme_owner_by_id.get(theme_id)
            if existing_owner is not None and existing_owner != owner:
                raise RuntimeError(
                    f"theme id {theme_id!r} is already owned by "
                    f"{existing_owner!r}"
                )
            display_name = self._translate_contribution_label(
                theme_profile.name_key,
                theme_profile.default_name,
            )
            appearance = theme_profile.appearance
            order = theme_profile.order
            contribution_id = theme_profile.id
            declarative = True
        else:
            theme_id = self._legacy_theme_id(owner)
            existing_owner = self._theme_owner_by_id.get(theme_id)
            if existing_owner is not None and existing_owner != owner:
                raise RuntimeError(
                    f"theme id {theme_id!r} is already owned by "
                    f"{existing_owner!r}"
                )
            display_name = str(plugin.get_theme_name())
            appearance = "dark"
            order = 0
            contribution_id = theme_id
            declarative = False

        payload = plugin.get_stylesheet()
        if not isinstance(payload, str):
            raise TypeError("legacy theme stylesheet payload must be a string")
        stylesheet = self._compose_theme_stylesheet(
            appearance,
            payload,
            include_modern_overlay=declarative,
        )
        projection = _LegacyThemeProjection(
            owner_plugin_id=owner,
            theme_id=theme_id,
            contribution_id=contribution_id,
            display_name=display_name,
            appearance=appearance,
            stylesheet=stylesheet,
            order=order,
            declarative=declarative,
        )

        layout_manager = getattr(self.kernel, "layout_manager", None)
        if layout_manager is None:
            raise RuntimeError("layout manager is unavailable")
        first_projection = not self._theme_projection_by_owner
        baseline = self._theme_baseline_state
        if first_projection:
            capture = getattr(layout_manager, "capture_theme_style_state", None)
            baseline = capture() if callable(capture) else None

        current = self._active_theme_projection(self._theme_projection_by_owner)
        tentative = dict(self._theme_projection_by_owner)
        tentative[owner] = projection
        desired = self._active_theme_projection(tentative)
        if desired is projection and desired is not current:
            layout_manager.register_theme(
                projection.display_name,
                projection.stylesheet,
            )

        self._theme_projection_by_owner[owner] = projection
        self._theme_owner_by_id[theme_id] = owner
        if first_projection:
            self._theme_baseline_state = baseline

    def _remove_theme_owner(self, plugin_id: str) -> None:
        owner = str(plugin_id or "").strip()
        projection = self._theme_projection_by_owner.get(owner)
        if projection is None:
            return

        layout_manager = getattr(self.kernel, "layout_manager", None)
        if layout_manager is None:
            raise RuntimeError("layout manager is unavailable")
        current = self._active_theme_projection(self._theme_projection_by_owner)
        tentative = dict(self._theme_projection_by_owner)
        tentative.pop(owner, None)
        desired = self._active_theme_projection(tentative)

        if current is projection:
            if desired is not None:
                layout_manager.register_theme(
                    desired.display_name,
                    desired.stylesheet,
                )
            elif self._theme_baseline_state is not None:
                restore = getattr(layout_manager, "restore_theme_style_state", None)
                if not callable(restore):
                    raise RuntimeError(
                        "layout manager cannot restore the captured theme baseline"
                    )
                restore(self._theme_baseline_state)

        self._theme_projection_by_owner.pop(owner, None)
        if self._theme_owner_by_id.get(projection.theme_id) == owner:
            self._theme_owner_by_id.pop(projection.theme_id, None)
        if not self._theme_projection_by_owner:
            self._theme_baseline_state = None

    def cleanup_plugin_ui(
        self,
        plugin: IRuntimePlugin,
        plugin_id: str,
        *,
        plugin_info: Mapping[str, Any] | None = None,
        fail_closed: bool = False,
    ) -> None:
        """Remove legacy UI contributions using Host-copied ownership facts."""
        try:
            info = plugin_info if plugin_info is not None else plugin.get_plugin_info()
            provides = info.get("provides", [])
            layout_manager = self.kernel.layout_manager

            contributions: tuple[EditorContribution, ...] = ()
            if info.get("editor_contributions"):
                contributions = self._copied_editor_contributions(plugin_id, info)
            viewport_contributions = tuple(
                item
                for item in contributions
                if isinstance(item, EditorViewportSurfaceContribution)
            )
            # Viewport removal is the only concrete surface cleanup that exposes
            # an explicit retryable failure result.  Resolve it before deleting
            # any dock projection, so an active Host plugin cannot be left with a
            # surviving viewport but an already-removed sibling dock.
            if viewport_contributions:
                for contribution in viewport_contributions:
                    removed = layout_manager.remove_viewport(contribution.viewport_id)
                    if removed is False:
                        raise RuntimeError(
                            "viewport contribution cleanup failed: "
                            f"{contribution.viewport_id}"
                        )
                    if (
                        self._declarative_viewport_owner_by_id.get(
                            contribution.viewport_id
                        )
                        == contribution.owner_plugin_id
                    ):
                        self._declarative_viewport_owner_by_id.pop(
                            contribution.viewport_id, None
                        )
            elif "viewport" in provides:
                viewport_id_factory = getattr(plugin, "get_viewport_id", None)
                if callable(viewport_id_factory):
                    removed = layout_manager.remove_viewport(viewport_id_factory())
                    if removed is False and fail_closed:
                        raise RuntimeError(
                            "legacy viewport cleanup failed: "
                            f"{plugin_id}"
                        )
                else:
                    logger.warning(
                        "Skipping legacy viewport cleanup; plugin lacks callable "
                        "get_viewport_id: %s",
                        plugin_id,
                    )

            dock_contributions = tuple(
                item
                for item in contributions
                if isinstance(item, EditorDockSurfaceContribution)
            )
            if dock_contributions:
                for contribution in dock_contributions:
                    layout_manager.remove_dock(contribution.dock_id)
                    if (
                        self._declarative_dock_owner_by_id.get(
                            contribution.dock_id
                        )
                        == contribution.owner_plugin_id
                    ):
                        self._declarative_dock_owner_by_id.pop(
                            contribution.dock_id, None
                        )
            elif "dock" in provides:
                config_factory = getattr(plugin, "get_dock_config", None)
                if callable(config_factory):
                    config = config_factory()
                    dock_title = config.get("title", plugin_id)
                    layout_manager.remove_dock(dock_title)
                else:
                    logger.warning(
                        "Skipping legacy dock cleanup; plugin lacks callable "
                        "get_dock_config: %s",
                        plugin_id,
                    )

            if hasattr(layout_manager, "remove_plugin_ui"):
                layout_manager.remove_plugin_ui(plugin_id)
            self._set_contribution_refresh_events(
                plugin_id, (), fail_closed=fail_closed
            )
        except Exception as error:
            logger.exception(
                "Failed to clean up plugin UI: plugin=%s error=%s",
                plugin_id,
                error,
            )
            if fail_closed:
                raise
        self._remove_theme_owner(plugin_id)


