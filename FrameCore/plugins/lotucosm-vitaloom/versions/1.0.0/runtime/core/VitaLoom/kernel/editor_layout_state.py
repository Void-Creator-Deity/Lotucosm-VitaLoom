# -*- coding: utf-8 -*-
"""Qt-free persisted Editor-shell layout facts.

This value object deliberately owns only portable JSON layout facts. Qt window
state bytes and native widgets remain the responsibility of LayoutManager, the
current concrete editor Host Adapter.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


_JSON_OBJECT = dict[str, Any]


@dataclass(frozen=True)
class EditorLayoutState:
    """A defensive, JSON-safe snapshot of persisted editor-shell layout state."""

    window_state: str
    geometry: _JSON_OBJECT
    dock_states: dict[str, _JSON_OBJECT]
    viewport_state: _JSON_OBJECT

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EditorLayoutState":
        """Copy known layout facts from one untrusted persisted JSON object."""
        if not isinstance(value, Mapping):
            raise TypeError("editor layout state must be a mapping")
        raw_window_state = value.get("window_state", "")
        return cls(
            window_state=raw_window_state if isinstance(raw_window_state, str) else "",
            geometry=_object_copy(value.get("geometry")),
            dock_states=_named_object_map_copy(value.get("dock_states")),
            viewport_state=_object_copy(value.get("viewport_state")),
        )

    def to_mapping(self) -> _JSON_OBJECT:
        """Return a deep JSON-safe copy suitable for persistence or another Host."""
        return {
            "window_state": self.window_state,
            "geometry": _object_copy(self.geometry),
            "dock_states": {
                name: _object_copy(state) for name, state in self.dock_states.items()
            },
            "viewport_state": _object_copy(self.viewport_state),
        }


def _object_copy(value: object) -> _JSON_OBJECT:
    if not isinstance(value, Mapping):
        return {}
    return _json_copy(dict(value))


def _named_object_map_copy(value: object) -> dict[str, _JSON_OBJECT]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(name): _object_copy(state)
        for name, state in value.items()
        if isinstance(name, str) and isinstance(state, Mapping)
    }


def _json_copy(value: _JSON_OBJECT) -> _JSON_OBJECT:
    """Reject non-JSON nested values rather than leaking Host objects outward."""
    try:
        copied = json.loads(json.dumps(value, ensure_ascii=False))
    except (TypeError, ValueError) as error:
        raise ValueError("editor layout state must contain JSON-safe values") from error
    if not isinstance(copied, dict):  # Defensive against a future serializer change.
        raise ValueError("editor layout state copy must remain an object")
    return copied


__all__ = ["EditorLayoutState"]
