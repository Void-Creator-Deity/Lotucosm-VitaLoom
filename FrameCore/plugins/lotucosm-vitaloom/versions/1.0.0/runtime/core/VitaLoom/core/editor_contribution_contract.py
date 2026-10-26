"""Qt-free declarative editor contributions owned by the VitaLoom engine plugin.

The contract contains immutable, JSON-safe facts only. Concrete editor shells
project those facts through their existing Adapter seam; this Module owns no
plugin discovery, lifecycle, registry, widgets, or callbacks.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from core.VitaLoom.kernel.plugin_ids import canonical_plugin_id


MENU_COMMAND_KIND = "menu_command"
MENU_SEPARATOR_KIND = "menu_separator"
TOOLBAR_COMMAND_KIND = "toolbar_command"
TOOLBAR_SEPARATOR_KIND = "toolbar_separator"
DOCK_SURFACE_KIND = "dock_surface"
VIEWPORT_SURFACE_KIND = "viewport_surface"
THEME_PROFILE_KIND = "theme_profile"
SUPPORTED_EDITOR_CONTRIBUTION_KINDS = frozenset(
    {
        MENU_COMMAND_KIND,
        MENU_SEPARATOR_KIND,
        TOOLBAR_COMMAND_KIND,
        TOOLBAR_SEPARATOR_KIND,
        DOCK_SURFACE_KIND,
        VIEWPORT_SURFACE_KIND,
        THEME_PROFILE_KIND,
    }
)
_PORTABLE_TOKEN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,127})$")
_DOCK_ID_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._ -]{0,127})$")
_EVENT_NAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._:-]{0,127})$")
_SEMANTIC_PALETTE_TOKEN_RE = re.compile(
    r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$"
)
_PORTABLE_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?$")
_DOCK_AREAS = frozenset({"left", "right", "top", "bottom"})
_THEME_APPEARANCES = frozenset({"dark", "light"})

class EditorContributionContractError(ValueError):
    """Stable contract rejection with a JSON-safe diagnostic payload."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = str(code)
        self.message = str(message)
        self.details = {
            str(key): _diagnostic_value(value)
            for key, value in (details or {}).items()
        }


@dataclass(frozen=True, slots=True)
class EditorMenuPathSegment:
    """One stable placement segment independent from a native menu object."""

    id: str
    label_key: str
    default_label: str

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "label_key": self.label_key,
            "default_label": self.default_label,
        }


@dataclass(frozen=True, slots=True)
class EditorMenuCommandContribution:
    """One command-backed menu fact with Host-injected canonical ownership."""

    owner_plugin_id: str
    id: str
    kind: str
    menu_path: tuple[EditorMenuPathSegment, ...]
    label_key: str
    default_label: str
    command_id: str
    command_payload: Mapping[str, Any]
    shortcut: str | None
    order: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_plugin_id": self.owner_plugin_id,
            "id": self.id,
            "kind": self.kind,
            "menu_path": [segment.to_dict() for segment in self.menu_path],
            "label_key": self.label_key,
            "default_label": self.default_label,
            "command_id": self.command_id,
            "command_payload": _thaw_json(self.command_payload),
            "shortcut": self.shortcut,
            "order": self.order,
        }


@dataclass(frozen=True, slots=True)
class EditorMenuSeparatorContribution:
    """One structural menu separator with no command or native menu object."""

    owner_plugin_id: str
    id: str
    kind: str
    menu_path: tuple[EditorMenuPathSegment, ...]
    order: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_plugin_id": self.owner_plugin_id,
            "id": self.id,
            "kind": self.kind,
            "menu_path": [segment.to_dict() for segment in self.menu_path],
            "order": self.order,
        }


@dataclass(frozen=True, slots=True)
class EditorLabelVariant:
    """One localized label selected from a closed state value mapping."""

    label_key: str
    default_label: str

    def to_dict(self) -> dict[str, str]:
        return {
            "label_key": self.label_key,
            "default_label": self.default_label,
        }


@dataclass(frozen=True, slots=True)
class EditorCommandStateProjection:
    """Read one top-level field from a read-only canonical command result."""

    command_id: str
    result_field: str
    label_variants: Mapping[str, EditorLabelVariant]
    refresh_events: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "result_field": self.result_field,
            "label_variants": {
                value: variant.to_dict()
                for value, variant in self.label_variants.items()
            },
            "refresh_events": list(self.refresh_events),
        }


@dataclass(frozen=True, slots=True)
class EditorToolbarCommandContribution:
    """One command-backed toolbar fact without native actions or icons."""

    owner_plugin_id: str
    id: str
    kind: str
    label_key: str
    default_label: str
    command_id: str
    command_payload: Mapping[str, Any]
    icon: str
    group: str
    order: int
    state: EditorCommandStateProjection | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_plugin_id": self.owner_plugin_id,
            "id": self.id,
            "kind": self.kind,
            "label_key": self.label_key,
            "default_label": self.default_label,
            "command_id": self.command_id,
            "command_payload": _thaw_json(self.command_payload),
            "icon": self.icon,
            "group": self.group,
            "order": self.order,
            "state": self.state.to_dict() if self.state is not None else None,
        }


@dataclass(frozen=True, slots=True)
class EditorToolbarSeparatorContribution:
    """One structural toolbar separator with no command or native action."""

    owner_plugin_id: str
    id: str
    kind: str
    group: str
    order: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_plugin_id": self.owner_plugin_id,
            "id": self.id,
            "kind": self.kind,
            "group": self.group,
            "order": self.order,
        }


