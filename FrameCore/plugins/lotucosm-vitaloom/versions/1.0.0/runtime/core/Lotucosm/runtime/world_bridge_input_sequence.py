"""Canonical, Qt-free input sequence for the opt-in WorldBridge boundary."""
from __future__ import annotations

import copy
import hashlib
import json
from collections import deque
from collections.abc import Mapping
from typing import Any

SCHEMA_VERSION = 1
STATUS = "worldbridge_input_sequence"
LIFECYCLE_ACTIONS = frozenset({"start", "pause", "resume", "stop", "reset", "tick"})
EVENT_KINDS = frozenset({"key_down", "key_up", "mouse_move", "mouse_down", "mouse_up"})
SCHEDULER_STATUS = "worldbridge_scheduler_input_queue"
DEFAULT_MAX_PENDING = 256
SUPPORTED_OVERFLOW_POLICIES = frozenset({"reject_newest"})
DISPATCH_PHASE = "sr_snapshot"
ROUTING_POLICY = "sr_snapshot_then_ps_handoff"


class WorldBridgeInputBackpressureError(ValueError):
    """Raised when the bounded canonical queue rejects a new event."""

    def __init__(self, receipt: Mapping[str, Any]) -> None:
        self.receipt = copy.deepcopy(dict(receipt))
        super().__init__("worldbridge input queue backpressure")


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


