"""Evidence contract for a failed live checkpoint restore with compensation."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

SCHEMA_VERSION = 1
STATUS = "worldbridge_e506_atomic_rollback_witness"


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["witness_digest"] = ""
    return hashlib.sha256(_canonical(payload)).hexdigest()


def build_worldbridge_e506_atomic_rollback_witness(
    *,
    checkpoint: Mapping[str, Any],
    failure_report: Mapping[str, Any],
    state_before_failure: Mapping[str, Any],
    state_after_failure: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(checkpoint, Mapping) or not isinstance(failure_report, Mapping):
        raise TypeError("E506 checkpoint and failure report must be mappings")
    if not isinstance(state_before_failure, Mapping) or not isinstance(state_after_failure, Mapping):
        raise TypeError("E506 state evidence must be mappings")
    report = copy.deepcopy(dict(failure_report))
    state_equal = dict(state_before_failure) == dict(state_after_failure)
    transport_equal = (
        state_before_failure.get("input_state", {}).get("shared_transport")
        == state_after_failure.get("input_state", {}).get("shared_transport")
    )
    attempted = report.get("applied_phases", [])
    compensated = report.get("compensated_phases", [])
    partial_phase_compensated = report.get("phase") in compensated
    rollback_complete = (
        report.get("rollback_performed") is True
        and report.get("compensation_complete") is True
        and state_equal
        and transport_equal
        and partial_phase_compensated
    )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "checkpoint_identity": {
            "checkpoint_id": checkpoint.get("checkpoint_id"),
            "sequence": checkpoint.get("sequence"),
            "digest": checkpoint.get("digest"),
        },
        "failure_report": report,
        "evidence": {
            "partial_phase_compensated": partial_phase_compensated,
            "state_restored": state_equal,
            "transport_continuity_preserved": transport_equal,
            "rollback_complete": rollback_complete,
        },
        "atomic_rollback_evidence": rollback_complete,
        "atomic_checkpoint": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
        "witness_digest": "",
    }
    witness["witness_digest"] = _digest(witness)
    return copy.deepcopy(witness)


def validate_worldbridge_e506_atomic_rollback_witness(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    identity = value.get("checkpoint_identity")
    if not isinstance(identity, Mapping) or not isinstance(identity.get("digest"), str):
        errors.append("checkpoint_identity_invalid")
    evidence = value.get("evidence")
    if not isinstance(evidence, Mapping):
        errors.append("evidence_missing")
    else:
        for field in (
            "partial_phase_compensated",
            "state_restored",
            "transport_continuity_preserved",
            "rollback_complete",
        ):
            if not isinstance(evidence.get(field), bool):
                errors.append(f"{field}_invalid")
        if value.get("atomic_rollback_evidence") is not (
            evidence.get("rollback_complete") is True
        ):
            errors.append("rollback_evidence_mismatch")
    for field in ("atomic_checkpoint", "replay_admitted", "default_ready", "lossless"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    if value.get("witness_digest") != _digest(value):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "build_worldbridge_e506_atomic_rollback_witness",
    "validate_worldbridge_e506_atomic_rollback_witness",
]
