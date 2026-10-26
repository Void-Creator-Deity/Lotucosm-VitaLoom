"""Compose pause/reset lifecycle and live handoff compensation evidence."""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from .world_bridge_e549_pause_reset_lifecycle_authority import (
    PROOF_FIELDS as PAUSE_PROOF_FIELDS,
    validate_worldbridge_e549_pause_reset_lifecycle_authority,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e550_pause_reset_error_isolation_authority"
SCOPE = "composed_real_viewport_pause_reset_and_handoff_compensation_evidence"
ADMISSION_EFFECT = "none"
FAILURE_PHASES = ("sr_to_ps_sync", "pond_update", "ps_to_sr_reflection")
FAILURE_CHECK_FIELDS = frozenset(
    {
        "handoff_suspended_cleared",
        "decision_status_verified",
        "compensation_performed",
        "rollback_performed",
        "failure_phase_matches",
        "transactional_failure_rethrown",
        "checkpoint_payload_restored",
        "pond_live_state_restored",
        "pond_organisms_identity_kept",
        "organism_identity_kept",
        "physics_targets_identity_kept",
        "receipt_replay_closed",
        "receipt_default_closed",
        "receipt_atomic_checkpoint_closed",
        "receipt_lossless_closed",
        "rollback_report_lossless_closed",
        "decision_replay_closed",
        "decision_default_closed",
        "decision_lossless_closed",
    }
)
PROOF_FIELDS = (
    "pause_reset_witness_valid",
    "pause_reset_lifecycle_complete",
    "failure_phase_order_complete",
    "state_restored_all_phases",
    "compensation_all_phases",
    "rollback_all_phases",
    "later_phases_skipped",
    "input_epoch_stable_across_failures",
    "owner_binding_stable",
    "runtime_reusable_across_failures",
    "error_isolation_evidence_valid",
)
CLOSED_ADMISSION_FIELDS = (
    "shared_pause_reset_authority",
    "cross_lane_error_isolation_admitted",
    "atomic_recovery",
    "cross_lane_transaction",
    "scheduler_owned",
    "atomic_checkpoint",
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
    "pause_reset_witness",
    "failure_isolation_phases",
    "phase_order",
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


def _later_phases_skipped(
    phase: str,
    receipt: Mapping[str, Any],
) -> bool:
    index = FAILURE_PHASES.index(phase)
    started = receipt.get("later_phases_not_run")
    if not isinstance(started, Mapping):
        return False
    return all(
        started.get(later) is True
        for later in FAILURE_PHASES[index + 1 :]
    )


def _phase_projection(
    value: object,
    *,
    expected_phase: str,
) -> tuple[list[str], dict[str, bool]]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return [f"{expected_phase}_evidence_not_mapping"], {}
    required = {
        "phase",
        "checks",
        "before_checkpoint_digest",
        "after_checkpoint_digest",
        "pond_live_state_digest",
        "decision_status",
        "rollback_report",
        "failure_receipt",
        "recovery_decision",
        "before_state_digest",
        "after_state_digest",
        "input_pause_reset_epoch_before",
        "input_pause_reset_epoch_after",
    }
    if set(value) != required:
        return [f"{expected_phase}_evidence_keys_invalid"], {}
    if value.get("phase") != expected_phase:
        errors.append(f"{expected_phase}_phase_mismatch")
    checks = value.get("checks")
    if not isinstance(checks, Mapping) or set(checks) != FAILURE_CHECK_FIELDS:
        errors.append(f"{expected_phase}_checks_invalid")
    elif any(checks.get(field) is not True for field in FAILURE_CHECK_FIELDS):
        errors.append(f"{expected_phase}_checks_not_all_true")

    before_digest = value.get("before_state_digest")
    after_digest = value.get("after_state_digest")
    before_checkpoint = value.get("before_checkpoint_digest")
    after_checkpoint = value.get("after_checkpoint_digest")
    state_restored = (
        isinstance(before_digest, str)
        and _DIGEST_RE.fullmatch(before_digest) is not None
        and before_digest == after_digest
        and before_digest == before_checkpoint
        and before_digest == after_checkpoint
    )
    if not state_restored:
        errors.append(f"{expected_phase}_state_not_restored")

    epoch_before = value.get("input_pause_reset_epoch_before")
    epoch_after = value.get("input_pause_reset_epoch_after")
    epoch_stable = (
        isinstance(epoch_before, int)
        and not isinstance(epoch_before, bool)
        and epoch_before == epoch_after
    )
    if not epoch_stable:
        errors.append(f"{expected_phase}_input_epoch_changed")

    receipt = value.get("failure_receipt")
    if not isinstance(receipt, Mapping):
        errors.append(f"{expected_phase}_failure_receipt_missing")
        receipt = {}
    if (
        receipt.get("status")
        != "worldbridge_cross_lane_transaction_failure_isolation_authority"
        or receipt.get("phase") != expected_phase
        or receipt.get("failure_isolated") is not True
        or receipt.get("preflight_completed") is not True
    ):
        errors.append(f"{expected_phase}_failure_receipt_invalid")
    later_skipped = _later_phases_skipped(expected_phase, receipt)
    if not later_skipped:
        errors.append(f"{expected_phase}_later_phases_ran")
    rollback = receipt.get("transaction_rollback")
    if not isinstance(rollback, Mapping):
        errors.append(f"{expected_phase}_rollback_missing")
        rollback = {}
    restore_report = rollback.get("restore_report")
    if not isinstance(restore_report, Mapping):
        errors.append(f"{expected_phase}_restore_report_missing")
        restore_report = {}
    rollback_complete = (
        receipt.get("rollback_performed") is True
        and receipt.get("cross_lane_transaction") is True
        and receipt.get("post_failure_state_restored") is True
        and rollback.get("capture_completed") is True
        and rollback.get("rollback_attempted") is True
        and rollback.get("rollback_complete") is True
        and rollback.get("rollback_performed") is True
        and rollback.get("cross_lane_transaction") is True
        and restore_report.get("restored") is True
        and restore_report.get("transaction_verified") is True
        and restore_report.get("tick_binding_validated") is True
        and restore_report.get("tick_binding_stable") is True
        and restore_report.get("owner_binding_validated") is True
        and restore_report.get("restore_order")
        == ["lifecycle", "input", "randomness", "ps", "sr", "topology", "bridge"]
    )
    if not rollback_complete:
        errors.append(f"{expected_phase}_rollback_incomplete")
    for field in (
        "atomic_checkpoint",
        "replay_admitted",
        "default_ready",
    ):
        if receipt.get(field) is not False or rollback.get(field) is not False:
            errors.append(f"{expected_phase}_{field}_overclaim")
    if (
        receipt.get("lossless_mapping") is not None
        or rollback.get("lossless_mapping") is not False
    ):
        errors.append(f"{expected_phase}_lossless_overclaim")

    decision = value.get("recovery_decision")
    if not isinstance(decision, Mapping):
        errors.append(f"{expected_phase}_recovery_decision_missing")
        decision = {}
    admissions = decision.get("admissions")
    compensation = (
        decision.get("status")
        == "worldbridge_verified_transaction_failure_containment"
        and decision.get("failure_phase") == expected_phase
        and decision.get("compensation_performed") is True
        and decision.get("rollback_performed") is True
        and decision.get("sr_live_state_repaired") is True
        and decision.get("ps_live_state_repaired") is True
        and decision.get("bridge_link_metadata_repaired") is True
        and isinstance(admissions, Mapping)
        and admissions.get("cross_lane_rollback") is True
        and admissions.get("inverse_mutation_compensation") is True
        and admissions.get("in_place_restore") is True
        and admissions.get("replay_admitted") is False
        and admissions.get("lossless_mapping") is False
        and admissions.get("default_ready") is False
    )
    if not compensation:
        errors.append(f"{expected_phase}_compensation_incomplete")

    return list(dict.fromkeys(errors)), {
        "state_restored": state_restored,
        "epoch_stable": epoch_stable,
        "later_skipped": later_skipped,
        "rollback_complete": rollback_complete,
        "compensation": compensation,
    }


def _evaluate(
    *,
    pause_reset_witness: object,
    failure_phases: object,
) -> tuple[list[str], dict[str, bool]]:
    errors: list[str] = []
    pause_validation = validate_worldbridge_e549_pause_reset_lifecycle_authority(
        pause_reset_witness
    )
    if pause_validation != {"valid": True, "errors": []}:
        errors.append("pause_reset_witness_invalid")
    if not isinstance(failure_phases, list):
        return errors + ["failure_phases_not_list"], {}
    if len(failure_phases) != len(FAILURE_PHASES):
        errors.append("failure_phase_count_mismatch")
    projections: list[dict[str, bool]] = []
    for index, expected_phase in enumerate(FAILURE_PHASES):
        if index >= len(failure_phases):
            break
        phase_errors, projection = _phase_projection(
            failure_phases[index],
            expected_phase=expected_phase,
        )
        errors.extend(phase_errors)
        if projection:
            projections.append(projection)

    pause_lifecycle_complete = (
        isinstance(pause_reset_witness, Mapping)
        and all(
            pause_reset_witness.get(field) is True
            for field in PAUSE_PROOF_FIELDS
        )
    )
    projection = {
        "pause_reset_witness_valid": pause_validation
        == {"valid": True, "errors": []},
        "pause_reset_lifecycle_complete": pause_lifecycle_complete,
        "failure_phase_order_complete": (
            len(failure_phases) == len(FAILURE_PHASES)
            and [
                row.get("phase") if isinstance(row, Mapping) else None
                for row in failure_phases
            ]
            == list(FAILURE_PHASES)
        ),
        "state_restored_all_phases": bool(projections)
        and all(item.get("state_restored") is True for item in projections),
        "compensation_all_phases": bool(projections)
        and all(item.get("compensation") is True for item in projections),
        "rollback_all_phases": bool(projections)
        and all(item.get("rollback_complete") is True for item in projections),
        "later_phases_skipped": bool(projections)
        and all(item.get("later_skipped") is True for item in projections),
        "input_epoch_stable_across_failures": bool(projections)
        and all(item.get("epoch_stable") is True for item in projections),
        "owner_binding_stable": bool(projections)
        and all(item.get("rollback_complete") is True for item in projections),
        "runtime_reusable_across_failures": (
            len(projections) == len(FAILURE_PHASES)
            and all(item.get("compensation") is True for item in projections)
        ),
        "error_isolation_evidence_valid": not errors,
    }
    for field in PROOF_FIELDS:
        if projection.get(field) is not True:
            errors.append(f"{field}_not_proven")
    return list(dict.fromkeys(errors)), projection


def build_worldbridge_e550_pause_reset_error_isolation_authority(
    *,
    pause_reset_witness: Mapping[str, Any],
    failure_isolation_phases: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build one detached composition of lifecycle and compensation evidence."""
    pause = _mapping_copy(pause_reset_witness, "pause_reset_witness")
    phases = _json_copy(list(failure_isolation_phases), "failure_isolation_phases")
    if not isinstance(phases, list) or any(
        not isinstance(item, dict) for item in phases
    ):
        raise TypeError("failure_isolation_phases must contain mappings")
    errors, projection = _evaluate(
        pause_reset_witness=pause,
        failure_phases=phases,
    )
    if errors:
        raise ValueError(
            "E550 pause/reset error-isolation witness rejected: "
            + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "pause_reset_witness": pause,
        "failure_isolation_phases": phases,
        "phase_order": list(FAILURE_PHASES),
        **projection,
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e550_pause_reset_error_isolation_authority(
    value: object,
) -> dict[str, Any]:
    """Revalidate E550 composition without trusting embedded proof flags."""
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
    if value.get("phase_order") != list(FAILURE_PHASES):
        errors.append("phase_order_mismatch")

    pause = value.get("pause_reset_witness")
    phases = value.get("failure_isolation_phases")
    if not isinstance(pause, Mapping) or not isinstance(phases, list):
        return {
            "valid": False,
            "errors": errors + ["witness_payload_invalid"],
        }
    revalidation, projection = _evaluate(
        pause_reset_witness=pause,
        failure_phases=phases,
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
    "FAILURE_CHECK_FIELDS",
    "FAILURE_PHASES",
    "PROOF_FIELDS",
    "SCHEMA_VERSION",
    "SCOPE",
    "STATUS",
    "WITNESS_KEYS",
    "build_worldbridge_e550_pause_reset_error_isolation_authority",
    "validate_worldbridge_e550_pause_reset_error_isolation_authority",
]
