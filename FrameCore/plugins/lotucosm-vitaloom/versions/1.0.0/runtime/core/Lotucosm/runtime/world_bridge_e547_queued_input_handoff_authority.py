# -*- coding: utf-8 -*-
"""Sealed read-only witness for one canonical SR input batch handed to PS.

The witness proves only a single completed tick's canonical input batch is
bound to the tick receipt, present unchanged in the shared-state envelope, and
received unchanged by the PS handoff owner. It does not prove a scheduler-owned
shared queue, backpressure, dropped-event policy, replay, checkpointing, or
default readiness.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from .world_bridge_e546_shared_clock_delta_authority import (
    validate_worldbridge_e546_shared_clock_delta_authority,
)
from .world_bridge_input_sequence import (
    WorldBridgeInputSequence,
    validate_worldbridge_input_events,
)
from .world_bridge_shared_state_transport import (
    validate_worldbridge_shared_state_envelope,
)
from .world_bridge_tick_authority import validate_worldbridge_tick_receipt

SCHEMA_VERSION = 1
STATUS = "worldbridge_e547_queued_input_handoff_authority"
SCOPE = "single_tick_sr_to_ps_canonical_input_batch"
ADMISSION_EFFECT = "none"
CLOSED_ADMISSION_FIELDS = (
    "shared_queued_input_ordering",
    "scheduler_owned",
    "cross_lane_input_ordering_admitted",
    "backpressure_admitted",
    "dropped_event_policy_admitted",
    "replay_admitted",
    "input_replay_admitted",
    "checkpoint_input_state",
    "tick_merge_admitted",
    "full_unified_replay_admitted",
    "lossless",
    "default_ready",
)
WITNESS_KEYS = (
    "schema_version",
    "status",
    "read_only",
    "scope",
    "completed_tick_receipt",
    "shared_clock_delta_witness",
    "canonical_input_events",
    "input_sequence_snapshot",
    "shared_state_envelope",
    "ps_received_input_events",
    "tick_sequence",
    "decision_digest",
    "pause_reset_epoch",
    "event_count",
    "input_digest",
    "first_input_sequence",
    "last_input_sequence",
    "batch_contiguous",
    "receipt_batch_bound",
    "envelope_batch_bound",
    "sr_pending_empty_after_tick",
    "canonical_event_ids_consumed",
    "ps_received_batch_identical",
    "same_tick_delta_observed",
    "grants_admission",
    "admission_effect",
    "shared_queued_input_ordering",
    "scheduler_owned",
    "cross_lane_input_ordering_admitted",
    "backpressure_admitted",
    "dropped_event_policy_admitted",
    "replay_admitted",
    "input_replay_admitted",
    "checkpoint_input_state",
    "tick_merge_admitted",
    "full_unified_replay_admitted",
    "lossless",
    "default_ready",
    "witness_digest",
)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _json_copy(value: object, field: str) -> Any:
    try:
        return json.loads(_canonical(value).decode("utf-8"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be finite canonical JSON") from exc


def _mapping_copy(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a mapping")
    copied = _json_copy(dict(value), field)
    if not isinstance(copied, dict):
        raise TypeError(f"{field} must remain a mapping")
    return copied


def _sequence_copy(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        raise TypeError("input events must be a sequence")
    copied = _json_copy(list(value), "input events")
    if not isinstance(copied, list) or any(
        not isinstance(row, dict) for row in copied
    ):
        raise TypeError("input events must contain mappings")
    return copied


def _witness_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["witness_digest"] = ""
    return _digest(payload)


def _batch_digest(events: list[dict[str, Any]]) -> str:
    return _digest(
        [
            {
                "event_id": event.get("event_id"),
                "sequence": event.get("sequence"),
                "pause_reset_epoch": event.get("pause_reset_epoch"),
                "kind": event.get("kind"),
                "payload": event.get("payload"),
                "event_digest": event.get("event_digest"),
            }
            for event in events
        ]
    )


def _batch_last_sequence(events: list[dict[str, Any]]) -> int:
    first = events[0].get("sequence") if events else None
    if isinstance(first, int) and not isinstance(first, bool):
        return first - 1
    return 0


def _transport_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "event_id": event.get("event_id"),
            "kind": event.get("kind"),
            "payload": {
                "canonical_sequence": event.get("sequence"),
                "pause_reset_epoch": event.get("pause_reset_epoch"),
                "event_digest": event.get("event_digest"),
                "data": event.get("payload"),
            },
        }
        for event in events
    ]


def _evaluate(
    *,
    receipt: Mapping[str, Any],
    clock_witness: Mapping[str, Any],
    events: list[dict[str, Any]],
    sequence_snapshot: Mapping[str, Any],
    envelope: Mapping[str, Any],
    ps_events: list[dict[str, Any]],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    receipt_validation = validate_worldbridge_tick_receipt(receipt)
    if receipt_validation != {"valid": True, "errors": []}:
        errors.extend(f"receipt_{item}" for item in receipt_validation["errors"])

    clock_validation = validate_worldbridge_e546_shared_clock_delta_authority(
        clock_witness
    )
    if clock_validation != {"valid": True, "errors": []}:
        errors.extend(f"clock_{item}" for item in clock_validation["errors"])
    if clock_witness.get("completed_tick_receipt") != dict(receipt):
        errors.append("clock_witness_receipt_mismatch")

    envelope_validation = validate_worldbridge_shared_state_envelope(envelope)
    if envelope_validation != {"valid": True, "errors": []}:
        errors.extend(f"envelope_{item}" for item in envelope_validation["errors"])

    epoch = receipt.get("pause_reset_epoch")
    validation = validate_worldbridge_input_events(
        events,
        last_sequence=_batch_last_sequence(events),
        pause_reset_epoch=(
            epoch if isinstance(epoch, int) and not isinstance(epoch, bool) else 0
        ),
    )
    if validation != {"valid": True, "errors": []}:
        errors.extend(f"canonical_input_{item}" for item in validation["errors"])
    ps_validation = validate_worldbridge_input_events(
        ps_events,
        last_sequence=_batch_last_sequence(ps_events),
        pause_reset_epoch=(
            epoch if isinstance(epoch, int) and not isinstance(epoch, bool) else 0
        ),
    )
    if ps_validation != {"valid": True, "errors": []}:
        errors.extend(f"ps_input_{item}" for item in ps_validation["errors"])

    try:
        WorldBridgeInputSequence.validate_snapshot(sequence_snapshot)
    except (TypeError, ValueError) as exc:
        errors.append(f"input_sequence_snapshot_invalid:{exc}")
        snapshot_pending: list[Any] = []
        snapshot_epoch = None
        snapshot_next = None
        snapshot_seen: list[Any] = []
    else:
        snapshot_pending = list(sequence_snapshot.get("pending", []))
        snapshot_epoch = sequence_snapshot.get("pause_reset_epoch")
        snapshot_next = sequence_snapshot.get("next_sequence")
        snapshot_seen = list(sequence_snapshot.get("seen_event_ids", []))

    if snapshot_pending:
        errors.append("input_sequence_pending_not_empty")
    if snapshot_epoch != epoch:
        errors.append("input_sequence_epoch_mismatch")
    if events:
        last_sequence = events[-1].get("sequence")
        if snapshot_next != (last_sequence + 1 if isinstance(last_sequence, int) else None):
            errors.append("input_sequence_cursor_mismatch")
        if not all(event.get("event_id") in snapshot_seen for event in events):
            errors.append("input_sequence_seen_ids_missing")
        if any(event.get("pause_reset_epoch") != epoch for event in events):
            errors.append("input_event_epoch_mismatch")

    event_count = len(events)
    if receipt.get("input_event_count") != event_count:
        errors.append("receipt_input_event_count_mismatch")
    input_digest = _batch_digest(events)
    if receipt.get("input_digest") != input_digest:
        errors.append("receipt_input_digest_mismatch")

    expected_transport = _transport_events(events)
    if envelope.get("input_events") != expected_transport:
        errors.append("envelope_input_batch_mismatch")
    lifecycle = envelope.get("lifecycle")
    if not isinstance(lifecycle, Mapping):
        errors.append("envelope_lifecycle_missing")
    else:
        if lifecycle.get("pause_reset_epoch") != epoch:
            errors.append("envelope_pause_reset_epoch_mismatch")
        if lifecycle.get("action") != "tick":
            errors.append("envelope_lifecycle_action_mismatch")
        if lifecycle.get("playing") is not True or lifecycle.get("paused") is not False:
            errors.append("envelope_lifecycle_flags_mismatch")
    clocks = envelope.get("clock_provenance")
    same_tick_delta = False
    if not isinstance(clocks, Mapping):
        errors.append("envelope_clock_provenance_missing")
    else:
        same_tick_delta = all(
            isinstance(clocks.get(lane), Mapping)
            and clocks[lane].get("delta") == receipt.get("delta_time")
            for lane in ("sr", "ps")
        )
        if not same_tick_delta:
            errors.append("envelope_lane_delta_mismatch")
    if ps_events != events:
        errors.append("ps_received_batch_mismatch")

    decision = receipt.get("clock_decision")
    projection = {
        "tick_sequence": receipt.get("tick_sequence"),
        "decision_digest": (
            decision.get("decision_digest")
            if isinstance(decision, Mapping)
            else None
        ),
        "pause_reset_epoch": epoch,
        "event_count": event_count,
        "input_digest": input_digest,
        "first_input_sequence": (
            events[0].get("sequence") if events else None
        ),
        "last_input_sequence": (
            events[-1].get("sequence") if events else None
        ),
        "batch_contiguous": validation == {"valid": True, "errors": []},
        "receipt_batch_bound": (
            receipt.get("input_event_count") == event_count
            and receipt.get("input_digest") == input_digest
        ),
        "envelope_batch_bound": envelope.get("input_events") == expected_transport,
        "sr_pending_empty_after_tick": not snapshot_pending,
        "canonical_event_ids_consumed": (
            not events
            or all(event.get("event_id") in snapshot_seen for event in events)
        ),
        "ps_received_batch_identical": ps_events == events,
        "same_tick_delta_observed": same_tick_delta,
    }
    return list(dict.fromkeys(errors)), projection


def build_worldbridge_e547_queued_input_handoff_authority(
    *,
    completed_tick_receipt: Mapping[str, Any],
    shared_clock_delta_witness: Mapping[str, Any],
    canonical_input_events: object,
    input_sequence_snapshot: Mapping[str, Any],
    shared_state_envelope: Mapping[str, Any],
    ps_received_input_events: object,
) -> dict[str, Any]:
    """Build a detached single-tick SR-to-PS canonical input-batch witness."""
    receipt = _mapping_copy(completed_tick_receipt, "completed_tick_receipt")
    clock_witness = _mapping_copy(
        shared_clock_delta_witness,
        "shared_clock_delta_witness",
    )
    events = _sequence_copy(canonical_input_events)
    snapshot = _mapping_copy(input_sequence_snapshot, "input_sequence_snapshot")
    envelope = _mapping_copy(shared_state_envelope, "shared_state_envelope")
    ps_events = _sequence_copy(ps_received_input_events)
    errors, projection = _evaluate(
        receipt=receipt,
        clock_witness=clock_witness,
        events=events,
        sequence_snapshot=snapshot,
        envelope=envelope,
        ps_events=ps_events,
    )
    if errors:
        raise ValueError(
            "E547 queued input handoff witness rejected: " + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "completed_tick_receipt": receipt,
        "shared_clock_delta_witness": clock_witness,
        "canonical_input_events": events,
        "input_sequence_snapshot": snapshot,
        "shared_state_envelope": envelope,
        "ps_received_input_events": ps_events,
        **projection,
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e547_queued_input_handoff_authority(
    value: object,
) -> dict[str, Any]:
    """Revalidate an E547 witness without trusting any embedded boolean."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    if set(value) != set(WITNESS_KEYS):
        errors.append("witness_keys_invalid")
    try:
        _canonical(value)
    except (TypeError, ValueError, OverflowError):
        return {"valid": False, "errors": errors + ["witness_not_canonical_json"]}
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_required")
    if value.get("scope") != SCOPE:
        errors.append("scope_mismatch")

    receipt = value.get("completed_tick_receipt")
    clock_witness = value.get("shared_clock_delta_witness")
    snapshot = value.get("input_sequence_snapshot")
    envelope = value.get("shared_state_envelope")
    events = value.get("canonical_input_events")
    ps_events = value.get("ps_received_input_events")
    if not all(
        isinstance(item, Mapping)
        for item in (receipt, clock_witness, snapshot, envelope)
    ):
        errors.append("witness_mapping_payload_invalid")
    if not isinstance(events, list) or not isinstance(ps_events, list):
        errors.append("witness_input_sequence_invalid")
    if errors:
        return {"valid": False, "errors": list(dict.fromkeys(errors))}
    try:
        clean_events = _sequence_copy(events)
        clean_ps_events = _sequence_copy(ps_events)
    except (TypeError, ValueError):
        return {"valid": False, "errors": errors + ["witness_input_not_canonical_json"]}

    revalidation, projection = _evaluate(
        receipt=receipt,
        clock_witness=clock_witness,
        events=clean_events,
        sequence_snapshot=snapshot,
        envelope=envelope,
        ps_events=clean_ps_events,
    )
    errors.extend(revalidation)
    for field, expected in projection.items():
        if value.get(field) != expected:
            errors.append(f"{field}_mismatch")
        if expected is not True and field in {
            "batch_contiguous",
            "receipt_batch_bound",
            "envelope_batch_bound",
            "sr_pending_empty_after_tick",
            "canonical_event_ids_consumed",
            "ps_received_batch_identical",
            "same_tick_delta_observed",
        }:
            errors.append(f"{field}_not_true")
    if value.get("grants_admission") is not False:
        errors.append("grants_admission_overclaim")
    if value.get("admission_effect") != ADMISSION_EFFECT:
        errors.append("admission_effect_mismatch")
    for field in CLOSED_ADMISSION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    digest = value.get("witness_digest")
    if (
        not isinstance(digest, str)
        or _DIGEST_RE.fullmatch(digest) is None
        or digest != _witness_digest(value)
    ):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}


__all__ = [
    "ADMISSION_EFFECT",
    "CLOSED_ADMISSION_FIELDS",
    "SCHEMA_VERSION",
    "SCOPE",
    "STATUS",
    "WITNESS_KEYS",
    "build_worldbridge_e547_queued_input_handoff_authority",
    "validate_worldbridge_e547_queued_input_handoff_authority",
]