@dataclass(frozen=True, slots=True)
class EditorDockSurfaceContribution:
    """One stable dock shell fact projected by a concrete editor Host."""

    owner_plugin_id: str
    id: str
    kind: str
    dock_id: str
    title_key: str
    default_title: str
    area: str
    default_visible: bool
    can_close: bool
    can_float: bool
    can_move: bool
    tabbed_with: str | None
    order: int
    refresh_events: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_plugin_id": self.owner_plugin_id,
            "id": self.id,
            "kind": self.kind,
            "dock_id": self.dock_id,
            "title_key": self.title_key,
            "default_title": self.default_title,
            "area": self.area,
            "default_visible": self.default_visible,
            "can_close": self.can_close,
            "can_float": self.can_float,
            "can_move": self.can_move,
            "tabbed_with": self.tabbed_with,
            "order": self.order,
            "refresh_events": list(self.refresh_events),
        }


@dataclass(frozen=True, slots=True)
class EditorViewportSurfaceContribution:
    """One stable viewport shell fact projected by a concrete editor Host."""

    owner_plugin_id: str
    id: str
    kind: str
    viewport_id: str
    name_key: str
    default_name: str
    order: int
    refresh_events: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_plugin_id": self.owner_plugin_id,
            "id": self.id,
            "kind": self.kind,
            "viewport_id": self.viewport_id,
            "name_key": self.name_key,
            "default_name": self.default_name,
            "order": self.order,
            "refresh_events": list(self.refresh_events),
        }


@dataclass(frozen=True, slots=True)
class EditorThemeProfileContribution:
    """One portable theme identity and semantic palette owned by a plugin."""

    owner_plugin_id: str
    id: str
    kind: str
    theme_id: str
    name_key: str
    default_name: str
    appearance: str
    palette: Mapping[str, str]
    order: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_plugin_id": self.owner_plugin_id,
            "id": self.id,
            "kind": self.kind,
            "theme_id": self.theme_id,
            "name_key": self.name_key,
            "default_name": self.default_name,
            "appearance": self.appearance,
            "palette": dict(self.palette),
            "order": self.order,
        }

EditorContribution = (
    EditorMenuCommandContribution
    | EditorMenuSeparatorContribution
    | EditorToolbarCommandContribution
    | EditorToolbarSeparatorContribution
    | EditorDockSurfaceContribution
    | EditorViewportSurfaceContribution
    | EditorThemeProfileContribution
)


def parse_editor_contributions(
    owner_plugin_id: str,
    raw_items: Sequence[Mapping[str, Any]] | None,
) -> tuple[EditorContribution, ...]:
    """Validate and normalize one plugin's declarative editor contributions.

    Ownership comes exclusively from the caller that already owns plugin
    registration. The returned tuple is ordered deterministically by explicit
    placement order and contribution id.
    """

    owner = canonical_plugin_id(str(owner_plugin_id or ""))
    if not owner:
        raise EditorContributionContractError(
            "contribution_owner_invalid",
            "editor contribution owner plugin id is empty",
        )
    if raw_items is None:
        return ()
    if (
        not isinstance(raw_items, Sequence)
        or isinstance(raw_items, (str, bytes, bytearray))
    ):
        raise EditorContributionContractError(
            "contribution_items_invalid",
            "editor_contributions must be an array",
            details={"owner_plugin_id": owner},
        )

    parsed: list[EditorContribution] = []
    seen_ids: set[str] = set()
    seen_dock_ids: set[str] = set()
    seen_viewport_ids: set[str] = set()
    seen_theme_ids: set[str] = set()
    for index, raw_item in enumerate(raw_items):
        if not isinstance(raw_item, Mapping):
            raise EditorContributionContractError(
                "contribution_item_invalid",
                "each editor contribution must be an object",
                details={
                    "owner_plugin_id": owner,
                    "index": index,
                    "value_type": type(raw_item).__name__,
                },
            )
        _reject_live_values(raw_item, path=f"editor_contributions[{index}]")
        if "owner_plugin_id" in raw_item or "owner" in raw_item:
            raise EditorContributionContractError(
                "contribution_owner_forbidden",
                "plugins cannot declare editor contribution ownership",
                details={"owner_plugin_id": owner, "index": index},
            )

        kind = _required_text(raw_item, "kind", owner=owner, index=index)
        if kind not in SUPPORTED_EDITOR_CONTRIBUTION_KINDS:
            raise EditorContributionContractError(
                "contribution_kind_unsupported",
                f"unsupported editor contribution kind {kind!r}",
                details={
                    "owner_plugin_id": owner,
                    "index": index,
                    "kind": kind,
                    "supported": sorted(SUPPORTED_EDITOR_CONTRIBUTION_KINDS),
                },
            )
        contribution_id = _required_text(
            raw_item, "id", owner=owner, index=index
        )
        if contribution_id in seen_ids:
            raise EditorContributionContractError(
                "contribution_duplicate_id",
                f"duplicate editor contribution id {contribution_id!r}",
                details={
                    "owner_plugin_id": owner,
                    "index": index,
                    "contribution_id": contribution_id,
                },
            )
        seen_ids.add(contribution_id)

        if kind == MENU_COMMAND_KIND:
            parsed.append(
                _parse_menu_command(
                    owner,
                    contribution_id,
                    raw_item,
                    index=index,
                )
            )
        elif kind == MENU_SEPARATOR_KIND:
            parsed.append(
                _parse_menu_separator(
                    owner,
                    contribution_id,
                    raw_item,
                    index=index,
                )
            )
        elif kind == TOOLBAR_COMMAND_KIND:
            parsed.append(
                _parse_toolbar_command(
                    owner,
                    contribution_id,
                    raw_item,
                    index=index,
                )
            )
        elif kind == TOOLBAR_SEPARATOR_KIND:
            parsed.append(
                _parse_toolbar_separator(
                    owner,
                    contribution_id,
                    raw_item,
                    index=index,
                )
            )
        elif kind == DOCK_SURFACE_KIND:
            dock = _parse_dock_surface(
                owner,
                contribution_id,
                raw_item,
                index=index,
            )
            if dock.dock_id in seen_dock_ids:
                raise EditorContributionContractError(
                    "contribution_duplicate_dock_id",
                    f"duplicate dock surface id {dock.dock_id!r}",
                    details={
                        "owner_plugin_id": owner,
                        "index": index,
                        "contribution_id": contribution_id,
                        "dock_id": dock.dock_id,
                    },
                )
            seen_dock_ids.add(dock.dock_id)
            parsed.append(dock)
        elif kind == VIEWPORT_SURFACE_KIND:
            viewport = _parse_viewport_surface(
                owner,
                contribution_id,
                raw_item,
                index=index,
            )
            if viewport.viewport_id in seen_viewport_ids:
                raise EditorContributionContractError(
                    "contribution_duplicate_viewport_id",
                    f"duplicate viewport surface id {viewport.viewport_id!r}",
                    details={
                        "owner_plugin_id": owner,
                        "index": index,
                        "contribution_id": contribution_id,
                        "viewport_id": viewport.viewport_id,
                    },
                )
            seen_viewport_ids.add(viewport.viewport_id)
            parsed.append(viewport)
        elif kind == THEME_PROFILE_KIND:
            profile = _parse_theme_profile(
                owner,
                contribution_id,
                raw_item,
                index=index,
            )
            if profile.theme_id in seen_theme_ids:
                raise EditorContributionContractError(
                    "contribution_duplicate_theme_id",
                    f"duplicate theme profile id {profile.theme_id!r}",
                    details={
                        "owner_plugin_id": owner,
                        "index": index,
                        "contribution_id": contribution_id,
                        "theme_id": profile.theme_id,
                    },
                )
            seen_theme_ids.add(profile.theme_id)
            parsed.append(profile)
    return tuple(sorted(parsed, key=lambda item: (item.order, item.id)))


