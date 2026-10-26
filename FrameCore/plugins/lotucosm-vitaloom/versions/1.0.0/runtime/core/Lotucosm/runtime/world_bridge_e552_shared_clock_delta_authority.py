"""Sealed variable-delta shared clock witness for one real viewport."""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from typing import Any

from .world_bridge_clock_ordering_authority import (
    validate_worldbridge_frame_clock_decision,
)
from .world_bridge_owner_gate import validate_worldbridge_owner_gate_snapshot
from .world_bridge_shared_state_transport import (
    validate_worldbridge_shared_state_envelope,
)
from .world_bridge_tick_authority import validate_worldbridge_tick_receipt


SCHEMA_VERSION = 1
STATUS = "worldbridge_e552_shared_clock_delta_authority"
SCOPE = "single_process_variable_delta_sr_ps_clock_consumption"
CONVERSION_POLICY = "one_ps_update_per_sr_delta_v1"
ADMISSION_EFFECT = "none"
PROOF_FIELDS = (
    "decisions_valid",
    "receipts_valid",
    "envelopes_valid",
    "shared_delta_bound",
    "ps_tick_advanced_once",
    "ps_simulation_time_advanced_by_delta",
    "sr_ps_time_aligned",
    "cumulative_time_conserved",
    "consumers_sr_before_ps",
    "owner_gate_serialized",
    "variable_delta_exercised",
    "cross_call_ordering_proven",
    "time_conversion_proven",
)
CLOSED_ADMISSION_FIELDS = (
    "atomic_checkpoint",
    "scheduler_owned",
    "quantum_scheduler_admitted",
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
    "conversion_policy",
    "clock_samples",
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


def _finite_number(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
    )


def _sample_projection(
    value: object,
    *,
    expected_index: int,
    previous: tuple[int, int, float] | None,
) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return [f"sample_{expected_index}_not_mapping"], None
    required = {
        "simulation_speed",
        "decision",
        "receipt",
        "envelope",
        "pond_before",
        "pond_after",
        "gate_snapshot",
    }
    if set(value) != required:
        return [f"sample_{expected_index}_keys_invalid"], None
    decision = value.get("decision")
    receipt = value.get("receipt")
    envelope = value.get("envelope")
    decision_validation = validate_worldbridge_frame_clock_decision(decision)
    receipt_validation = validate_worldbridge_tick_receipt(receipt)
    envelope_validation = validate_worldbridge_shared_state_envelope(envelope)
    if decision_validation != {"valid": True, "errors": []}:
        errors.append(f"sample_{expected_index}_decision_invalid")
        decision = {}
    if receipt_validation != {"valid": True, "errors": []}:
        errors.append(f"sample_{expected_index}_receipt_invalid")
        receipt = {}
    if envelope_validation != {"valid": True, "errors": []}:
        errors.append(f"sample_{expected_index}_envelope_invalid")
        envelope = {}

    speed = value.get("simulation_speed")
    if not _finite_number(speed):
        errors.append(f"sample_{expected_index}_speed_invalid")
    delta = decision.get("sr_delta_seconds")
    receipt_delta = receipt.get("delta_time")
    sr_clock = (
        envelope.get("clock_provenance", {}).get("sr", {})
        if isinstance(envelope, Mapping)
        else {}
    )
    ps_clock = (
        envelope.get("clock_provenance", {}).get("ps", {})
        if isinstance(envelope, Mapping)
        else {}
    )
    shared_delta = (
        _finite_number(delta)
        and _finite_number(receipt_delta)
        and _finite_number(sr_clock.get("delta"))
        and _finite_number(ps_clock.get("delta"))
        and math.isclose(float(delta), float(receipt_delta), abs_tol=1e-12)
        and math.isclose(float(delta), float(sr_clock.get("delta")), abs_tol=1e-12)
        and math.isclose(float(delta), float(ps_clock.get("delta")), abs_tol=1e-12)
    )
    if not shared_delta:
        errors.append(f"sample_{expected_index}_shared_delta_mismatch")
        delta = 0.0
    if (
        decision.get("bridge_handoff_requested") is not True
        or receipt.get("delta_time") != delta
    ):
        errors.append(f"sample_{expected_index}_handoff_binding_mismatch")

    before = value.get("pond_before")
    after = value.get("pond_after")
    before_time = before.get("time") if isinstance(before, Mapping) else None
    after_time = after.get("time") if isinstance(after, Mapping) else None
    before_sim = (
        before.get("simulation_time") if isinstance(before, Mapping) else None
    )
    after_sim = (
        after.get("simulation_time") if isinstance(after, Mapping) else None
    )
    tick_once = (
        _finite_number(before_time)
        and _finite_number(after_time)
        and math.isclose(
            float(after_time) - float(before_time), 1.0, abs_tol=1e-12
        )
    )
    simulation_advanced = (
        _finite_number(before_sim)
        and _finite_number(after_sim)
        and math.isclose(
            float(after_sim) - float(before_sim),
            float(delta),
            abs_tol=1e-9,
        )
    )
    if not tick_once:
        errors.append(f"sample_{expected_index}_ps_tick_mismatch")
    if not simulation_advanced:
        errors.append(f"sample_{expected_index}_ps_simulation_time_mismatch")
    time_aligned = (
        simulation_advanced
        and _finite_number(sr_clock.get("time"))
        and _finite_number(ps_clock.get("time"))
        and math.isclose(
            float(sr_clock.get("time")),
            float(after_sim),
            abs_tol=1e-9,
        )
        and math.isclose(
            float(ps_clock.get("time")),
            float(after_sim),
            abs_tol=1e-9,
        )
    )
    if not time_aligned:
        errors.append(f"sample_{expected_index}_clock_time_misaligned")

    consumers = receipt.get("clock_consumers")
    consumer_names = (
        [item.get("consumer") for item in consumers if isinstance(item, Mapping)]
        if isinstance(consumers, list)
        else []
    )
    consumers_ordered = consumer_names == ["sr", "ps"]
    if not consumers_ordered:
        errors.append(f"sample_{expected_index}_consumer_order_mismatch")
    if receipt.get("clock_decision_digest") != decision.get("decision_digest"):
        errors.append(f"sample_{expected_index}_decision_digest_mismatch")

    gate = value.get("gate_snapshot")
    gate_validation = validate_worldbridge_owner_gate_snapshot(gate)
    gate_held = (
        gate_validation == {"valid": True, "errors": []}
        and gate.get("locked") is True
        and gate.get("depth", 0) >= 1
        and gate.get("current_operation") == "bridge_handoff"
        and gate.get("owner_thread_id") == gate.get("current_thread_id")
    )
    if not gate_held:
        errors.append(f"sample_{expected_index}_owner_gate_not_held")

    tick_sequence = receipt.get("tick_sequence")
    decision_sequence = decision.get("decision_sequence")
    ps_tick = ps_clock.get("tick")
    cursor = None
    if all(
        isinstance(item, int) and not isinstance(item, bool)
        for item in (tick_sequence, decision_sequence, ps_tick)
    ):
        cursor = (tick_sequence, decision_sequence, float(delta))
        if previous is not None:
            if tick_sequence != previous[0] + 1:
                errors.append(f"sample_{expected_index}_tick_sequence_not_contiguous")
            if decision_sequence != previous[1] + 1:
                errors.append(
                    f"sample_{expected_index}_decision_sequence_not_contiguous"
                )
    else:
        errors.append(f"sample_{expected_index}_sequence_invalid")

    return list(dict.fromkeys(errors)), {
        "delta": float(delta),
        "before_simulation_time": float(before_sim),
        "after_simulation_time": float(after_sim),
        "ps_tick": ps_tick,
        "shared_delta": shared_delta,
        "tick_once": tick_once,
        "simulation_advanced": simulation_advanced,
        "time_aligned": time_aligned,
        "consumers_ordered": consumers_ordered,
        "gate_held": gate_held,
        "cursor": cursor,
    }


def _evaluate(clock_samples: object) -> tuple[list[str], dict[str, bool]]:
    errors: list[str] = []
    if not isinstance(clock_samples, list):
        return ["clock_samples_not_list"], {}
    if len(clock_samples) < 2:
        errors.append("clock_samples_insufficient")
    projections: list[dict[str, Any]] = []
    previous: tuple[int, int, float] | None = None
    for index, value in enumerate(clock_samples):
        sample_errors, projection = _sample_projection(
            value,
            expected_index=index,
            previous=previous,
        )
        errors.extend(sample_errors)
        if projection is None:
            continue
        projections.append(projection)
        if projection.get("cursor") is not None:
            previous = projection["cursor"]

    deltas = [sample["delta"] for sample in projections]
    variable = len({round(delta, 12) for delta in deltas}) >= 2
    if not variable:
        errors.append("variable_delta_not_exercised")
    cumulative_conserved = False
    if projections:
        total_delta = sum(sample["delta"] for sample in projections)
        measured = (
            projections[-1]["after_simulation_time"]
            - projections[0]["before_simulation_time"]
        )
        cumulative_conserved = math.isclose(
            total_delta, measured, abs_tol=1e-8
        )
    if not cumulative_conserved:
        errors.append("cumulative_time_not_conserved")

    projection = {
        "decisions_valid": bool(projections),
        "receipts_valid": bool(projections),
        "envelopes_valid": bool(projections),
        "shared_delta_bound": bool(projections)
        and all(sample["shared_delta"] is True for sample in projections),
        "ps_tick_advanced_once": bool(projections)
        and all(sample["tick_once"] is True for sample in projections),
        "ps_simulation_time_advanced_by_delta": bool(projections)
        and all(
            sample["simulation_advanced"] is True for sample in projections
        ),
        "sr_ps_time_aligned": bool(projections)
        and all(sample["time_aligned"] is True for sample in projections),
        "cumulative_time_conserved": cumulative_conserved,
        "consumers_sr_before_ps": bool(projections)
        and all(
            sample["consumers_ordered"] is True for sample in projections
        ),
        "owner_gate_serialized": bool(projections)
        and all(sample["gate_held"] is True for sample in projections),
        "variable_delta_exercised": variable,
        "cross_call_ordering_proven": bool(projections)
        and all(sample["gate_held"] is True for sample in projections),
        "time_conversion_proven": (
            bool(projections)
            and all(sample["shared_delta"] is True for sample in projections)
            and all(
                sample["simulation_advanced"] is True
                for sample in projections
            )
            and all(sample["time_aligned"] is True for sample in projections)
            and cumulative_conserved
        ),
    }
    for field in PROOF_FIELDS:
        if projection.get(field) is not True:
            errors.append(f"{field}_not_proven")
    return list(dict.fromkeys(errors)), projection


def build_worldbridge_e552_shared_clock_delta_authority(
    *,
    clock_samples: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build one detached variable-delta shared-clock witness."""
    samples = _json_copy(clock_samples, "clock_samples")
    if not isinstance(samples, list) or any(
        not isinstance(item, dict) for item in samples
    ):
        raise TypeError("clock_samples must contain mappings")
    errors, projection = _evaluate(samples)
    if errors:
        raise ValueError(
            "E552 shared-clock witness rejected: " + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "conversion_policy": CONVERSION_POLICY,
        "clock_samples": samples,
        **projection,
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e552_shared_clock_delta_authority(
    value: object,
) -> dict[str, Any]:
    """Revalidate E552 without trusting embedded proof booleans."""
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
    if value.get("conversion_policy") != CONVERSION_POLICY:
        errors.append("conversion_policy_mismatch")
    revalidation, projection = _evaluate(value.get("clock_samples"))
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
    "CONVERSION_POLICY",
    "PROOF_FIELDS",
    "SCHEMA_VERSION",
    "SCOPE",
    "STATUS",
    "WITNESS_KEYS",
    "build_worldbridge_e552_shared_clock_delta_authority",
    "validate_worldbridge_e552_shared_clock_delta_authority",
]
