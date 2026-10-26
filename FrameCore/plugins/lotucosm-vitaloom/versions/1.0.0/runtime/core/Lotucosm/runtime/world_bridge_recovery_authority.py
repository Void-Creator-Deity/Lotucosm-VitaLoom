# -*- coding: utf-8 -*-
"""Qt-free WorldBridge post-failure containment and fresh-restart authority.

A phase-labelled handoff receipt proves only that a live handoff failed; E236
and E237 deliberately do not provide rollback or cross-lane restore.  This
module therefore classifies the safe host response: retain the receipt and
suspend subsequent *opt-in* handoffs for the current runtime lifetime.  A
host may later discard both runtime instances and build fresh ones through its
normal lifecycle, but that is a new run, not compensation or recovery of the
partially mutated run.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_cross_lane_recovery_compensation_controlled_restart_authority"
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
DO_NOT_CLAIM = (
    "cross_lane_rollback",
    "inverse_mutation_compensation",
    "in_place_sr_ps_restore",
    "atomic_recovery",
    "full_unified_runtime_replay",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)


def classify_worldbridge_handoff_failure_containment(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy-owned host-action recommendation for one labelled failure.

    The classifier performs no runtime mutation, I/O, restart, scheduler
    control, or UI interaction.  It deliberately accepts only the receipt
    vocabulary emitted by ``WorldBridgeHandoffFailure`` so callers cannot turn
    arbitrary exceptions into a recovery admission.
    """
    if not isinstance(receipt, Mapping):
        raise TypeError("receipt must be a mapping")
    phase = receipt.get("phase")
    if phase not in VALID_FAILURE_PHASES:
        raise ValueError("receipt phase is not a recognised WorldBridge handoff phase")
    if receipt.get("failure_isolated") is not True:
        raise ValueError("receipt must describe an isolated WorldBridge handoff failure")
    if receipt.get("rollback_performed") is not False:
        raise ValueError("receipt must not claim rollback")
    if receipt.get("cross_lane_transaction") is not False:
        raise ValueError("receipt must not claim a cross-lane transaction")
    if receipt.get("atomic_checkpoint") is not False:
        raise ValueError("receipt must not claim an atomic checkpoint")

    partial_mutation_possible = receipt.get("partial_mutation_possible")
    if not isinstance(partial_mutation_possible, bool):
        raise ValueError("receipt partial_mutation_possible must be bool")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "failure_phase": phase,
        "partial_mutation_possible": partial_mutation_possible,
        "host_action": "suspend_future_opt_in_handoffs_for_current_runtime",
        "preserve_failure_receipt": True,
        "sr_host_tick_may_continue": True,
        "ps_live_state_repaired": False,
        "sr_live_state_repaired": False,
        "bridge_link_metadata_repaired": False,
        "compensation_performed": False,
        "rollback_performed": False,
        "controlled_fresh_restart": {
            "available_only_through_host_stop_or_scene_reload": True,
            "requires_discarding_current_sr_and_ps_runtime_instances": True,
            "restores_failed_runtime_state": False,
            "replays_failed_handoff": False,
        },
        "admissions": {
            "receipt_classification": True,
            "future_opt_in_handoff_suspension": True,
            "controlled_fresh_restart": True,
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


def classify_worldbridge_verified_transaction_failure(
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Classify a failed opt-in handoff whose owner digest was restored.

    This is separate from the legacy failure-isolation classifier: legacy
    receipts must continue to reject rollback claims, while a transactional
    receipt is accepted only when its nested coordinator report proves a
    complete reverse restore and fresh target digest.
    """
    if not isinstance(receipt, Mapping):
        raise TypeError("receipt must be a mapping")
    if receipt.get("failure_isolated") is not True:
        raise ValueError("receipt must describe an isolated WorldBridge handoff failure")
    if receipt.get("rollback_performed") is not True:
        raise ValueError("transactional failure receipt must record completed compensation")
    if receipt.get("cross_lane_transaction") is not True:
        raise ValueError("transactional failure receipt must record a cross-lane transaction")
    report = receipt.get("transaction_rollback")
    if not isinstance(report, Mapping):
        raise ValueError("verified transaction rollback report is missing")
    if report.get("rollback_complete") is not True:
        raise ValueError("transaction rollback is not complete")
    if report.get("transactional_ps") is not True:
        raise ValueError("transactional PS owner evidence is missing")
    if receipt.get("atomic_checkpoint") is not False:
        raise ValueError("transactional failure cannot claim an atomic checkpoint")
    restore_report = report.get("restore_report")
    if not isinstance(restore_report, Mapping):
        raise ValueError("transaction rollback restore report is missing")
    if restore_report.get("restored") is not True:
        raise ValueError("transaction rollback restore report is not restored")
    if restore_report.get("transaction_verified") is not True:
        raise ValueError("transaction rollback fresh digest verification is missing")
    target_digest = restore_report.get("target_state_digest")
    rollback_digest = restore_report.get("rollback_state_digest")
    if (
        not isinstance(target_digest, str)
        or not target_digest
        or target_digest != rollback_digest
    ):
        raise ValueError("transaction rollback state digest evidence is inconsistent")
    target_live_digest = restore_report.get("target_live_ps_state_digest")
    rollback_live_digest = restore_report.get("rollback_live_ps_state_digest")
    captured_live_digest = report.get("captured_live_ps_state_digest")
    if (
        not isinstance(target_live_digest, str)
        or not target_live_digest
        or target_live_digest != rollback_live_digest
        or target_live_digest != captured_live_digest
    ):
        raise ValueError("transaction rollback live PS digest evidence is inconsistent")
    if report.get("checkpoint_digest") != restore_report.get("checkpoint_digest"):
        raise ValueError("transaction rollback checkpoint identity is inconsistent")
    if report.get("checkpoint_id") != restore_report.get("checkpoint_id"):
        raise ValueError("transaction rollback checkpoint id is inconsistent")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_verified_transaction_failure_containment",
        "read_only": True,
        "failure_phase": receipt.get("phase"),
        "partial_mutation_possible": receipt.get("partial_mutation_possible") is True,
        "host_action": "retain_verified_rollback_receipt_and_keep_replay_quarantined",
        "preserve_failure_receipt": True,
        "sr_host_tick_may_continue": True,
        "ps_live_state_repaired": True,
        "sr_live_state_repaired": True,
        "bridge_link_metadata_repaired": True,
        "compensation_performed": True,
        "rollback_performed": True,
        "controlled_fresh_restart": {
            "available_only_through_host_stop_or_scene_reload": True,
            "required": False,
            "restores_prior_state": True,
            "replays_failed_handoff": False,
        },
        "admissions": {
            "receipt_classification": True,
            "future_opt_in_handoff_suspension": False,
            "controlled_fresh_restart": True,
            "cross_lane_rollback": True,
            "inverse_mutation_compensation": True,
            "in_place_restore": True,
            "atomic_recovery": False,
            "replay_admitted": False,
            "lossless_mapping": False,
            "default_ready": False,
        },
        "rollback_report": dict(report),
        "do_not_claim": [
            "atomic_recovery",
            "full_unified_runtime_replay",
            "lossless_worldbridge_mapping",
            "unified_pond_default_ready",
        ],
    }


def classify_worldbridge_handoff_failure(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Route one labelled handoff failure to the strongest applicable containment.

    Host adapters must not inspect nested compensation evidence themselves.
    This Qt-free entry point selects the verified transaction classifier only
    when the receipt carries completed compensation evidence, and otherwise
    falls back to the legacy fail-closed containment classifier.  Both returned
    decisions are copy-owned and read-only; the ``handoff_suspended`` flag tells
    the caller whether the current runtime must stay quarantined.
    """
    if not isinstance(receipt, Mapping):
        raise TypeError("receipt must be a mapping")
    report = receipt.get("transaction_rollback")
    if isinstance(report, Mapping) and report.get("rollback_complete") is True:
        decision = classify_worldbridge_verified_transaction_failure(receipt)
        handoff_suspended = False
    else:
        decision = classify_worldbridge_handoff_failure_containment(receipt)
        handoff_suspended = True
    return {
        "schema_version": SCHEMA_VERSION,
        "handoff_suspended": handoff_suspended,
        "decision": decision,
    }


def build_worldbridge_recovery_compensation_controlled_restart_contract() -> dict[str, Any]:
    """Describe the strongest current post-failure authority without recovering state."""
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "runtime_mode": "dual",
        "authority_scope": "classify_labelled_failure_suspend_current_opt_in_handoffs_and_describe_host_fresh_restart_only",
        "failure_response": {
            "requires_phase_labelled_failure_receipt": True,
            "retain_copy_owned_receipt": True,
            "suspend_future_opt_in_handoffs_for_current_runtime": True,
            "sr_tick_may_continue_after_containment": True,
            "automatic_restart": False,
            "automatic_retry": False,
        },
        "fresh_restart_boundary": {
            "host_lifecycle_owner": "legacy_gameviewport_stop_or_scene_reload_then_normal_start",
            "discard_current_sr_runtime_instance": True,
            "discard_current_ps_pond_instance": True,
            "reuses_partially_mutated_pond": False,
            "restores_prior_state": False,
            "replays_failed_handoff": False,
        },
        "compensation": {
            "cross_lane_rollback": False,
            "inverse_mutation_compensation": False,
            "in_place_sr_ps_restore": False,
            "atomic_recovery": False,
            "bridge_link_repair": False,
        },
        "admissions": {
            "receipt_classification": True,
            "future_opt_in_handoff_suspension": True,
            "controlled_fresh_restart": True,
            "cross_lane_rollback": False,
            "inverse_mutation_compensation": False,
            "in_place_restore": False,
            "atomic_recovery": False,
            "replay_admitted": False,
            "lossless_mapping": False,
            "default_ready": False,
        },
        "required_future_evidence": [
            "versioned_complete_sr_ps_checkpoint_and_restore_order",
            "partial_pond_system_mutation_compensation",
            "bridge_identity_link_restoration",
            "shared_input_lifecycle_clock_rng_restore_protocol",
            "cross_lane_replay_parity_evidence",
        ],
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    contract["contract_valid"] = validate_worldbridge_recovery_compensation_controlled_restart_contract(contract)["valid"]
    return contract


def validate_worldbridge_recovery_compensation_controlled_restart_contract(contract: object) -> dict[str, Any]:
    """Reject rollback/replay language masquerading as a fresh lifecycle restart."""
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
    if contract.get("authority_scope") != "classify_labelled_failure_suspend_current_opt_in_handoffs_and_describe_host_fresh_restart_only":
        errors.append("authority_scope_overclaim")
    response = contract.get("failure_response")
    if not isinstance(response, Mapping):
        errors.append("failure_response_missing")
    else:
        for field in (
            "requires_phase_labelled_failure_receipt",
            "retain_copy_owned_receipt",
            "suspend_future_opt_in_handoffs_for_current_runtime",
            "sr_tick_may_continue_after_containment",
        ):
            if response.get(field) is not True:
                errors.append(f"{field}_required")
        for field in ("automatic_restart", "automatic_retry"):
            if response.get(field) is not False:
                errors.append(f"{field}_overclaim")
    restart = contract.get("fresh_restart_boundary")
    if not isinstance(restart, Mapping):
        errors.append("fresh_restart_boundary_missing")
    else:
        for field in (
            "discard_current_sr_runtime_instance",
            "discard_current_ps_pond_instance",
        ):
            if restart.get(field) is not True:
                errors.append(f"{field}_required")
        for field in ("reuses_partially_mutated_pond", "restores_prior_state", "replays_failed_handoff"):
            if restart.get(field) is not False:
                errors.append(f"{field}_overclaim")
    compensation = contract.get("compensation")
    if not isinstance(compensation, Mapping):
        errors.append("compensation_missing")
    elif any(compensation.get(field) is not False for field in compensation):
        errors.append("compensation_overclaim")
    admissions = contract.get("admissions")
    if not isinstance(admissions, Mapping):
        errors.append("admissions_missing")
    else:
        for field in ("receipt_classification", "future_opt_in_handoff_suspension", "controlled_fresh_restart"):
            if admissions.get(field) is not True:
                errors.append(f"{field}_required")
        for field in (
            "cross_lane_rollback",
            "inverse_mutation_compensation",
            "in_place_restore",
            "atomic_recovery",
            "replay_admitted",
            "lossless_mapping",
            "default_ready",
        ):
            if admissions.get(field) is not False:
                errors.append(f"{field}_overclaim")
    if not isinstance(contract.get("do_not_claim"), list) or set(DO_NOT_CLAIM) - set(contract.get("do_not_claim", [])):
        errors.append("do_not_claim_incomplete")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "DO_NOT_CLAIM",
    "classify_worldbridge_handoff_failure",
    "classify_worldbridge_handoff_failure_containment",
    "build_worldbridge_recovery_compensation_controlled_restart_contract",
    "validate_worldbridge_recovery_compensation_controlled_restart_contract",
]
