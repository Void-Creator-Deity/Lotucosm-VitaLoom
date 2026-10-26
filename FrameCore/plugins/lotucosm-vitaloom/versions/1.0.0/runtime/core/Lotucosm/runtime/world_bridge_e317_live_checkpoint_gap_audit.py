# -*- coding: utf-8 -*-
"""E317 read-only audit of the gap between synthetic and live checkpointing."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_e317_live_checkpoint_gap_audit"


def build_worldbridge_e317_live_checkpoint_gap_audit() -> dict[str, Any]:
    """Return source-backed admission prerequisites without adding authority."""
    audit: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "runtime_mode": "dual",
        "pond_time_persistence": {
            "available": True,
            "kind": "lane_local_portable_field",
            "legacy_payload_default": 0,
            "root_entity_registration": True,
        },
        "live_checkpoint_gaps": {
            "in_place_ps_pond_restore": True,
            "sr_runtime_entity_restore": "partial_slice_only",
            "bridge_identity_restore": True,
            "input_and_lifecycle_restore": True,
            "rng_state_and_draw_order_restore": True,
            "scheduler_plugin_native_state_restore": True,
            "same_instant_atomic_capture": True,
            "partial_failure_compensation": True,
        },
        "opt_in_live_adapter_admission": {
            "versioned_sr_ps_bundle": False,
            "fresh_and_in_place_restore_parity": False,
        "identity_and_registration_parity": False,
            "atomic_failure_rollback_evidence": False,
            "default_ready": False,
        },
        "decision": "audit_only_live_adapter_not_admitted",
    }
    audit["contract_valid"] = validate_worldbridge_e317_live_checkpoint_gap_audit(audit)["valid"]
    return audit


def validate_worldbridge_e317_live_checkpoint_gap_audit(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_must_be_mapping"]}
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if contract.get("status") != STATUS:
        errors.append("status_mismatch")
    if contract.get("read_only") is not True or contract.get("runtime_mode") != "dual":
        errors.append("authority_boundary_mismatch")
    persistence = contract.get("pond_time_persistence")
    if not isinstance(persistence, Mapping) or persistence.get("available") is not True:
        errors.append("pond_time_persistence_missing")
    gaps = contract.get("live_checkpoint_gaps")
    if not isinstance(gaps, Mapping) or not gaps:
        errors.append("live_gap_inventory_mismatch")
    elif any(value not in (True, "partial_slice_only") for value in gaps.values()):
        errors.append("live_gap_inventory_mismatch")
    admissions = contract.get("opt_in_live_adapter_admission")
    if not isinstance(admissions, Mapping):
        errors.append("admission_inventory_missing")
    else:
        for field in (
            "versioned_sr_ps_bundle",
            "fresh_and_in_place_restore_parity",
            "identity_and_registration_parity",
            "atomic_failure_rollback_evidence",
            "default_ready",
        ):
            if admissions.get(field) is not False:
                errors.append(f"{field}_overclaim")
    if contract.get("decision") != "audit_only_live_adapter_not_admitted":
        errors.append("decision_overclaim")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "build_worldbridge_e317_live_checkpoint_gap_audit",
    "validate_worldbridge_e317_live_checkpoint_gap_audit",
]
