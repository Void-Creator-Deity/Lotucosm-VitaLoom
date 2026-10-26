from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_e557_field_roundtrip_authority import (
    CLOSED_ADMISSION_FIELDS,
    PROOF_FIELDS,
    REMAINING_MAPPING_BLOCKERS,
    build_worldbridge_e557_field_roundtrip_authority,
    validate_worldbridge_e557_field_roundtrip_authority,
)
from core.Lotucosm.runtime.world_bridge_mapping_audit import (
    build_worldbridge_mapping_audit,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from tools.check_worldbridge_e537_field_roundtrip import verify as verify_e537

from test_worldbridge_e556_unified_default_runtime_readiness import prerequisites


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
def witness(prerequisites: dict[str, object]) -> dict[str, object]:
    return build_worldbridge_e557_field_roundtrip_authority(
        field_roundtrip_result=verify_e537(),
        full_unified_replay_witness=prerequisites["replay"],
    )


def test_e557_closes_all_owner_reachable_field_cells(
    witness: dict[str, object],
) -> None:
    assert validate_worldbridge_e557_field_roundtrip_authority(witness) == {
        "valid": True,
        "errors": [],
    }
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["restored_cell_count"] == 27
    assert witness["owner_absent_cells"] == [
        {"field": "hierarchy", "lane": "sr"},
        {"field": "render_identity", "lane": "ps"},
    ]
    assert witness["fail_closed_cells"] == [
        {"field": "scripts", "lane": "sr"}
    ]
    assert witness["remaining_mapping_blockers"] == list(
        REMAINING_MAPPING_BLOCKERS
    )
    assert witness["grants_admission"] is False
    assert witness["admission_effect"] == "none"
    assert all(witness[field] is False for field in CLOSED_ADMISSION_FIELDS)


def test_e557_rejects_unclassified_cell_after_reseal(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["field_roundtrip_result"]["matrix"][0]["verdict"] = "unknown"
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e557_field_roundtrip_authority(candidate)
    assert validation["valid"] is False
    assert "unclassified_field_cells" in validation["errors"]


def test_e557_rejects_aggregate_drift_after_reseal(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["field_roundtrip_result"]["restored_cells"] = 26
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e557_field_roundtrip_authority(candidate)
    assert validation["valid"] is False
    assert "field_aggregate_mismatch" in validation["errors"]


def test_e557_rejects_replay_authority_tamper(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["full_unified_replay_witness"]["trace_count"] += 1
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e557_field_roundtrip_authority(candidate)
    assert validation["valid"] is False
    assert any(error.startswith("replay_") for error in validation["errors"])


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e557_rejects_each_admission_overclaim(
    witness: dict[str, object],
    field: str,
) -> None:
    candidate = copy.deepcopy(witness)
    candidate[field] = True
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e557_field_roundtrip_authority(candidate)
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]


def test_e557_rejects_extra_keys(
    witness: dict[str, object],
) -> None:
    candidate = _reseal_witness({**witness, "unexpected": True})

    validation = validate_worldbridge_e557_field_roundtrip_authority(candidate)
    assert validation["valid"] is False
    assert "witness_keys_invalid" in validation["errors"]


def test_e557_mapping_audit_and_runtime_status_retain_local_closure(
    witness: dict[str, object],
) -> None:
    audit = build_worldbridge_mapping_audit(witness)
    evidence = audit["field_roundtrip_evidence"]
    assert audit["available_field_cells_closed"] is True
    assert audit["lossless"] is False
    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]
    assert evidence["restored_cell_count"] == 27
    assert evidence["remaining_mapping_blockers"] == list(
        REMAINING_MAPPING_BLOCKERS
    )

    status = build_runtime_worldbridge_status(
        field_roundtrip_witness=witness
    )
    status_audit = status["mapping_audit"]
    assert status_audit["available_field_cells_closed"] is True
    assert status_audit["field_roundtrip_evidence"]["witness_digest"] == witness[
        "witness_digest"
    ]
    assert status["default_ready"] is False
