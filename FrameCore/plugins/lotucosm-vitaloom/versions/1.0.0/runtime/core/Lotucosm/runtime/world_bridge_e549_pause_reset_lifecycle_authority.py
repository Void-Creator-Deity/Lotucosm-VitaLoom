"""Sealed read-only witness for one real viewport pause/resume lifecycle."""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .world_bridge_input_sequence import (
    WorldBridgeInputSequence,
    validate_worldbridge_input_events,
)
from .world_bridge_shared_state_transport import (
    validate_worldbridge_shared_state_envelope,
)
from .world_bridge_tick_authority import validate_worldbridge_tick_receipt


SCHEMA_VERSION = 1
STATUS = "worldbridge_e549_pause_reset_lifecycle_authority"
SCOPE = "single_viewport_pause_resume_transport_regression_isolation"
ADMISSION_EFFECT = "none"
PROOF_FIELDS = (
    "lifecycle_actions_complete",
    "pause_epoch_advanced",
    "resume_epoch_advanced",
    "pending_cleared_on_pause",
    "pending_cleared_on_resume",
    "pre_pause_events_discarded",
    "paused_events_discarded",
    "pause_receipt_invalidated",
    "pause_transport_accepted",
    "resume_transport_accepted",
    "stale_epoch_rejected",
    "stale_rejection_atomic",
    "post_resume_receipt_epoch_bound",
    "post_resume_input_bound",
    "post_resume_envelope_bound",
    "receiver_cursor_bound",
)
CLOSED_ADMISSION_FIELDS = (
    "shared_pause_reset_authority",
    "cross_lane_error_isolation_admitted",
    "scheduler_owned",
    "shared_queue",
    "atomic_checkpoint",
    "cross_lane_atomicity",
    "input_replay_admitted",
    "replay_admitted",
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
    "pause_transition",
    "resume_transition",
    "stale_transport_attempt",
    "post_resume_tick",
    *PROOF_FIELDS,
    "grants_admission",
    "admission_effect",
    *CLOSED_ADMISSION_FIELDS,
    "witness_digest",
)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_RECEIVER_KEYS = {
    "last_sequence",
    "last_capture_epoch",
    "last_pause_reset_epoch",
    "last_input_sequence",
    "last_input_pause_reset_epoch",
    "rng_context_id",
    "rng_snapshot_digest",
    "accepted_count",
    "accepted_envelopes",
}


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


def _batch_digest(events: Sequence[Mapping[str, Any]]) -> str:
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


def _validate_snapshot(value: object, field: str) -> list[str]:
    if not isinstance(value, Mapping):
        return [f"{field}_not_mapping"]
    try:
        WorldBridgeInputSequence.validate_snapshot(value)
    except (TypeError, ValueError):
        return [f"{field}_invalid"]
    return []


def _validate_receiver(value: object, field: str) -> list[str]:
    if not isinstance(value, Mapping):
        return [f"{field}_not_mapping"]
    if set(value) != _RECEIVER_KEYS:
        return [f"{field}_keys_invalid"]
    errors: list[str] = []
    accepted = value.get("accepted_envelopes")
    count = value.get("accepted_count")
    if not isinstance(accepted, list):
        errors.append(f"{field}_accepted_not_list")
        accepted = []
    if isinstance(count, bool) or not isinstance(count, int) or count < len(accepted):
        errors.append(f"{field}_count_invalid")
    previous_sequence: int | None = None
    for index, envelope in enumerate(accepted):
        validation = validate_worldbridge_shared_state_envelope(envelope)
        if validation != {"valid": True, "errors": []}:
            errors.append(f"{field}_envelope_{index}_invalid")
            continue
        sequence = envelope["sequence"]
        if previous_sequence is not None and sequence != previous_sequence + 1:
            errors.append(f"{field}_window_sequence_invalid")
        previous_sequence = sequence
    last_sequence = value.get("last_sequence")
    if accepted and last_sequence != accepted[-1].get("sequence"):
        errors.append(f"{field}_last_sequence_mismatch")
    if not accepted and last_sequence is not None:
        errors.append(f"{field}_empty_sequence_mismatch")
    last_epoch = value.get("last_pause_reset_epoch")
    if accepted and last_epoch != accepted[-1].get("lifecycle", {}).get(
        "pause_reset_epoch"
    ):
        errors.append(f"{field}_last_epoch_mismatch")
    return errors


