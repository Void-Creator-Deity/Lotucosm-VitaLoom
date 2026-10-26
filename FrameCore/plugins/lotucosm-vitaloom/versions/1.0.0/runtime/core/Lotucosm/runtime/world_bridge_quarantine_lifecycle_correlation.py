# -*- coding: utf-8 -*-
"""Qt-free lifecycle evidence projection for retained WorldBridge quarantine facts.

E241 correlates only adapter-local opaque lifecycle tokens already captured by the
legacy host. It observes boundaries; it cannot create, repair, restart, reuse,
or replay a runtime.
"""
from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_lifecycle_correlation"
DIAGNOSTIC_STATUS = "worldbridge_quarantine_diagnostic_provenance"
SCOPE = "same_adapter_worldbridge_quarantine_lifecycle_evidence"
DISPOSAL_BOUNDARIES = frozenset({"scene_runtime_discard", "simulation_stop"})
DO_NOT_CLAIM = (
    "same_runtime_safe_retry",
    "automatic_quarantine_clear",
    "fresh_boundary_is_state_recovery",
    "cross_lane_rollback",
    "in_place_sr_ps_restore",
    "full_unified_runtime_replay",
    "cross_adapter_lifecycle_correlation",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)


def _copy_mapping(value: object, name: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping or None")
    return copy.deepcopy(dict(value))


def _opaque_string(mapping: Mapping[str, Any], key: str, name: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}.{key} must be a non-empty opaque string")
    return value


def _validate_tuple(value: Mapping[str, Any], name: str) -> dict[str, str]:
    return {
        "sr_runtime_epoch": _opaque_string(value, "sr_runtime_epoch", name),
        "pond_lifetime_token": _opaque_string(value, "pond_lifetime_token", name),
    }


def _validate_diagnostic(value: Mapping[str, Any]) -> dict[str, Any]:
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("diagnostic schema_version mismatch")
    if value.get("status") != DIAGNOSTIC_STATUS:
        raise ValueError("diagnostic status mismatch")
    if value.get("read_only") is not True or value.get("availability") != "available":
        raise ValueError("diagnostic must be available and read-only")
    quarantined = value.get("current_runtime_quarantined")
    if not isinstance(quarantined, bool):
        raise ValueError("diagnostic current_runtime_quarantined must be bool")
    negative = value.get("negative_capabilities")
    if not isinstance(negative, Mapping):
        raise ValueError("diagnostic negative_capabilities missing")
    for key in (
        "may_clear_quarantine", "may_retry_same_runtime_handoff",
        "may_construct_or_reuse_pond", "may_call_sr_ps_bridge_mutator",
        "rollback_performed", "compensation_performed", "in_place_restore",
        "replay_admitted", "default_ready",
    ):
        if negative.get(key) is not False:
            raise ValueError(f"diagnostic negative_capabilities.{key} must be false")
    return {
        "current_runtime_quarantined": quarantined,
        "evidence_lifetime_relation": value.get("evidence_lifetime_relation"),
    }


def _validate_disposal(value: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("disposal_observation schema_version mismatch")
    if value.get("authority") != STATUS:
        raise ValueError("disposal_observation authority mismatch")
    boundary = value.get("disposal_boundary")
    if boundary not in DISPOSAL_BOUNDARIES:
        raise ValueError("disposal_observation boundary is not recognised")
    if value.get("observed_while_quarantined") is not True:
        raise ValueError("disposal_observation must be observed while quarantined")
    return {"disposal_boundary": boundary, "tuple": _validate_tuple(value, "disposal_observation")}


def _same(left: Mapping[str, str], right: Mapping[str, str]) -> bool:
    return left["sr_runtime_epoch"] == right["sr_runtime_epoch"] and left["pond_lifetime_token"] == right["pond_lifetime_token"]


def _public_tuple(value: Mapping[str, str] | None) -> dict[str, Any]:
    if value is None:
        return {"available": False, "sr_runtime_epoch": None, "pond_lifetime_token": None}
    return {"available": True, **value}


def build_worldbridge_quarantine_lifecycle_evidence(*, sr_runtime_epoch: object, pond_lifetime_token: object) -> dict[str, Any] | None:
    """Capture opaque same-adapter evidence only when a full pair exists."""
    if sr_runtime_epoch is None or pond_lifetime_token is None:
        return None
    if not isinstance(sr_runtime_epoch, str) or not sr_runtime_epoch.strip():
        raise ValueError("sr_runtime_epoch must be a non-empty opaque string or None")
    if not isinstance(pond_lifetime_token, str) or not pond_lifetime_token.strip():
        raise ValueError("pond_lifetime_token must be a non-empty opaque string or None")
    return {
        "schema_version": SCHEMA_VERSION,
        "authority": STATUS,
        "sr_runtime_epoch": sr_runtime_epoch,
        "pond_lifetime_token": pond_lifetime_token,
    }


def build_worldbridge_quarantine_disposal_observation(*, failure_lifecycle: Mapping[str, Any] | None, active_lifecycle: Mapping[str, Any] | None, disposal_boundary: str, handoff_suspended: bool) -> dict[str, Any] | None:
    """Record only explicit disposal of the captured quarantined tuple."""
    if not isinstance(handoff_suspended, bool):
        raise TypeError("handoff_suspended must be bool")
    if disposal_boundary not in DISPOSAL_BOUNDARIES:
        raise ValueError("disposal_boundary is not recognised")
    failure = _copy_mapping(failure_lifecycle, "failure_lifecycle")
    active = _copy_mapping(active_lifecycle, "active_lifecycle")
    if not handoff_suspended or failure is None or active is None:
        return None
    failure_tuple = _validate_tuple(failure, "failure_lifecycle")
    active_tuple = _validate_tuple(active, "active_lifecycle")
    if not _same(failure_tuple, active_tuple):
        return None
    return {
        "schema_version": SCHEMA_VERSION,
        "authority": STATUS,
        "disposal_boundary": disposal_boundary,
        "observed_while_quarantined": True,
        **failure_tuple,
    }


def project_worldbridge_quarantine_lifecycle_correlation(*, diagnostic: Mapping[str, Any], failure_lifecycle: Mapping[str, Any] | None, disposal_observation: Mapping[str, Any] | None, current_lifecycle: Mapping[str, Any] | None) -> dict[str, Any]:
    """Project bounded lifecycle evidence without inferring recovery authority."""
    diagnostic_view = _validate_diagnostic(_copy_mapping(diagnostic, "diagnostic") or {})
    failure = _copy_mapping(failure_lifecycle, "failure_lifecycle")
    current = _copy_mapping(current_lifecycle, "current_lifecycle")
    failure_tuple = _validate_tuple(failure, "failure_lifecycle") if failure is not None else None
    current_tuple = _validate_tuple(current, "current_lifecycle") if current is not None else None
    disposal = _validate_disposal(_copy_mapping(disposal_observation, "disposal_observation"))
    quarantined = diagnostic_view["current_runtime_quarantined"]
    disposal_matches_failure = disposal is not None and failure_tuple is not None and _same(disposal["tuple"], failure_tuple)
    if quarantined:
        if failure_tuple is None or current_tuple is None:
            state = "current_quarantined_lifecycle_evidence_incomplete"
        elif not _same(failure_tuple, current_tuple):
            raise ValueError("quarantined current lifecycle differs from captured failure lifecycle")
        else:
            state = "current_quarantined_failure_tuple_observed"
        fresh_boundary_observed = False
    elif failure_tuple is None:
        state = "no_captured_failure_lifecycle_evidence"
        fresh_boundary_observed = False
    elif current_tuple is None:
        state = "historical_after_observed_disposal_no_current_sr_pond_pair" if disposal_matches_failure else "historical_or_unverified_after_current_quarantine_cleared"
        fresh_boundary_observed = False
    elif (
        disposal_matches_failure
        and current_tuple["sr_runtime_epoch"] != failure_tuple["sr_runtime_epoch"]
        and current_tuple["pond_lifetime_token"] != failure_tuple["pond_lifetime_token"]
    ):
        state = "fresh_instance_boundary_observed"
        fresh_boundary_observed = True
    else:
        state = "current_lifecycle_not_proven_fresh_from_failure"
        fresh_boundary_observed = False
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": SCOPE,
        "read_only": True,
        "availability": "available",
        "current_runtime_quarantined": quarantined,
        "diagnostic_evidence_lifetime_relation": diagnostic_view["evidence_lifetime_relation"],
        "correlation": {
            "state": state,
            "same_adapter_only": True,
            "failure_lifecycle": _public_tuple(failure_tuple),
            "observed_disposal": {
                "recorded": disposal is not None,
                "boundary": disposal["disposal_boundary"] if disposal is not None else None,
                "matches_captured_failure_lifecycle": disposal_matches_failure,
            },
            "current_lifecycle": _public_tuple(current_tuple),
            "fresh_instance_boundary_observed": fresh_boundary_observed,
        },
        "negative_capabilities": {
            "may_clear_quarantine": False,
            "may_retry_same_runtime_handoff": False,
            "may_construct_or_reuse_pond": False,
            "may_call_sr_ps_bridge_mutator": False,
            "fresh_boundary_is_state_recovery": False,
            "rollback_performed": False,
            "compensation_performed": False,
            "in_place_restore": False,
            "replay_admitted": False,
            "cross_adapter_lifecycle_correlation": False,
            "default_ready": False,
        },
        "do_not_claim": list(DO_NOT_CLAIM),
    }


def build_worldbridge_quarantine_lifecycle_correlation_contract() -> dict[str, Any]:
    """Describe E241's observation-only same-adapter lifecycle authority."""
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "runtime_mode": "dual",
        "authority_scope": "validate_and_project_same_adapter_opaque_sr_pond_lifecycle_observations_only",
        "inputs": {
            "e240_copy_isolated_diagnostic": True,
            "opaque_sr_snapshot_epoch": True,
            "opaque_adapter_local_pond_lifetime_token": True,
            "explicit_disposal_observation": True,
            "live_sr_or_pond_object": False,
            "global_or_cross_adapter_identity": False,
        },
        "admissions": {
            "current_quarantine_tuple_observation": True,
            "same_adapter_fresh_boundary_observation": True,
            "same_runtime_safe_retry": False,
            "automatic_quarantine_clear": False,
            "fresh_boundary_is_state_recovery": False,
            "cross_lane_rollback": False,
            "in_place_restore": False,
            "replay_admitted": False,
            "cross_adapter_lifecycle_correlation": False,
            "default_ready": False,
        },
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    contract["contract_valid"] = validate_worldbridge_quarantine_lifecycle_correlation_contract(contract)["valid"]
    return contract


def validate_worldbridge_quarantine_lifecycle_correlation_contract(contract: object) -> dict[str, Any]:
    """Reject identity, repair, replay, and default-ready overclaims."""
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_must_be_mapping"]}
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if contract.get("status") != STATUS:
        errors.append("status_mismatch")
    if contract.get("read_only") is not True:
        errors.append("read_only_required")
    if contract.get("runtime_mode") != "dual":
        errors.append("runtime_mode_mismatch")
    if contract.get("authority_scope") != "validate_and_project_same_adapter_opaque_sr_pond_lifecycle_observations_only":
        errors.append("authority_scope_overclaim")
    inputs = contract.get("inputs")
    if not isinstance(inputs, Mapping):
        errors.append("inputs_missing")
    else:
        for key in ("e240_copy_isolated_diagnostic", "opaque_sr_snapshot_epoch", "opaque_adapter_local_pond_lifetime_token", "explicit_disposal_observation"):
            if inputs.get(key) is not True:
                errors.append(f"inputs_{key}_required")
        for key in ("live_sr_or_pond_object", "global_or_cross_adapter_identity"):
            if inputs.get(key) is not False:
                errors.append(f"inputs_{key}_overclaim")
    admissions = contract.get("admissions")
    if not isinstance(admissions, Mapping):
        errors.append("admissions_missing")
    else:
        for key in ("current_quarantine_tuple_observation", "same_adapter_fresh_boundary_observation"):
            if admissions.get(key) is not True:
                errors.append(f"admissions_{key}_required")
        for key in ("same_runtime_safe_retry", "automatic_quarantine_clear", "fresh_boundary_is_state_recovery", "cross_lane_rollback", "in_place_restore", "replay_admitted", "cross_adapter_lifecycle_correlation", "default_ready"):
            if admissions.get(key) is not False:
                errors.append(f"admissions_{key}_overclaim")
    if not isinstance(contract.get("do_not_claim"), list) or set(DO_NOT_CLAIM) - set(contract.get("do_not_claim", [])):
        errors.append("do_not_claim_incomplete")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "DISPOSAL_BOUNDARIES", "DO_NOT_CLAIM", "SCHEMA_VERSION", "STATUS",
    "build_worldbridge_quarantine_disposal_observation",
    "build_worldbridge_quarantine_lifecycle_correlation_contract",
    "build_worldbridge_quarantine_lifecycle_evidence",
    "project_worldbridge_quarantine_lifecycle_correlation",
    "validate_worldbridge_quarantine_lifecycle_correlation_contract",
]
