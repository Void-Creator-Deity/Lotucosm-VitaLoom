"""Scheduler-owned bounded input queue and same-tick PS handoff witness."""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from .world_bridge_e547_queued_input_handoff_authority import (
    validate_worldbridge_e547_queued_input_handoff_authority,
)
from .world_bridge_input_sequence import (
    DISPATCH_PHASE,
    ROUTING_POLICY,
    validate_worldbridge_scheduler_input_queue_snapshot,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e553_scheduler_input_queue_authority"
SCOPE = "single_process_scheduler_owned_bounded_input_queue_and_tick_handoff"
ADMISSION_EFFECT = "none"
PROOF_FIELDS = (
    "scheduler_owner_declared",
    "canonical_event_schema_bound",
    "capacity_and_policy_declared",
    "backpressure_rejected_newest",
    "backpressure_atomic",
    "rejected_event_not_sequenced",
    "dispatch_phase_bound",
    "dispatch_receipt_bound",
    "ps_handoff_same_batch",
    "dispatch_cursor_advanced",
    "queue_empty_after_dispatch",
    "drop_policy_explicit",
    "drop_receipt_bound",
    "drop_not_replayed",
    "monotonic_sequence",
)
CLOSED_ADMISSION_FIELDS = (
    "scheduler_owned",
    "shared_queued_input_ordering",
    "cross_lane_input_ordering_admitted",
    "backpressure_admitted",
    "dropped_event_policy_admitted",
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
    "queued_input_handoff_witness",
    "scheduler_before",
    "backpressure_attempt",
    "scheduler_after_dispatch",
    "dispatch_receipt",
    "drop_attempt",
    *PROOF_FIELDS,
    "grants_admission",
    "admission_effect",
    *CLOSED_ADMISSION_FIELDS,
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


def _witness_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["witness_digest"] = ""
    return _digest(payload)


def _snapshot_errors(value: object, field: str) -> list[str]:
    validation = validate_worldbridge_scheduler_input_queue_snapshot(value)
    if validation == {"valid": True, "errors": []}:
        return []
    return [f"{field}_{item}" for item in validation["errors"]]


def _evaluate(
    *,
    handoff: Mapping[str, Any],
    scheduler_before: Mapping[str, Any],
    backpressure_attempt: Mapping[str, Any],
    scheduler_after_dispatch: Mapping[str, Any],
    dispatch_receipt: Mapping[str, Any],
    drop_attempt: Mapping[str, Any],
) -> tuple[list[str], dict[str, bool]]:
    errors: list[str] = []
    handoff_validation = validate_worldbridge_e547_queued_input_handoff_authority(
        handoff
    )
    if handoff_validation != {"valid": True, "errors": []}:
        errors.extend(f"handoff_{item}" for item in handoff_validation["errors"])

    errors.extend(_snapshot_errors(scheduler_before, "scheduler_before"))
    errors.extend(
        _snapshot_errors(scheduler_after_dispatch, "scheduler_after_dispatch")
    )
    required_attempt = {"before", "rejected_receipt", "after"}
    if set(backpressure_attempt) != required_attempt:
        errors.append("backpressure_attempt_keys_invalid")
        attempt_before: Mapping[str, Any] = {}
        receipt: Mapping[str, Any] = {}
        attempt_after: Mapping[str, Any] = {}
    else:
        attempt_before = backpressure_attempt.get("before")
        receipt = backpressure_attempt.get("rejected_receipt")
        attempt_after = backpressure_attempt.get("after")
        if not all(
            isinstance(item, Mapping)
            for item in (attempt_before, receipt, attempt_after)
        ):
            errors.append("backpressure_attempt_payload_invalid")
            attempt_before = {}
            receipt = {}
            attempt_after = {}
    errors.extend(_snapshot_errors(attempt_before, "backpressure_before"))
    errors.extend(_snapshot_errors(attempt_after, "backpressure_after"))

    capacity_policy = (
        scheduler_before.get("overflow_policy") == "reject_newest"
        and scheduler_after_dispatch.get("overflow_policy") == "reject_newest"
        and isinstance(scheduler_before.get("max_pending"), int)
        and scheduler_before.get("max_pending", 0) >= 1
    )
    if not capacity_policy:
        errors.append("capacity_or_policy_mismatch")
    rejection_ok = (
        receipt.get("status") == "worldbridge_input_backpressure_receipt"
        and receipt.get("overflow_policy") == "reject_newest"
        and receipt.get("max_pending") == attempt_before.get("max_pending")
        and receipt.get("pending_count") == attempt_before.get("pending_count")
        and attempt_before.get("pending_count") == attempt_before.get("max_pending")
    )
    if not rejection_ok:
        errors.append("backpressure_receipt_mismatch")
    rejection_atomic = (
        isinstance(attempt_before, Mapping)
        and isinstance(attempt_after, Mapping)
        and attempt_before.get("pending_count")
        == attempt_after.get("pending_count")
        and attempt_before.get("next_sequence")
        == attempt_after.get("next_sequence")
        and attempt_before.get("accepted_count")
        == attempt_after.get("accepted_count")
        and attempt_after.get("rejected_count")
        == attempt_before.get("rejected_count", -1) + 1
        and attempt_after.get("backpressure_receipts", [])[-1] == receipt
    )
    if not rejection_atomic:
        errors.append("backpressure_mutated_queue")

    dispatch_count = scheduler_after_dispatch.get("dispatch_count")
    dispatch_receipts = scheduler_after_dispatch.get("dispatch_receipts")
    dispatch_bound = (
        isinstance(dispatch_count, int)
        and dispatch_count >= 1
        and isinstance(dispatch_receipts, list)
        and dispatch_receipts
        and dispatch_receipts[-1] == dict(dispatch_receipt)
    )
    if not dispatch_bound:
        errors.append("dispatch_receipt_not_committed")
    phase_bound = (
        dispatch_receipt.get("dispatch_phase") == DISPATCH_PHASE
        and dispatch_receipt.get("routing_policy") == ROUTING_POLICY
        and scheduler_after_dispatch.get("dispatch_phase") == DISPATCH_PHASE
        and scheduler_after_dispatch.get("routing_policy") == ROUTING_POLICY
    )
    if not phase_bound:
        errors.append("dispatch_phase_mismatch")

    handoff_events = handoff.get("canonical_input_events")
    handoff_event_ids = (
        [event.get("event_id") for event in handoff_events]
        if isinstance(handoff_events, list)
        else []
    )
    handoff_bound = (
        handoff.get("ps_received_batch_identical") is True
        and handoff.get("envelope_batch_bound") is True
        and dispatch_receipt.get("event_ids") == handoff_event_ids
        and dispatch_receipt.get("event_count") == len(handoff_event_ids)
    )
    if not handoff_bound:
        errors.append("queued_input_handoff_mismatch")
    cursor_advanced = (
        scheduler_after_dispatch.get("next_sequence")
        == attempt_after.get("next_sequence")
        and scheduler_after_dispatch.get("pause_reset_epoch")
        == attempt_after.get("pause_reset_epoch")
        and scheduler_after_dispatch.get("accepted_count")
        == attempt_after.get("accepted_count")
    )
    if not cursor_advanced:
        errors.append("dispatch_cursor_changed_unexpectedly")
    empty_after_dispatch = scheduler_after_dispatch.get("pending_count") == 0
    if not empty_after_dispatch:
        errors.append("queue_not_empty_after_dispatch")

    if set(drop_attempt) != {"before", "drop_receipt", "after"}:
        errors.append("drop_attempt_keys_invalid")
        drop_before: Mapping[str, Any] = {}
        drop_receipt: Mapping[str, Any] = {}
        drop_after: Mapping[str, Any] = {}
    else:
        drop_before = drop_attempt.get("before")
        drop_receipt = drop_attempt.get("drop_receipt")
        drop_after = drop_attempt.get("after")
        if not all(
            isinstance(item, Mapping)
            for item in (drop_before, drop_receipt, drop_after)
        ):
            errors.append("drop_attempt_payload_invalid")
            drop_before = {}
            drop_receipt = {}
            drop_after = {}
    errors.extend(_snapshot_errors(drop_before, "drop_before"))
    errors.extend(_snapshot_errors(drop_after, "drop_after"))
    drop_policy = (
        drop_receipt.get("status") == "worldbridge_input_drop_receipt"
        and drop_receipt.get("reason") == "lifecycle:pause"
        and drop_receipt.get("dropped_count")
        == drop_before.get("pending_count")
        and drop_after.get("pending_count") == 0
        and drop_after.get("dropped_count")
        == drop_before.get("dropped_count", -1)
        + drop_receipt.get("dropped_count", -1)
        and drop_after.get("drop_receipts", [])[-1] == drop_receipt
    )
    if not drop_policy:
        errors.append("drop_receipt_mismatch")
    drop_not_replayed = (
        drop_after.get("next_sequence") == drop_before.get("next_sequence")
        and not any(
            event_id in handoff_event_ids
            for event_id in drop_receipt.get("dropped_event_ids", [])
        )
    )
    if not drop_not_replayed:
        errors.append("dropped_event_reappeared")

    monotonic = all(
        isinstance(item.get("next_sequence"), int)
        and isinstance(item.get("dispatch_count"), int)
        and isinstance(item.get("rejected_count"), int)
        for item in (
            scheduler_before,
            attempt_after,
            scheduler_after_dispatch,
            drop_before,
            drop_after,
        )
    )
    if not monotonic:
        errors.append("scheduler_counters_invalid")

    projection = {
        "scheduler_owner_declared": (
            scheduler_after_dispatch.get("scheduler_owner_id")
            == "game_viewport.input_scheduler"
        ),
        "canonical_event_schema_bound": (
            scheduler_after_dispatch.get("canonical_event_schema")
            == "worldbridge_input_sequence"
        ),
        "capacity_and_policy_declared": capacity_policy,
        "backpressure_rejected_newest": rejection_ok,
        "backpressure_atomic": rejection_atomic,
        "rejected_event_not_sequenced": (
            attempt_before.get("next_sequence")
            == attempt_after.get("next_sequence")
        ),
        "dispatch_phase_bound": phase_bound,
        "dispatch_receipt_bound": dispatch_bound,
        "ps_handoff_same_batch": handoff_bound,
        "dispatch_cursor_advanced": cursor_advanced,
        "queue_empty_after_dispatch": empty_after_dispatch,
        "drop_policy_explicit": drop_policy,
        "drop_receipt_bound": drop_policy,
        "drop_not_replayed": drop_not_replayed,
        "monotonic_sequence": monotonic,
    }
    for field in PROOF_FIELDS:
        if projection.get(field) is not True:
            errors.append(f"{field}_not_proven")
    return list(dict.fromkeys(errors)), projection


def build_worldbridge_e553_scheduler_input_queue_authority(
    *,
    queued_input_handoff_witness: Mapping[str, Any],
    scheduler_before: Mapping[str, Any],
    backpressure_attempt: Mapping[str, Any],
    scheduler_after_dispatch: Mapping[str, Any],
    dispatch_receipt: Mapping[str, Any],
    drop_attempt: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one detached scheduler queue and same-tick handoff witness."""
    handoff = _mapping_copy(
        queued_input_handoff_witness, "queued_input_handoff_witness"
    )
    before = _mapping_copy(scheduler_before, "scheduler_before")
    backpressure = _mapping_copy(backpressure_attempt, "backpressure_attempt")
    after = _mapping_copy(scheduler_after_dispatch, "scheduler_after_dispatch")
    dispatch = _mapping_copy(dispatch_receipt, "dispatch_receipt")
    drop = _mapping_copy(drop_attempt, "drop_attempt")
    errors, projection = _evaluate(
        handoff=handoff,
        scheduler_before=before,
        backpressure_attempt=backpressure,
        scheduler_after_dispatch=after,
        dispatch_receipt=dispatch,
        drop_attempt=drop,
    )
    if errors:
        raise ValueError(
            "E553 scheduler input queue witness rejected: " + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "queued_input_handoff_witness": handoff,
        "scheduler_before": before,
        "backpressure_attempt": backpressure,
        "scheduler_after_dispatch": after,
        "dispatch_receipt": dispatch,
        "drop_attempt": drop,
        **projection,
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e553_scheduler_input_queue_authority(
    value: object,
) -> dict[str, Any]:
    """Revalidate E553 without trusting embedded proof booleans."""
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
    handoff = value.get("queued_input_handoff_witness")
    before = value.get("scheduler_before")
    backpressure = value.get("backpressure_attempt")
    after = value.get("scheduler_after_dispatch")
    dispatch = value.get("dispatch_receipt")
    drop = value.get("drop_attempt")
    if not all(
        isinstance(item, Mapping)
        for item in (handoff, before, backpressure, after, dispatch, drop)
    ):
        return {
            "valid": False,
            "errors": errors + ["witness_payload_invalid"],
        }
    revalidation, projection = _evaluate(
        handoff=handoff,
        scheduler_before=before,
        backpressure_attempt=backpressure,
        scheduler_after_dispatch=after,
        dispatch_receipt=dispatch,
        drop_attempt=drop,
    )
    errors.extend(revalidation)
    for field, expected in projection.items():
        if value.get(field) != expected:
            errors.append(f"{field}_mismatch")
        if field in PROOF_FIELDS and value.get(field) is not True:
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
    "PROOF_FIELDS",
    "SCHEMA_VERSION",
    "SCOPE",
    "STATUS",
    "WITNESS_KEYS",
    "build_worldbridge_e553_scheduler_input_queue_authority",
    "validate_worldbridge_e553_scheduler_input_queue_authority",
]
