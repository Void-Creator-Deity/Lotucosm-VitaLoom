from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    build_worldbridge_e538_shared_contracts,
)
from core.Lotucosm.runtime.world_bridge_e555_full_unified_runtime_replay_authority import (
    build_worldbridge_e555_full_unified_runtime_replay_authority,
)
from core.Lotucosm.runtime.world_bridge_e556_unified_default_runtime_readiness import (
    CLOSED_ADMISSION_FIELDS,
    PROOF_FIELDS,
    build_worldbridge_e556_unified_default_runtime_readiness,
    validate_worldbridge_e556_unified_default_runtime_readiness,
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


def _unified_evidence(replay: dict[str, object]) -> dict[str, object]:
    artifact = replay["e533_artifact"]
    project_binding = artifact["project_binding"]
    record = artifact["source_capture"]["records"][0]
    rng_context_id = record["envelope"]["rng_context_snapshot"]["context_id"]
    receipts = []
    for sequence in (1, 2, 3):
        receipts.append(
            {
                "tick_sequence": sequence,
                "decision_digest": _digest({"decision": sequence}),
                "receipt_digest": _digest({"receipt": sequence}),
                "rng_context_id": rng_context_id,
                "pond_time_before": sequence - 1,
                "pond_time_after": sequence,
            }
        )
    return {
        "project_binding": copy.deepcopy(project_binding),
        "resolved_runtime_mode": "unified_pond",
        "unified_pond_enabled": True,
        "tick_authority_sequence": 3,
        "scheduler_snapshot": {
            "scheduler_owner_id": "game_viewport.input_scheduler",
            "accepted_count": 3,
            "rejected_count": 0,
        },
        "rng_context_id": rng_context_id,
        "native_backend_selection": {
            "selected_backend_id": "python",
            "status": "reference_python",
        },
        "tick_receipts": receipts,
        "fallback_used": False,
        "duplicate_tick_authority_detected": False,
    }


@pytest.fixture(scope="module")
def prerequisites(tmp_path_factory) -> dict[str, object]:
    with pytest.MonkeyPatch.context() as monkeypatch:
        e554 = _build_e554_witness(
            monkeypatch,
            tmp_path_factory.mktemp("e556-e554"),
        )
    witnesses = {
        "pause_reset_error_isolation_witness": _build_e550_witness(),
        "scene_pond_checkpoint_witness": _build_e551_witness(),
        "shared_clock_delta_witness": _build_e552_witness(),
        "scheduler_input_queue_witness": _build_e553_witness(),
        "shared_randomness_authority_witness": e554,
    }
    contract = build_worldbridge_e538_shared_contracts(**witnesses)
    replay = build_worldbridge_e555_full_unified_runtime_replay_authority(
        e533_artifact=verify_e533()["artifact"],
        shared_contract=contract,
    )
    return {
        **witnesses,
        "contract": contract,
        "replay": replay,
    }


@pytest.fixture(scope="module")
def witness(prerequisites: dict[str, object]) -> dict[str, object]:
    return build_worldbridge_e556_unified_default_runtime_readiness(
        full_unified_replay_witness=prerequisites["replay"],
        unified_mode_evidence=_unified_evidence(prerequisites["replay"]),
    )


def test_e556_ready_default_is_explicit_unified_not_implicit(
    witness: dict[str, object],
) -> None:
    assert validate_worldbridge_e556_unified_default_runtime_readiness(
        witness
    ) == {"valid": True, "errors": []}
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["live_tick_count"] == 3
    assert witness["tick_sequences"] == [1, 2, 3]
    assert witness["runtime_mode_policy"]["samples"]["default_mode"] == {
        "resolved_mode": "dual",
        "unified_enabled": False,
    }
    assert witness["runtime_mode_policy"]["samples"]["explicit_unified"] == {
        "resolved_mode": "unified_pond",
        "unified_enabled": True,
    }
    assert witness["grants_admission"] is False
    assert witness["admission_effect"] == "none"
    assert all(witness[field] is False for field in CLOSED_ADMISSION_FIELDS)


def test_e556_rejects_tick_gap_after_reseal(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["unified_mode_evidence"]["tick_receipts"][1]["tick_sequence"] = 3
    candidate = _reseal_witness(candidate)

    validation = (
        validate_worldbridge_e556_unified_default_runtime_readiness(candidate)
    )
    assert validation["valid"] is False
    assert "tick_sequence_not_continuous" in validation["errors"]


def test_e556_rejects_policy_tamper_after_reseal(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["runtime_mode_policy"]["samples"]["default_mode"][
        "unified_enabled"
    ] = True
    candidate = _reseal_witness(candidate)

    validation = (
        validate_worldbridge_e556_unified_default_runtime_readiness(candidate)
    )
    assert validation["valid"] is False
    assert "runtime_mode_policy_mismatch" in validation["errors"]


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e556_rejects_each_admission_overclaim(
    witness: dict[str, object],
    field: str,
) -> None:
    candidate = copy.deepcopy(witness)
    candidate[field] = True
    candidate = _reseal_witness(candidate)

    validation = (
        validate_worldbridge_e556_unified_default_runtime_readiness(candidate)
    )
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]


def test_e556_full_admission_closes_default_readiness_only(
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
        full_unified_replay_witness=prerequisites["replay"],
        unified_default_runtime_readiness_witness=witness,
    )

    assert contract["admissions"]["default_ready"] is True
    assert contract["remaining_admission_blockers"] == []
    assert "unified_pond_default_ready" not in contract["do_not_claim"]
    assert contract["admissions"]["tick_merge_admitted"] is False
    assert contract["admissions"]["cross_lane_behavior_admitted"] is False
    assert contract["admissions"]["lossless"] is False


def test_e556_invalid_readiness_keeps_default_blocker(
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
        full_unified_replay_witness=prerequisites["replay"],
        unified_default_runtime_readiness_witness=tampered,
    )

    assert contract["admissions"]["default_ready"] is False
    assert contract["remaining_admission_blockers"] == [
        "unified_default_runtime_readiness_not_proven"
    ]


def test_e556_tick_admission_and_status_expose_final_readiness(
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
        "full_unified_replay_witness": prerequisites["replay"],
        "unified_default_runtime_readiness_witness": witness,
    }
    admission = build_worldbridge_tick_replay_admission(**kwargs)
    assert admission["default_ready"] is True
    assert admission["replay_admitted"] is True
    assert admission["full_unified_replay_admitted"] is True
    assert admission["tick_merge_admitted"] is False
    assert admission["remaining_admission_blockers"] == []
    evidence = admission["unified_default_runtime_readiness_evidence"]
    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]

    status = build_runtime_worldbridge_status(**kwargs)
    status_admission = status["tick_replay_admission"]
    assert status_admission["default_ready"] is True
    assert status_admission["replay_admitted"] is True
    assert status_admission["unified_default_runtime_readiness_evidence"][
        "witness_digest"
    ] == witness["witness_digest"]
    assert status["e538_shared_contracts"]["remaining_admission_blockers"] == []
