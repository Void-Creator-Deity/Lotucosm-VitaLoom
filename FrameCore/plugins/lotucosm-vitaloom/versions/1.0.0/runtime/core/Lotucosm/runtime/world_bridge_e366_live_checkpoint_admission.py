# -*- coding: utf-8 -*-
"""E366 aggregation contract for live checkpoint admission evidence."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .world_bridge_live_checkpoint_admission import (
    validate_worldbridge_live_checkpoint_admission_witness,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e366_live_checkpoint_admission"
REQUIRED_EVIDENCE = (
    "fresh_restore_parity",
    "in_place_restore_parity",
    "identity_registration_parity",
    "atomic_failure_rollback",
)


def build_worldbridge_e366_live_checkpoint_admission_contract(
    witness: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Aggregate one validated witness without opening any runtime authority."""
    evidence = {field: False for field in REQUIRED_EVIDENCE}
    witness_valid = False
    if witness is not None:
        witness_validation = validate_worldbridge_live_checkpoint_admission_witness(witness)
        witness_valid = witness_validation["valid"] is True
        if witness_valid:
            raw = witness.get("evidence")
            if isinstance(raw, Mapping):
                evidence = {field: raw.get(field) is True for field in REQUIRED_EVIDENCE}
    all_evidence = all(evidence.values())
    contract = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "runtime_mode": "dual",
        "witness_present": witness is not None,
        "witness_valid": witness_valid,
        "evidence": evidence,
        "all_required_evidence": all_evidence,
        "opt_in_live_adapter_admitted": witness_valid and all_evidence,
        "live_adapter_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
        "source": "explicit_game_viewport_checkpoint_witness_only",
    }
    contract["contract_valid"] = validate_worldbridge_e366_live_checkpoint_admission_contract(contract)["valid"]
    return contract


def validate_worldbridge_e366_live_checkpoint_admission_contract(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["contract_must_be_mapping"]}
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS or value.get("runtime_mode") != "dual":
        errors.append("boundary_mismatch")
    evidence = value.get("evidence")
    if not isinstance(evidence, Mapping) or any(not isinstance(evidence.get(field), bool) for field in REQUIRED_EVIDENCE):
        errors.append("evidence_shape_invalid")
    else:
        expected = all(evidence.get(field) is True for field in REQUIRED_EVIDENCE)
        if value.get("all_required_evidence") is not expected:
            errors.append("evidence_summary_mismatch")
        if value.get("opt_in_live_adapter_admitted") is not (bool(value.get("witness_valid")) and expected):
            errors.append("admission_summary_mismatch")
    for field in ("live_adapter_admitted", "replay_admitted", "default_ready", "lossless"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "REQUIRED_EVIDENCE",
    "STATUS",
    "build_worldbridge_e366_live_checkpoint_admission_contract",
    "validate_worldbridge_e366_live_checkpoint_admission_contract",
]
