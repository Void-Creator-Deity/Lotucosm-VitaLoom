from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    build_worldbridge_e538_shared_contracts,
)
from core.Lotucosm.runtime.world_bridge_e555_full_unified_runtime_replay_authority import (
    CLOSED_ADMISSION_FIELDS,
    PROOF_FIELDS,
    build_worldbridge_e555_full_unified_runtime_replay_authority,
    validate_worldbridge_e555_full_unified_runtime_replay_authority,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from tools.check_worldbridge_e533_capture_binding import verify as verify_e533

from test_worldbridge_e550_pause_reset_error_isolation_authority import (
    _build as _build_e550_witness,
)
from test_worldbridge_e551_scene_pond_checkpoint_authority import (
    _build_witness as _build_e551_witness,
)
from test_worldbridge_e552_shared_clock_delta_authority import (
    _build_witness as _build_e552_witness,
)
from test_worldbridge_e553_scheduler_input_queue_authority import (
    _build_witness as _build_e553_witness,
)
from test_worldbridge_e554_shared_randomness_authority import (
    _build_witness as _build_e554_witness,
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
def prerequisites(tmp_path_factory) -> dict[str, object]:
    with pytest.MonkeyPatch.context() as monkeypatch:
        e554 = _build_e554_witness(
            monkeypatch,
            tmp_path_factory.mktemp("e555-e554"),
        )
    witnesses = {
        "pause_reset_error_isolation_witness": _build_e550_witness(),
        "scene_pond_checkpoint_witness": _build_e551_witness(),
        "shared_clock_delta_witness": _build_e552_witness(),
        "scheduler_input_queue_witness": _build_e553_witness(),
        "shared_randomness_authority_witness": e554,
    }
    contract = build_worldbridge_e538_shared_contracts(**witnesses)
    return {
        **witnesses,
        "contract": contract,
        "artifact": verify_e533()["artifact"],
    }


@pytest.fixture(scope="module")
def witness(prerequisites: dict[str, object]) -> dict[str, object]:
    return build_worldbridge_e555_full_unified_runtime_replay_authority(
        e533_artifact=prerequisites["artifact"],
        shared_contract=prerequisites["contract"],
    )


def test_e555_requires_shared_prerequisites_but_leaves_replay_and_readiness_open(
    prerequisites: dict[str, object],
) -> None:
    contract = prerequisites["contract"]
    assert contract["remaining_admission_blockers"] == [
        "full_unified_runtime_replay_not_proven",
        "unified_default_runtime_readiness_not_proven",
    ]
    assert contract["admissions"]["replay_admitted"] is False
    assert contract["admissions"]["full_unified_replay_admitted"] is False
    assert contract["admissions"]["default_ready"] is False


def test_e555_builds_multi_tick_source_fresh_replay_authority(
    witness: dict[str, object],
) -> None:
    assert validate_worldbridge_e555_full_unified_runtime_replay_authority(
        witness
    ) == {"valid": True, "errors": []}
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["trace_count"] == 4
    assert witness["source_runtime_epoch"] != witness["fresh_runtime_epoch"]
    assert witness["grants_admission"] is False
    assert witness["admission_effect"] == "none"
    assert all(witness[field] is False for field in CLOSED_ADMISSION_FIELDS)
    assert witness["e539_trace"]["all_portable_state_parity"] is True
    assert witness["e539_trace"]["source_fresh_parity_proven"] is True


def test_e555_trace_tamper_is_recomputed_and_rejected(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["e539_trace"]["trace_count"] += 1
    candidate = _reseal_witness(candidate)

    validation = (
        validate_worldbridge_e555_full_unified_runtime_replay_authority(
            candidate
        )
    )
    assert validation["valid"] is False
    assert "e539_trace_recompute_mismatch" in validation["errors"]


def test_e555_artifact_tamper_is_rejected(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["e533_artifact"]["source_capture"]["records"][0]["event"][
        "tick"
    ] += 1
    candidate = _reseal_witness(candidate)

    validation = (
        validate_worldbridge_e555_full_unified_runtime_replay_authority(
            candidate
        )
    )
    assert validation["valid"] is False
    assert any(
        error.startswith("artifact_")
        for error in validation["errors"]
    )


def test_e555_rejects_precondition_contract_overclaim(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["shared_contract"]["admissions"]["replay_admitted"] = True
    candidate = _reseal_witness(candidate)

    validation = (
        validate_worldbridge_e555_full_unified_runtime_replay_authority(
            candidate
        )
    )
    assert validation["valid"] is False
    assert "contract_contract_payload_mismatch" in validation["errors"]


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e555_rejects_each_admission_overclaim(
    witness: dict[str, object],
    field: str,
) -> None:
    candidate = copy.deepcopy(witness)
    candidate[field] = True
    candidate = _reseal_witness(candidate)

    validation = (
        validate_worldbridge_e555_full_unified_runtime_replay_authority(
            candidate
        )
    )
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]


def test_e555_admission_opens_only_full_replay(
    prerequisites: dict[str, object],
    witness: dict[str, object],
) -> None:
    contract = build_worldbridge_e538_shared_contracts(
        pause_reset_error_isolation_witness=prerequisites[
            "pause_reset_error_isolation_witness"
        ],
        scene_pond_checkpoint_witness=prerequisites[
            "scene_pond_checkpoint_witness"
        ],
        shared_clock_delta_witness=prerequisites["shared_clock_delta_witness"],
        scheduler_input_queue_witness=prerequisites[
            "scheduler_input_queue_witness"
        ],
        shared_randomness_authority_witness=prerequisites[
            "shared_randomness_authority_witness"
        ],
        full_unified_replay_witness=witness,
    )

    assert contract["admissions"]["replay_admitted"] is True
    assert contract["admissions"]["full_unified_replay_admitted"] is True
    assert contract["admissions"]["default_ready"] is False
    assert contract["remaining_admission_blockers"] == [
        "unified_default_runtime_readiness_not_proven"
    ]
    assert "full_unified_runtime_replay" not in contract["do_not_claim"]
    assert "unified_pond_default_ready" in contract["do_not_claim"]


def test_e555_invalid_replay_witness_keeps_replay_blocker_closed(
    prerequisites: dict[str, object],
    witness: dict[str, object],
) -> None:
    tampered = copy.deepcopy(witness)
    tampered["witness_digest"] = "0" * 64
    contract = build_worldbridge_e538_shared_contracts(
        pause_reset_error_isolation_witness=prerequisites[
            "pause_reset_error_isolation_witness"
        ],
        scene_pond_checkpoint_witness=prerequisites[
            "scene_pond_checkpoint_witness"
        ],
        shared_clock_delta_witness=prerequisites["shared_clock_delta_witness"],
        scheduler_input_queue_witness=prerequisites[
            "scheduler_input_queue_witness"
        ],
        shared_randomness_authority_witness=prerequisites[
            "shared_randomness_authority_witness"
        ],
        full_unified_replay_witness=tampered,
    )

    assert contract["admissions"]["replay_admitted"] is False
    assert contract["admissions"]["full_unified_replay_admitted"] is False
    assert contract["remaining_admission_blockers"] == [
        "full_unified_runtime_replay_not_proven",
        "unified_default_runtime_readiness_not_proven",
    ]


def test_e555_tick_admission_and_runtime_status_retain_replay_evidence(
    prerequisites: dict[str, object],
    witness: dict[str, object],
) -> None:
    kwargs = {
        "pause_reset_error_isolation_witness": prerequisites[
            "pause_reset_error_isolation_witness"
        ],
        "scene_pond_checkpoint_witness": prerequisites[
            "scene_pond_checkpoint_witness"
        ],
        "shared_clock_delta_authority_witness": prerequisites[
            "shared_clock_delta_witness"
        ],
        "scheduler_input_queue_witness": prerequisites[
            "scheduler_input_queue_witness"
        ],
        "shared_randomness_authority_witness": prerequisites[
            "shared_randomness_authority_witness"
        ],
        "full_unified_replay_witness": witness,
    }
    admission = build_worldbridge_tick_replay_admission(**kwargs)
    assert admission["replay_admitted"] is True
    assert admission["full_unified_replay_admitted"] is True
    assert admission["tick_merge_admitted"] is False
    assert admission["default_ready"] is False
    assert admission["remaining_admission_blockers"] == [
        "unified_default_runtime_readiness_not_proven"
    ]
    evidence = admission["full_unified_replay_evidence"]
    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]

    status = build_runtime_worldbridge_status(**kwargs)
    status_admission = status["tick_replay_admission"]
    assert status_admission["replay_admitted"] is True
    assert status_admission["full_unified_replay_admitted"] is True
    assert status_admission["default_ready"] is False
    assert status_admission["full_unified_replay_evidence"][
        "witness_digest"
    ] == witness["witness_digest"]
