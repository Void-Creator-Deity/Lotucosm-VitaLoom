# -*- coding: utf-8
"""Versioned, opt-in SR-local input events.

This module is a runtime-owned log primitive.  It is deliberately not wired to
GameViewport, Pond, the shared input queue, or cross-lane replay.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Optional


SCHEMA_VERSION = 1
STATUS = "sr_local_input_event_log"
_DIGEST_FIELD = "digest"

DEFAULT_ACTIONS = frozenset(
    {
        "key_down",
        "key_up",
        "mouse_move",
        "mouse_left_down",
        "mouse_left_up",
        "thrust",
        "turn",
    }
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(state: Mapping[str, Any]) -> str:
    payload = dict(state)
    payload[_DIGEST_FIELD] = ""
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _copy_json_value(value: Any) -> Any:
    try:
        encoded = _canonical(value)
        return json.loads(encoded.decode("utf-8"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("payload must be finite canonical JSON") from exc


def _validate_non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


@dataclass(frozen=True)
class SrInputEvent:
    """Immutable event returned by append and events_since."""

    sequence: int
    tick: int
    action: str
    payload: Any

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "tick": self.tick,
            "action": self.action,
            "payload": _copy_json_value(self.payload),
        }


class SrInputEventLog:
    """Validated local event log with atomic snapshot restoration."""

    def __init__(self, allowed_actions: Optional[Sequence[str]] = None) -> None:
        actions = DEFAULT_ACTIONS if allowed_actions is None else frozenset(allowed_actions)
        if not actions or any(not isinstance(action, str) or not action for action in actions):
            raise ValueError("allowed_actions must contain non-empty strings")
        self._allowed_actions = actions
        self._events: list[SrInputEvent] = []
        self._last_tick: Optional[int] = None

    @property
    def cursor(self) -> int:
        return len(self._events)

    @property
    def allowed_actions(self) -> frozenset[str]:
        return self._allowed_actions

    def append(
        self,
        tick: int,
        action: str,
        value: Any = None,
        *,
        payload: Any = None,
    ) -> SrInputEvent:
        """Append one event; sequence is assigned and cannot be supplied."""
        tick_value = _validate_non_negative_int(tick, "tick")
        if not isinstance(action, str) or action not in self._allowed_actions:
            raise ValueError("unknown input action")
        if value is not None and payload is not None:
            raise ValueError("provide either value or payload, not both")
        payload_value = value if payload is None else payload
        normalized_payload = _copy_json_value(payload_value)
        if self._last_tick is not None and tick_value < self._last_tick:
            raise ValueError("event tick must be monotonic")
        event = SrInputEvent(self.cursor, tick_value, action, normalized_payload)
        self._events.append(event)
        self._last_tick = tick_value
        return SrInputEvent(event.sequence, event.tick, event.action, _copy_json_value(event.payload))

    def events_since(self, cursor: int = 0) -> list[dict[str, Any]]:
        cursor_value = _validate_non_negative_int(cursor, "cursor")
        if cursor_value > self.cursor:
            raise ValueError("cursor is beyond the log")
        return [event.to_dict() for event in self._events[cursor_value:]]

    def capture_state(self) -> dict[str, Any]:
        state: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS,
            "allowed_actions": sorted(self._allowed_actions),
            "cursor": self.cursor,
            "events": [event.to_dict() for event in self._events],
            "digest": "",
        }
        state["digest"] = _digest(state)
        return copy.deepcopy(state)

    def restore_state(self, state: Mapping[str, Any]) -> None:
        """Validate a complete snapshot before replacing this log atomically."""
        candidate = self._parse_state(state)
        self._events = candidate
        self._last_tick = candidate[-1].tick if candidate else None

    def _parse_state(self, state: Mapping[str, Any]) -> list[SrInputEvent]:
        if not isinstance(state, Mapping):
            raise TypeError("event log state must be a mapping")
        required = {"schema_version", "status", "allowed_actions", "cursor", "events", "digest"}
        if set(state) != required:
            raise ValueError("event log state fields do not match")
        if state["schema_version"] != SCHEMA_VERSION or state["status"] != STATUS:
            raise ValueError("event log schema mismatch")
        actions = state["allowed_actions"]
        if not isinstance(actions, list) or frozenset(actions) != self._allowed_actions:
            raise ValueError("event log allowed actions mismatch")
        cursor = _validate_non_negative_int(state["cursor"], "cursor")
        events = state["events"]
        if not isinstance(events, list) or cursor != len(events):
            raise ValueError("event log cursor mismatch")
        digest = state["digest"]
        if not isinstance(digest, str) or digest != _digest(state):
            raise ValueError("event log digest mismatch")

        parsed: list[SrInputEvent] = []
        last_tick: Optional[int] = None
        for expected_sequence, raw in enumerate(events):
            if not isinstance(raw, Mapping) or set(raw) != {"sequence", "tick", "action", "payload"}:
                raise ValueError("invalid event fields")
            sequence = _validate_non_negative_int(raw["sequence"], "sequence")
            if sequence != expected_sequence:
                raise ValueError("event sequence gap or duplicate")
            tick = _validate_non_negative_int(raw["tick"], "tick")
            if last_tick is not None and tick < last_tick:
                raise ValueError("event tick must be monotonic")
            action = raw["action"]
            if not isinstance(action, str) or action not in self._allowed_actions:
                raise ValueError("unknown input action")
            payload = _copy_json_value(raw["payload"])
            parsed.append(SrInputEvent(sequence, tick, action, payload))
            last_tick = tick
        return parsed


def validate_sr_input_event_log_state(state: object, allowed_actions: Optional[Sequence[str]] = None) -> dict[str, Any]:
    """Return structured validation evidence without mutating a caller log."""
    try:
        log = SrInputEventLog(allowed_actions)
        log._parse_state(state)  # validation-only path; no state mutation
    except (TypeError, ValueError) as exc:
        return {"valid": False, "errors": [str(exc)]}
    return {"valid": True, "errors": []}


__all__ = [
    "DEFAULT_ACTIONS",
    "SCHEMA_VERSION",
    "STATUS",
    "SrInputEvent",
    "SrInputEventLog",
    "validate_sr_input_event_log_state",
]