class WorldBridgeInputSequence:
    """Own ordered input events and lifecycle epochs without Qt or live objects."""

    def __init__(
        self,
        *,
        scheduler_owner_id: str = "viewport_private_sr_input_buffer",
        max_pending: int = DEFAULT_MAX_PENDING,
        overflow_policy: str = "reject_newest",
    ) -> None:
        if (
            not isinstance(scheduler_owner_id, str)
            or not scheduler_owner_id.strip()
        ):
            raise ValueError("scheduler_owner_id must be non-empty")
        if (
            isinstance(max_pending, bool)
            or not isinstance(max_pending, int)
            or max_pending < 1
        ):
            raise ValueError("max_pending must be a positive integer")
        if overflow_policy not in SUPPORTED_OVERFLOW_POLICIES:
            raise ValueError("unsupported overflow_policy")
        self._sequence = 0
        self._pause_reset_epoch = 0
        self._pending: list[dict[str, Any]] = []
        self._seen_ids: set[str] = set()
        self._scheduler_owner_id = scheduler_owner_id
        self._max_pending = max_pending
        self._overflow_policy = overflow_policy
        self._accepted_count = 0
        self._rejected_count = 0
        self._dropped_count = 0
        self._dispatch_count = 0
        self._last_drop_reason: str | None = None
        self._backpressure_receipts: deque[dict[str, Any]] = deque(maxlen=64)
        self._drop_receipts: deque[dict[str, Any]] = deque(maxlen=64)
        self._dispatch_receipts: deque[dict[str, Any]] = deque(maxlen=64)

    @property
    def pause_reset_epoch(self) -> int:
        return self._pause_reset_epoch

    @property
    def scheduler_owner_id(self) -> str:
        return self._scheduler_owner_id

    def lifecycle(self, action: str) -> dict[str, Any]:
        if action not in LIFECYCLE_ACTIONS:
            raise ValueError("unsupported lifecycle action")
        if action in {"start", "pause", "resume", "stop", "reset"}:
            dropped_ids = [event["event_id"] for event in self._pending]
            if dropped_ids:
                receipt = {
                    "schema_version": SCHEMA_VERSION,
                    "status": "worldbridge_input_drop_receipt",
                    "reason": f"lifecycle:{action}",
                    "pause_reset_epoch": self._pause_reset_epoch,
                    "dropped_event_ids": dropped_ids,
                    "dropped_count": len(dropped_ids),
                    "batch_digest": _digest(self._pending),
                }
                self._drop_receipts.append(receipt)
                self._dropped_count += len(dropped_ids)
                self._last_drop_reason = f"lifecycle:{action}"
            self._pause_reset_epoch += 1
            self._pending.clear()
        return {"action": action, "pause_reset_epoch": self._pause_reset_epoch}

    def append(self, kind: str, payload: Mapping[str, Any], *, event_id: str | None = None) -> dict[str, Any]:
        if kind not in EVENT_KINDS:
            raise ValueError("unsupported input event kind")
        if not isinstance(payload, Mapping):
            raise TypeError("input event payload must be a mapping")
        if len(self._pending) >= self._max_pending:
            identifier = event_id or f"input-{self._sequence + 1}"
            receipt = {
                "schema_version": SCHEMA_VERSION,
                "status": "worldbridge_input_backpressure_receipt",
                "scheduler_owner_id": self._scheduler_owner_id,
                "overflow_policy": self._overflow_policy,
                "pause_reset_epoch": self._pause_reset_epoch,
                "pending_count": len(self._pending),
                "max_pending": self._max_pending,
                "rejected_event_id": identifier,
                "rejected_kind": kind,
                "rejected_payload_digest": _digest(dict(payload)),
                "next_sequence_unchanged": self._sequence + 1,
            }
            self._backpressure_receipts.append(receipt)
            self._rejected_count += 1
            raise WorldBridgeInputBackpressureError(receipt)
        self._sequence += 1
        identifier = event_id or f"input-{self._sequence}"
        if not isinstance(identifier, str) or not identifier or identifier in self._seen_ids:
            raise ValueError("duplicate or invalid input event id")
        event = {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS,
            "event_id": identifier,
            "sequence": self._sequence,
            "pause_reset_epoch": self._pause_reset_epoch,
            "kind": kind,
            "payload": copy.deepcopy(dict(payload)),
        }
        event["event_digest"] = _digest({key: value for key, value in event.items() if key != "event_digest"})
        self._seen_ids.add(identifier)
        self._pending.append(event)
        self._accepted_count += 1
        return copy.deepcopy(event)

    def consume(self) -> list[dict[str, Any]]:
        events = copy.deepcopy(self._pending)
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "status": "worldbridge_input_dispatch_receipt",
            "scheduler_owner_id": self._scheduler_owner_id,
            "dispatch_phase": DISPATCH_PHASE,
            "routing_policy": ROUTING_POLICY,
            "pause_reset_epoch": self._pause_reset_epoch,
            "event_ids": [event["event_id"] for event in events],
            "event_count": len(events),
            "first_sequence": events[0]["sequence"] if events else None,
            "last_sequence": events[-1]["sequence"] if events else None,
            "batch_digest": _digest(events),
        }
        self._dispatch_receipts.append(receipt)
        self._dispatch_count += 1
        self._pending.clear()
        return events

    def configure_policy(
        self,
        *,
        max_pending: int,
        overflow_policy: str = "reject_newest",
    ) -> dict[str, Any]:
        """Set queue capacity while empty; pending events are never discarded."""
        if self._pending:
            raise ValueError("cannot change input policy with pending events")
        if (
            isinstance(max_pending, bool)
            or not isinstance(max_pending, int)
            or max_pending < 1
        ):
            raise ValueError("max_pending must be a positive integer")
        if overflow_policy not in SUPPORTED_OVERFLOW_POLICIES:
            raise ValueError("unsupported overflow_policy")
        self._max_pending = max_pending
        self._overflow_policy = overflow_policy
        return self.scheduler_snapshot()

    def scheduler_snapshot(self) -> dict[str, Any]:
        pending = self.snapshot()["pending"]
        return {
            "schema_version": SCHEMA_VERSION,
            "status": SCHEDULER_STATUS,
            "scheduler_owner_id": self._scheduler_owner_id,
            "canonical_event_schema": STATUS,
            "dispatch_phase": DISPATCH_PHASE,
            "routing_policy": ROUTING_POLICY,
            "max_pending": self._max_pending,
            "overflow_policy": self._overflow_policy,
            "pending_count": len(pending),
            "next_sequence": self._sequence + 1,
            "pause_reset_epoch": self._pause_reset_epoch,
            "accepted_count": self._accepted_count,
            "rejected_count": self._rejected_count,
            "dropped_count": self._dropped_count,
            "dispatch_count": self._dispatch_count,
            "last_drop_reason": self._last_drop_reason,
            "backpressure_receipts": copy.deepcopy(
                list(self._backpressure_receipts)
            ),
            "drop_receipts": copy.deepcopy(list(self._drop_receipts)),
            "dispatch_receipts": copy.deepcopy(list(self._dispatch_receipts)),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS,
            "pause_reset_epoch": self._pause_reset_epoch,
            "next_sequence": self._sequence + 1,
            "seen_event_ids": sorted(self._seen_ids),
            "pending": copy.deepcopy(self._pending),
        }

    def restore_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        """Restore the opt-in cursor atomically after validating event digests."""
        self.validate_snapshot(snapshot)
        epoch = snapshot["pause_reset_epoch"]
        next_sequence = snapshot["next_sequence"]
        seen = snapshot["seen_event_ids"]
        pending = snapshot["pending"]
        self._pause_reset_epoch = epoch
        self._sequence = next_sequence - 1
        self._seen_ids = set(seen)
        self._pending = copy.deepcopy(pending)

    @staticmethod
    def validate_snapshot(snapshot: Mapping[str, Any]) -> None:
        """Validate a cursor snapshot without touching the live sequence."""
        if not isinstance(snapshot, Mapping):
            raise TypeError("input sequence snapshot must be a mapping")
        required = {
            "schema_version", "status", "pause_reset_epoch", "next_sequence",
            "seen_event_ids", "pending",
        }
        if set(snapshot) != required:
            raise ValueError("input sequence snapshot schema mismatch")
        if snapshot.get("schema_version") != SCHEMA_VERSION or snapshot.get("status") != STATUS:
            raise ValueError("input sequence snapshot version mismatch")
        epoch = snapshot.get("pause_reset_epoch")
        next_sequence = snapshot.get("next_sequence")
        if isinstance(epoch, bool) or not isinstance(epoch, int) or epoch < 0:
            raise ValueError("input sequence snapshot epoch invalid")
        if isinstance(next_sequence, bool) or not isinstance(next_sequence, int) or next_sequence < 1:
            raise ValueError("input sequence snapshot cursor invalid")
        seen = snapshot.get("seen_event_ids")
        pending = snapshot.get("pending")
        if (
            not isinstance(seen, list)
            or any(not isinstance(value, str) or not value for value in seen)
            or len(set(seen)) != len(seen)
        ):
            raise ValueError("input sequence snapshot seen ids invalid")
        if not isinstance(pending, list):
            raise ValueError("input sequence snapshot pending invalid")
        last_sequence = next_sequence - 1
        validation = validate_worldbridge_input_events(
            pending,
            last_sequence=(pending[0].get("sequence", 1) - 1 if pending else last_sequence),
            pause_reset_epoch=epoch,
        )
        if pending and not validation["valid"]:
            raise ValueError("input sequence snapshot pending events invalid")
        if pending and pending[-1].get("sequence") != last_sequence:
            raise ValueError("input sequence snapshot cursor does not cover pending events")
        if any(
            not isinstance(event, Mapping) or event.get("event_id") not in seen
            for event in pending
        ):
            raise ValueError("input sequence snapshot pending ids invalid")