def _parse_menu_command(
    owner: str,
    contribution_id: str,
    raw_item: Mapping[str, Any],
    *,
    index: int,
) -> EditorMenuCommandContribution:
    allowed_fields = {
        "id",
        "kind",
        "menu_path",
        "label_key",
        "default_label",
        "command_id",
        "command_payload",
        "shortcut",
        "order",
    }
    unknown_fields = sorted(str(key) for key in raw_item if key not in allowed_fields)
    if unknown_fields:
        raise EditorContributionContractError(
            "contribution_field_unknown",
            "editor contribution contains unsupported fields",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
                "fields": unknown_fields,
            },
        )

    raw_path = raw_item.get("menu_path")
    if (
        not isinstance(raw_path, Sequence)
        or isinstance(raw_path, (str, bytes, bytearray))
        or not raw_path
    ):
        raise EditorContributionContractError(
            "contribution_menu_path_invalid",
            "menu_path must be a non-empty array",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
            },
        )
    menu_path = tuple(
        _parse_menu_path_segment(
            segment,
            owner=owner,
            contribution_id=contribution_id,
            item_index=index,
            segment_index=segment_index,
        )
        for segment_index, segment in enumerate(raw_path)
    )

    payload = raw_item.get("command_payload", {})
    if not isinstance(payload, Mapping):
        raise EditorContributionContractError(
            "contribution_command_payload_invalid",
            "command_payload must be an object",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
                "value_type": type(payload).__name__,
            },
        )
    _validate_json_value(
        payload,
        path=f"editor_contributions[{index}].command_payload",
        owner=owner,
        contribution_id=contribution_id,
    )

    shortcut_value = raw_item.get("shortcut")
    if shortcut_value is None:
        shortcut = None
    elif isinstance(shortcut_value, str) and shortcut_value.strip():
        shortcut = shortcut_value.strip()
    else:
        raise EditorContributionContractError(
            "contribution_shortcut_invalid",
            "menu shortcut must be a non-empty plain string or null",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
                "value_type": type(shortcut_value).__name__,
            },
        )

    order = raw_item.get("order", 0)
    if not isinstance(order, int) or isinstance(order, bool):
        raise EditorContributionContractError(
            "contribution_order_invalid",
            "editor contribution order must be an integer",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
                "value_type": type(order).__name__,
            },
        )

    return EditorMenuCommandContribution(
        owner_plugin_id=owner,
        id=contribution_id,
        kind=MENU_COMMAND_KIND,
        menu_path=menu_path,
        label_key=_required_text(raw_item, "label_key", owner=owner, index=index),
        default_label=_required_text(
            raw_item, "default_label", owner=owner, index=index
        ),
        command_id=_required_text(raw_item, "command_id", owner=owner, index=index),
        command_payload=_freeze_json(payload),
        shortcut=shortcut,
        order=order,
    )




