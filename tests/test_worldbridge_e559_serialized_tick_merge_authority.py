from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    build_worldbridge_e538_shared_contracts,
)
from core.Lotucosm.runtime.world_bridge_e559_serialized_tick_merge_authority import (
    CLOSED_ADMISSION_FIELDS,
    PROOF_FIELDS,
    TICK_MERGE_POLICY,
    build_worldbridge_e559_serialized_tick_merge_authority,
    validate_worldbridge_e559_serialized_tick_merge_authority,
)
from core.Lotucosm.runtime.world_bridge_mapping_audit import (
    build_worldbridge_mapping_audit,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)

from test_worldbridge_e558_cross_lane_behavior_authority import (
    field_witness,
    prerequisites,
    witness as behavior_witness,
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
def witness(behavior_witness: dict[str, object]) -> dict[str, object]:
    replay = behavior_witness["field_roundtrip_witness"][
        "full_unified_replay_witness"
    ]
    return build_worldbridge_e559_serialized_tick_merge_authority(
        full_unified_replay_witness=replay,
        cross_lane_behavior_witness=behavior_witness,
    )


def test_e559_binds_one_frame_dispatcher_and_one_ps_update(
    witness: dict[str, object],
) -> None:
    assert validate_worldbridge_e559_serialized_tick_merge_authority(
        witness
    ) == {"valid": True, "errors": []}
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["tick_merge_policy"] == TICK_MERGE_POLICY
    assert witness["frame_dispatcher_entrypoint"] == (
        "GameViewport._update_scene_runtime_entities_locked"
    )
    assert witness["pond_updates_per_frame"] == 1
    assert witness["tick_owner_evidence"] == {
        "wrapper_delegates_to_locked_dispatcher": True,
        "dispatcher_begin_count": 1,
        "dispatcher_complete_count": 1,
        "dispatcher_abort_count": 1,
        "driver_tick_boundary_count": 0,
        "tick_authority_owner_count": 1,
        "duplicate_tick_owner_count": 0,
    }
    assert witness["remaining_tick_merge_blockers"] == [
        "behavior_equivalence_not_proven",
        "lossless_mapping_not_proven",
    ]
    assert witness["grants_admission"] is False
    assert witness["admission_effect"] == "none"
    assert all(witness[field] is False for field in CLOSED_ADMISSION_FIELDS)


def test_e559_rejects_tick_owner_tamper(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["tick_owner_evidence"]["driver_tick_boundary_count"] = 1
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e559_serialized_tick_merge_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "tick_owner_evidence_mismatch" in validation["errors"]


def test_e559_rejects_clock_delta_tamper(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["full_unified_replay_witness"]["shared_contract"][
        "shared_clock_delta_witness"
    ]["clock_samples"][0]["pond_after"]["simulation_time"] += 1.0
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e559_serialized_tick_merge_authority(
        candidate
    )
    assert validation["valid"] is False
    assert any(error.startswith("clock_") for error in validation["errors"])


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e559_rejects_admission_overclaim(
    witness: dict[str, object],
    field: str,
) -> None:
    candidate = copy.deepcopy(witness)
    candidate[field] = True
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e559_serialized_tick_merge_authority(
        candidate
    )
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]


def test_e559_e538_opens_tick_merge_only(
    behavior_witness: dict[str, object],
    witness: dict[str, object],
) -> None:
    contract = build_worldbridge_e538_shared_contracts(
        cross_lane_behavior_witness=behavior_witness,
        serialized_tick_merge_witness=witness,
    )

    assert contract["admissions"]["cross_lane_behavior_admitted"] is True
    assert contract["admissions"]["tick_merge_admitted"] is True
    assert contract["admissions"]["behavior_equivalence_admitted"] is False
    assert contract["admissions"]["lossless"] is False
    assert contract["admissions"]["default_ready"] is False
    assert "sr_ps_tick_merge" not in contract["do_not_claim"]
    assert "cross_lane_behavior_equivalence" in contract["do_not_claim"]


def test_e559_admission_status_and_mapping_audit_expose_tick_merge(
    field_witness: dict[str, object],
    behavior_witness: dict[str, object],
    witness: dict[str, object],
) -> None:
    admission = build_worldbridge_tick_replay_admission(
        cross_lane_behavior_witness=behavior_witness,
        serialized_tick_merge_witness=witness,
    )
    evidence = admission["serialized_tick_merge_evidence"]
    assert admission["tick_merge_admitted"] is True
    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]
    assert admission["lossless"] is False

    audit = build_worldbridge_mapping_audit(
        field_witness,
        behavior_witness,
        witness,
    )
    assert audit["tick_merge_admitted"] is True
    assert audit["tick_merge_evidence"]["witness_digest"] == witness[
        "witness_digest"
    ]
    assert "sr_ps_tick_merge" not in audit["do_not_claim"]
    assert audit["lossless"] is False

    status = build_runtime_worldbridge_status(
        field_roundtrip_witness=field_witness,
        cross_lane_behavior_witness=behavior_witness,
        serialized_tick_merge_witness=witness,
    )
    assert status["tick_replay_admission"]["tick_merge_admitted"] is True
    assert status["mapping_audit"]["tick_merge_admitted"] is True
    assert status["default_ready"] is False