def _transition_projection(
    transition: Mapping[str, Any],
    *,
    expected_action: str,
    require_receipt_before: bool,
) -> tuple[list[str], dict[str, bool]]:
    errors: list[str] = []
    required = {
        "action",
        "before",
        "after",
        "receipt_before",
        "receipt_after",
        "envelope",
        "receiver_after",
        "discarded_event_ids",
    }
    if set(transition) != required:
        return [f"{expected_action}_transition_keys_invalid"], {}
    if transition.get("action") != expected_action:
        errors.append(f"{expected_action}_action_mismatch")

    before = transition.get("before")
    after = transition.get("after")
    errors.extend(_validate_snapshot(before, f"{expected_action}_before"))
    errors.extend(_validate_snapshot(after, f"{expected_action}_after"))
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        return list(dict.fromkeys(errors)), {}

    before_epoch = before.get("pause_reset_epoch")
    after_epoch = after.get("pause_reset_epoch")
    epoch_advanced = (
        isinstance(before_epoch, int)
        and not isinstance(before_epoch, bool)
        and isinstance(after_epoch, int)
        and not isinstance(after_epoch, bool)
        and after_epoch == before_epoch + 1
    )
    if not epoch_advanced:
        errors.append(f"{expected_action}_epoch_not_advanced")
    before_pending = before.get("pending")
    after_pending = after.get("pending")
    pending_cleared = isinstance(after_pending, list) and not after_pending
    if not pending_cleared:
        errors.append(f"{expected_action}_pending_not_cleared")

    before_seen = set(before.get("seen_event_ids") or [])
    after_seen = set(after.get("seen_event_ids") or [])
    if not before_seen.issubset(after_seen):
        errors.append(f"{expected_action}_seen_cursor_regressed")
    before_next = before.get("next_sequence")
    after_next = after.get("next_sequence")
    if (
        not isinstance(before_next, int)
        or isinstance(before_next, bool)
        or not isinstance(after_next, int)
        or isinstance(after_next, bool)
        or after_next < before_next
    ):
        errors.append(f"{expected_action}_next_sequence_regressed")

    discarded = transition.get("discarded_event_ids")
    if (
        not isinstance(discarded, list)
        or any(not isinstance(item, str) or not item for item in discarded)
        or len(set(discarded)) != len(discarded)
    ):
        errors.append(f"{expected_action}_discarded_ids_invalid")
        discarded = []
    before_pending_ids = {
        event.get("event_id")
        for event in (before_pending if isinstance(before_pending, list) else [])
        if isinstance(event, Mapping)
    }
    if any(item not in before_pending_ids for item in discarded):
        errors.append(f"{expected_action}_discarded_ids_not_pending")
    if any(item not in after_seen for item in discarded):
        errors.append(f"{expected_action}_discarded_ids_not_seen")

    receipt_before = transition.get("receipt_before")
    receipt_after = transition.get("receipt_after")
    if receipt_after is not None:
        errors.append(f"{expected_action}_receipt_not_invalidated")
    if require_receipt_before:
        validation = validate_worldbridge_tick_receipt(receipt_before)
        if validation != {"valid": True, "errors": []}:
            errors.append(f"{expected_action}_receipt_before_invalid")
        elif (
            receipt_before.get("pause_reset_epoch") != before_epoch
        ):
            errors.append(f"{expected_action}_receipt_epoch_mismatch")
    elif receipt_before is not None:
        errors.append(f"{expected_action}_receipt_before_overclaim")

    envelope = transition.get("envelope")
    validation = validate_worldbridge_shared_state_envelope(envelope)
    if validation != {"valid": True, "errors": []}:
        errors.append(f"{expected_action}_envelope_invalid")
        envelope = {}
    lifecycle = envelope.get("lifecycle") if isinstance(envelope, Mapping) else {}
    if not isinstance(lifecycle, Mapping) or lifecycle.get("action") != expected_action:
        errors.append(f"{expected_action}_envelope_action_mismatch")
    if not isinstance(lifecycle, Mapping) or lifecycle.get("pause_reset_epoch") != after_epoch:
        errors.append(f"{expected_action}_envelope_epoch_mismatch")
    expected_paused = expected_action == "pause"
    if (
        not isinstance(lifecycle, Mapping)
        or lifecycle.get("playing") is not True
        or lifecycle.get("paused") is not expected_paused
    ):
        errors.append(f"{expected_action}_envelope_lifecycle_mismatch")
    if not isinstance(envelope, Mapping) or envelope.get("input_events") != []:
        errors.append(f"{expected_action}_envelope_pending_not_empty")

    receiver = transition.get("receiver_after")
    errors.extend(_validate_receiver(receiver, f"{expected_action}_receiver"))
    if isinstance(receiver, Mapping):
        if receiver.get("last_sequence") != envelope.get("sequence"):
            errors.append(f"{expected_action}_receiver_sequence_mismatch")
        if receiver.get("last_pause_reset_epoch") != after_epoch:
            errors.append(f"{expected_action}_receiver_epoch_mismatch")

    return list(dict.fromkeys(errors)), {
        "epoch_advanced": epoch_advanced,
        "pending_cleared": pending_cleared,
        "transport_accepted": not any(
            error.startswith(f"{expected_action}_envelope_")
            or error.startswith(f"{expected_action}_receiver_")
            for error in errors
        ),
    }