def _parse_menu_separator(
    owner: str,
    contribution_id: str,
    raw_item: Mapping[str, Any],
    *,
    index: int,
) -> EditorMenuSeparatorContribution:
    allowed_fields = {"id", "kind", "menu_path", "order"}
    unknown_fields = sorted(str(key) for key in raw_item if key not in allowed_fields)
    if unknown_fields:
        raise EditorContributionContractError(
            "contribution_field_unknown",
            "editor contribution contains unsupported fields",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
                "fields": unknown_fields,
            },
        )

    raw_path = raw_item.get("menu_path")
    if (
        not isinstance(raw_path, Sequence)
        or isinstance(raw_path, (str, bytes, bytearray))
        or not raw_path
    ):
        raise EditorContributionContractError(
            "contribution_menu_path_invalid",
            "menu_path must be a non-empty array",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
            },
        )
    menu_path = tuple(
        _parse_menu_path_segment(
            segment,
            owner=owner,
            contribution_id=contribution_id,
            item_index=index,
            segment_index=segment_index,
        )
        for segment_index, segment in enumerate(raw_path)
    )
    return EditorMenuSeparatorContribution(
        owner_plugin_id=owner,
        id=contribution_id,
        kind=MENU_SEPARATOR_KIND,
        menu_path=menu_path,
        order=_parse_order(
            raw_item.get("order", 0),
            owner=owner,
            contribution_id=contribution_id,
            index=index,
        ),
    )


def _parse_toolbar_command(
    owner: str,
    contribution_id: str,
    raw_item: Mapping[str, Any],
    *,
    index: int,
) -> EditorToolbarCommandContribution:
    allowed_fields = {
        "id",
        "kind",
        "label_key",
        "default_label",
        "command_id",
        "command_payload",
        "icon",
        "group",
        "order",
        "state",
    }
    unknown_fields = sorted(str(key) for key in raw_item if key not in allowed_fields)
    if unknown_fields:
        raise EditorContributionContractError(
            "contribution_field_unknown",
            "editor contribution contains unsupported fields",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
                "fields": unknown_fields,
            },
        )

    payload = raw_item.get("command_payload", {})
    if not isinstance(payload, Mapping):
        raise EditorContributionContractError(
            "contribution_command_payload_invalid",
            "command_payload must be an object",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
                "value_type": type(payload).__name__,
            },
        )
    _validate_json_value(
        payload,
        path=f"editor_contributions[{index}].command_payload",
        owner=owner,
        contribution_id=contribution_id,
    )

    icon = _portable_token(
        raw_item.get("icon"),
        code="contribution_icon_invalid",
        field="icon",
        owner=owner,
        contribution_id=contribution_id,
        index=index,
    )
    group = _portable_token(
        raw_item.get("group"),
        code="contribution_group_invalid",
        field="group",
        owner=owner,
        contribution_id=contribution_id,
        index=index,
    )
    order = _parse_order(
        raw_item.get("order", 0),
        owner=owner,
        contribution_id=contribution_id,
        index=index,
    )
    raw_state = raw_item.get("state")
    state = None
    if raw_state is not None:
        state = _parse_command_state_projection(
            raw_state,
            owner=owner,
            contribution_id=contribution_id,
            index=index,
        )

    return EditorToolbarCommandContribution(
        owner_plugin_id=owner,
        id=contribution_id,
        kind=TOOLBAR_COMMAND_KIND,
        label_key=_required_text(raw_item, "label_key", owner=owner, index=index),
        default_label=_required_text(
            raw_item, "default_label", owner=owner, index=index
        ),
        command_id=_required_text(raw_item, "command_id", owner=owner, index=index),
        command_payload=_freeze_json(payload),
        icon=icon,
        group=group,
        order=order,
        state=state,
    )



def _parse_toolbar_separator(
    owner: str,
    contribution_id: str,
    raw_item: Mapping[str, Any],
    *,
    index: int,
) -> EditorToolbarSeparatorContribution:
    allowed_fields = {"id", "kind", "group", "order"}
    unknown_fields = sorted(str(key) for key in raw_item if key not in allowed_fields)
    if unknown_fields:
        raise EditorContributionContractError(
            "contribution_field_unknown",
            "editor contribution contains unsupported fields",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
                "fields": unknown_fields,
            },
        )
    return EditorToolbarSeparatorContribution(
        owner_plugin_id=owner,
        id=contribution_id,
        kind=TOOLBAR_SEPARATOR_KIND,
        group=_portable_token(
            raw_item.get("group"),
            code="contribution_group_invalid",
            field="group",
            owner=owner,
            contribution_id=contribution_id,
            index=index,
        ),
        order=_parse_order(
            raw_item.get("order", 0),
            owner=owner,
            contribution_id=contribution_id,
            index=index,
        ),
    )


