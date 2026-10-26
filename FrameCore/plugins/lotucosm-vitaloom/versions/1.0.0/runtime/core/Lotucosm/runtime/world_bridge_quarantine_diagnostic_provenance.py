# -*- coding: utf-8 -*-
"""Qt-free, copy-isolated provenance projection for WorldBridge quarantine.

E240 exposes only a small diagnostic read model over the records already
produced by E236 (failure receipt), E238 (containment decision), and E239
(opt-in writer admission).  It cannot change those records or any live SR/PS
state, and it deliberately does not turn a diagnostic into recovery authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_diagnostic_provenance"
SCOPE = "current_runtime_worldbridge_failure_quarantine"
FAILURE_RECEIPT_STATUS = "worldbridge_cross_lane_transaction_failure_isolation_authority"
RECOVERY_STATUS = "worldbridge_cross_lane_recovery_compensation_controlled_restart_authority"
ADMISSION_STATUS = "worldbridge_failure_quarantine_opt_in_handoff_readmission_authority"
VALID_FAILURE_PHASES = frozenset(
    {
        "preflight",
        "trace_sr_capture",
        "sr_to_ps_sync",
        "pond_update",
        "trace_ps_capture",
        "ps_to_sr_reflection",
    }
)
VALID_ENTRY_POINTS = frozenset({"scene_prebridge", "spawn_bridge", "tick_handoff"})
QUARANTINE_HOST_ACTION = "skip_quarantined_current_runtime_opt_in_bridge_writer"
CONTAINMENT_HOST_ACTION = "suspend_future_opt_in_handoffs_for_current_runtime"
DO_NOT_CLAIM = (
    "same_runtime_safe_retry",
    "automatic_quarantine_clear",
    "cross_lane_rollback",
    "inverse_mutation_compensation",
    "in_place_sr_ps_restore",
    "atomic_recovery",
    "full_unified_runtime_replay",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)


def _mapping_copy(value: object, name: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping or None")
    return copy.deepcopy(dict(value))


def _require_bool(mapping: Mapping[str, Any], key: str, label: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{label}.{key} must be bool")
    return value


def _validate_failure_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if receipt.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("failure_receipt schema_version mismatch")
    if receipt.get("status") != FAILURE_RECEIPT_STATUS:
        raise ValueError("failure_receipt status mismatch")
    phase = receipt.get("phase")
    if phase not in VALID_FAILURE_PHASES:
        raise ValueError("failure_receipt phase is not recognised")
    for key, expected in (
        ("failure_isolated", True),
        ("rollback_performed", False),
        ("cross_lane_transaction", False),
        ("atomic_checkpoint", False),
        ("replay_admitted", False),
        ("default_ready", False),
    ):
        if receipt.get(key) is not expected:
            raise ValueError(f"failure_receipt.{key} violates provenance boundary")
    return {
        "phase": phase,
        "partial_mutation_possible": _require_bool(
            receipt,
            "partial_mutation_possible",
            "failure_receipt",
        ),
        "failure_isolated": True,
    }


def _validate_recovery_decision(decision: Mapping[str, Any], *, phase: str) -> dict[str, Any]:
    if decision.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("recovery_decision schema_version mismatch")
    if decision.get("status") != RECOVERY_STATUS:
        raise ValueError("recovery_decision status mismatch")
    if decision.get("read_only") is not True:
        raise ValueError("recovery_decision must be read-only")
    if decision.get("failure_phase") != phase:
        raise ValueError("recovery_decision failure phase does not match receipt")
    if decision.get("host_action") != CONTAINMENT_HOST_ACTION:
        raise ValueError("recovery_decision host action mismatch")
    for key in (
        "preserve_failure_receipt",
        "sr_host_tick_may_continue",
    ):
        if decision.get(key) is not True:
            raise ValueError(f"recovery_decision.{key} must be true")
    for key in (
        "ps_live_state_repaired",
        "sr_live_state_repaired",
        "bridge_link_metadata_repaired",
        "compensation_performed",
        "rollback_performed",
    ):
        if decision.get(key) is not False:
            raise ValueError(f"recovery_decision.{key} must be false")
    restart = decision.get("controlled_fresh_restart")
    if not isinstance(restart, Mapping):
        raise ValueError("recovery_decision controlled_fresh_restart missing")
    if restart.get("requires_discarding_current_sr_and_ps_runtime_instances") is not True:
        raise ValueError("recovery_decision must require fresh instances")
    for key in ("restores_failed_runtime_state", "replays_failed_handoff"):
        if restart.get(key) is not False:
            raise ValueError(f"recovery_decision controlled_fresh_restart.{key} must be false")
    return {
        "host_action": CONTAINMENT_HOST_ACTION,
        "sr_host_tick_may_continue": True,
        "requires_discarding_current_sr_and_ps_runtime_instances": True,
        "restores_failed_runtime_state": False,
        "replays_failed_handoff": False,
    }


def _validate_admission_decision(
    decision: Mapping[str, Any],
    *,
    current_runtime_quarantined: bool,
) -> dict[str, Any]:
    if decision.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("quarantine_admission schema_version mismatch")
    if decision.get("status") != ADMISSION_STATUS:
        raise ValueError("quarantine_admission status mismatch")
    if decision.get("read_only") is not True:
        raise ValueError("quarantine_admission must be read-only")
    entry_point = decision.get("entry_point")
    if entry_point not in VALID_ENTRY_POINTS:
        raise ValueError("quarantine_admission entry_point is not recognised")
    for key in ("restores_failed_runtime_state", "replays_failed_handoff"):
        if decision.get(key) is not False:
            raise ValueError(f"quarantine_admission.{key} must be false")
    admitted = _require_bool(decision, "admitted", "quarantine_admission")
    if current_runtime_quarantined:
        required = {
            "admitted": False,
            "host_action": QUARANTINE_HOST_ACTION,
            "may_construct_or_reuse_pond": False,
            "may_call_sr_ps_bridge_mutator": False,
            "current_runtime_quarantined": True,
            "requires_fresh_runtime_lifecycle_before_re_admission": True,
        }
        for key, expected in required.items():
            if decision.get(key) is not expected:
                raise ValueError(f"quarantine_admission.{key} violates quarantine")
    return {
        "recorded": True,
        "entry_point": entry_point,
        "admitted": admitted,
        "host_action": str(decision.get("host_action")),
        "may_construct_or_reuse_pond": _require_bool(
            decision,
            "may_construct_or_reuse_pond",
            "quarantine_admission",
        ),
        "may_call_sr_ps_bridge_mutator": _require_bool(
            decision,
            "may_call_sr_ps_bridge_mutator",
            "quarantine_admission",
        ),
        "requires_fresh_runtime_lifecycle_before_re_admission": _require_bool(
            decision,
            "requires_fresh_runtime_lifecycle_before_re_admission",
            "quarantine_admission",
        ),
    }


def project_worldbridge_quarantine_diagnostic(
    *,
    handoff_suspended: bool,
    failure_receipt: Mapping[str, Any] | None,
    recovery_decision: Mapping[str, Any] | None,
    quarantine_admission: Mapping[str, Any] | None,
    restore_diagnostic: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a bounded operator read model from validated existing evidence.

    A suspended runtime must supply matching E236/E238 provenance.  The most
    recent E239 admission is optional because a labelled failure can occur
    before the next writer is denied; when present during quarantine it must
    itself be a denied writer decision.  No mutable source mapping is retained.
    """
    if not isinstance(handoff_suspended, bool):
        raise TypeError("handoff_suspended must be bool")
    receipt = _mapping_copy(failure_receipt, "failure_receipt")
    recovery = _mapping_copy(recovery_decision, "recovery_decision")
    admission = _mapping_copy(quarantine_admission, "quarantine_admission")
    restore = _validate_restore_diagnostic(restore_diagnostic)

    if handoff_suspended:
        if receipt is None or recovery is None:
            raise ValueError("suspended quarantine requires failure receipt and containment decision")
        failure = _validate_failure_receipt(receipt)
        containment = _validate_recovery_decision(recovery, phase=failure["phase"])
        admission_view = (
            _validate_admission_decision(admission, current_runtime_quarantined=True)
            if admission is not None
            else {
                "recorded": False,
                "entry_point": None,
                "admitted": None,
                "host_action": None,
                "may_construct_or_reuse_pond": None,
                "may_call_sr_ps_bridge_mutator": None,
                "requires_fresh_runtime_lifecycle_before_re_admission": True,
            }
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS,
            "scope": SCOPE,
            "read_only": True,
            "availability": "available",
            "current_runtime_quarantined": True,
            "failure": {"recorded": True, **failure},
            "containment": {"recorded": True, **containment},
            "last_opt_in_bridge_admission": admission_view,
            "restore_diagnostic": restore,
            "fresh_lifecycle_boundary": {
                "required_before_opt_in_re_admission": True,
                "requires_discarding_current_sr_and_ps_runtime_instances": True,
                "restores_failed_runtime_state": False,
                "replays_failed_handoff": False,
            },
            "negative_capabilities": {
                "may_clear_quarantine": False,
                "may_retry_same_runtime_handoff": False,
                "may_construct_or_reuse_pond": False,
                "may_call_sr_ps_bridge_mutator": False,
                "rollback_performed": False,
                "compensation_performed": False,
                "in_place_restore": False,
                "replay_admitted": False,
                "default_ready": False,
            },
            "do_not_claim": list(DO_NOT_CLAIM),
        }

    if (receipt is None) != (recovery is None):
        raise ValueError("unquarantined historical evidence requires both receipt and containment decision")
    if receipt is not None and recovery is not None:
        historical_failure = _validate_failure_receipt(receipt)
        historical_containment = _validate_recovery_decision(
            recovery,
            phase=historical_failure["phase"],
        )
        failure_view = {"recorded": True, **historical_failure}
        containment_view = {"recorded": True, **historical_containment}
        evidence_lifetime_relation = "historical_or_unverified_after_current_quarantine_cleared"
    else:
        failure_view = {
            "recorded": False,
            "phase": None,
            "partial_mutation_possible": None,
            "failure_isolated": None,
        }
        containment_view = {
            "recorded": False,
            "host_action": None,
            "sr_host_tick_may_continue": None,
            "requires_discarding_current_sr_and_ps_runtime_instances": False,
            "restores_failed_runtime_state": False,
            "replays_failed_handoff": False,
        }
        evidence_lifetime_relation = "no_retained_failure_evidence"
    admission_view = (
        _validate_admission_decision(admission, current_runtime_quarantined=False)
        if admission is not None
        else {
            "recorded": False,
            "entry_point": None,
            "admitted": None,
            "host_action": None,
            "may_construct_or_reuse_pond": None,
            "may_call_sr_ps_bridge_mutator": None,
            "requires_fresh_runtime_lifecycle_before_re_admission": False,
        }
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": SCOPE,
        "read_only": True,
        "availability": "available",
        "current_runtime_quarantined": False,
        "evidence_lifetime_relation": evidence_lifetime_relation,
        "failure": failure_view,
        "containment": containment_view,
        "last_opt_in_bridge_admission": admission_view,
        "restore_diagnostic": restore,
        "fresh_lifecycle_boundary": {
            "required_before_opt_in_re_admission": False,
            "requires_discarding_current_sr_and_ps_runtime_instances": False,
            "restores_failed_runtime_state": False,
            "replays_failed_handoff": False,
        },
        "negative_capabilities": {
            "may_clear_quarantine": False,
            "may_retry_same_runtime_handoff": False,
            "may_construct_or_reuse_pond": False,
            "may_call_sr_ps_bridge_mutator": False,
            "rollback_performed": False,
            "compensation_performed": False,
            "in_place_restore": False,
            "replay_admitted": False,
            "default_ready": False,
        },
        "do_not_claim": list(DO_NOT_CLAIM),
    }