def _evaluate(
    *,
    pause_transition: Mapping[str, Any],
    resume_transition: Mapping[str, Any],
    stale_attempt: Mapping[str, Any],
    post_tick: Mapping[str, Any],
) -> tuple[list[str], dict[str, bool]]:
    errors: list[str] = []
    pause_errors, pause = _transition_projection(
        pause_transition,
        expected_action="pause",
        require_receipt_before=True,
    )
    resume_errors, resume = _transition_projection(
        resume_transition,
        expected_action="resume",
        require_receipt_before=False,
    )
    errors.extend(pause_errors)
    errors.extend(resume_errors)

    pause_after = pause_transition.get("after")
    resume_before = resume_transition.get("before")
    if (
        not isinstance(pause_after, Mapping)
        or not isinstance(resume_before, Mapping)
        or pause_after.get("pause_reset_epoch") != resume_before.get("pause_reset_epoch")
    ):
        errors.append("pause_resume_epoch_discontinuity")
    pause_envelope = pause_transition.get("envelope")
    resume_envelope = resume_transition.get("envelope")
    if isinstance(pause_envelope, Mapping) and isinstance(resume_envelope, Mapping):
        if resume_envelope.get("sequence") != pause_envelope.get("sequence", -1) + 1:
            errors.append("pause_resume_transport_sequence_discontinuity")
        if resume_envelope.get("capture_epoch") != pause_envelope.get("capture_epoch", -1) + 1:
            errors.append("pause_resume_transport_capture_discontinuity")

    if set(stale_attempt) != {
        "envelope",
        "receiver_before",
        "receiver_after",
        "error",
    }:
        errors.append("stale_attempt_keys_invalid")
    stale_envelope = stale_attempt.get("envelope")
    stale_validation = validate_worldbridge_shared_state_envelope(stale_envelope)
    if stale_validation != {"valid": True, "errors": []}:
        errors.append("stale_envelope_invalid")
        stale_envelope = {}
    receiver_before = stale_attempt.get("receiver_before")
    receiver_after = stale_attempt.get("receiver_after")
    errors.extend(_validate_receiver(receiver_before, "stale_receiver_before"))
    errors.extend(_validate_receiver(receiver_after, "stale_receiver_after"))
    stale_rejected = isinstance(stale_attempt.get("error"), str) and (
        "pause_reset_epoch regression" in stale_attempt["error"]
    )
    if not stale_rejected:
        errors.append("stale_epoch_not_rejected")
    stale_atomic = (
        isinstance(receiver_before, Mapping)
        and isinstance(receiver_after, Mapping)
        and receiver_before == receiver_after
    )
    if not stale_atomic:
        errors.append("stale_rejection_mutated_receiver")
    if isinstance(receiver_before, Mapping) and isinstance(stale_envelope, Mapping):
        last_sequence = receiver_before.get("last_sequence")
        if not isinstance(last_sequence, int) or stale_envelope.get("sequence") != last_sequence + 1:
            errors.append("stale_sequence_not_next")
        last_epoch = receiver_before.get("last_pause_reset_epoch")
        stale_epoch = stale_envelope.get("lifecycle", {}).get("pause_reset_epoch")
        if not isinstance(last_epoch, int) or not isinstance(stale_epoch, int) or stale_epoch >= last_epoch:
            errors.append("stale_epoch_not_regression")

    if set(post_tick) != {
        "receipt",
        "input_events",
        "envelope",
        "receiver_after",
        "sequence_snapshot",
    }:
        errors.append("post_tick_keys_invalid")
    receipt = post_tick.get("receipt")
    receipt_validation = validate_worldbridge_tick_receipt(receipt)
    if receipt_validation != {"valid": True, "errors": []}:
        errors.append("post_tick_receipt_invalid")
        receipt = {}
    resume_after = resume_transition.get("after")
    post_epoch = receipt.get("pause_reset_epoch") if isinstance(receipt, Mapping) else None
    if not isinstance(resume_after, Mapping) or post_epoch != resume_after.get("pause_reset_epoch"):
        errors.append("post_tick_epoch_mismatch")
    pause_receipt = pause_transition.get("receipt_before")
    if isinstance(receipt, Mapping) and isinstance(pause_receipt, Mapping):
        if receipt.get("tick_sequence", 0) <= pause_receipt.get("tick_sequence", 0):
            errors.append("post_tick_sequence_not_advanced")

    events = post_tick.get("input_events")
    if not isinstance(events, list):
        errors.append("post_tick_input_not_list")
        events = []
    event_validation = validate_worldbridge_input_events(
        events,
        last_sequence=(events[0].get("sequence", 1) - 1 if events else 0),
        pause_reset_epoch=post_epoch if isinstance(post_epoch, int) else 0,
    )
    if events and event_validation != {"valid": True, "errors": []}:
        errors.append("post_tick_input_invalid")
    input_bound = (
        isinstance(receipt, Mapping)
        and receipt.get("input_event_count") == len(events)
        and receipt.get("input_digest") == _batch_digest(events)
    )
    if not input_bound:
        errors.append("post_tick_input_receipt_mismatch")

    sequence_snapshot = post_tick.get("sequence_snapshot")
    errors.extend(_validate_snapshot(sequence_snapshot, "post_tick_sequence"))
    if isinstance(sequence_snapshot, Mapping):
        if sequence_snapshot.get("pending"):
            errors.append("post_tick_pending_not_empty")
        if sequence_snapshot.get("pause_reset_epoch") != post_epoch:
            errors.append("post_tick_snapshot_epoch_mismatch")
        seen = set(sequence_snapshot.get("seen_event_ids") or [])
        if any(event.get("event_id") not in seen for event in events):
            errors.append("post_tick_input_not_seen")

    envelope = post_tick.get("envelope")
    envelope_validation = validate_worldbridge_shared_state_envelope(envelope)
    if envelope_validation != {"valid": True, "errors": []}:
        errors.append("post_tick_envelope_invalid")
        envelope = {}
    envelope_inputs = envelope.get("input_events") if isinstance(envelope, Mapping) else None
    envelope_bound = (
        isinstance(envelope_inputs, list)
        and len(envelope_inputs) == len(events)
        and envelope.get("lifecycle", {}).get("action") == "tick"
        and envelope.get("lifecycle", {}).get("pause_reset_epoch") == post_epoch
        and [
            item.get("event_id")
            for item in envelope_inputs
            if isinstance(item, Mapping)
        ]
        == [event.get("event_id") for event in events]
    )
    if not envelope_bound:
        errors.append("post_tick_envelope_input_mismatch")

    receiver_after = post_tick.get("receiver_after")
    errors.extend(_validate_receiver(receiver_after, "post_tick_receiver"))
    receiver_bound = (
        isinstance(receiver_after, Mapping)
        and isinstance(envelope, Mapping)
        and receiver_after.get("last_sequence") == envelope.get("sequence")
        and receiver_after.get("last_pause_reset_epoch") == post_epoch
        and receiver_after.get("last_input_sequence") == (events[-1].get("sequence") if events else None)
    )
    if not receiver_bound:
        errors.append("post_tick_receiver_not_bound")

    pre_ids: set[str] = set()
    paused_ids: set[str] = set()
    if set(pause_transition) == {
        "action",
        "before",
        "after",
        "receipt_before",
        "receipt_after",
        "envelope",
        "receiver_after",
        "discarded_event_ids",
    }:
        pre_ids = set(pause_transition.get("discarded_event_ids") or [])
    if set(resume_transition) == {
        "action",
        "before",
        "after",
        "receipt_before",
        "receipt_after",
        "envelope",
        "receiver_after",
        "discarded_event_ids",
    }:
        paused_ids = set(resume_transition.get("discarded_event_ids") or [])
    post_ids = {event.get("event_id") for event in events}
    pre_discarded = bool(pre_ids) and not bool(pre_ids & post_ids)
    paused_discarded = bool(paused_ids) and not bool(paused_ids & post_ids)
    if not pre_discarded:
        errors.append("pre_pause_events_not_discarded")
    if not paused_discarded:
        errors.append("paused_events_not_discarded")

    projection = {
        "lifecycle_actions_complete": (
            pause_transition.get("action") == "pause"
            and resume_transition.get("action") == "resume"
        ),
        "pause_epoch_advanced": pause.get("epoch_advanced") is True,
        "resume_epoch_advanced": resume.get("epoch_advanced") is True,
        "pending_cleared_on_pause": pause.get("pending_cleared") is True,
        "pending_cleared_on_resume": resume.get("pending_cleared") is True,
        "pre_pause_events_discarded": pre_discarded,
        "paused_events_discarded": paused_discarded,
        "pause_receipt_invalidated": pause_transition.get("receipt_after") is None,
        "pause_transport_accepted": pause.get("transport_accepted") is True,
        "resume_transport_accepted": resume.get("transport_accepted") is True,
        "stale_epoch_rejected": stale_rejected,
        "stale_rejection_atomic": stale_atomic,
        "post_resume_receipt_epoch_bound": (
            isinstance(receipt, Mapping)
            and receipt.get("pause_reset_epoch") == (
                resume_after.get("pause_reset_epoch")
                if isinstance(resume_after, Mapping)
                else None
            )
        ),
        "post_resume_input_bound": input_bound,
        "post_resume_envelope_bound": envelope_bound,
        "receiver_cursor_bound": receiver_bound,
    }
    return list(dict.fromkeys(errors)), projection


