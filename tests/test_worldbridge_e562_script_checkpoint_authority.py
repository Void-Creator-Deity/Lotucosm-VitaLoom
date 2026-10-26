from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    build_worldbridge_e538_shared_contracts,
)
from core.Lotucosm.runtime.world_bridge_e562_script_checkpoint_authority import (
    CLOSED_ADMISSION_FIELDS,
    POLICY,
    PROOF_FIELDS,
    SCOPE,
    build_worldbridge_e562_script_checkpoint_authority,
    validate_worldbridge_e562_script_checkpoint_authority,
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


def _raseal(witness: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(witness)
    sealed["witness_digest"] = ""
    sealed["witness_digest"] = _digest(sealed)
    return sealed


def _graph_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "worldbridge_sr_script_checkpoint",
        "policy": "project_source_bound_scene_script_descriptor_v1",
        "runtime_epoch": "epoch-1",
        "entities": [
            {
                "entity_id": "sr:one",
                "scripts": [
                    {
                        "script_type": "probe.Probe",
                        "source_path": "scripts/probe.py",
                        "source_sha256": "a" * 64,
                        "properties": {"value": 1},
                        "runtime_state": {"_counter": 2},
                        "rebound_state_fields": ["owner"],
                    }
                ],
            }
        ],
        "graph_digest": "",
    }


def _graph() -> dict[str, object]:
    graph = _graph_payload()
    digest_value = copy.deepcopy(graph)
    digest_value["graph_digest"] = ""
    graph["graph_digest"] = _digest(digest_value)
    return graph


@pytest.fixture()
def witness() -> dict[str, object]:
    graph = _graph()
    return build_worldbridge_e562_script_checkpoint_authority(
        runtime_epoch="epoch-1",
        source_script_graph=graph,
        restore_result={
            "status": "worldbridge_sr_script_checkpoint_restore",
            "runtime_epoch": "epoch-1",
            "restored_entities": 1,
            "restored_scripts": 1,
        },
        recaptured_script_graph=copy.deepcopy(graph),
    )


def test_e562_proves_source_bound_same_host_script_roundtrip(
    witness: dict[str, object],
) -> None:
    assert validate_worldbridge_e562_script_checkpoint_authority(
        witness
    ) == {"valid": True, "errors": []}
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["scope"] == SCOPE
    assert witness["policy"] == POLICY
    assert witness["remaining_script_blockers"] == [
        "cross_session_script_rehydration_not_proven",
        "arbitrary_external_script_state_not_admitted",
    ]
    assert witness["grants_admission"] is False
    assert all(witness[field] is False for field in CLOSED_ADMISSION_FIELDS)


def test_e562_rejects_descriptor_drift(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["recaptured_script_graph"]["entities"][0]["scripts"][0][
        "runtime_state"
    ]["_counter"] = 3
    candidate = _raseal(candidate)

    validation = validate_worldbridge_e562_script_checkpoint_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "script_descriptors_mismatch" in validation["errors"]


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e562_rejects_admission_overclaim(
    witness: dict[str, object],
    field: str,
) -> None:
    candidate = copy.deepcopy(witness)
    candidate[field] = True
    candidate = _raseal(candidate)

    validation = validate_worldbridge_e562_script_checkpoint_authority(
        candidate
    )
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]


def test_e538_and_status_expose_script_checkpoint_scope_only(
    witness: dict[str, object],
) -> None:
    contract = build_worldbridge_e538_shared_contracts(
        script_checkpoint_witness=witness,
    )
    assert contract["contract_valid"] is True
    assert contract["admissions"]["script_checkpoint_admitted"] is True
    assert contract["admissions"]["lossless"] is False
    assert contract["admissions"]["default_ready"] is False
    assert "portable_sr_executable_script_checkpoint" in contract[
        "do_not_claim"
    ]

    admission = build_worldbridge_tick_replay_admission(
        script_checkpoint_witness=witness,
    )
    assert admission["script_checkpoint_admitted"] is True
    assert admission["lossless"] is False

    audit = build_worldbridge_mapping_audit(
        script_checkpoint_witness=witness,
    )
    assert audit["script_checkpoint_admitted"] is True
    assert audit["script_checkpoint_evidence"]["witness_digest"] == witness[
        "witness_digest"
    ]

    status = build_runtime_worldbridge_status(
        script_checkpoint_witness=witness,
    )
    assert status["tick_replay_admission"]["script_checkpoint_admitted"] is True
    assert status["mapping_audit"]["script_checkpoint_admitted"] is True
    assert status["default_ready"] is False