def validate_worldbridge_scheduler_input_queue_snapshot(
    value: object,
) -> dict[str, Any]:
    """Validate scheduler owner, capacity, routing and bounded receipts."""
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["snapshot_not_mapping"]}
    required = {
        "schema_version",
        "status",
        "scheduler_owner_id",
        "canonical_event_schema",
        "dispatch_phase",
        "routing_policy",
        "max_pending",
        "overflow_policy",
        "pending_count",
        "next_sequence",
        "pause_reset_epoch",
        "accepted_count",
        "rejected_count",
        "dropped_count",
        "dispatch_count",
        "last_drop_reason",
        "backpressure_receipts",
        "drop_receipts",
        "dispatch_receipts",
    }
    errors: list[str] = []
    if set(value) != required:
        errors.append("snapshot_keys_invalid")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != SCHEDULER_STATUS:
        errors.append("status_mismatch")
    owner = value.get("scheduler_owner_id")
    if not isinstance(owner, str) or not owner.strip():
        errors.append("scheduler_owner_invalid")
    if value.get("canonical_event_schema") != STATUS:
        errors.append("canonical_event_schema_mismatch")
    if value.get("dispatch_phase") != DISPATCH_PHASE:
        errors.append("dispatch_phase_mismatch")
    if value.get("routing_policy") != ROUTING_POLICY:
        errors.append("routing_policy_mismatch")
    max_pending = value.get("max_pending")
    if (
        isinstance(max_pending, bool)
        or not isinstance(max_pending, int)
        or max_pending < 1
    ):
        errors.append("max_pending_invalid")
    if value.get("overflow_policy") not in SUPPORTED_OVERFLOW_POLICIES:
        errors.append("overflow_policy_invalid")
    for field in (
        "pending_count",
        "next_sequence",
        "pause_reset_epoch",
        "accepted_count",
        "rejected_count",
        "dropped_count",
        "dispatch_count",
    ):
        item = value.get(field)
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            errors.append(f"{field}_invalid")
    if (
        isinstance(value.get("next_sequence"), int)
        and not isinstance(value.get("next_sequence"), bool)
        and value["next_sequence"] < 1
    ):
        errors.append("next_sequence_invalid")
    if (
        isinstance(max_pending, int)
        and not isinstance(max_pending, bool)
        and isinstance(value.get("pending_count"), int)
        and not isinstance(value.get("pending_count"), bool)
        and value["pending_count"] > max_pending
    ):
        errors.append("pending_count_exceeds_capacity")
    for field, expected_status in (
        ("backpressure_receipts", "worldbridge_input_backpressure_receipt"),
        ("drop_receipts", "worldbridge_input_drop_receipt"),
        ("dispatch_receipts", "worldbridge_input_dispatch_receipt"),
    ):
        receipts = value.get(field)
        if not isinstance(receipts, list) or len(receipts) > 64:
            errors.append(f"{field}_invalid")
            continue
        if any(
            not isinstance(receipt, Mapping)
            or receipt.get("status") != expected_status
            for receipt in receipts
        ):
            errors.append(f"{field}_entry_invalid")
    backpressure = value.get("backpressure_receipts")
    if isinstance(backpressure, list) and isinstance(
        value.get("rejected_count"), int
    ):
        if len(backpressure) > value["rejected_count"]:
            errors.append("backpressure_receipt_count_mismatch")
    dispatch_receipts = value.get("dispatch_receipts")
    if isinstance(dispatch_receipts, list) and isinstance(
        value.get("dispatch_count"), int
    ):
        if len(dispatch_receipts) > value["dispatch_count"]:
            errors.append("dispatch_receipt_count_mismatch")
    drop_reason = value.get("last_drop_reason")
    if drop_reason is not None and (
        not isinstance(drop_reason, str) or not drop_reason.strip()
    ):
        errors.append("last_drop_reason_invalid")
    return {"valid": not errors, "errors": errors}