def build_worldbridge_e549_pause_reset_lifecycle_authority(
    *,
    pause_transition: Mapping[str, Any],
    resume_transition: Mapping[str, Any],
    stale_transport_attempt: Mapping[str, Any],
    post_resume_tick: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a detached pause/resume and stale-transport rejection witness."""
    pause = _mapping_copy(pause_transition, "pause_transition")
    resume = _mapping_copy(resume_transition, "resume_transition")
    stale = _mapping_copy(stale_transport_attempt, "stale_transport_attempt")
    post = _mapping_copy(post_resume_tick, "post_resume_tick")
    errors, projection = _evaluate(
        pause_transition=pause,
        resume_transition=resume,
        stale_attempt=stale,
        post_tick=post,
    )
    if errors:
        raise ValueError(
            "E549 pause/reset lifecycle witness rejected: " + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "pause_transition": pause,
        "resume_transition": resume,
        "stale_transport_attempt": stale,
        "post_resume_tick": post,
        **projection,
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e549_pause_reset_lifecycle_authority(
    value: object,
) -> dict[str, Any]:
    """Revalidate an E549 witness without trusting embedded proof booleans."""
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

    pause = value.get("pause_transition")
    resume = value.get("resume_transition")
    stale = value.get("stale_transport_attempt")
    post = value.get("post_resume_tick")
    if not all(isinstance(item, Mapping) for item in (pause, resume, stale, post)):
        return {
            "valid": False,
            "errors": errors + ["witness_mapping_payload_invalid"],
        }
    revalidation, projection = _evaluate(
        pause_transition=pause,
        resume_transition=resume,
        stale_attempt=stale,
        post_tick=post,
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
    "build_worldbridge_e549_pause_reset_lifecycle_authority",
    "validate_worldbridge_e549_pause_reset_lifecycle_authority",
]
