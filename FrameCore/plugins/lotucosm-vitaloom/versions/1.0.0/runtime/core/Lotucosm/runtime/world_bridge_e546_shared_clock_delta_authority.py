# -*- coding: utf-8 -*-
"""Sealed read-only witness for one frame-clock delta consumed by SR then PS.

The witness does not own a scheduler, a clock, or either lane. It rebuilds all
authority claims from a detached completed-tick receipt and, when supplied,
from the immediately previous receipt. A valid witness proves only that one
clock decision's frame delta was consumed in the order 'sr' then optionally
'ps'. It never admits a shared clock, time conversion, tick merge, replay,
lossless transport, or default readiness.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from .world_bridge_clock_ordering_authority import (
    validate_worldbridge_frame_clock_decision,
)
from .world_bridge_tick_authority import validate_worldbridge_tick_receipt

SCHEMA_VERSION = 1
STATUS = "worldbridge_e546_shared_clock_delta_authority"
ADMISSION_EFFECT = "none"
SINGLE_TICK_SCOPE = "single_tick_no_previous_receipt"
CHAINED_SCOPE = "adjacent_receipt_chain"
CLOCK_FIELDS = ("clock_decision", "clock_decision_digest", "clock_consumers")
CONSUMER_ORDER = ("sr", "ps")
WITNESS_KEYS = (
    "schema_version",
    "status",
    "read_only",
    "completed_tick_receipt",
    "previous_completed_tick_receipt",
    "owner_token",
    "runtime_epoch",
    "decision_sequence",
    "decision_digest",
    "delta_time",
    "paused",
    "bridge_handoff_requested",
    "consumer_order",
    "sequence_continuity_checked",
    "sequence_strictly_increasing",
    "decision_digest_not_reused",
    "sequence_scope",
    "receipt_validated",
    "decision_validated",
    "owner_epoch_validated",
    "delta_validated",
    "consumer_order_validated",
    "handoff_validated",
    "grants_admission",
    "admission_effect",
    "shared_clock",
    "time_conversion_admitted",
    "tick_merge_admitted",
    "full_unified_replay_admitted",
    "lossless",
    "replay_admitted",
    "default_ready",
    "witness_digest",
)
CLOSED_ADMISSION_FIELDS = (
    "shared_clock",
    "time_conversion_admitted",
    "tick_merge_admitted",
    "full_unified_replay_admitted",
    "lossless",
    "replay_admitted",
    "default_ready",
)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$")


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


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
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None


def _clean_token(value: object, field: str) -> str:
    if not isinstance(value, str) or _TOKEN_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a clean identifier")
    return value


def _clock_projection(receipt: Mapping[str, Any]) -> dict[str, Any]:
    decision = receipt.get("clock_decision")
    digest = receipt.get("clock_decision_digest")
    consumers = receipt.get("clock_consumers")
    return {
        "decision_sequence": (
            decision.get("decision_sequence") if isinstance(decision, Mapping) else None
        ),
        "decision_digest": digest,
        "owner_token": (
            decision.get("owner_token") if isinstance(decision, Mapping) else None
        ),
        "runtime_epoch": (
            decision.get("runtime_epoch") if isinstance(decision, Mapping) else None
        ),
        "delta_time": receipt.get("delta_time"),
        "paused": receipt.get("paused"),
        "bridge_handoff_requested": (
            decision.get("bridge_handoff_requested")
            if isinstance(decision, Mapping)
            else None
        ),
    }


def _receipt_errors(receipt: Mapping[str, Any], field: str) -> list[str]:
    validation = validate_worldbridge_tick_receipt(receipt)
    errors = [f"{field}_{item}" for item in validation["errors"]]
    if any(name not in receipt for name in CLOCK_FIELDS):
        errors.append(f"{field}_clock_fields_required")
    return errors


def _consumer_order_errors(receipt: Mapping[str, Any], field: str) -> list[str]:
    errors: list[str] = []
    decision = receipt.get("clock_decision")
    consumers = receipt.get("clock_consumers")
    digest = receipt.get("clock_decision_digest")
    tick_sequence = receipt.get("tick_sequence")
    if not isinstance(decision, Mapping):
        return [f"{field}_decision_not_mapping"]
    if not isinstance(consumers, list):
        return [f"{field}_consumers_not_list"]
    expected = ["sr", "ps"] if decision.get("bridge_handoff_requested") is True else ["sr"]
    names: list[str] = []
    for row in consumers:
        if not isinstance(row, Mapping):
            errors.append(f"{field}_consumer_not_mapping")
            continue
        names.append(row.get("consumer"))
        if row.get("decision_digest") != digest:
            errors.append(f"{field}_consumer_decision_digest_mismatch")
        if row.get("tick_sequence") != tick_sequence:
            errors.append(f"{field}_consumer_tick_sequence_mismatch")
    if names != expected:
        errors.append(f"{field}_consumer_order_mismatch")
    if len(set(names)) != len(names):
        errors.append(f"{field}_consumer_duplicate")
    return errors


def _boundary_errors(
    receipt: Mapping[str, Any],
    *,
    owner_token: str,
    runtime_epoch: str,
    field: str,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    decision = receipt.get("clock_decision")
    if not isinstance(decision, Mapping):
        return [f"{field}_clock_decision_missing"], {}
    decision_validation = validate_worldbridge_frame_clock_decision(decision)
    if decision_validation != {"valid": True, "errors": []}:
        errors.extend(
            f"{field}_{item.removeprefix('decision_')}"
            for item in decision_validation["errors"]
        )
    if decision.get("owner_token") != owner_token:
        errors.append(f"{field}_owner_token_mismatch")
    if decision.get("runtime_epoch") != runtime_epoch:
        errors.append(f"{field}_runtime_epoch_mismatch")
    if receipt.get("clock_decision_digest") != decision.get("decision_digest"):
        errors.append(f"{field}_decision_digest_field_mismatch")
    if receipt.get("delta_time") != decision.get("sr_delta_seconds"):
        errors.append(f"{field}_delta_mismatch")
    if receipt.get("paused") != decision.get("paused"):
        errors.append(f"{field}_paused_mismatch")
    if decision.get("time_conversion_admitted") is not False:
        errors.append(f"{field}_time_conversion_overclaim")
    errors.extend(_consumer_order_errors(receipt, field))
    return errors, dict(decision)


def _sequence_errors(
    receipt: Mapping[str, Any],
    previous: Mapping[str, Any] | None,
) -> tuple[list[str], bool, bool]:
    errors: list[str] = []
    decision = receipt.get("clock_decision")
    if not isinstance(decision, Mapping):
        return ["current_clock_decision_missing"], False, False
    current_sequence = decision.get("decision_sequence")
    current_digest = decision.get("decision_digest")
    if previous is None:
        return errors, False, False
    previous_decision = previous.get("clock_decision")
    if not isinstance(previous_decision, Mapping):
        return ["previous_clock_decision_missing"], True, False
    previous_sequence = previous_decision.get("decision_sequence")
    previous_digest = previous_decision.get("decision_digest")
    if (
        isinstance(current_sequence, bool)
        or not isinstance(current_sequence, int)
        or isinstance(previous_sequence, bool)
        or not isinstance(previous_sequence, int)
    ):
        errors.append("decision_sequence_invalid")
    elif current_sequence <= previous_sequence:
        errors.append("decision_sequence_not_increasing")
    if not _is_digest(current_digest) or current_digest == previous_digest:
        errors.append("decision_digest_reused")
    current_tick = receipt.get("tick_sequence")
    previous_tick = previous.get("tick_sequence")
    if (
        isinstance(current_tick, bool)
        or not isinstance(current_tick, int)
        or isinstance(previous_tick, bool)
        or not isinstance(previous_tick, int)
        or current_tick <= previous_tick
    ):
        errors.append("receipt_tick_sequence_not_increasing")
    if decision.get("owner_token") != previous_decision.get("owner_token"):
        errors.append("decision_owner_token_continuity_mismatch")
    if decision.get("runtime_epoch") != previous_decision.get("runtime_epoch"):
        errors.append("decision_runtime_epoch_continuity_mismatch")
    return errors, True, True


def build_worldbridge_e546_shared_clock_delta_authority(
    *,
    completed_tick_receipt: Mapping[str, Any],
    owner_token: str,
    runtime_epoch: str,
    previous_completed_tick_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a detached witness for one SR-first clock-delta consumption."""
    clean_owner = _clean_token(owner_token, "owner_token")
    clean_epoch = _clean_token(runtime_epoch, "runtime_epoch")
    current = _mapping_copy(completed_tick_receipt, "completed_tick_receipt")
    previous = (
        None
        if previous_completed_tick_receipt is None
        else _mapping_copy(previous_completed_tick_receipt, "previous_completed_tick_receipt")
    )
    errors = _receipt_errors(current, "receipt")
    if previous is not None:
        errors.extend(_receipt_errors(previous, "previous_receipt"))
    boundary, decision = _boundary_errors(
        current,
        owner_token=clean_owner,
        runtime_epoch=clean_epoch,
        field="clock",
    )
    errors.extend(boundary)
    if previous is not None:
        previous_boundary, previous_decision = _boundary_errors(
            previous,
            owner_token=clean_owner,
            runtime_epoch=clean_epoch,
            field="previous_clock",
        )
        errors.extend(previous_boundary)
        if previous_decision.get("owner_token") != decision.get("owner_token"):
            errors.append("adjacent_owner_token_mismatch")
        if previous_decision.get("runtime_epoch") != decision.get("runtime_epoch"):
            errors.append("adjacent_runtime_epoch_mismatch")
    sequence_errors, continuity_checked, digest_not_reused = _sequence_errors(
        current, previous
    )
    errors.extend(sequence_errors)
    if errors:
        raise ValueError(
            "E546 shared clock delta witness rejected: "
            + ",".join(dict.fromkeys(errors))
        )

    consumers = current["clock_consumers"]
    consumer_order = [row["consumer"] for row in consumers]
    witness = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "completed_tick_receipt": current,
        "previous_completed_tick_receipt": previous,
        "owner_token": clean_owner,
        "runtime_epoch": clean_epoch,
        "decision_sequence": decision["decision_sequence"],
        "decision_digest": decision["decision_digest"],
        "delta_time": current["delta_time"],
        "paused": current["paused"],
        "bridge_handoff_requested": decision["bridge_handoff_requested"],
        "consumer_order": consumer_order,
        "sequence_continuity_checked": continuity_checked,
        "sequence_strictly_increasing": continuity_checked,
        "decision_digest_not_reused": digest_not_reused,
        "sequence_scope": CHAINED_SCOPE if previous is not None else SINGLE_TICK_SCOPE,
        "receipt_validated": True,
        "decision_validated": True,
        "owner_epoch_validated": True,
        "delta_validated": True,
        "consumer_order_validated": True,
        "handoff_validated": True,
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        "shared_clock": False,
        "time_conversion_admitted": False,
        "tick_merge_admitted": False,
        "full_unified_replay_admitted": False,
        "lossless": False,
        "replay_admitted": False,
        "default_ready": False,
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e546_shared_clock_delta_authority(
    value: object,
) -> dict[str, Any]:
    """Revalidate a detached E546 witness without trusting its booleans."""
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
    current = value.get("completed_tick_receipt")
    previous = value.get("previous_completed_tick_receipt")
    if not isinstance(current, Mapping):
        errors.append("receipt_not_mapping")
        current = None
    if previous is not None and not isinstance(previous, Mapping):
        errors.append("previous_receipt_not_mapping")
        previous = None
    try:
        clean_owner = _clean_token(value.get("owner_token"), "owner_token")
    except ValueError:
        errors.append("owner_token_invalid")
        clean_owner = ""
    try:
        clean_epoch = _clean_token(value.get("runtime_epoch"), "runtime_epoch")
    except ValueError:
        errors.append("runtime_epoch_invalid")
        clean_epoch = ""
    if current is not None:
        errors.extend(_receipt_errors(current, "receipt"))
        if previous is not None:
            errors.extend(_receipt_errors(previous, "previous_receipt"))
        boundary, decision = _boundary_errors(
            current,
            owner_token=clean_owner,
            runtime_epoch=clean_epoch,
            field="clock",
        )
        errors.extend(boundary)
        sequence_errors, continuity_checked, digest_not_reused = _sequence_errors(
            current, previous
        )
        errors.extend(sequence_errors)
        consumers = current.get("clock_consumers")
        consumer_order = (
            [row.get("consumer") for row in consumers if isinstance(row, Mapping)]
            if isinstance(consumers, list)
            else None
        )
        projection = _clock_projection(current)
        for field in (
            "decision_sequence",
            "decision_digest",
            "owner_token",
            "runtime_epoch",
            "delta_time",
            "paused",
            "bridge_handoff_requested",
        ):
            if value.get(field) != projection.get(field):
                errors.append(f"{field}_mismatch")
        if value.get("consumer_order") != consumer_order:
            errors.append("consumer_order_mismatch")
        if previous is not None:
            previous_boundary, _ = _boundary_errors(
                previous,
                owner_token=clean_owner,
                runtime_epoch=clean_epoch,
                field="previous_clock",
            )
            errors.extend(previous_boundary)
        expected_scope = CHAINED_SCOPE if previous is not None else SINGLE_TICK_SCOPE
        if value.get("sequence_scope") != expected_scope:
            errors.append("sequence_scope_mismatch")
        if value.get("sequence_continuity_checked") is not continuity_checked:
            errors.append("sequence_continuity_checked_mismatch")
        if value.get("sequence_strictly_increasing") is not continuity_checked:
            errors.append("sequence_strictly_increasing_mismatch")
        if value.get("decision_digest_not_reused") is not digest_not_reused:
            errors.append("decision_digest_not_reused_mismatch")
        if decision.get("owner_token") != clean_owner:
            errors.append("decision_owner_token_mismatch")
        if decision.get("runtime_epoch") != clean_epoch:
            errors.append("decision_runtime_epoch_mismatch")
    for field in (
        "receipt_validated",
        "decision_validated",
        "owner_epoch_validated",
        "delta_validated",
        "consumer_order_validated",
        "handoff_validated",
    ):
        if value.get(field) is not True:
            errors.append(f"{field}_not_true")
    if value.get("grants_admission") is not False:
        errors.append("grants_admission_overclaim")
    if value.get("admission_effect") != ADMISSION_EFFECT:
        errors.append("admission_effect_mismatch")
    for field in CLOSED_ADMISSION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    digest = value.get("witness_digest")
    if not _is_digest(digest) or digest != _witness_digest(value):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}


__all__ = [
    "ADMISSION_EFFECT",
    "CHAINED_SCOPE",
    "CLOSED_ADMISSION_FIELDS",
    "CLOCK_FIELDS",
    "CONSUMER_ORDER",
    "SCHEMA_VERSION",
    "SINGLE_TICK_SCOPE",
    "STATUS",
    "WITNESS_KEYS",
    "build_worldbridge_e546_shared_clock_delta_authority",
    "validate_worldbridge_e546_shared_clock_delta_authority",
]
