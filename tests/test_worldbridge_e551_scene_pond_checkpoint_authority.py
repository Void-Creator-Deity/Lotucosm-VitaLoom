from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from core.Lotucosm.runtime.world_bridge_e551_scene_pond_checkpoint_authority import (
    CLOSED_ADMISSION_FIELDS,
    PROOF_FIELDS,
    build_worldbridge_e551_scene_pond_checkpoint_authority,
    validate_worldbridge_e551_scene_pond_checkpoint_authority,
)
from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    SCENE_POND_CHECKPOINT_BLOCKER,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from tools.check_worldbridge_e505_fresh_host_reconstruction import (
    verify as verify_e505,
)
from tools.check_worldbridge_e551_scene_pond_checkpoint_authority import (
    _atomic_capture_probe,
)


ROOT = Path(__file__).resolve().parents[1]


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
    fresh = verify_e505()
    project = (
        ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    )
    atomic = _atomic_capture_probe(
        project, project / "scenes" / "challenge_scene.pond"
    )
    return build_worldbridge_e551_scene_pond_checkpoint_authority(
        checkpoint=fresh["source_checkpoint"],
        fresh_dual_lane_witness=fresh["witness"],
        atomic_capture_evidence=atomic,
    )


def test_e551_validates_checkpoint_capture_and_fresh_host_parity(
    witness: dict[str, object],
) -> None:
    assert validate_worldbridge_e551_scene_pond_checkpoint_authority(witness) == {
        "valid": True,
        "errors": [],
    }
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["grants_admission"] is False
    assert witness["admission_effect"] == "none"


def test_e551_rejects_incomplete_sr_runtime_state(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["checkpoint"]["sr_state"].pop("runtime_restore_envelope")
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e551_scene_pond_checkpoint_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "sr_runtime_state_complete_not_proven" in validation["errors"]


def test_e551_rejects_incomplete_ps_pond_state(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["checkpoint"]["ps_state"].pop("organisms")
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e551_scene_pond_checkpoint_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "ps_pond_state_complete_not_proven" in validation["errors"]


def test_e551_rejects_unheld_capture_gate(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["atomic_capture_evidence"]["checkpoint_gate_snapshot"][
        "locked"
    ] = False
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e551_scene_pond_checkpoint_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "competing_capture_not_blocked" in validation["errors"]


def test_e551_rejects_competing_capture_entered_during_hold(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["atomic_capture_evidence"][
        "competing_entered_before_release"
    ] = True
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e551_scene_pond_checkpoint_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "competing_capture_not_blocked" in validation["errors"]


def test_e551_rejects_gate_release_drift(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["atomic_capture_evidence"]["live_gate_after"]["locked"] = True
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e551_scene_pond_checkpoint_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "capture_gate_not_released" in validation["errors"]


def test_e551_rejects_fresh_host_parity_drift(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["fresh_dual_lane_witness"]["fresh_dual_lane_parity"] = False
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e551_scene_pond_checkpoint_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "fresh_dual_lane_witness_invalid" in validation["errors"]


def test_e551_rejects_extra_keys_after_reseal(
    witness: dict[str, object],
) -> None:
    candidate = _reseal_witness({**witness, "unexpected": True})

    validation = validate_worldbridge_e551_scene_pond_checkpoint_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "witness_keys_invalid" in validation["errors"]


def test_e551_rejects_proof_tamper_after_reseal(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["same_process_atomic_capture"] = False
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e551_scene_pond_checkpoint_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "same_process_atomic_capture_mismatch" in validation["errors"]


def test_e551_rejects_digest_tamper(witness: dict[str, object]) -> None:
    candidate = copy.deepcopy(witness)
    candidate["witness_digest"] = "0" * 64

    validation = validate_worldbridge_e551_scene_pond_checkpoint_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "witness_digest_mismatch" in validation["errors"]


def test_e551_admission_clears_only_checkpoint_blocker(
    witness: dict[str, object],
) -> None:
    baseline = build_worldbridge_tick_replay_admission()
    admission = build_worldbridge_tick_replay_admission(
        scene_pond_checkpoint_witness=witness
    )

    evidence = admission["scene_pond_checkpoint_evidence"]
    assert evidence["validated"] is True
    assert evidence["grants_admission"] is False
    assert admission["remaining_admission_blockers"] == [
        blocker
        for blocker in baseline["remaining_admission_blockers"]
        if blocker != SCENE_POND_CHECKPOINT_BLOCKER
    ]
    requirement = admission["shared_contracts"]["requirements"][
        "shared_scene_pond_checkpoint"
    ]
    assert requirement["capability_admitted"] is True
    assert requirement["blocking"] is False
    assert requirement["missing_requirements"] == []
    admissions = admission["shared_contracts"]["admissions"]
    assert admissions["shared_scene_pond_checkpoint"] is True
    assert admissions["atomic_capture_admitted"] is True
    assert admissions["cross_lane_checkpoint_available"] is True
    assert admissions["cross_lane_restore_available"] is True
    assert admission["tick_merge_admitted"] is False
    assert admission["full_unified_replay_admitted"] is False
    assert admission["default_ready"] is False


def test_e551_runtime_status_retains_checkpoint_admission(
    witness: dict[str, object],
) -> None:
    status = build_runtime_worldbridge_status(
        scene_pond_checkpoint_witness=witness
    )

    evidence = status["tick_replay_admission"][
        "scene_pond_checkpoint_evidence"
    ]
    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]
    shared = status["e538_shared_contracts"]
    assert shared["admissions"]["shared_scene_pond_checkpoint"] is True
    assert shared["admissions"]["atomic_capture_admitted"] is True
    assert SCENE_POND_CHECKPOINT_BLOCKER not in shared[
        "remaining_admission_blockers"
    ]
    assert status["tick_replay_admission"]["default_ready"] is False


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e551_rejects_closed_admission_overclaim(
    witness: dict[str, object], field: str
) -> None:
    candidate = copy.deepcopy(witness)
    candidate[field] = True
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e551_scene_pond_checkpoint_authority(
        candidate
    )
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]