def _validate_restore_diagnostic(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {"recorded": False, "code": None, "errors": []}
    if not isinstance(value, Mapping):
        raise TypeError("restore_diagnostic must be a mapping or None")
    code = value.get("code")
    errors = value.get("errors")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("restore_diagnostic.schema_version must be current")
    if not isinstance(code, str) or not code.strip():
        raise ValueError("restore_diagnostic.code must be a non-empty string")
    if not isinstance(errors, list) or any(not isinstance(item, str) or not item.strip() for item in errors):
        raise ValueError("restore_diagnostic.errors must be a list of strings")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "code": code,
        "errors": list(errors),
    }
    for field in ("checkpoint_id", "checkpoint_digest"):
        if field in value:
            payload[field] = value[field]
    expected_digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    if value.get("diagnostic_digest") != expected_digest:
        raise ValueError("restore_diagnostic.diagnostic_digest mismatch")
    result = {"recorded": True, **payload, "diagnostic_digest": expected_digest}
    for field in ("checkpoint_id", "checkpoint_digest"):
        if field in value:
            if not isinstance(value[field], (str, int)) or isinstance(value[field], bool):
                raise ValueError(f"restore_diagnostic.{field} is invalid")
            result[field] = value[field]
    return result

def build_worldbridge_quarantine_diagnostic_provenance_contract() -> dict[str, Any]:
    """Describe E240's narrow diagnostic-only authority."""
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "runtime_mode": "dual",
        "authority_scope": "validate_and_project_labelled_failure_containment_and_writer_admission_diagnostics_only",
        "inputs": {
            "labelled_failure_receipt": True,
            "read_only_containment_decision": True,
            "read_only_opt_in_writer_admission": True,
            "live_pond_or_sr_entity": False,
            "exception_stack_or_scheduler_handle": False,
        },
        "operator_visibility": {
            "current_runtime_quarantine_state": True,
            "failure_phase": True,
            "partial_mutation_warning": True,
            "containment_host_action": True,
            "last_opt_in_writer_admission": True,
            "fresh_lifecycle_required_before_re_admission": True,
        },
        "admissions": {
            "copy_isolated_diagnostic_projection": True,
            "query_only_host_visibility": True,
            "same_runtime_safe_retry": False,
            "automatic_quarantine_clear": False,
            "cross_lane_rollback": False,
            "inverse_mutation_compensation": False,
            "in_place_restore": False,
            "atomic_recovery": False,
            "replay_admitted": False,
            "lossless_mapping": False,
            "default_ready": False,
        },
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    contract["contract_valid"] = validate_worldbridge_quarantine_diagnostic_provenance_contract(contract)["valid"]
    return contract


