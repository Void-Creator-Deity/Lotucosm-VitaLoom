from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    build_worldbridge_e538_shared_contracts,
)
from core.Lotucosm.runtime.world_bridge_e565_cross_lane_atomic_checkpoint import (
    CLOSED_ADMISSION_FIELDS,
    PROOF_FIELDS,
    validate_worldbridge_e565_cross_lane_atomic_checkpoint_authority,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from tools.check_worldbridge_e565_cross_lane_atomic_checkpoint import (
    verify,
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


def _reseal(witness: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(witness)
    sealed["witness_digest"] = ""
    sealed["witness_digest"] = _digest(sealed)
    return sealed


@pytest.fixture(scope="module")
def evidence() -> dict[str, object]:
    result = verify()
    assert result["ok"] is True
    return result


def test_e565_proves_cross_process_cross_lane_atomic_checkpoint(
    evidence: dict[str, object],
) -> None:
    witness = evidence["witness"]
    assert isinstance(witness, dict)
    assert validate_worldbridge_e565_cross_lane_atomic_checkpoint_authority(
        witness
    ) == {"valid": True, "errors": []}
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["atomic_sr_ps_checkpoint"] is True
    assert witness["cross_lane_restore_admitted"] is True
    assert all(
        witness[field] is False for field in CLOSED_ADMISSION_FIELDS
    )
    assert witness["child_result"]["child_pid"] != witness["child_result"][
        "parent_pid"
    ]


def test_e565_admission_reaches_contract_admission_and_status(
    evidence: dict[str, object],
) -> None:
    witness = evidence["witness"]
    assert isinstance(witness, dict)
    contract = build_worldbridge_e538_shared_contracts(
        cross_lane_atomic_checkpoint_witness=witness,
    )
    assert contract["contract_valid"] is True
    assert contract["admissions"]["atomic_sr_ps_checkpoint_admitted"] is True
    assert "atomic_sr_ps_checkpoint" not in contract["do_not_claim"]
    assert (
        "portable_sr_executable_script_checkpoint"
        in contract["do_not_claim"]
    )

    admission = build_worldbridge_tick_replay_admission(
        cross_lane_atomic_checkpoint_witness=witness,
    )
    assert admission["atomic_sr_ps_checkpoint_admitted"] is True
    assert (
        admission["cross_lane_atomic_checkpoint_evidence"]["witness_digest"]
        == witness["witness_digest"]
    )
    assert admission["default_ready"] is False

    status = build_runtime_worldbridge_status(
        cross_lane_atomic_checkpoint_witness=witness,
    )
    assert status["atomic_sr_ps_checkpoint_admitted"] is True
    assert "atomic_sr_ps_checkpoint" not in status["do_not_claim"]
    assert status["default_ready"] is False


def test_e565_rejects_global_atomicity_overclaim(
    evidence: dict[str, object],
) -> None:
    witness = evidence["witness"]
    assert isinstance(witness, dict)
    candidate = copy.deepcopy(witness)
    candidate["global_cross_process_atomicity"] = True
    candidate = _reseal(candidate)
    validation = (
        validate_worldbridge_e565_cross_lane_atomic_checkpoint_authority(
            candidate
        )
    )
    assert validation["valid"] is False
    assert "global_cross_process_atomicity_overclaim" in validation["errors"]
