# -*- coding: utf-8 -*-
"""Sealed read-only witness for one tick's SR-before-PS RNG draw order.

The witness proves only that one completed tick's bound deterministic context
recorded SR draws, preserved lane-local stream isolation, then recorded PS
draws, with receipt and E502/E547 evidence agreeing. It admits no shared seed,
RNG checkpoint, replay, tick merge, or default runtime.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from .world_bridge_deterministic_randomness_context import (
    validate_worldbridge_deterministic_randomness_snapshot,
)
from .world_bridge_e502_rng_draw_order_witness import (
    PHASE_ORDER,
    validate_worldbridge_e502_rng_draw_order_witness,
)
from .world_bridge_e547_queued_input_handoff_authority import (
    validate_worldbridge_e547_queued_input_handoff_authority,
)
from .world_bridge_tick_authority import validate_worldbridge_tick_receipt

SCHEMA_VERSION = 1
STATUS = "worldbridge_e548_rng_draw_order_authority"
SCOPE = "single_tick_sr_before_ps_lane_local_rng_draws"
ADMISSION_EFFECT = "none"
CLOSED_ADMISSION_FIELDS = (
    "shared_random_seed_contract",
    "cross_lane_rng_draw_order_admitted",
    "process_global_entropy_admitted",
    "rng_checkpoint_admitted",
    "rng_replay_admitted",
    "replay_admitted",
    "tick_merge_admitted",
    "full_unified_replay_admitted",
    "lossless",
    "default_ready",
)
PROOF_FIELDS = (
    "phase_order_valid",
    "registration_order_stable",
    "receipt_phase_binding",
    "context_start_bound",
    "context_end_bound",
    "sr_draw_observed",
    "ps_draw_observed",
    "sr_before_ps",
    "lane_stream_isolation",
    "global_entropy_isolated",
    "snapshot_bound",
)
WITNESS_KEYS = (
    "schema_version",
    "status",
    "read_only",
    "scope",
    "completed_tick_receipt",
    "queued_input_handoff_witness",
    "rng_draw_order_witness",
    "rng_context_snapshot",
    "tick_sequence",
    "decision_digest",
    "rng_context_id",
    "rng_start_digest",
    "rng_end_digest",
    "phase_order",
    "registration_order",
    "phase_draw_counts",
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


def _stream_counts(observation: Mapping[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    streams = observation.get("streams")
    if isinstance(streams, list):
        for stream in streams:
            if isinstance(stream, Mapping):
                name = stream.get("stream_name")
                count = stream.get("draw_count")
                if isinstance(name, str) and isinstance(count, int) and not isinstance(count, bool):
                    result[name] = count
    return result


def _phase_matches_receipt(
    receipt: Mapping[str, Any],
    observations: list[Mapping[str, Any]],
) -> bool:
    phases = receipt.get("rng_phases")
    if not isinstance(phases, list) or len(phases) != len(PHASE_ORDER):
        return False
    for index, phase in enumerate(PHASE_ORDER):
        record = phases[index]
        observation = observations[index]
        if not isinstance(record, Mapping):
            return False
        if (
            record.get("phase") != phase
            or record.get("order") != index
            or record.get("draw_counts") != _stream_counts(observation)
        ):
            return False
    return True


def _evaluate(
    *,
    receipt: Mapping[str, Any],
    queued_input: Mapping[str, Any],
    draw_order: Mapping[str, Any],
    snapshot: Mapping[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    receipt_validation = validate_worldbridge_tick_receipt(receipt)
    if receipt_validation != {"valid": True, "errors": []}:
        errors.extend(f"receipt_{item}" for item in receipt_validation["errors"])

    queued_validation = validate_worldbridge_e547_queued_input_handoff_authority(
        queued_input
    )
    if queued_validation != {"valid": True, "errors": []}:
        errors.extend(f"queued_{item}" for item in queued_validation["errors"])
    if queued_input.get("completed_tick_receipt") != dict(receipt):
        errors.append("queued_witness_receipt_mismatch")

    draw_validation = validate_worldbridge_e502_rng_draw_order_witness(draw_order)
    if draw_validation != {"valid": True, "errors": []}:
        errors.extend(f"draw_{item}" for item in draw_validation["errors"])

    snapshot_validation = validate_worldbridge_deterministic_randomness_snapshot(
        snapshot
    )
    if snapshot_validation != {"valid": True, "errors": []}:
        errors.extend(f"snapshot_{item}" for item in snapshot_validation["errors"])

    observations = draw_order.get("observations")
    if not isinstance(observations, list) or len(observations) != len(PHASE_ORDER):
        observations = []
        errors.append("draw_observations_tick_scope_invalid")
    clean_observations = [
        item for item in observations if isinstance(item, Mapping)
    ]
    if len(clean_observations) != len(observations):
        errors.append("draw_observation_mapping_invalid")

    envelope = queued_input.get("shared_state_envelope")
    envelope_digest = envelope.get("envelope_digest") if isinstance(envelope, Mapping) else None
    if draw_order.get("envelope_digests") != [envelope_digest]:
        errors.append("draw_envelope_binding_mismatch")

    phase_names = [item.get("phase") for item in clean_observations]
    phase_orders = [item.get("order") for item in clean_observations]
    phase_order_valid = (
        phase_names == list(PHASE_ORDER)
        and phase_orders == list(range(len(PHASE_ORDER)))
    )
    if not phase_order_valid:
        errors.append("draw_phase_order_mismatch")

    registration = draw_order.get("registration_order")
    registration_order_stable = isinstance(registration, list) and all(
        item.get("registration") == registration for item in clean_observations
    )
    if not registration_order_stable:
        errors.append("draw_registration_order_unstable")
    if not isinstance(registration, list) or not {"sr.runtime", "ps.pond"}.issubset(
        set(registration)
    ):
        errors.append("draw_required_streams_missing")

    context_ids = [item.get("context_id") for item in clean_observations]
    rng_context_id = receipt.get("rng_context_id")
    if any(context_id != rng_context_id for context_id in context_ids):
        errors.append("draw_context_id_mismatch")
    if snapshot.get("context_id") != rng_context_id:
        errors.append("snapshot_context_id_mismatch")

    first_digest = clean_observations[0].get("snapshot_digest") if clean_observations else None
    last_digest = clean_observations[-1].get("snapshot_digest") if clean_observations else None
    context_start_bound = first_digest == receipt.get("rng_start_digest")
    context_end_bound = (
        last_digest == receipt.get("rng_end_digest")
        and snapshot.get("snapshot_digest") == receipt.get("rng_end_digest")
    )
    if not context_start_bound:
        errors.append("draw_start_snapshot_mismatch")
    if not context_end_bound:
        errors.append("draw_end_snapshot_mismatch")

    receipt_phase_binding = _phase_matches_receipt(receipt, clean_observations)
    if not receipt_phase_binding:
        errors.append("receipt_rng_phase_mismatch")

    counts = [_stream_counts(item) for item in clean_observations]
    zero_counts = {name: 0 for name in (registration if isinstance(registration, list) else [])}
    while len(counts) < len(PHASE_ORDER):
        counts.append(dict(zero_counts))
    sr_counts = [item.get("sr.runtime", 0) for item in counts]
    ps_counts = [item.get("ps.pond", 0) for item in counts]
    sr_draw_observed = sr_counts[1] > sr_counts[0]
    ps_draw_observed = ps_counts[3] > ps_counts[2]
    sr_before_ps = (
        phase_order_valid
        and sr_draw_observed
        and ps_draw_observed
        and sr_counts[1] <= sr_counts[2]
    )
    lane_stream_isolation = (
        sr_counts[1] == sr_counts[2] == sr_counts[3]
        and ps_counts[0] == ps_counts[1] == ps_counts[2]
    )
    global_entropy_isolated = all(
        snapshot.get(field) is False
        for field in (
            "global_python_random_touched",
            "global_numpy_random_touched",
            "restore_performed",
            "replay_input",
            "checkpoint_state",
            "replay_admitted",
            "default_ready",
        )
    )
    snapshot_bound = (
        snapshot.get("snapshot_digest") == receipt.get("rng_end_digest")
        and snapshot.get("context_id") == rng_context_id
    )
    for field, value in (
        ("sr_draw_observed", sr_draw_observed),
        ("ps_draw_observed", ps_draw_observed),
        ("sr_before_ps", sr_before_ps),
        ("lane_stream_isolation", lane_stream_isolation),
    ):
        if value is not True:
            errors.append(f"{field}_not_observed")

    decision = receipt.get("clock_decision")
    projection = {
        "tick_sequence": receipt.get("tick_sequence"),
        "decision_digest": (
            decision.get("decision_digest")
            if isinstance(decision, Mapping)
            else None
        ),
        "rng_context_id": rng_context_id,
        "rng_start_digest": receipt.get("rng_start_digest"),
        "rng_end_digest": receipt.get("rng_end_digest"),
        "phase_order": list(PHASE_ORDER),
        "registration_order": list(registration) if isinstance(registration, list) else None,
        "phase_draw_counts": counts if len(clean_observations) == len(PHASE_ORDER) else None,
        "phase_order_valid": phase_order_valid,
        "registration_order_stable": registration_order_stable,
        "receipt_phase_binding": receipt_phase_binding,
        "context_start_bound": context_start_bound,
        "context_end_bound": context_end_bound,
        "sr_draw_observed": sr_draw_observed,
        "ps_draw_observed": ps_draw_observed,
        "sr_before_ps": sr_before_ps,
        "lane_stream_isolation": lane_stream_isolation,
        "global_entropy_isolated": global_entropy_isolated,
        "snapshot_bound": snapshot_bound,
    }
    return list(dict.fromkeys(errors)), projection


def build_worldbridge_e548_rng_draw_order_authority(
    *,
    completed_tick_receipt: Mapping[str, Any],
    queued_input_handoff_witness: Mapping[str, Any],
    rng_draw_order_witness: Mapping[str, Any],
    rng_context_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a detached single-tick cross-lane RNG draw-order witness."""
    receipt = _mapping_copy(completed_tick_receipt, "completed_tick_receipt")
    queued = _mapping_copy(
        queued_input_handoff_witness,
        "queued_input_handoff_witness",
    )
    draw_order = _mapping_copy(rng_draw_order_witness, "rng_draw_order_witness")
    snapshot = _mapping_copy(rng_context_snapshot, "rng_context_snapshot")
    errors, projection = _evaluate(
        receipt=receipt,
        queued_input=queued,
        draw_order=draw_order,
        snapshot=snapshot,
    )
    if errors:
        raise ValueError(
            "E548 RNG draw-order witness rejected: " + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "completed_tick_receipt": receipt,
        "queued_input_handoff_witness": queued,
        "rng_draw_order_witness": draw_order,
        "rng_context_snapshot": snapshot,
        **projection,
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e548_rng_draw_order_authority(
    value: object,
) -> dict[str, Any]:
    """Revalidate an E548 witness without trusting embedded proof booleans."""
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
    queued = value.get("queued_input_handoff_witness")
    draw_order = value.get("rng_draw_order_witness")
    snapshot = value.get("rng_context_snapshot")
    if not all(
        isinstance(item, Mapping)
        for item in (receipt, queued, draw_order, snapshot)
    ):
        return {
            "valid": False,
            "errors": errors + ["witness_mapping_payload_invalid"],
        }

    revalidation, projection = _evaluate(
        receipt=receipt,
        queued_input=queued,
        draw_order=draw_order,
        snapshot=snapshot,
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
    "build_worldbridge_e548_rng_draw_order_authority",
    "validate_worldbridge_e548_rng_draw_order_authority",
]
