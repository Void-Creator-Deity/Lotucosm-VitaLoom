"""Atomic-capture and fresh-host evidence for one dual-lane checkpoint."""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from .world_bridge_e504_fresh_dual_lane_witness import (
    validate_worldbridge_e504_fresh_dual_lane_witness,
)
from .world_bridge_live_checkpoint import validate_worldbridge_live_checkpoint
from .world_bridge_owner_gate import validate_worldbridge_owner_gate_snapshot


SCHEMA_VERSION = 1
STATUS = "worldbridge_e551_scene_pond_checkpoint_authority"
SCOPE = "single_process_atomic_capture_with_fresh_host_dual_lane_parity"
ADMISSION_EFFECT = "none"
PROOF_FIELDS = (
    "versioned_checkpoint_valid",
    "sr_runtime_state_complete",
    "ps_pond_state_complete",
    "bridge_identity_restored",
    "fresh_host_dual_lane_parity",
    "capture_gate_held",
    "competing_access_blocked",
    "competing_access_not_entered",
    "capture_gate_released",
    "same_process_atomic_capture",
    "checkpoint_digest_bound",
)
CLOSED_ADMISSION_FIELDS = (
    "atomic_checkpoint",
    "cross_process_atomicity",
    "scheduler_owned",
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
    "checkpoint",
    "fresh_dual_lane_witness",
    "atomic_capture_evidence",
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


def _evaluate(
    *,
    checkpoint: Mapping[str, Any],
    fresh_dual_lane_witness: Mapping[str, Any],
    atomic_capture: Mapping[str, Any],
) -> tuple[list[str], dict[str, bool]]:
    errors: list[str] = []
    checkpoint_validation = validate_worldbridge_live_checkpoint(checkpoint)
    versioned_valid = checkpoint_validation == {"valid": True, "errors": []}
    if not versioned_valid:
        errors.append("checkpoint_invalid")
    if checkpoint.get("schema_version") != 1 or checkpoint.get("runtime_mode") != "dual":
        errors.append("checkpoint_version_or_mode_mismatch")
    digest_value = checkpoint.get("digest")
    digest_valid = (
        isinstance(digest_value, str)
        and _DIGEST_RE.fullmatch(digest_value) is not None
    )
    if not digest_valid:
        errors.append("checkpoint_digest_invalid")

    sr_state = checkpoint.get("sr_state")
    required_sr = {
        "runtime_restore_envelope",
        "structure_fingerprint",
        "script_entropy_audits",
        "script_entropy_receipts",
        "topology_receipt",
    }
    sr_complete = isinstance(sr_state, Mapping) and required_sr.issubset(sr_state)
    if not sr_complete:
        errors.append("sr_runtime_state_incomplete")
    ps_state = checkpoint.get("ps_state")
    required_ps = {
        "organisms",
        "resources",
        "time",
        "simulation_time",
        "worldbridge_organism_scripts",
        "worldbridge_organism_lifecycle",
        "worldbridge_organism_hierarchy",
    }
    ps_complete = isinstance(ps_state, Mapping) and required_ps.issubset(ps_state)
    if not ps_complete:
        errors.append("ps_pond_state_incomplete")
    for field in (
        "bridge_identity_links",
        "input_state",
        "randomness_state",
        "lifecycle",
        "topology_owner_state",
    ):
        if checkpoint.get(field) is None:
            errors.append(f"{field}_missing")

    lifecycle = checkpoint.get("lifecycle")
    gate_snapshot = (
        lifecycle.get("owner_gate_snapshot")
        if isinstance(lifecycle, Mapping)
        else None
    )
    gate_validation = validate_worldbridge_owner_gate_snapshot(gate_snapshot)
    capture_gate_held = (
        gate_validation == {"valid": True, "errors": []}
        and gate_snapshot.get("locked") is True
        and gate_snapshot.get("current_operation")
        in {"capture_live_checkpoint", "capture_live_checkpoint_transaction"}
        and gate_snapshot.get("depth", 0) >= 1
        and gate_snapshot.get("owner_thread_id")
        == gate_snapshot.get("current_thread_id")
    )
    if not capture_gate_held:
        errors.append("capture_gate_not_held")

    required_atomic = {
        "checkpoint_gate_snapshot",
        "live_gate_after",
        "competing_operation",
        "competing_blocked",
        "competing_entered_before_release",
        "blocked_attempts_before",
        "blocked_attempts_after",
        "holder_completed",
    }
    if set(atomic_capture) != required_atomic:
        errors.append("atomic_capture_evidence_keys_invalid")
        atomic_capture = {}
    gate_before = validate_worldbridge_owner_gate_snapshot(
        atomic_capture.get("checkpoint_gate_snapshot")
    )
    gate_after = validate_worldbridge_owner_gate_snapshot(
        atomic_capture.get("live_gate_after")
    )
    competing_blocked = (
        gate_before == {"valid": True, "errors": []}
        and atomic_capture.get("competing_operation")
        == "capture_live_checkpoint"
        and atomic_capture.get("competing_blocked") is True
        and atomic_capture.get("competing_entered_before_release") is False
        and isinstance(atomic_capture.get("blocked_attempts_before"), int)
        and not isinstance(atomic_capture.get("blocked_attempts_before"), bool)
        and isinstance(atomic_capture.get("blocked_attempts_after"), int)
        and not isinstance(atomic_capture.get("blocked_attempts_after"), bool)
        and atomic_capture["blocked_attempts_after"]
        > atomic_capture["blocked_attempts_before"]
    )
    if not competing_blocked:
        errors.append("competing_capture_not_blocked")
    gate_released = (
        gate_after == {"valid": True, "errors": []}
        and atomic_capture.get("live_gate_after", {}).get("locked") is False
        and atomic_capture.get("holder_completed") is True
    )
    if not gate_released:
        errors.append("capture_gate_not_released")

    fresh_validation = validate_worldbridge_e504_fresh_dual_lane_witness(
        fresh_dual_lane_witness
    )
    fresh_valid = fresh_validation == {"valid": True, "errors": []}
    if not fresh_valid:
        errors.append("fresh_dual_lane_witness_invalid")
    bridge_restored = fresh_dual_lane_witness.get("bridge_identity_equal") is True
    fresh_parity = fresh_dual_lane_witness.get("fresh_dual_lane_parity") is True
    if not bridge_restored:
        errors.append("bridge_identity_restore_mismatch")
    if not fresh_parity:
        errors.append("fresh_dual_lane_parity_missing")
    digest_bound = (
        digest_valid
        and fresh_dual_lane_witness.get("source_checkpoint_digest")
        == digest_value
    )
    if not digest_bound:
        errors.append("fresh_witness_checkpoint_digest_mismatch")

    same_process_atomic = (
        capture_gate_held
        and competing_blocked
        and gate_released
    )
    projection = {
        "versioned_checkpoint_valid": versioned_valid,
        "sr_runtime_state_complete": sr_complete,
        "ps_pond_state_complete": ps_complete,
        "bridge_identity_restored": bridge_restored,
        "fresh_host_dual_lane_parity": fresh_parity,
        "capture_gate_held": capture_gate_held,
        "competing_access_blocked": competing_blocked,
        "competing_access_not_entered": (
            atomic_capture.get("competing_entered_before_release") is False
        ),
        "capture_gate_released": gate_released,
        "same_process_atomic_capture": same_process_atomic,
        "checkpoint_digest_bound": digest_bound,
    }
    for field in PROOF_FIELDS:
        if projection.get(field) is not True:
            errors.append(f"{field}_not_proven")
    return list(dict.fromkeys(errors)), projection


def build_worldbridge_e551_scene_pond_checkpoint_authority(
    *,
    checkpoint: Mapping[str, Any],
    fresh_dual_lane_witness: Mapping[str, Any],
    atomic_capture_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a detached checkpoint capture/parity witness."""
    checkpoint_copy = _mapping_copy(checkpoint, "checkpoint")
    fresh = _mapping_copy(fresh_dual_lane_witness, "fresh_dual_lane_witness")
    atomic = _mapping_copy(atomic_capture_evidence, "atomic_capture_evidence")
    errors, projection = _evaluate(
        checkpoint=checkpoint_copy,
        fresh_dual_lane_witness=fresh,
        atomic_capture=atomic,
    )
    if errors:
        raise ValueError(
            "E551 checkpoint witness rejected: " + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "checkpoint": checkpoint_copy,
        "fresh_dual_lane_witness": fresh,
        "atomic_capture_evidence": atomic,
        **projection,
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e551_scene_pond_checkpoint_authority(
    value: object,
) -> dict[str, Any]:
    """Revalidate E551 without trusting embedded proof booleans."""
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
    checkpoint = value.get("checkpoint")
    fresh = value.get("fresh_dual_lane_witness")
    atomic = value.get("atomic_capture_evidence")
    if not all(isinstance(item, Mapping) for item in (checkpoint, fresh, atomic)):
        return {
            "valid": False,
            "errors": errors + ["witness_payload_invalid"],
        }
    revalidation, projection = _evaluate(
        checkpoint=checkpoint,
        fresh_dual_lane_witness=fresh,
        atomic_capture=atomic,
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
    "build_worldbridge_e551_scene_pond_checkpoint_authority",
    "validate_worldbridge_e551_scene_pond_checkpoint_authority",
]
