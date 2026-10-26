from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_e553_scheduler_input_queue_authority import (
    CLOSED_ADMISSION_FIELDS,
    PROOF_FIELDS,
    validate_worldbridge_e553_scheduler_input_queue_authority,
)
from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    SHARED_QUEUED_INPUT_BLOCKER,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from tools.check_worldbridge_e553_scheduler_input_queue_authority import (
    verify as verify_e553,
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


@pytest.fixture(scope="module")
def witness() -> dict[str, object]:
    return _build_witness()


def _build_witness() -> dict[str, object]:
    return verify_e553()["witness"]


def test_e553_validates_scheduler_owned_bounded_queue(
    witness: dict[str, object],
) -> None:
    assert validate_worldbridge_e553_scheduler_input_queue_authority(witness) == {
        "valid": True,
        "errors": [],
    }
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["grants_admission"] is False
    assert witness["admission_effect"] == "none"


def test_e553_rejects_backpressure_sequence_advance(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["backpressure_attempt"]["after"]["next_sequence"] += 1
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e553_scheduler_input_queue_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "backpressure_mutated_queue" in validation["errors"]


def test_e553_rejects_backpressure_pending_mutation(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["backpressure_attempt"]["after"]["pending_count"] = 1
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e553_scheduler_input_queue_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "backpressure_mutated_queue" in validation["errors"]


def test_e553_rejects_dispatch_receipt_event_drift(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["dispatch_receipt"]["event_ids"] = ["input-other"]
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e553_scheduler_input_queue_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "dispatch_receipt_not_committed" in validation["errors"]
    assert "queued_input_handoff_mismatch" in validation["errors"]


def test_e553_rejects_drop_reason_drift(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["drop_attempt"]["drop_receipt"]["reason"] = "manual_clear"
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e553_scheduler_input_queue_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "drop_receipt_mismatch" in validation["errors"]


def test_e553_rejects_dropped_event_reappearing(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["drop_attempt"]["drop_receipt"]["dropped_event_ids"][0] = (
        candidate["queued_input_handoff_witness"]["canonical_input_events"][0][
            "event_id"
        ]
    )
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e553_scheduler_input_queue_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "dropped_event_reappeared" in validation["errors"]


def test_e553_rejects_invalid_nested_handoff_witness(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["queued_input_handoff_witness"]["witness_digest"] = "0" * 64
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e553_scheduler_input_queue_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "handoff_witness_digest_mismatch" in validation["errors"]


def test_e553_rejects_extra_keys_after_reseal(
    witness: dict[str, object],
) -> None:
    candidate = _reseal_witness({**witness, "unexpected": True})

    validation = validate_worldbridge_e553_scheduler_input_queue_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "witness_keys_invalid" in validation["errors"]


def test_e553_rejects_proof_tamper_after_reseal(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["drop_not_replayed"] = False
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e553_scheduler_input_queue_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "drop_not_replayed_mismatch" in validation["errors"]


def test_e553_rejects_digest_tamper(witness: dict[str, object]) -> None:
    candidate = copy.deepcopy(witness)
    candidate["witness_digest"] = "0" * 64

    validation = validate_worldbridge_e553_scheduler_input_queue_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "witness_digest_mismatch" in validation["errors"]


def test_e553_admission_clears_only_queued_input_blocker(
    witness: dict[str, object],
) -> None:
    baseline = build_worldbridge_tick_replay_admission()
    admission = build_worldbridge_tick_replay_admission(
        scheduler_input_queue_witness=witness
    )

    evidence = admission["scheduler_input_queue_evidence"]
    assert evidence["validated"] is True
    assert evidence["grants_admission"] is False
    assert admission["remaining_admission_blockers"] == [
        blocker
        for blocker in baseline["remaining_admission_blockers"]
        if blocker != SHARED_QUEUED_INPUT_BLOCKER
    ]
    requirement = admission["shared_contracts"]["requirements"][
        "shared_queued_input_ordering"
    ]
    assert requirement["capability_admitted"] is True
    assert requirement["blocking"] is False
    assert requirement["missing_requirements"] == []
    admissions = admission["shared_contracts"]["admissions"]
    assert admissions["scheduler_owned"] is True
    assert admissions["shared_queued_input_ordering"] is True
    assert admissions["cross_lane_input_ordering_admitted"] is True
    assert admissions["backpressure_admitted"] is True
    assert admissions["dropped_event_policy_admitted"] is True
    assert admission["tick_merge_admitted"] is False
    assert admission["full_unified_replay_admitted"] is False
    assert admission["default_ready"] is False


def test_e553_runtime_status_retains_queue_admission(
    witness: dict[str, object],
) -> None:
    status = build_runtime_worldbridge_status(
        scheduler_input_queue_witness=witness
    )

    evidence = status["tick_replay_admission"][
        "scheduler_input_queue_evidence"
    ]
    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]
    shared = status["e538_shared_contracts"]
    assert shared["admissions"]["shared_queued_input_ordering"] is True
    assert shared["admissions"]["scheduler_owned"] is True
    assert SHARED_QUEUED_INPUT_BLOCKER not in shared[
        "remaining_admission_blockers"
    ]
    assert status["tick_replay_admission"]["default_ready"] is False


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e553_rejects_closed_admission_overclaim(
    witness: dict[str, object], field: str
) -> None:
    candidate = copy.deepcopy(witness)
    candidate[field] = True
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e553_scheduler_input_queue_authority(
        candidate
    )
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]
