# -*- coding: utf-8 -*-
"""Compose E549 lifecycle and E536 handoff compensation evidence."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:
    from tools._runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e550_pause_reset_error_isolation_authority import (
    FAILURE_PHASES,
    PROOF_FIELDS,
    build_worldbridge_e550_pause_reset_error_isolation_authority,
    validate_worldbridge_e550_pause_reset_error_isolation_authority,
)
from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    PAUSE_RESET_ERROR_ISOLATION_BLOCKER,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from tools.check_worldbridge_e536_live_handoff_transaction import (
    verify as verify_e536,
)
from tools.check_worldbridge_e549_pause_reset_lifecycle_authority import (
    verify as verify_e549,
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _reseal_witness(witness: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(witness)
    sealed["witness_digest"] = ""
    sealed["witness_digest"] = hashlib.sha256(
        json.dumps(
            sealed,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return sealed


def verify() -> dict[str, object]:
    lifecycle = verify_e549()
    failure = verify_e536()
    _require(lifecycle["contract_valid"] is True, "E549 checker failed")
    _require(failure["contract_valid"] is True, "E536 checker failed")
    _require(
        failure["verified_compensation_all_owners"] is True,
        "E536 compensation incomplete",
    )

    witness = build_worldbridge_e550_pause_reset_error_isolation_authority(
        pause_reset_witness=lifecycle["witness"],
        failure_isolation_phases=failure["evidence"],
    )
    _require(
        validate_worldbridge_e550_pause_reset_error_isolation_authority(witness)
        == {"valid": True, "errors": []},
        "E550 witness invalid",
    )
    _require(
        all(witness[field] is True for field in PROOF_FIELDS),
        "E550 did not prove every composed boundary",
    )
    _require(witness["grants_admission"] is False, "E550 granted admission")
    _require(witness["admission_effect"] == "none", "E550 changed effect")

    baseline = build_worldbridge_tick_replay_admission()
    admission = build_worldbridge_tick_replay_admission(
        pause_reset_error_isolation_witness=witness
    )
    evidence = admission["pause_reset_error_isolation_evidence"]
    _require(evidence["validated"] is True, "admission rejected E550")
    _require(evidence["grants_admission"] is False, "E550 granted evidence")
    expected_blockers = [
        blocker
        for blocker in baseline["remaining_admission_blockers"]
        if blocker != PAUSE_RESET_ERROR_ISOLATION_BLOCKER
    ]
    _require(
        admission["remaining_admission_blockers"] == expected_blockers,
        "E550 did not clear exactly the pause/reset blocker",
    )
    pause_requirement = admission["shared_contracts"]["requirements"][
        "shared_pause_reset_error_isolation"
    ]
    _require(
        pause_requirement["capability_admitted"] is True,
        "E550 capability not admitted",
    )
    _require(
        pause_requirement["blocking"] is False,
        "E550 requirement remains blocking",
    )
    _require(
        admission["shared_contracts"]["admissions"][
            "shared_pause_reset_authority"
        ]
        is True,
        "E550 pause/reset admission remains closed",
    )
    _require(
        admission["shared_contracts"]["admissions"][
            "cross_lane_error_isolation_admitted"
        ]
        is True,
        "E550 error isolation admission remains closed",
    )
    _require(
        admission["shared_contracts"]["admissions"][
            "partial_failure_compensation_admitted"
        ]
        is True,
        "E550 compensation admission remains closed",
    )
    _require(admission["tick_merge_admitted"] is False, "tick merge opened")
    _require(
        admission["full_unified_replay_admitted"] is False,
        "full replay opened",
    )
    _require(admission["default_ready"] is False, "default readiness opened")

    status = build_runtime_worldbridge_status(
        pause_reset_error_isolation_witness=witness
    )
    status_evidence = status["tick_replay_admission"][
        "pause_reset_error_isolation_evidence"
    ]
    _require(status_evidence["validated"] is True, "status dropped E550")
    _require(
        status_evidence["witness_digest"] == witness["witness_digest"],
        "status changed E550 digest",
    )
    _require(
        status["tick_replay_admission"]["default_ready"] is False,
        "status opened readiness",
    )

    tampered = copy.deepcopy(witness)
    tampered["failure_isolation_phases"][1]["rollback_report"][
        "rollback_complete"
    ] = False
    tampered["failure_isolation_phases"][1]["failure_receipt"][
        "transaction_rollback"
    ]["rollback_complete"] = False
    tampered = _reseal_witness(tampered)
    tampered_validation = (
        validate_worldbridge_e550_pause_reset_error_isolation_authority(tampered)
    )
    _require(
        tampered_validation["valid"] is False,
        "E550 tampered rollback was accepted",
    )
    _require(
        "pond_update_rollback_incomplete" in tampered_validation["errors"],
        "E550 tampered rollback was not diagnosed",
    )

    return {
        "schema_version": 1,
        "status": "worldbridge_e550_pause_reset_error_isolation_authority",
        "real_game_viewport": True,
        "read_only": True,
        "pause_reset_epochs": [
            lifecycle["pause_reset_epoch_before"],
            lifecycle["pause_reset_epoch_paused"],
            lifecycle["pause_reset_epoch_resumed"],
        ],
        "failure_phase_order": list(FAILURE_PHASES),
        "failure_state_digests": [
            {
                "phase": row["phase"],
                "before": row["before_state_digest"],
                "after": row["after_state_digest"],
                "input_epoch_before": row["input_pause_reset_epoch_before"],
                "input_epoch_after": row["input_pause_reset_epoch_after"],
            }
            for row in witness["failure_isolation_phases"]
        ],
        "proof": {field: witness[field] for field in PROOF_FIELDS},
        "witness_validated": True,
        "witness_digest": witness["witness_digest"],
        "witness": witness,
        "admission_evidence": evidence,
        "runtime_status_evidence_validated": status_evidence["validated"],
        "tampered_rollback_rejected": True,
        "tampered_errors": tampered_validation["errors"],
        "shared_pause_reset_authority": False,
        "cross_lane_error_isolation_admitted": False,
        "shared_pause_reset_authority_admitted": True,
        "cross_lane_error_isolation_capability_admitted": True,
        "partial_failure_compensation_capability_admitted": True,
        "remaining_admission_blockers": admission[
            "remaining_admission_blockers"
        ],
        "atomic_recovery": False,
        "cross_lane_transaction": False,
        "atomic_checkpoint": False,
        "replay_admitted": False,
        "tick_merge_admitted": False,
        "full_unified_replay_admitted": False,
        "default_ready": False,
        "grants_admission": False,
        "admission_effect": "none",
        "contract_valid": True,
        "errors": [],
        "ok": True,
    }


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
