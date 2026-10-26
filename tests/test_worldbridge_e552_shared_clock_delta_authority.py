from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_e552_shared_clock_delta_authority import (
    CLOSED_ADMISSION_FIELDS,
    PROOF_FIELDS,
    validate_worldbridge_e552_shared_clock_delta_authority,
)
from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    SHARED_CLOCK_DELTA_BLOCKER,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from tools.check_worldbridge_e552_shared_clock_delta_authority import (
    verify as verify_e552,
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
    return verify_e552()["witness"]


def test_e552_validates_variable_delta_clock_consumption(
    witness: dict[str, object],
) -> None:
    assert validate_worldbridge_e552_shared_clock_delta_authority(witness) == {
        "valid": True,
        "errors": [],
    }
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["grants_admission"] is False
    assert witness["admission_effect"] == "none"


def test_e552_rejects_ps_simulation_time_drift(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["clock_samples"][1]["pond_after"]["simulation_time"] += 0.01
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e552_shared_clock_delta_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "sample_1_ps_simulation_time_mismatch" in validation["errors"]


def test_e552_rejects_ps_tick_not_advanced_once(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["clock_samples"][0]["pond_after"]["time"] = candidate[
        "clock_samples"
    ][0]["pond_before"]["time"]
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e552_shared_clock_delta_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "sample_0_ps_tick_mismatch" in validation["errors"]


def test_e552_rejects_unheld_owner_gate(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["clock_samples"][2]["gate_snapshot"]["current_operation"] = "idle"
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e552_shared_clock_delta_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "sample_2_owner_gate_not_held" in validation["errors"]


def test_e552_rejects_consumer_order_drift(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["clock_samples"][0]["receipt"]["clock_consumers"].reverse()
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e552_shared_clock_delta_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "sample_0_receipt_invalid" in validation["errors"]


def test_e552_rejects_non_contiguous_tick_sequence(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["clock_samples"][2]["receipt"]["tick_sequence"] += 2
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e552_shared_clock_delta_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "sample_2_receipt_invalid" in validation["errors"]


def test_e552_rejects_variable_delta_proof_tamper(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["variable_delta_exercised"] = False
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e552_shared_clock_delta_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "variable_delta_exercised_mismatch" in validation["errors"]


def test_e552_rejects_extra_keys_after_reseal(
    witness: dict[str, object],
) -> None:
    candidate = _reseal_witness({**witness, "unexpected": True})

    validation = validate_worldbridge_e552_shared_clock_delta_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "witness_keys_invalid" in validation["errors"]


def test_e552_rejects_digest_tamper(witness: dict[str, object]) -> None:
    candidate = copy.deepcopy(witness)
    candidate["witness_digest"] = "0" * 64

    validation = validate_worldbridge_e552_shared_clock_delta_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "witness_digest_mismatch" in validation["errors"]


def test_e552_admission_clears_only_shared_clock_blocker(
    witness: dict[str, object],
) -> None:
    baseline = build_worldbridge_tick_replay_admission()
    admission = build_worldbridge_tick_replay_admission(
        shared_clock_delta_authority_witness=witness
    )

    evidence = admission["shared_clock_delta_authority_evidence"]
    assert evidence["validated"] is True
    assert evidence["grants_admission"] is False
    assert admission["remaining_admission_blockers"] == [
        blocker
        for blocker in baseline["remaining_admission_blockers"]
        if blocker != SHARED_CLOCK_DELTA_BLOCKER
    ]
    requirement = admission["shared_contracts"]["requirements"][
        "shared_clock_and_delta"
    ]
    assert requirement["capability_admitted"] is True
    assert requirement["blocking"] is False
    assert requirement["missing_requirements"] == []
    admissions = admission["shared_contracts"]["admissions"]
    assert admissions["shared_clock"] is True
    assert admissions["time_conversion_admitted"] is True
    assert admissions["cross_call_ordering_admitted"] is True
    assert admission["tick_merge_admitted"] is False
    assert admission["full_unified_replay_admitted"] is False
    assert admission["default_ready"] is False


def test_e552_runtime_status_retains_clock_admission(
    witness: dict[str, object],
) -> None:
    status = build_runtime_worldbridge_status(
        shared_clock_delta_authority_witness=witness
    )

    evidence = status["tick_replay_admission"][
        "shared_clock_delta_authority_evidence"
    ]
    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]
    shared = status["e538_shared_contracts"]
    assert shared["admissions"]["shared_clock"] is True
    assert shared["admissions"]["time_conversion_admitted"] is True
    assert SHARED_CLOCK_DELTA_BLOCKER not in shared[
        "remaining_admission_blockers"
    ]
    assert status["tick_replay_admission"]["default_ready"] is False


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e552_rejects_closed_admission_overclaim(
    witness: dict[str, object], field: str
) -> None:
    candidate = copy.deepcopy(witness)
    candidate[field] = True
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e552_shared_clock_delta_authority(
        candidate
    )
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]
