#!/usr/bin/env python3
"""Verify scoped E560 behavior equivalence on production lane owners."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:
    from tools._runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    build_worldbridge_e538_shared_contracts,
)
from core.Lotucosm.runtime.world_bridge_e560_behavior_equivalence_authority import (
    PROOF_FIELDS,
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
import tools.check_worldbridge_e558_cross_lane_behavior_authority as e558_tool
from tools.check_worldbridge_e554_shared_randomness_authority import (
    _trusted_sample_project,
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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


def _verify_equivalence(
    behavior_witness: dict[str, object],
) -> dict[str, object]:
    witness = build_worldbridge_e560_behavior_equivalence_authority(
        cross_lane_behavior_witness=behavior_witness,
    )
    validation = validate_worldbridge_e560_behavior_equivalence_authority(
        witness
    )
    _require(
        validation == {"valid": True, "errors": []},
        "E560 witness invalid",
    )
    _require(
        all(witness[field] is True for field in PROOF_FIELDS),
        "E560 did not prove the declared behavior overlap",
    )
    _require(witness["grants_admission"] is False, "E560 granted admission")

    contract = build_worldbridge_e538_shared_contracts(
        cross_lane_behavior_witness=behavior_witness,
        behavior_equivalence_witness=witness,
    )
    _require(
        contract["contract_valid"] is True,
        "E538 rejected the E560 contract",
    )
    _require(
        contract["admissions"]["behavior_equivalence_admitted"] is True,
        "E538 rejected scoped behavior equivalence",
    )
    _require(
        "cross_lane_behavior_equivalence" not in contract["do_not_claim"],
        "E538 retained the scoped equivalence exclusion",
    )
    _require(
        "cross_lane_behavior_equivalence_outside_declared_scope"
        in contract["do_not_claim"],
        "E538 lost the outside-scope exclusion",
    )
    _require(
        contract["admissions"]["lossless"] is False,
        "E560 opened lossless mapping",
    )

    admission = build_worldbridge_tick_replay_admission(
        cross_lane_behavior_witness=behavior_witness,
        behavior_equivalence_witness=witness,
    )
    _require(
        admission["behavior_equivalence_admitted"] is True,
        "tick admission rejected scoped behavior equivalence",
    )
    _require(
        admission["lossless"] is False,
        "tick admission opened lossless mapping",
    )

    field_witness = behavior_witness["field_roundtrip_witness"]
    audit = build_worldbridge_mapping_audit(
        field_witness,
        behavior_witness,
        None,
        witness,
    )
    _require(
        audit["behavior_equivalence_admitted"] is True,
        "mapping audit rejected scoped behavior equivalence",
    )
    _require(
        audit["behavior_equivalence_evidence"]["witness_digest"]
        == witness["witness_digest"],
        "mapping audit changed the E560 digest",
    )
    _require(
        audit["lossless"] is False,
        "mapping audit opened lossless mapping",
    )

    status = build_runtime_worldbridge_status(
        field_roundtrip_witness=field_witness,
        cross_lane_behavior_witness=behavior_witness,
        behavior_equivalence_witness=witness,
    )
    _require(
        status["tick_replay_admission"]["behavior_equivalence_admitted"]
        is True,
        "runtime status rejected scoped behavior equivalence",
    )
    _require(
        status["default_ready"] is False,
        "runtime status opened default readiness",
    )

    tampered = copy.deepcopy(witness)
    tampered["behavior_equivalence_evidence"]["active_gate_cases"][
        "sr_inactive"
    ]["observed"] = 1
    tampered = _reseal_witness(tampered)
    tampered_validation = (
        validate_worldbridge_e560_behavior_equivalence_authority(tampered)
    )
    _require(tampered_validation["valid"] is False, "tampered E560 accepted")
    _require(
        "behavior_equivalence_evidence_mismatch"
        in tampered_validation["errors"],
        "E560 did not diagnose gate-evidence tamper",
    )

    evidence = witness["behavior_equivalence_evidence"]
    return {
        "schema_version": 1,
        "status": "worldbridge_e560_behavior_equivalence_authority",
        "real_game_viewport_routing": True,
        "real_sr_ps_gate_producers": True,
        "read_only": True,
        "scope": witness["scope"],
        "equivalence_policy": witness["equivalence_policy"],
        "eligible_behavior_routes": witness["eligible_behavior_routes"],
        "lane_local_behavior_routes": witness[
            "lane_local_behavior_routes"
        ],
        "active_roundtrip_cases": evidence["active_roundtrip_cases"],
        "active_gate_cases": evidence["active_gate_cases"],
        "proof": {field: witness[field] for field in PROOF_FIELDS},
        "remaining_behavior_blockers": witness[
            "remaining_behavior_blockers"
        ],
        "witness_validated": True,
        "witness_digest": witness["witness_digest"],
        "routing_witness_digest": witness["routing_witness_digest"],
        "equivalence_result_digest": witness["equivalence_result_digest"],
        "behavior_equivalence_admitted": admission[
            "behavior_equivalence_admitted"
        ],
        "lossless": admission["lossless"],
        "tick_merge_admitted": admission["tick_merge_admitted"],
        "default_ready": admission["default_ready"],
        "tampered_gate_evidence_rejected": True,
        "tampered_errors": tampered_validation["errors"],
        "witness": witness,
        "contract_valid": True,
        "errors": [],
        "ok": True,
    }


def verify() -> dict[str, object]:
    # E554 revalidates dynamic-script inventory and E560 revalidates the whole
    # E558/E555/E554 chain. Keep one trusted project alive until both checks
    # have completed; releasing it between producers would invalidate paths.
    with _trusted_sample_project(ROOT) as project:
        with patch.object(
            e558_tool,
            "_trusted_sample_project",
            lambda _root: nullcontext(project),
        ), patch(
            "tools.check_worldbridge_e554_shared_randomness_authority."
            "_trusted_sample_project",
            lambda _root: nullcontext(project),
        ):
            e558 = e558_tool.verify()
            return _verify_equivalence(e558["witness"])


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