def validate_worldbridge_input_events(events: object, *, last_sequence: int = 0, pause_reset_epoch: int = 0) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(events, list):
        return {"valid": False, "errors": ["events_not_list"]}
    expected = last_sequence + 1
    seen: set[str] = set()
    for index, event in enumerate(events):
        if not isinstance(event, Mapping):
            errors.append(f"event_{index}_not_mapping")
            continue
        required = {"schema_version", "status", "event_id", "sequence", "pause_reset_epoch", "kind", "payload", "event_digest"}
        if set(event) != required:
            errors.append(f"event_{index}_schema_invalid")
            continue
        if event.get("schema_version") != SCHEMA_VERSION or event.get("status") != STATUS:
            errors.append(f"event_{index}_version_invalid")
        if event.get("sequence") != expected:
            errors.append(f"event_{index}_sequence_invalid")
        expected += 1
        if event.get("pause_reset_epoch") != pause_reset_epoch:
            errors.append(f"event_{index}_epoch_invalid")
        identifier = event.get("event_id")
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            errors.append(f"event_{index}_id_invalid")
        else:
            seen.add(identifier)
        if event.get("kind") not in EVENT_KINDS or not isinstance(event.get("payload"), Mapping):
            errors.append(f"event_{index}_payload_invalid")
        elif event.get("event_digest") != _digest({key: value for key, value in event.items() if key != "event_digest"}):
            errors.append(f"event_{index}_digest_invalid")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "DEFAULT_MAX_PENDING",
    "DISPATCH_PHASE",
    "EVENT_KINDS",
    "LIFECYCLE_ACTIONS",
    "ROUTING_POLICY",
    "SCHEDULER_STATUS",
    "STATUS",
    "SUPPORTED_OVERFLOW_POLICIES",
    "WorldBridgeInputBackpressureError",
    "WorldBridgeInputSequence",
    "validate_worldbridge_input_events",
    "validate_worldbridge_scheduler_input_queue_snapshot",
]
