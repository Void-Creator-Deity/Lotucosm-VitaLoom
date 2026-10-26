"""Runtime projection for an explicitly executed E367 GameViewport witness."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .world_bridge_e366_live_checkpoint_admission import (
    build_worldbridge_e366_live_checkpoint_admission_contract,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e367_live_viewport_witness"


def build_worldbridge_e367_live_viewport_witness_contract(
    witness: Mapping[str, Any] | None = None,
    cleanup: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project one explicit CLI witness without executing a UI host."""
    aggregate = build_worldbridge_e366_live_checkpoint_admission_contract(witness)
    cleanup_value = cleanup if isinstance(cleanup, Mapping) else {}
    cleanup_receipt = {
        "factory_restored": cleanup_value.get("factory_restored") is True,
        "viewport_deleted": cleanup_value.get("viewport_deleted") is True,
    }
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "source": "explicit_e367_game_viewport_cli_witness",
        "witness_present": witness is not None,
        "witness_valid": aggregate["witness_valid"],
        "evidence": dict(aggregate["evidence"]),
        "cleanup": cleanup_receipt,
        "cleanup_complete": all(cleanup_receipt.values()),
        "opt_in_live_adapter_admitted": (
            aggregate["opt_in_live_adapter_admitted"] and all(cleanup_receipt.values())
        ),
        "live_adapter_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    result["contract_valid"] = validate_worldbridge_e367_live_viewport_witness_contract(result)["valid"]
    return result


def validate_worldbridge_e367_live_viewport_witness_contract(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["contract_must_be_mapping"]}
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    evidence = value.get("evidence")
    if not isinstance(evidence, Mapping):
        errors.append("evidence_missing")
    elif any(not isinstance(evidence.get(field), bool) for field in (
        "fresh_restore_parity", "in_place_restore_parity",
        "identity_registration_parity", "atomic_failure_rollback",
    )):
        errors.append("evidence_shape_invalid")
    cleanup = value.get("cleanup")
    if not isinstance(cleanup, Mapping) or any(
        not isinstance(cleanup.get(field), bool)
        for field in ("factory_restored", "viewport_deleted")
    ):
        errors.append("cleanup_shape_invalid")
    else:
        expected_cleanup = all(cleanup[field] is True for field in (
            "factory_restored", "viewport_deleted"
        ))
        if value.get("cleanup_complete") is not expected_cleanup:
            errors.append("cleanup_summary_mismatch")
    expected_admitted = bool(value.get("witness_valid")) and all(
        evidence.get(field) is True
        for field in (
            "fresh_restore_parity", "in_place_restore_parity",
            "identity_registration_parity", "atomic_failure_rollback",
        )
    ) if isinstance(evidence, Mapping) else False
    expected_admitted = expected_admitted and value.get("cleanup_complete") is True
    if value.get("opt_in_live_adapter_admitted") is not expected_admitted:
        errors.append("admission_summary_mismatch")
    for field in ("live_adapter_admitted", "replay_admitted", "default_ready", "lossless"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "SCHEMA_VERSION",
    "STATUS",
    "build_worldbridge_e367_live_viewport_witness_contract",
    "validate_worldbridge_e367_live_viewport_witness_contract",
]
