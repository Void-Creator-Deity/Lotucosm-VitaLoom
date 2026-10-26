# -*- coding: utf-8 -*-
"""Evidence contract for opt-in live checkpoint adapter admission.

This module does not capture or mutate runtime objects.  It validates the
evidence produced by the concrete checkpoint coordinator: versioned SR/PS
bundle identity, fresh/in-place parity, bridge registration parity, and
failure rollback.  Even a complete opt-in witness never changes the default
dual-lane or replay boundary.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_live_checkpoint_admission"
REQUIRED_BUNDLE_FIELDS = (
    "runtime_version",
    "sr_schema_version",
    "ps_schema_version",
    "bridge_schema_version",
)
REQUIRED_EVIDENCE_FIELDS = (
    "fresh_restore_parity",
    "in_place_restore_parity",
    "identity_registration_parity",
    "atomic_failure_rollback",
)


def _bool_fields(value: Mapping[str, Any], fields: tuple[str, ...], prefix: str) -> list[str]:
    errors: list[str] = []
    for field in fields:
        if not isinstance(value.get(field), bool):
            errors.append(f"{prefix}_{field}_invalid")
    return errors


def build_worldbridge_live_checkpoint_admission_witness(
    *,
    checkpoint: Mapping[str, Any],
    versioned_bundle: Mapping[str, Any],
    fresh_restore: Mapping[str, Any],
    in_place_restore: Mapping[str, Any],
    identity_registration: Mapping[str, Any],
    rollback: Mapping[str, Any],
    restore_diagnostic: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic admission witness from explicit evidence only."""
    evidence = {
        "fresh_restore_parity": fresh_restore.get("parity") is True,
        "in_place_restore_parity": in_place_restore.get("parity") is True,
        "identity_registration_parity": identity_registration.get("parity") is True,
        "atomic_failure_rollback": rollback.get("atomic") is True
        and rollback.get("target_preserved") is True,
    }
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "runtime_mode": "dual",
        "checkpoint_identity": {
            "checkpoint_id": checkpoint.get("checkpoint_id"),
            "sequence": checkpoint.get("sequence"),
            "digest": checkpoint.get("digest"),
        },
        "versioned_bundle": dict(versioned_bundle),
        "evidence": evidence,
        "opt_in_live_adapter_admitted": all(evidence.values()),
        "live_adapter_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    if restore_diagnostic is not None:
        diagnostic = _copy_restore_diagnostic(
            restore_diagnostic,
            checkpoint_identity=witness["checkpoint_identity"],
        )
        diagnostic["diagnostic_digest"] = _diagnostic_digest(diagnostic)
        witness["restore_diagnostic"] = diagnostic
    witness["contract_valid"] = validate_worldbridge_live_checkpoint_admission_witness(witness)["valid"]
    return witness


def validate_worldbridge_live_checkpoint_admission_witness(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_must_be_mapping"]}
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("runtime_mode") != "dual":
        errors.append("runtime_mode_mismatch")
    identity = value.get("checkpoint_identity")
    if not isinstance(identity, Mapping) or not identity.get("checkpoint_id") or not isinstance(identity.get("digest"), str):
        errors.append("checkpoint_identity_missing")
    bundle = value.get("versioned_bundle")
    if not isinstance(bundle, Mapping):
        errors.append("versioned_bundle_missing")
    else:
        for field in REQUIRED_BUNDLE_FIELDS:
            if not bundle.get(field):
                errors.append(f"versioned_bundle_{field}_missing")
    evidence = value.get("evidence")
    if not isinstance(evidence, Mapping):
        errors.append("evidence_missing")
    else:
        errors.extend(_bool_fields(evidence, REQUIRED_EVIDENCE_FIELDS, "evidence"))
        expected_admitted = all(evidence.get(field) is True for field in REQUIRED_EVIDENCE_FIELDS)
        if value.get("opt_in_live_adapter_admitted") is not expected_admitted:
            errors.append("opt_in_admission_mismatch")
    for field in ("live_adapter_admitted", "replay_admitted", "default_ready", "lossless"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    if "restore_diagnostic" in value:
        try:
            diagnostic = _copy_restore_diagnostic(
                value["restore_diagnostic"],
                checkpoint_identity=identity if isinstance(identity, Mapping) else None,
            )
            if value["restore_diagnostic"].get("diagnostic_digest") != _diagnostic_digest(diagnostic):
                errors.append("restore_diagnostic_digest_mismatch")
        except (TypeError, ValueError):
            errors.append("restore_diagnostic_invalid")
    return {"valid": not errors, "errors": errors}


def _copy_restore_diagnostic(
    value: Mapping[str, Any], *, checkpoint_identity: Mapping[str, Any] | None
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("restore diagnostic must be a mapping")
    code = value.get("code")
    errors = value.get("errors")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("restore diagnostic schema version is invalid")
    if not isinstance(code, str) or not code.strip():
        raise ValueError("restore diagnostic code is invalid")
    if not isinstance(errors, list) or any(not isinstance(item, str) or not item.strip() for item in errors):
        raise ValueError("restore diagnostic errors are invalid")
    if checkpoint_identity is not None:
        if value.get("checkpoint_id") != checkpoint_identity.get("checkpoint_id"):
            raise ValueError("restore diagnostic checkpoint id mismatch")
        if value.get("checkpoint_digest") != checkpoint_identity.get("digest"):
            raise ValueError("restore diagnostic checkpoint digest mismatch")
    return {
        "schema_version": SCHEMA_VERSION,
        "code": code,
        "errors": list(errors),
        **({
            "checkpoint_id": checkpoint_identity.get("checkpoint_id"),
            "checkpoint_digest": checkpoint_identity.get("digest"),
        } if checkpoint_identity is not None else {
            "checkpoint_id": value.get("checkpoint_id"),
            "checkpoint_digest": value.get("checkpoint_digest"),
        }),
    }


def _diagnostic_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload.pop("diagnostic_digest", None)
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


__all__ = [
    "STATUS",
    "SCHEMA_VERSION",
    "build_worldbridge_live_checkpoint_admission_witness",
    "validate_worldbridge_live_checkpoint_admission_witness",
]
