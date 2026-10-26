# -*- coding: utf-8 -*-
"""Qt-free evidence and failure receipts for one opt-in WorldBridge hand-off.

This module describes a failure-isolation boundary, not a distributed
transaction.  Existing SR and PS public objects do not expose a shared,
complete checkpoint/restore protocol, so a failed hand-off may have already
mutated either lane.  Callers may use the structured exception receipt to
contain a tick failure without asserting rollback, atomicity, or replay.
"""
from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_cross_lane_transaction_failure_isolation_authority"
PHASE_PREFLIGHT = "preflight"
PHASE_SR_TO_PS_SYNC = "sr_to_ps_sync"
PHASE_POND_UPDATE = "pond_update"
PHASE_PS_TO_SR_REFLECTION = "ps_to_sr_reflection"
PHASE_TRACE_SR_CAPTURE = "trace_sr_capture"
PHASE_TRACE_PS_CAPTURE = "trace_ps_capture"
VALID_FAILURE_PHASES = (
    PHASE_PREFLIGHT,
    PHASE_TRACE_SR_CAPTURE,
    PHASE_SR_TO_PS_SYNC,
    PHASE_POND_UPDATE,
    PHASE_TRACE_PS_CAPTURE,
    PHASE_PS_TO_SR_REFLECTION,
)
DO_NOT_CLAIM = (
    "cross_lane_transaction",
    "rollback_performed",
    "atomic_checkpoint",
    "lossless_worldbridge_mapping",
    "full_unified_runtime_replay",
    "unified_pond_default_ready",
)


def build_worldbridge_handoff_failure_receipt(
    phase: str,
    *,
    trace_requested: bool,
    preflight_completed: bool,
    sr_to_ps_sync_started: bool,
    pond_update_started: bool,
    ps_to_sr_reflection_started: bool,
    cause: BaseException,
) -> dict[str, Any]:
    """Build a truthful, copy-owned receipt for a failed bridge phase.

    ``*_started`` records only that live work began.  It must not be read as a
    rollback-safe checkpoint or as proof that a whole phase completed.  This
    makes partial mutation risk explicit where current public seams cannot
    restore SR and PS state together.
    """
    if phase not in VALID_FAILURE_PHASES:
        raise ValueError(f"unsupported WorldBridge handoff failure phase: {phase!r}")
    if not isinstance(trace_requested, bool):
        raise TypeError("trace_requested must be bool")
    flags = {
        "preflight_completed": preflight_completed,
        "sr_to_ps_sync_started": sr_to_ps_sync_started,
        "pond_update_started": pond_update_started,
        "ps_to_sr_reflection_started": ps_to_sr_reflection_started,
    }
    if any(not isinstance(value, bool) for value in flags.values()):
        raise TypeError("handoff progress flags must be bool")
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "phase": phase,
        "trace_requested": trace_requested,
        "failure_isolated": True,
        "preflight_completed": preflight_completed,
        "phase_started": {
            "sr_to_ps_sync": sr_to_ps_sync_started,
            "pond_update": pond_update_started,
            "ps_to_sr_reflection": ps_to_sr_reflection_started,
        },
        "later_phases_not_run": {
            "sr_to_ps_sync": not sr_to_ps_sync_started,
            "pond_update": not pond_update_started,
            "ps_to_sr_reflection": not ps_to_sr_reflection_started,
        },
        "partial_mutation_possible": bool(
            sr_to_ps_sync_started or pond_update_started or ps_to_sr_reflection_started
        ),
        "rollback_performed": False,
        "cross_lane_transaction": False,
        "atomic_checkpoint": False,
        "replay_admitted": False,
        "default_ready": False,
        "cause_type": type(cause).__name__,
        "cause_message": str(cause),
    }
    mapper_fields = (
        "direction",
        "failed_field",
        "phase",
        "mutation_started",
        "rollback_attempted",
        "rollback_complete",
        "rollback_errors",
    )
    if all(hasattr(cause, field) for field in mapper_fields):
        direction = getattr(cause, "direction")
        failed_field = getattr(cause, "failed_field")
        mapper_phase = getattr(cause, "phase")
        mutation_started = getattr(cause, "mutation_started")
        rollback_attempted = getattr(cause, "rollback_attempted")
        rollback_complete = getattr(cause, "rollback_complete")
        rollback_errors = getattr(cause, "rollback_errors")
        if (
            isinstance(direction, str)
            and isinstance(failed_field, str)
            and isinstance(mapper_phase, str)
            and isinstance(mutation_started, bool)
            and isinstance(rollback_attempted, bool)
            and isinstance(rollback_complete, bool)
            and isinstance(rollback_errors, tuple)
            and all(isinstance(item, str) for item in rollback_errors)
        ):
            receipt["field_batch_failure"] = {
                "direction": direction,
                "failed_field": failed_field,
                "phase": mapper_phase,
                "mutation_started": mutation_started,
                "rollback_attempted": rollback_attempted,
                "rollback_complete": rollback_complete,
                "rollback_errors": list(rollback_errors),
            }
    return receipt


