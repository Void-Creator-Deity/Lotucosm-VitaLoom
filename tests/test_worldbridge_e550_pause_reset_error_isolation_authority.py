from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_e549_pause_reset_lifecycle_authority import (
    build_worldbridge_e549_pause_reset_lifecycle_authority,
)
from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    PAUSE_RESET_ERROR_ISOLATION_BLOCKER,
)
from core.Lotucosm.runtime.world_bridge_e550_pause_reset_error_isolation_authority import (
    CLOSED_ADMISSION_FIELDS,
    FAILURE_CHECK_FIELDS,
    FAILURE_PHASES,
    PROOF_FIELDS,
    build_worldbridge_e550_pause_reset_error_isolation_authority,
    validate_worldbridge_e550_pause_reset_error_isolation_authority,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)

from test_worldbridge_e549_pause_reset_lifecycle_authority import (
    _fixture as _pause_fixture,
)


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _reseal_witness(witness: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(witness)
    sealed["witness_digest"] = ""
    sealed["witness_digest"] = _digest(sealed)
    return sealed


def _pause_witness() -> dict[str, object]:
    return build_worldbridge_e549_pause_reset_lifecycle_authority(
        **_pause_fixture()
    )


def _failure_phase(phase: str) -> dict[str, object]:
    index = FAILURE_PHASES.index(phase)
    state_digest = "a" * 64
    restore_report = {
        "restored": True,
        "transaction_verified": True,
        "tick_binding_validated": True,
        "tick_binding_stable": True,
        "owner_binding_validated": True,
        "restore_order": [
            "lifecycle",
            "input",
            "randomness",
            "ps",
            "sr",
            "topology",
            "bridge",
        ],
    }
    rollback = {
        "capture_completed": True,
        "rollback_attempted": True,
        "rollback_complete": True,
        "rollback_performed": True,
        "cross_lane_transaction": True,
        "atomic_checkpoint": False,
        "replay_admitted": False,
        "lossless_mapping": False,
        "default_ready": False,
        "restore_report": restore_report,
    }
    later = {
        candidate: candidate_index > index
        for candidate_index, candidate in enumerate(FAILURE_PHASES)
    }
    receipt = {
        "status": "worldbridge_cross_lane_transaction_failure_isolation_authority",
        "phase": phase,
        "failure_isolated": True,
        "preflight_completed": True,
        "later_phases_not_run": later,
        "rollback_performed": True,
        "cross_lane_transaction": True,
        "post_failure_state_restored": True,
        "atomic_checkpoint": False,
        "replay_admitted": False,
        "default_ready": False,
        "transaction_rollback": rollback,
    }
    decision = {
        "status": "worldbridge_verified_transaction_failure_containment",
        "failure_phase": phase,
        "compensation_performed": True,
        "rollback_performed": True,
        "sr_live_state_repaired": True,
        "ps_live_state_repaired": True,
        "bridge_link_metadata_repaired": True,
        "admissions": {
            "cross_lane_rollback": True,
            "inverse_mutation_compensation": True,
            "in_place_restore": True,
            "replay_admitted": False,
            "lossless_mapping": False,
            "default_ready": False,
        },
    }
    return {
        "phase": phase,
        "checks": {field: True for field in FAILURE_CHECK_FIELDS},
        "before_checkpoint_digest": state_digest,
        "after_checkpoint_digest": state_digest,
        "pond_live_state_digest": "b" * 64,
        "decision_status": decision["status"],
        "rollback_report": copy.deepcopy(rollback),
        "failure_receipt": receipt,
        "recovery_decision": decision,
        "before_state_digest": state_digest,
        "after_state_digest": state_digest,
        "input_pause_reset_epoch_before": 0,
        "input_pause_reset_epoch_after": 0,
    }


def _fixture() -> dict[str, object]:
    return {
        "pause_reset_witness": _pause_witness(),
        "failure_isolation_phases": [
            _failure_phase(phase) for phase in FAILURE_PHASES
        ],
    }


def _build(fixture: dict[str, object] | None = None) -> dict[str, object]:
    return build_worldbridge_e550_pause_reset_error_isolation_authority(
        **(fixture or _fixture())
    )


def _assert_rejected(fixture: dict[str, object], error: str) -> None:
    with pytest.raises(ValueError, match=error):
        _build(fixture)


def test_e550_builds_and_validates_composed_evidence() -> None:
    witness = _build()

    assert validate_worldbridge_e550_pause_reset_error_isolation_authority(
        witness
    ) == {"valid": True, "errors": []}
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["grants_admission"] is False
    assert witness["admission_effect"] == "none"


def test_e550_rejects_failure_phase_order_drift() -> None:
    fixture = _fixture()
    fixture["failure_isolation_phases"][1]["phase"] = "ps_to_sr_reflection"
    fixture["failure_isolation_phases"][1]["failure_receipt"][
        "phase"
    ] = "ps_to_sr_reflection"
    fixture["failure_isolation_phases"][1]["recovery_decision"][
        "failure_phase"
    ] = "ps_to_sr_reflection"
    _assert_rejected(fixture, "pond_update_phase_mismatch")


def test_e550_rejects_state_digest_drift() -> None:
    fixture = _fixture()
    fixture["failure_isolation_phases"][0]["after_state_digest"] = "c" * 64
    _assert_rejected(fixture, "sr_to_ps_sync_state_not_restored")


def test_e550_rejects_incomplete_rollback() -> None:
    fixture = _fixture()
    row = fixture["failure_isolation_phases"][1]
    row["failure_receipt"]["transaction_rollback"]["rollback_complete"] = False
    _assert_rejected(fixture, "pond_update_rollback_incomplete")


def test_e550_rejects_input_epoch_change() -> None:
    fixture = _fixture()
    fixture["failure_isolation_phases"][2][
        "input_pause_reset_epoch_after"
    ] = 1
    _assert_rejected(fixture, "ps_to_sr_reflection_input_epoch_changed")


def test_e550_rejects_later_phase_execution() -> None:
    fixture = _fixture()
    fixture["failure_isolation_phases"][0]["failure_receipt"][
        "later_phases_not_run"
    ]["pond_update"] = False
    _assert_rejected(fixture, "sr_to_ps_sync_later_phases_ran")


def test_e550_rejects_invalid_pause_reset_witness() -> None:
    fixture = _fixture()
    fixture["pause_reset_witness"]["pause_transition"]["after"][
        "pause_reset_epoch"
    ] = 0
    _assert_rejected(fixture, "pause_reset_witness_invalid")


def test_e550_rejects_extra_keys_after_reseal() -> None:
    witness = _build()
    candidate = _reseal_witness({**witness, "unexpected": True})

    validation = (
        validate_worldbridge_e550_pause_reset_error_isolation_authority(candidate)
    )
    assert validation["valid"] is False
    assert "witness_keys_invalid" in validation["errors"]


def test_e550_rejects_proof_tamper_after_reseal() -> None:
    witness = _build()
    witness["rollback_all_phases"] = False
    candidate = _reseal_witness(witness)

    validation = (
        validate_worldbridge_e550_pause_reset_error_isolation_authority(candidate)
    )
    assert validation["valid"] is False
    assert "rollback_all_phases_mismatch" in validation["errors"]


def test_e550_rejects_digest_tamper() -> None:
    witness = _build()
    witness["witness_digest"] = "0" * 64

    validation = (
        validate_worldbridge_e550_pause_reset_error_isolation_authority(witness)
    )
    assert validation["valid"] is False
    assert "witness_digest_mismatch" in validation["errors"]


def test_e550_admission_evidence_is_read_only() -> None:
    witness = _build()
    baseline = build_worldbridge_tick_replay_admission()
    admission = build_worldbridge_tick_replay_admission(
        pause_reset_error_isolation_witness=witness
    )

    evidence = admission["pause_reset_error_isolation_evidence"]
    assert evidence["validated"] is True
    assert evidence["grants_admission"] is False
    assert evidence["witness_digest"] == witness["witness_digest"]
    assert admission["remaining_admission_blockers"] == [
        blocker
        for blocker in baseline["remaining_admission_blockers"]
        if blocker != PAUSE_RESET_ERROR_ISOLATION_BLOCKER
    ]
    pause_requirement = admission["shared_contracts"]["requirements"][
        "shared_pause_reset_error_isolation"
    ]
    assert pause_requirement["capability_admitted"] is True
    assert pause_requirement["blocking"] is False
    assert pause_requirement["missing_requirements"] == []
    assert admission["shared_contracts"]["admissions"][
        "shared_pause_reset_authority"
    ] is True
    assert admission["shared_contracts"]["admissions"][
        "cross_lane_error_isolation_admitted"
    ] is True
    assert admission["shared_contracts"]["admissions"][
        "partial_failure_compensation_admitted"
    ] is True
    assert admission["tick_merge_admitted"] is False
    assert admission["full_unified_replay_admitted"] is False
    assert admission["default_ready"] is False


def test_e550_runtime_status_retains_composed_evidence() -> None:
    witness = _build()
    status = build_runtime_worldbridge_status(
        pause_reset_error_isolation_witness=witness
    )

    evidence = status["tick_replay_admission"][
        "pause_reset_error_isolation_evidence"
    ]
    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]
    assert evidence["admission_effect"] == "none"
    assert status["tick_replay_admission"]["default_ready"] is False
    shared = status["e538_shared_contracts"]
    assert shared["admissions"]["shared_pause_reset_authority"] is True
    assert shared["admissions"]["cross_lane_error_isolation_admitted"] is True
    assert shared["admissions"][
        "partial_failure_compensation_admitted"
    ] is True
    assert "shared_pause_reset_error_isolation_contract_missing" not in shared[
        "remaining_admission_blockers"
    ]


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e550_rejects_closed_admission_overclaim(field: str) -> None:
    witness = _build()
    witness[field] = True
    candidate = _reseal_witness(witness)

    validation = (
        validate_worldbridge_e550_pause_reset_error_isolation_authority(candidate)
    )
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]
