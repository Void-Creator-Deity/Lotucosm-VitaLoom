from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    build_worldbridge_e538_shared_contracts,
)
from core.Lotucosm.runtime.world_bridge_e561_lossless_mapping_authority import (
    CLOSED_ADMISSION_FIELDS,
    FIELD_DISPOSITIONS,
    LOSSLESS_POLICY,
    NONPORTABLE_OWNER_BOUNDARIES,
    PROOF_FIELDS,
    SCOPE,
    build_worldbridge_e561_lossless_mapping_authority,
    validate_worldbridge_e561_lossless_mapping_authority,
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
from test_worldbridge_e560_behavior_equivalence_authority import (
    witness as behavior_equivalence_witness,
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
    field_witness: dict[str, object],
    behavior_equivalence_witness: dict[str, object],
) -> dict[str, object]:
    return build_worldbridge_e561_lossless_mapping_authority(
        field_roundtrip_witness=field_witness,
        behavior_equivalence_witness=behavior_equivalence_witness,
    )


def test_e561_declares_every_field_without_silent_loss(
    witness: dict[str, object],
) -> None:
    assert validate_worldbridge_e561_lossless_mapping_authority(witness) == {
        "valid": True,
        "errors": [],
    }
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["scope"] == SCOPE
    assert witness["lossless_policy"] == LOSSLESS_POLICY
    assert witness["silent_loss_cells"] == []
    assert witness["remaining_lossless_blockers"] == []
    assert witness["nonportable_owner_boundaries"] == list(
        NONPORTABLE_OWNER_BOUNDARIES
    )
    assert witness["portable_checkpoint_lossless"] is False
    assert witness["grants_admission"] is False
    assert witness["admission_effect"] == "none"
    assert all(witness[field] is False for field in CLOSED_ADMISSION_FIELDS)


def test_e561_disposition_matrix_covers_all_declared_fields(
    witness: dict[str, object],
) -> None:
    matrix = witness["field_disposition_matrix"]
    assert len(matrix) == len(FIELD_DISPOSITIONS)
    assert {item["field"] for item in matrix} == set(FIELD_DISPOSITIONS)
    assert {
        item["field"]: item["disposition"] for item in matrix
    } == FIELD_DISPOSITIONS
    cells = {
        (item["field"], lane): lane_data["verdict"]
        for item in matrix
        for lane, lane_data in item["lanes"].items()
    }
    assert cells[("hierarchy", "sr")] == "lane_owner_absent"
    assert cells[("render_identity", "ps")] == "lane_owner_absent"
    assert cells[("scripts", "sr")] == "fail_closed_restore"
    assert sum(value == "restored" for value in cells.values()) == 27


def test_e561_rejects_disposition_tamper(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["field_disposition_matrix"][0]["disposition"] = "silent_drop"
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e561_lossless_mapping_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "field_disposition_matrix_mismatch" in validation["errors"]


def test_e561_rejects_silent_loss_overclaim(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["silent_loss_cells"] = [{"field": "scripts", "lane": "sr"}]
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e561_lossless_mapping_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "silent_loss_cells_mismatch" in validation["errors"]


def test_e561_rejects_portable_script_checkpoint_overclaim(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["portable_checkpoint_lossless"] = True
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e561_lossless_mapping_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "portable_checkpoint_lossless_mismatch" in validation["errors"]


def test_e561_rejects_embedded_field_authority_tamper(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["field_roundtrip_witness"]["restored_cell_count"] = 26
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e561_lossless_mapping_authority(
        candidate
    )
    assert validation["valid"] is False
    assert any(
        error.startswith("field_") for error in validation["errors"]
    )


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e561_rejects_admission_overclaim(
    witness: dict[str, object],
    field: str,
) -> None:
    candidate = copy.deepcopy(witness)
    candidate[field] = True
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e561_lossless_mapping_authority(
        candidate
    )
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]


def test_e538_opens_lossless_mapping_only(
    witness: dict[str, object],
) -> None:
    contract = build_worldbridge_e538_shared_contracts(
        lossless_mapping_witness=witness,
    )

    assert contract["contract_valid"] is True
    assert contract["admissions"]["lossless"] is True
    assert contract["admissions"]["cross_lane_behavior_admitted"] is False
    assert contract["admissions"]["behavior_equivalence_admitted"] is False
    assert contract["admissions"]["tick_merge_admitted"] is False
    assert contract["admissions"]["default_ready"] is False
    assert "lossless_worldbridge_mapping" not in contract["do_not_claim"]
    assert (
        "cross_lane_behavior_equivalence_outside_declared_scope"
        in contract["do_not_claim"]
    )
    assert "portable_sr_executable_script_checkpoint" in contract[
        "do_not_claim"
    ]
    assert "cross_session_script_rehydration" in contract["do_not_claim"]


def test_e561_admission_and_status_expose_lossless_scope(
    field_witness: dict[str, object],
    behavior_witness: dict[str, object],
    behavior_equivalence_witness: dict[str, object],
    witness: dict[str, object],
) -> None:
    admission = build_worldbridge_tick_replay_admission(
        lossless_mapping_witness=witness,
    )
    evidence = admission["lossless_mapping_evidence"]
    assert admission["lossless"] is True
    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]
    assert evidence["portable_checkpoint_lossless"] is False
    assert evidence["scope"] == SCOPE

    audit = build_worldbridge_mapping_audit(
        field_witness,
        behavior_witness,
        None,
        behavior_equivalence_witness,
        witness,
    )
    assert audit["lossless"] is True
    assert audit["lossless_mapping_evidence"]["witness_digest"] == (
        witness["witness_digest"]
    )
    assert "lossless_worldbridge_mapping" not in audit["do_not_claim"]

    status = build_runtime_worldbridge_status(
        field_roundtrip_witness=field_witness,
        cross_lane_behavior_witness=behavior_witness,
        behavior_equivalence_witness=behavior_equivalence_witness,
        lossless_mapping_witness=witness,
    )
    assert status["tick_replay_admission"]["lossless"] is True
    assert status["mapping_audit"]["lossless"] is True
    assert status["default_ready"] is False