class WorldBridgeHandoffFailure(RuntimeError):
    """A phase-labelled bridge error that deliberately reports no rollback."""

    def __init__(
        self,
        phase: str,
        cause: BaseException,
        *,
        trace_requested: bool,
        preflight_completed: bool,
        sr_to_ps_sync_started: bool,
        pond_update_started: bool,
        ps_to_sr_reflection_started: bool,
    ) -> None:
        self.phase = phase
        self.cause = cause
        self.receipt = build_worldbridge_handoff_failure_receipt(
            phase,
            trace_requested=trace_requested,
            preflight_completed=preflight_completed,
            sr_to_ps_sync_started=sr_to_ps_sync_started,
            pond_update_started=pond_update_started,
            ps_to_sr_reflection_started=ps_to_sr_reflection_started,
            cause=cause,
        )
        super().__init__(f"WorldBridge handoff failed in {phase}: {cause}")

    def attach_transaction_rollback(self, report: Mapping[str, Any]) -> None:
        """Attach digest-verified compensation evidence for an opt-in tick."""
        if not isinstance(report, Mapping):
            raise TypeError("transaction rollback report must be a mapping")
        copied = copy.deepcopy(dict(report))
        complete = copied.get("rollback_complete") is True
        self.receipt["transaction_rollback"] = copied
        self.receipt["rollback_performed"] = complete
        self.receipt["cross_lane_transaction"] = complete
        self.receipt["post_failure_state_restored"] = complete
        self.receipt["atomic_checkpoint"] = False
        self.receipt["replay_admitted"] = False
        self.receipt["default_ready"] = False


def build_worldbridge_transaction_failure_isolation_contract() -> dict[str, Any]:
    """Return the static, non-mutating E236 authority boundary."""
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "runtime_mode": "dual",
        "authority_scope": "one_opt_in_ordered_handoff_preflight_and_phase_labelled_failure_isolation_only",
        "handoff": {
            "preflight_before_live_sync": True,
            "plain_step_missing_update_policy": "preserve_legacy_noop_update_behavior",
            "trace_step_requires_callable_update_before_live_sync": True,
            "ordered_phases": [
                "preflight",
                "sr_to_ps_sync",
                "pond_update",
                "ps_to_sr_reflection",
            ],
            "trace_extra_observations": ["trace_sr_capture", "trace_ps_capture"],
            "post_failure_later_phases_are_skipped": True,
            "phase_labelled_failure_receipt": True,
        },
        "failure_semantics": {
            "failure_isolation": "exception_is_rethrown_with_phase_receipt_then_ui_adapter_may_contain_tick",
            "partial_mutation_possible_after_live_phase_starts": True,
            "rollback_performed": False,
            "cross_lane_transaction": False,
            "atomic_checkpoint": False,
            "checkpoint_restore_available": False,
        },
        "admissions": {
            "cross_lane_transaction": False,
            "rollback": False,
            "atomicity": False,
            "checkpoint_restore": False,
            "replay_admitted": False,
            "lossless_mapping": False,
            "default_ready": False,
        },
        "required_future_evidence": [
            "complete_sr_and_ps_checkpoint_restore_protocol",
            "rollback_order_and_failure_policy",
            "partial_update_compensation_for_pond_and_organism_systems",
            "serialized_cross_lane_rng_and_input_state",
            "replay_parity_evidence",
        ],
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    contract["contract_valid"] = validate_worldbridge_transaction_failure_isolation_contract(contract)["valid"]
    return contract


def validate_worldbridge_transaction_failure_isolation_contract(contract: object) -> dict[str, Any]:
    """Reject any transaction, rollback, replay, or readiness overclaim."""
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
    if contract.get("authority_scope") != "one_opt_in_ordered_handoff_preflight_and_phase_labelled_failure_isolation_only":
        errors.append("authority_scope_overclaim")
    handoff = contract.get("handoff")
    if not isinstance(handoff, Mapping):
        errors.append("handoff_missing")
    else:
        for field in ("preflight_before_live_sync", "trace_step_requires_callable_update_before_live_sync", "post_failure_later_phases_are_skipped", "phase_labelled_failure_receipt"):
            if handoff.get(field) is not True:
                errors.append(f"{field}_required")
        if handoff.get("plain_step_missing_update_policy") != "preserve_legacy_noop_update_behavior":
            errors.append("plain_step_compatibility_mismatch")
    semantics = contract.get("failure_semantics")
    if not isinstance(semantics, Mapping):
        errors.append("failure_semantics_missing")
    else:
        if semantics.get("partial_mutation_possible_after_live_phase_starts") is not True:
            errors.append("partial_mutation_risk_required")
        for field in ("rollback_performed", "cross_lane_transaction", "atomic_checkpoint", "checkpoint_restore_available"):
            if semantics.get(field) is not False:
                errors.append(f"{field}_overclaim")
    admissions = contract.get("admissions")
    if not isinstance(admissions, Mapping):
        errors.append("admissions_missing")
    else:
        for field in ("cross_lane_transaction", "rollback", "atomicity", "checkpoint_restore", "replay_admitted", "lossless_mapping", "default_ready"):
            if admissions.get(field) is not False:
                errors.append(f"{field}_overclaim")
    if not isinstance(contract.get("do_not_claim"), list) or set(DO_NOT_CLAIM) - set(contract.get("do_not_claim", [])):
        errors.append("do_not_claim_incomplete")
    return {"valid": not errors, "errors": errors}
