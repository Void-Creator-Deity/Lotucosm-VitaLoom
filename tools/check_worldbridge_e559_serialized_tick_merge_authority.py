#!/usr/bin/env python3
"""Verify E559 serialized tick merge on real runtime evidence."""
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
from core.Lotucosm.runtime.world_bridge_e559_serialized_tick_merge_authority import (
    PROOF_FIELDS,
    build_worldbridge_e559_serialized_tick_merge_authority,
    validate_worldbridge_e559_serialized_tick_merge_authority,
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
from tools.check_worldbridge_e554_shared_randomness_authority import (
    _trusted_sample_project,
)
import tools.check_worldbridge_e557_field_roundtrip_authority as e557_tool
import tools.check_worldbridge_e558_cross_lane_behavior_authority as e558_tool


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


def _verify_tick_merge(behavior_witness: dict[str, object]) -> dict[str, object]:
    field_witness = behavior_witness["field_roundtrip_witness"]
    replay_witness = field_witness["full_unified_replay_witness"]
    witness = build_worldbridge_e559_serialized_tick_merge_authority(
        full_unified_replay_witness=replay_witness,
        cross_lane_behavior_witness=behavior_witness,
    )
    validation = validate_worldbridge_e559_serialized_tick_merge_authority(
        witness
    )
    _require(
        validation == {"valid": True, "errors": []},
        "E559 witness invalid",
    )
    _require(
        all(witness[field] is True for field in PROOF_FIELDS),
        "E559 did not prove every tick-merge boundary",
    )
    _require(witness["grants_admission"] is False, "E559 granted admission")
    _require(witness["pond_updates_per_frame"] == 1, "E559 PS update count drift")

    contract = build_worldbridge_e538_shared_contracts(
        cross_lane_behavior_witness=behavior_witness,
        serialized_tick_merge_witness=witness,
    )
    _require(
        contract["admissions"]["tick_merge_admitted"] is True,
        "E538 rejected tick merge",
    )
    _require(
        contract["admissions"]["cross_lane_behavior_admitted"] is True,
        "E538 rejected behavior routing",
    )
    _require(
        contract["admissions"]["lossless"] is False,
        "tick merge opened lossless",
    )
    _require(
        contract["admissions"]["default_ready"] is False,
        "tick merge opened default readiness",
    )

    admission = build_worldbridge_tick_replay_admission(
        cross_lane_behavior_witness=behavior_witness,
        serialized_tick_merge_witness=witness,
    )
    _require(admission["tick_merge_admitted"] is True, "tick admission rejected tick merge")
    _require(
        admission["serialized_tick_merge_evidence"]["witness_digest"]
        == witness["witness_digest"],
        "tick admission changed E559 digest",
    )
    _require(admission["lossless"] is False, "tick admission opened lossless")

    audit = build_worldbridge_mapping_audit(
        field_witness,
        behavior_witness,
        witness,
    )
    _require(audit["tick_merge_admitted"] is True, "mapping audit rejected tick merge")
    _require(
        "sr_ps_tick_merge" not in audit["do_not_claim"],
        "mapping audit retained tick-merge exclusion",
    )
    _require(audit["lossless"] is False, "mapping audit opened lossless")

    status = build_runtime_worldbridge_status(
        field_roundtrip_witness=field_witness,
        cross_lane_behavior_witness=behavior_witness,
        serialized_tick_merge_witness=witness,
    )
    _require(
        status["tick_replay_admission"]["tick_merge_admitted"] is True,
        "runtime status rejected tick merge",
    )
    _require(
        status["mapping_audit"]["tick_merge_admitted"] is True,
        "runtime mapping audit rejected tick merge",
    )
    _require(status["default_ready"] is False, "status opened default readiness")

    tampered = copy.deepcopy(witness)
    tampered["tick_owner_evidence"]["dispatcher_begin_count"] = 2
    tampered = _reseal_witness(tampered)
    tampered_validation = (
        validate_worldbridge_e559_serialized_tick_merge_authority(tampered)
    )
    _require(tampered_validation["valid"] is False, "tampered E559 accepted")
    _require(
        "tick_owner_evidence_mismatch" in tampered_validation["errors"],
        "E559 did not diagnose tick-owner tamper",
    )

    return {
        "schema_version": 1,
        "status": "worldbridge_e559_serialized_tick_merge_authority",
        "real_game_viewport": True,
        "read_only": True,
        "tick_merge_policy": witness["tick_merge_policy"],
        "frame_dispatcher_entrypoint": witness["frame_dispatcher_entrypoint"],
        "pond_updates_per_frame": witness["pond_updates_per_frame"],
        "tick_owner_evidence": witness["tick_owner_evidence"],
        "proof": {field: witness[field] for field in PROOF_FIELDS},
        "remaining_tick_merge_blockers": witness[
            "remaining_tick_merge_blockers"
        ],
        "witness_validated": True,
        "witness_digest": witness["witness_digest"],
        "replay_witness_digest": witness["replay_witness_digest"],
        "behavior_witness_digest": witness["behavior_witness_digest"],
        "scheduler_witness_digest": witness["scheduler_witness_digest"],
        "clock_witness_digest": witness["clock_witness_digest"],
        "rng_witness_digest": witness["rng_witness_digest"],
        "tick_merge_admitted": admission["tick_merge_admitted"],
        "cross_lane_behavior_admitted": admission[
            "cross_lane_behavior_admitted"
        ],
        "behavior_equivalence_admitted": False,
        "lossless": admission["lossless"],
        "default_ready": admission["default_ready"],
        "tampered_tick_owner_rejected": True,
        "tampered_errors": tampered_validation["errors"],
        "witness": witness,
        "contract_valid": True,
        "errors": [],
        "ok": True,
    }


def verify() -> dict[str, object]:
    with _trusted_sample_project(ROOT) as e554_project:
        with patch.object(
            e558_tool,
            "_trusted_sample_project",
            lambda _root: nullcontext(e554_project),
        ), patch.object(
            e557_tool,
            "_trusted_sample_project",
            lambda _root: nullcontext(e554_project),
        ), patch(
            "tools.check_worldbridge_e554_shared_randomness_authority."
            "_trusted_sample_project",
            lambda _root: nullcontext(e554_project),
        ):
            e558 = e558_tool.verify()
            return _verify_tick_merge(e558["witness"])


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