def _parse_dock_surface(
    owner: str,
    contribution_id: str,
    raw_item: Mapping[str, Any],
    *,
    index: int,
) -> EditorDockSurfaceContribution:
    allowed_fields = {
        "id", "kind", "dock_id", "title_key", "default_title",
        "area", "default_visible", "can_close", "can_float",
        "can_move", "tabbed_with", "order", "refresh_events",
    }
    unknown_fields = sorted(str(key) for key in raw_item if key not in allowed_fields)
    if unknown_fields:
        raise EditorContributionContractError(
            "contribution_dock_field_unknown",
            "dock surface contribution contains unsupported fields",
            details={
                "owner_plugin_id": owner, "index": index,
                "contribution_id": contribution_id, "fields": unknown_fields,
            },
        )

    dock_id = _dock_id(
        raw_item.get("dock_id"), code="contribution_dock_id_invalid",
        field="dock_id", owner=owner, contribution_id=contribution_id, index=index,
    )
    area = _required_text(raw_item, "area", owner=owner, index=index)
    if area not in _DOCK_AREAS:
        raise EditorContributionContractError(
            "contribution_dock_area_invalid",
            "dock surface area must be one of left/right/top/bottom",
            details={
                "owner_plugin_id": owner, "index": index,
                "contribution_id": contribution_id, "area": area,
                "supported": sorted(_DOCK_AREAS),
            },
        )

    raw_tab = raw_item.get("tabbed_with")
    tabbed_with = None
    if raw_tab is not None:
        tabbed_with = _dock_id(
            raw_tab, code="contribution_dock_tab_invalid", field="tabbed_with",
            owner=owner, contribution_id=contribution_id, index=index,
        )
        if tabbed_with == dock_id:
            raise EditorContributionContractError(
                "contribution_dock_tab_invalid",
                "dock surface cannot tab with itself",
                details={
                    "owner_plugin_id": owner, "index": index,
                    "contribution_id": contribution_id, "dock_id": dock_id,
                },
            )

    raw_events = raw_item.get("refresh_events", [])
    if not isinstance(raw_events, Sequence) or isinstance(raw_events, (str, bytes, bytearray)):
        raise EditorContributionContractError(
            "contribution_event_invalid",
            "dock surface refresh_events must be an array",
            details={
                "owner_plugin_id": owner, "index": index,
                "contribution_id": contribution_id,
            },
        )
    events: list[str] = []
    seen_events: set[str] = set()
    for raw_event in raw_events:
        _validate_json_value(
            raw_event, path=f"editor_contributions[{index}].refresh_events",
            owner=owner, contribution_id=contribution_id,
        )
        if not isinstance(raw_event, str) or not _EVENT_NAME_RE.fullmatch(raw_event):
            raise EditorContributionContractError(
                "contribution_event_invalid",
                "dock surface refresh event must be a portable event name",
                details={
                    "owner_plugin_id": owner, "index": index,
                    "contribution_id": contribution_id,
                    "event": _diagnostic_value(raw_event),
                },
            )
        if raw_event in seen_events:
            raise EditorContributionContractError(
                "contribution_event_duplicate",
                "dock surface refresh events cannot contain duplicates",
                details={
                    "owner_plugin_id": owner, "index": index,
                    "contribution_id": contribution_id, "event": raw_event,
                },
            )
        seen_events.add(raw_event)
        events.append(raw_event)

    return EditorDockSurfaceContribution(
        owner_plugin_id=owner, id=contribution_id, kind=DOCK_SURFACE_KIND,
        dock_id=dock_id,
        title_key=_required_text(raw_item, "title_key", owner=owner, index=index),
        default_title=_required_text(raw_item, "default_title", owner=owner, index=index),
        area=area,
        default_visible=_dock_flag(raw_item.get("default_visible", True), field="default_visible", owner=owner, contribution_id=contribution_id, index=index),
        can_close=_dock_flag(raw_item.get("can_close", True), field="can_close", owner=owner, contribution_id=contribution_id, index=index),
        can_float=_dock_flag(raw_item.get("can_float", True), field="can_float", owner=owner, contribution_id=contribution_id, index=index),
        can_move=_dock_flag(raw_item.get("can_move", True), field="can_move", owner=owner, contribution_id=contribution_id, index=index),
        tabbed_with=tabbed_with,
        order=_parse_order(raw_item.get("order", 0), owner=owner, contribution_id=contribution_id, index=index),
        refresh_events=tuple(events),
    )


def _parse_viewport_surface(
    owner: str,
    contribution_id: str,
    raw_item: Mapping[str, Any],
    *,
    index: int,
) -> EditorViewportSurfaceContribution:
    allowed_fields = {
        "id",
        "kind",
        "viewport_id",
        "name_key",
        "default_name",
        "order",
        "refresh_events",
    }
    unknown_fields = sorted(
        str(key) for key in raw_item if key not in allowed_fields
    )
    if unknown_fields:
        raise EditorContributionContractError(
            "contribution_viewport_field_unknown",
            "viewport surface contribution contains unsupported fields",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
                "fields": unknown_fields,
            },
        )

    viewport_id = _portable_token(
        raw_item.get("viewport_id"),
        code="contribution_viewport_id_invalid",
        field="viewport_id",
        owner=owner,
        contribution_id=contribution_id,
        index=index,
    )
    name_key = _portable_token(
        raw_item.get("name_key"),
        code="contribution_viewport_name_key_invalid",
        field="name_key",
        owner=owner,
        contribution_id=contribution_id,
        index=index,
    )

    raw_events = raw_item.get("refresh_events", [])
    if not isinstance(raw_events, Sequence) or isinstance(
        raw_events, (str, bytes, bytearray)
    ):
        raise EditorContributionContractError(
            "contribution_event_invalid",
            "viewport surface refresh_events must be an array",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
            },
        )
    events: list[str] = []
    seen_events: set[str] = set()
    for raw_event in raw_events:
        _validate_json_value(
            raw_event,
            path=f"editor_contributions[{index}].refresh_events",
            owner=owner,
            contribution_id=contribution_id,
        )
        if not isinstance(raw_event, str) or not _EVENT_NAME_RE.fullmatch(
            raw_event
        ):
            raise EditorContributionContractError(
                "contribution_event_invalid",
                "viewport surface refresh event must be a portable event name",
                details={
                    "owner_plugin_id": owner,
                    "index": index,
                    "contribution_id": contribution_id,
                    "event": _diagnostic_value(raw_event),
                },
            )
        if raw_event in seen_events:
            raise EditorContributionContractError(
                "contribution_event_duplicate",
                "viewport surface refresh events cannot contain duplicates",
                details={
                    "owner_plugin_id": owner,
                    "index": index,
                    "contribution_id": contribution_id,
                    "event": raw_event,
                },
            )
        seen_events.add(raw_event)
        events.append(raw_event)

    return EditorViewportSurfaceContribution(
        owner_plugin_id=owner,
        id=contribution_id,
        kind=VIEWPORT_SURFACE_KIND,
        viewport_id=viewport_id,
        name_key=name_key,
        default_name=_required_text(
            raw_item, "default_name", owner=owner, index=index
        ),
        order=_parse_order(
            raw_item.get("order", 0),
            owner=owner,
            contribution_id=contribution_id,
            index=index,
        ),
        refresh_events=tuple(events),
    )