def validate_worldbridge_quarantine_diagnostic_provenance_contract(contract: object) -> dict[str, Any]:
    """Reject recovery authority, mutable-runtime, and default-ready overclaims."""
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
    if contract.get("authority_scope") != "validate_and_project_labelled_failure_containment_and_writer_admission_diagnostics_only":
        errors.append("authority_scope_overclaim")
    inputs = contract.get("inputs")
    if not isinstance(inputs, Mapping):
        errors.append("inputs_missing")
    else:
        for key in ("labelled_failure_receipt", "read_only_containment_decision", "read_only_opt_in_writer_admission"):
            if inputs.get(key) is not True:
                errors.append(f"inputs_{key}_required")
        for key in ("live_pond_or_sr_entity", "exception_stack_or_scheduler_handle"):
            if inputs.get(key) is not False:
                errors.append(f"inputs_{key}_overclaim")
    visibility = contract.get("operator_visibility")
    if not isinstance(visibility, Mapping) or any(visibility.get(key) is not True for key in (
        "current_runtime_quarantine_state",
        "failure_phase",
        "partial_mutation_warning",
        "containment_host_action",
        "last_opt_in_writer_admission",
        "fresh_lifecycle_required_before_re_admission",
    )):
        errors.append("operator_visibility_incomplete")
    admissions = contract.get("admissions")
    if not isinstance(admissions, Mapping):
        errors.append("admissions_missing")
    else:
        for key in ("copy_isolated_diagnostic_projection", "query_only_host_visibility"):
            if admissions.get(key) is not True:
                errors.append(f"admissions_{key}_required")
        for key in (
            "same_runtime_safe_retry", "automatic_quarantine_clear", "cross_lane_rollback",
            "inverse_mutation_compensation", "in_place_restore", "atomic_recovery",
            "replay_admitted", "lossless_mapping", "default_ready",
        ):
            if admissions.get(key) is not False:
                errors.append(f"admissions_{key}_overclaim")
    if not isinstance(contract.get("do_not_claim"), list) or set(DO_NOT_CLAIM) - set(contract.get("do_not_claim", [])):
        errors.append("do_not_claim_incomplete")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "DO_NOT_CLAIM",
    "SCHEMA_VERSION",
    "STATUS",
    "build_worldbridge_quarantine_diagnostic_provenance_contract",
    "project_worldbridge_quarantine_diagnostic",
    "validate_worldbridge_quarantine_diagnostic_provenance_contract",
]
