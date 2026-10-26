from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    build_worldbridge_e538_shared_contracts,
)
from core.Lotucosm.runtime.world_bridge_e560_behavior_equivalence_authority import (
    CLOSED_ADMISSION_FIELDS,
    ELIGIBLE_BEHAVIOR_ROUTES,
    EQUIVALENCE_POLICY,
    LANE_LOCAL_BEHAVIOR_ROUTES,
    PROOF_FIELDS,
    SCOPE,
    build_worldbridge_e560_behavior_equivalence_authority,
    validate_worldbridge_e560_behavior_equivalence_authority,
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
def witness(
    behavior_witness: dict[str, object],
) -> dict[str, object]:
    return build_worldbridge_e560_behavior_equivalence_authority(
        cross_lane_behavior_witness=behavior_witness,
    )


def test_e560_proves_only_the_declared_active_lifecycle_overlap(
    witness: dict[str, object],
) -> None:
    assert validate_worldbridge_e560_behavior_equivalence_authority(
        witness
    ) == {"valid": True, "errors": []}
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["scope"] == SCOPE
    assert witness["equivalence_policy"] == EQUIVALENCE_POLICY
    assert witness["eligible_behavior_routes"] == list(
        ELIGIBLE_BEHAVIOR_ROUTES
    )
    assert witness["lane_local_behavior_routes"] == (
        LANE_LOCAL_BEHAVIOR_ROUTES
    )
    assert witness["remaining_behavior_blockers"] == [
        "lossless_mapping_not_proven"
    ]
    assert witness["grants_admission"] is False
    assert witness["admission_effect"] == "none"
    assert all(witness[field] is False for field in CLOSED_ADMISSION_FIELDS)


def test_e560_evidence_contains_non_vacuous_roundtrip_and_gate_cases(
    witness: dict[str, object],
) -> None:
    evidence = witness["behavior_equivalence_evidence"]
    cases = {
        (item["direction"], item["input"]): item
        for item in evidence["active_roundtrip_cases"]
    }
    assert set(cases) == {
        ("sr_to_ps", False),
        ("sr_to_ps", True),
        ("ps_to_sr", False),
        ("ps_to_sr", True),
    }
    assert all(item["matches"] is True for item in cases.values())
    assert evidence["active_gate_cases"] == {
        "sr_inactive": {"expected": 0, "observed": 0},
        "sr_active": {"expected": 1, "observed": 1},
        "ps_inactive": {"expected": 0, "observed": 0},
        "ps_active": {"expected": 1, "observed": 1},
    }
    assert evidence["visible_probe"] == {
        "before": False,
        "after": False,
        "sr_local": True,
    }


def test_e560_rejects_roundtrip_evidence_tamper(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["behavior_equivalence_evidence"]["active_roundtrip_cases"][0][
        "observed"
    ] = True
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e560_behavior_equivalence_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "behavior_equivalence_evidence_mismatch" in validation["errors"]


def test_e560_rejects_lane_local_route_promotion(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["behavior_equivalence_evidence"]["lane_local_routes"][
        "visible"
    ] = "sr_to_ps_and_ps_to_sr"
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e560_behavior_equivalence_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "behavior_equivalence_evidence_mismatch" in validation["errors"]


def test_e560_rejects_embedded_routing_tamper(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["cross_lane_behavior_witness"]["behavior_routing"][
        "visible"
    ] = "sr_to_ps_and_ps_to_sr"
    candidate["cross_lane_behavior_witness"] = _reseal_witness(
        candidate["cross_lane_behavior_witness"]
    )
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e560_behavior_equivalence_authority(
        candidate
    )
    assert validation["valid"] is False
    assert any(
        error.startswith("routing_") for error in validation["errors"]
    )


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e560_rejects_admission_overclaim(
    witness: dict[str, object],
    field: str,
) -> None:
    candidate = copy.deepcopy(witness)
    candidate[field] = True
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e560_behavior_equivalence_authority(
        candidate
    )
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]


def test_e560_without_routing_authority_does_not_open_equivalence(
    witness: dict[str, object],
) -> None:
    contract = build_worldbridge_e538_shared_contracts(
        behavior_equivalence_witness=witness,
    )
    assert contract["contract_valid"] is True
    assert contract["admissions"]["behavior_equivalence_admitted"] is False
    assert "cross_lane_behavior_equivalence" in contract["do_not_claim"]


def test_e538_opens_scoped_equivalence_only_with_both_witnesses(
    behavior_witness: dict[str, object],
    witness: dict[str, object],
) -> None:
    contract = build_worldbridge_e538_shared_contracts(
        cross_lane_behavior_witness=behavior_witness,
        behavior_equivalence_witness=witness,
    )

    assert contract["contract_valid"] is True
    assert contract["admissions"]["cross_lane_behavior_admitted"] is True
    assert contract["admissions"]["behavior_routing_admitted"] is True
    assert contract["admissions"]["behavior_equivalence_admitted"] is True
    assert contract["admissions"]["lossless"] is False
    assert contract["admissions"]["tick_merge_admitted"] is False
    assert contract["admissions"]["default_ready"] is False
    assert "cross_lane_behavior_equivalence" not in contract["do_not_claim"]
    assert (
        "cross_lane_behavior_equivalence_outside_declared_scope"
        in contract["do_not_claim"]
    )


def test_e560_admission_mapping_and_status_expose_scope(
    field_witness: dict[str, object],
    behavior_witness: dict[str, object],
    witness: dict[str, object],
) -> None:
    admission = build_worldbridge_tick_replay_admission(
        cross_lane_behavior_witness=behavior_witness,
        behavior_equivalence_witness=witness,
    )
    evidence = admission["behavior_equivalence_evidence"]
    assert admission["behavior_equivalence_admitted"] is True
    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]
    assert evidence["scope"] == SCOPE
    assert admission["lossless"] is False

    audit = build_worldbridge_mapping_audit(
        field_witness,
        behavior_witness,
        None,
        witness,
    )
    assert audit["behavior_equivalence_admitted"] is True
    assert audit["behavior_equivalence_evidence"]["witness_digest"] == (
        witness["witness_digest"]
    )
    assert "cross_lane_behavior_equivalence" not in audit["do_not_claim"]
    assert audit["lossless"] is False

    status = build_runtime_worldbridge_status(
        field_roundtrip_witness=field_witness,
        cross_lane_behavior_witness=behavior_witness,
        behavior_equivalence_witness=witness,
    )
    assert status["tick_replay_admission"][
        "behavior_equivalence_admitted"
    ] is True
    assert status["mapping_audit"]["behavior_equivalence_admitted"] is True
    assert status["default_ready"] is False