def _parse_theme_profile(
    owner: str,
    contribution_id: str,
    raw_item: Mapping[str, Any],
    *,
    index: int,
) -> EditorThemeProfileContribution:
    allowed_fields = {
        "id",
        "kind",
        "theme_id",
        "name_key",
        "default_name",
        "appearance",
        "palette",
        "order",
    }
    unknown_fields = sorted(
        str(key) for key in raw_item if key not in allowed_fields
    )
    if unknown_fields:
        raise EditorContributionContractError(
            "contribution_theme_field_unknown",
            "theme profile contribution contains unsupported fields",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
                "fields": unknown_fields,
            },
        )

    theme_id = _portable_token(
        raw_item.get("theme_id"),
        code="contribution_theme_id_invalid",
        field="theme_id",
        owner=owner,
        contribution_id=contribution_id,
        index=index,
    )
    name_key = _portable_token(
        raw_item.get("name_key"),
        code="contribution_theme_name_key_invalid",
        field="name_key",
        owner=owner,
        contribution_id=contribution_id,
        index=index,
    )
    appearance = _required_text(
        raw_item, "appearance", owner=owner, index=index
    )
    if appearance not in _THEME_APPEARANCES:
        raise EditorContributionContractError(
            "contribution_theme_appearance_invalid",
            "theme appearance must be one of the portable appearance values",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
                "appearance": appearance,
                "supported": sorted(_THEME_APPEARANCES),
            },
        )

    raw_palette = raw_item.get("palette")
    _validate_json_value(
        raw_palette,
        path=f"editor_contributions[{index}].palette",
        owner=owner,
        contribution_id=contribution_id,
    )
    if not isinstance(raw_palette, Mapping) or not raw_palette:
        raise EditorContributionContractError(
            "contribution_theme_palette_invalid",
            "theme palette must be a non-empty object",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
            },
        )

    palette: dict[str, str] = {}
    for token, color in sorted(raw_palette.items(), key=lambda item: str(item[0])):
        if not isinstance(token, str) or not _SEMANTIC_PALETTE_TOKEN_RE.fullmatch(
            token
        ):
            raise EditorContributionContractError(
                "contribution_theme_palette_token_invalid",
                "theme palette keys must be portable semantic tokens",
                details={
                    "owner_plugin_id": owner,
                    "index": index,
                    "contribution_id": contribution_id,
                    "token": _diagnostic_value(token),
                },
            )
        if not isinstance(color, str) or not _PORTABLE_COLOR_RE.fullmatch(color):
            raise EditorContributionContractError(
                "contribution_theme_palette_color_invalid",
                "theme palette colors must be #RRGGBB or #RRGGBBAA values",
                details={
                    "owner_plugin_id": owner,
                    "index": index,
                    "contribution_id": contribution_id,
                    "token": token,
                    "color": _diagnostic_value(color),
                },
            )
        palette[token] = color.lower()

    return EditorThemeProfileContribution(
        owner_plugin_id=owner,
        id=contribution_id,
        kind=THEME_PROFILE_KIND,
        theme_id=theme_id,
        name_key=name_key,
        default_name=_required_text(
            raw_item, "default_name", owner=owner, index=index
        ),
        appearance=appearance,
        palette=MappingProxyType(palette),
        order=_parse_order(
            raw_item.get("order", 0),
            owner=owner,
            contribution_id=contribution_id,
            index=index,
        ),
    )

