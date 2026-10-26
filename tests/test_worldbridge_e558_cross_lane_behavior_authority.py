from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    build_worldbridge_e538_shared_contracts,
)
from core.Lotucosm.runtime.world_bridge_e558_cross_lane_behavior_authority import (
    CLOSED_ADMISSION_FIELDS,
    PROOF_FIELDS,
    build_worldbridge_e558_cross_lane_behavior_authority,
    validate_worldbridge_e558_cross_lane_behavior_authority,
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
from tools.check_worldbridge_e538_lane_local_roundtrip import (
    build_worldbridge_lane_local_roundtrip_evidence,
)

from test_worldbridge_e557_field_roundtrip_authority import (
    prerequisites,
    witness as field_witness,
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
def witness(field_witness: dict[str, object]) -> dict[str, object]:
    return build_worldbridge_e558_cross_lane_behavior_authority(
        field_roundtrip_witness=field_witness,
        lane_local_roundtrip_evidence=(
            build_worldbridge_lane_local_roundtrip_evidence()
        ),
    )


def test_e558_proves_behavior_routing_without_equivalence(
    witness: dict[str, object],
) -> None:
    assert validate_worldbridge_e558_cross_lane_behavior_authority(witness) == {
        "valid": True,
        "errors": [],
    }
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["behavior_routing"] == {
        "active": "sr_to_ps_and_ps_to_sr",
        "visible": "sr_local_presentation_only",
        "membrane_behavior": "ps_lane_local",
        "sr_scripts": "fail_closed_on_portable_restore",
        "ps_scripts": "lane_local_transaction_restore",
        "hierarchy": "ps_local_restore_with_sr_topology_owner",
    }
    assert witness["remaining_behavior_blockers"] == [
        "behavior_equivalence_not_proven",
        "lossless_mapping_not_proven",
        "sr_ps_tick_merge_not_proven",
    ]
    assert witness["grants_admission"] is False
    assert witness["admission_effect"] == "none"
    assert all(witness[field] is False for field in CLOSED_ADMISSION_FIELDS)


def test_e558_rejects_active_evidence_tamper(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["active_behavior_evidence"]["visible_sr_local"] = False
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e558_cross_lane_behavior_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "active_behavior_evidence_mismatch" in validation["errors"]


def test_e558_rejects_lane_roundtrip_tamper(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["lane_local_roundtrip_evidence"]["sr"]["fields"][
        "membrane_attach"
    ]["state"] = "mismatch"
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e558_cross_lane_behavior_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "lane_local_admission_mismatch" in validation["errors"]


def test_e558_rejects_membrane_audit_tamper(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["membrane_behavior_audit"]["cross_lane_behavior_isolated"] = False
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e558_cross_lane_behavior_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "membrane_behavior_audit_mismatch" in validation["errors"]


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e558_rejects_admission_overclaim(
    witness: dict[str, object],
    field: str,
) -> None:
    candidate = copy.deepcopy(witness)
    candidate[field] = True
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e558_cross_lane_behavior_authority(
        candidate
    )
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]


def test_e558_e538_admission_opens_routing_only(
    witness: dict[str, object],
) -> None:
    baseline = build_worldbridge_e538_shared_contracts()
    contract = build_worldbridge_e538_shared_contracts(
        cross_lane_behavior_witness=witness
    )

    assert contract["admissions"]["cross_lane_behavior_admitted"] is True
    assert contract["admissions"]["behavior_routing_admitted"] is True
    assert contract["admissions"]["lossless"] is False
    assert contract["admissions"]["tick_merge_admitted"] is False
    assert contract["admissions"]["default_ready"] is False
    assert contract["remaining_admission_blockers"] == baseline[
        "remaining_admission_blockers"
    ]
    assert "cross_lane_behavior_equivalence" in contract["do_not_claim"]


def test_e558_admission_and_status_expose_behavior_evidence(
    field_witness: dict[str, object],
    witness: dict[str, object],
) -> None:
    admission = build_worldbridge_tick_replay_admission(
        cross_lane_behavior_witness=witness
    )
    evidence = admission["cross_lane_behavior_evidence"]
    assert admission["cross_lane_behavior_admitted"] is True
    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]
    assert admission["tick_merge_admitted"] is False
    assert admission["lossless"] is False

    audit = build_worldbridge_mapping_audit(
        field_witness,
        witness,
    )
    assert audit["cross_lane_behavior_admitted"] is True
    assert audit["behavior_authority_evidence"]["witness_digest"] == witness[
        "witness_digest"
    ]
    assert audit["lossless"] is False

    status = build_runtime_worldbridge_status(
        field_roundtrip_witness=field_witness,
        cross_lane_behavior_witness=witness,
    )
    assert status["tick_replay_admission"][
        "cross_lane_behavior_admitted"
    ] is True
    assert status["mapping_audit"]["cross_lane_behavior_admitted"] is True
    assert status["default_ready"] is False