def _parse_command_state_projection(
    raw_state: Any,
    *,
    owner: str,
    contribution_id: str,
    index: int,
) -> EditorCommandStateProjection:
    if not isinstance(raw_state, Mapping):
        raise EditorContributionContractError(
            "contribution_toolbar_state_invalid",
            "toolbar state projection must be an object",
            details={
                "owner_plugin_id": owner,
                "contribution_id": contribution_id,
                "index": index,
                "value_type": type(raw_state).__name__,
            },
        )
    allowed_fields = {
        "command_id",
        "result_field",
        "label_variants",
        "refresh_events",
    }
    unknown_fields = sorted(
        str(key) for key in raw_state if key not in allowed_fields
    )
    if unknown_fields:
        raise EditorContributionContractError(
            "contribution_toolbar_state_field_unknown",
            "toolbar state projection contains unsupported fields",
            details={
                "owner_plugin_id": owner,
                "contribution_id": contribution_id,
                "index": index,
                "fields": unknown_fields,
            },
        )

    command_id = _required_text(
        raw_state,
        "command_id",
        owner=owner,
        index=index,
        path="state",
    )
    result_field = _portable_token(
        raw_state.get("result_field"),
        code="contribution_toolbar_state_field_invalid",
        field="state.result_field",
        owner=owner,
        contribution_id=contribution_id,
        index=index,
    )
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", result_field):
        raise EditorContributionContractError(
            "contribution_toolbar_state_field_invalid",
            "state.result_field must name one top-level result field",
            details={
                "owner_plugin_id": owner,
                "contribution_id": contribution_id,
                "index": index,
                "field": result_field,
            },
        )

    raw_variants = raw_state.get("label_variants")
    if not isinstance(raw_variants, Mapping) or not raw_variants:
        raise EditorContributionContractError(
            "contribution_toolbar_state_variants_invalid",
            "toolbar state label_variants must be a non-empty object",
            details={
                "owner_plugin_id": owner,
                "contribution_id": contribution_id,
                "index": index,
            },
        )
    variants: dict[str, EditorLabelVariant] = {}
    for raw_value in sorted(raw_variants, key=lambda value: str(value)):
        value = _portable_token(
            raw_value,
            code="contribution_toolbar_state_variant_key_invalid",
            field="state.label_variants key",
            owner=owner,
            contribution_id=contribution_id,
            index=index,
        )
        raw_variant = raw_variants[raw_value]
        if not isinstance(raw_variant, Mapping):
            raise EditorContributionContractError(
                "contribution_toolbar_state_variant_invalid",
                "toolbar state label variant must be an object",
                details={
                    "owner_plugin_id": owner,
                    "contribution_id": contribution_id,
                    "index": index,
                    "variant": value,
                },
            )
        unknown_variant_fields = sorted(
            str(key)
            for key in raw_variant
            if key not in {"label_key", "default_label"}
        )
        if unknown_variant_fields:
            raise EditorContributionContractError(
                "contribution_toolbar_state_variant_field_unknown",
                "toolbar state label variant contains unsupported fields",
                details={
                    "owner_plugin_id": owner,
                    "contribution_id": contribution_id,
                    "index": index,
                    "variant": value,
                    "fields": unknown_variant_fields,
                },
            )
        variants[value] = EditorLabelVariant(
            label_key=_required_text(
                raw_variant,
                "label_key",
                owner=owner,
                index=index,
                path=f"state.label_variants.{value}",
            ),
            default_label=_required_text(
                raw_variant,
                "default_label",
                owner=owner,
                index=index,
                path=f"state.label_variants.{value}",
            ),
        )

    raw_events = raw_state.get("refresh_events")
    if (
        not isinstance(raw_events, Sequence)
        or isinstance(raw_events, (str, bytes, bytearray))
        or not raw_events
    ):
        raise EditorContributionContractError(
            "contribution_toolbar_refresh_events_invalid",
            "toolbar state refresh_events must be a non-empty array",
            details={
                "owner_plugin_id": owner,
                "contribution_id": contribution_id,
                "index": index,
            },
        )
    events: list[str] = []
    seen_events: set[str] = set()
    for raw_event in raw_events:
        _validate_json_value(
            raw_event,
            path=f"editor_contributions[{index}].state.refresh_events",
            owner=owner,
            contribution_id=contribution_id,
        )
        if not isinstance(raw_event, str) or not _EVENT_NAME_RE.fullmatch(raw_event):
            raise EditorContributionContractError(
                "contribution_toolbar_refresh_event_invalid",
                "toolbar state refresh event must be a portable event name",
                details={
                    "owner_plugin_id": owner,
                    "contribution_id": contribution_id,
                    "index": index,
                    "event": _diagnostic_value(raw_event),
                },
            )
        if raw_event in seen_events:
            raise EditorContributionContractError(
                "contribution_toolbar_refresh_event_duplicate",
                "toolbar state refresh events cannot contain duplicates",
                details={
                    "owner_plugin_id": owner,
                    "contribution_id": contribution_id,
                    "index": index,
                    "event": raw_event,
                },
            )
        seen_events.add(raw_event)
        events.append(raw_event)

    return EditorCommandStateProjection(
        command_id=command_id,
        result_field=result_field,
        label_variants=MappingProxyType(variants),
        refresh_events=tuple(events),
    )


def _dock_id(
    value: Any, *, code: str, field: str, owner: str,
    contribution_id: str, index: int,
) -> str:
    _validate_json_value(
        value, path=f"editor_contributions[{index}].{field}",
        owner=owner, contribution_id=contribution_id,
    )
    if not isinstance(value, str) or not _DOCK_ID_RE.fullmatch(value):
        raise EditorContributionContractError(
            code, f"{field} must be a stable dock id",
            details={
                "owner_plugin_id": owner, "contribution_id": contribution_id,
                "index": index, "field": field,
                "value": _diagnostic_value(value),
            },
        )
    return value


def _dock_flag(
    value: Any, *, field: str, owner: str,
    contribution_id: str, index: int,
) -> bool:
    if not isinstance(value, bool):
        raise EditorContributionContractError(
            "contribution_dock_flag_invalid", f"{field} must be a boolean",
            details={
                "owner_plugin_id": owner, "contribution_id": contribution_id,
                "index": index, "field": field,
                "value_type": type(value).__name__,
            },
        )
    return value


def _portable_token(
    value: Any,
    *,
    code: str,
    field: str,
    owner: str,
    contribution_id: str,
    index: int,
) -> str:
    _validate_json_value(
        value,
        path=f"editor_contributions[{index}].{field}",
        owner=owner,
        contribution_id=contribution_id,
    )
    if not isinstance(value, str) or not _PORTABLE_TOKEN_RE.fullmatch(value):
        raise EditorContributionContractError(
            code,
            f"{field} must be a portable token",
            details={
                "owner_plugin_id": owner,
                "contribution_id": contribution_id,
                "index": index,
                "field": field,
                "value": _diagnostic_value(value),
            },
        )
    return value


def _parse_order(
    value: Any,
    *,
    owner: str,
    contribution_id: str,
    index: int,
) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise EditorContributionContractError(
            "contribution_order_invalid",
            "editor contribution order must be an integer",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "contribution_id": contribution_id,
                "value_type": type(value).__name__,
            },
        )
    return value


def _parse_menu_path_segment(
    raw_segment: Any,
    *,
    owner: str,
    contribution_id: str,
    item_index: int,
    segment_index: int,
) -> EditorMenuPathSegment:
    if not isinstance(raw_segment, Mapping):
        raise EditorContributionContractError(
            "contribution_menu_path_segment_invalid",
            "each menu_path segment must be an object",
            details={
                "owner_plugin_id": owner,
                "contribution_id": contribution_id,
                "index": item_index,
                "segment_index": segment_index,
                "value_type": type(raw_segment).__name__,
            },
        )
    allowed_fields = {"id", "label_key", "default_label"}
    unknown_fields = sorted(
        str(key) for key in raw_segment if key not in allowed_fields
    )
    if unknown_fields:
        raise EditorContributionContractError(
            "contribution_menu_path_field_unknown",
            "menu_path segment contains unsupported fields",
            details={
                "owner_plugin_id": owner,
                "contribution_id": contribution_id,
                "index": item_index,
                "segment_index": segment_index,
                "fields": unknown_fields,
            },
        )
    return EditorMenuPathSegment(
        id=_required_text(
            raw_segment,
            "id",
            owner=owner,
            index=item_index,
            path=f"menu_path[{segment_index}]",
        ),
        label_key=_required_text(
            raw_segment,
            "label_key",
            owner=owner,
            index=item_index,
            path=f"menu_path[{segment_index}]",
        ),
        default_label=_required_text(
            raw_segment,
            "default_label",
            owner=owner,
            index=item_index,
            path=f"menu_path[{segment_index}]",
        ),
    )


def _required_text(
    mapping: Mapping[str, Any],
    field: str,
    *,
    owner: str,
    index: int,
    path: str = "",
) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise EditorContributionContractError(
            "contribution_text_invalid",
            f"{field} must be a non-empty string",
            details={
                "owner_plugin_id": owner,
                "index": index,
                "field": f"{path}.{field}" if path else field,
                "value_type": type(value).__name__,
            },
        )
    return value.strip()


def _reject_live_values(value: Any, *, path: str) -> None:
    if callable(value) or hasattr(value, "get_plugin_info"):
        raise EditorContributionContractError(
            "contribution_live_value_forbidden",
            "editor contributions cannot contain callbacks or live plugin objects",
            details={"path": path, "value_type": type(value).__name__},
        )
    if isinstance(value, Mapping):
        for key, nested in value.items():
            _reject_live_values(nested, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _reject_live_values(nested, path=f"{path}[{index}]")


def _validate_json_value(
    value: Any,
    *,
    path: str,
    owner: str,
    contribution_id: str,
) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if math.isfinite(value):
            return
    elif isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                break
            _validate_json_value(
                nested,
                path=f"{path}.{key}",
                owner=owner,
                contribution_id=contribution_id,
            )
        else:
            return
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _validate_json_value(
                nested,
                path=f"{path}[{index}]",
                owner=owner,
                contribution_id=contribution_id,
            )
        return
    raise EditorContributionContractError(
        "contribution_value_not_json_safe",
        "editor contribution values must be strict JSON data",
        details={
            "owner_plugin_id": owner,
            "contribution_id": contribution_id,
            "path": path,
            "value_type": type(value).__name__,
        },
    )


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_json(nested) for key, nested in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(nested) for nested in value)
    return value


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(nested) for nested in value]
    return value


def _diagnostic_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, Mapping):
        return {
            str(key): _diagnostic_value(nested)
            for key, nested in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_diagnostic_value(nested) for nested in value]
    return type(value).__name__


__all__ = [
    "EditorContribution",
    "EditorDockSurfaceContribution",
    "EditorCommandStateProjection",
    "EditorContributionContractError",
    "EditorLabelVariant",
    "EditorMenuCommandContribution",
    "EditorMenuPathSegment",
    "EditorThemeProfileContribution",
    "EditorToolbarCommandContribution",
    "EditorViewportSurfaceContribution",
    "DOCK_SURFACE_KIND",
    "MENU_COMMAND_KIND",
    "THEME_PROFILE_KIND",
    "TOOLBAR_COMMAND_KIND",
    "VIEWPORT_SURFACE_KIND",
    "SUPPORTED_EDITOR_CONTRIBUTION_KINDS",
    "parse_editor_contributions",
]