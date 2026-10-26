#!/usr/bin/env python3
"""Verify E558 behavior routing on a real GameViewport and Pond producer."""
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
from core.Lotucosm.runtime.world_bridge_e558_cross_lane_behavior_authority import (
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
from tools.check_worldbridge_e554_shared_randomness_authority import (
    _trusted_sample_project,
)
import tools.check_worldbridge_e557_field_roundtrip_authority as e557_tool


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


def _verify_behavior(field_witness: dict[str, object]) -> dict[str, object]:
    lane_evidence = build_worldbridge_lane_local_roundtrip_evidence()
    witness = build_worldbridge_e558_cross_lane_behavior_authority(
        field_roundtrip_witness=field_witness,
        lane_local_roundtrip_evidence=lane_evidence,
    )
    validation = validate_worldbridge_e558_cross_lane_behavior_authority(
        witness
    )
    _require(
        validation == {"valid": True, "errors": []},
        "E558 witness invalid",
    )
    _require(
        all(witness[field] is True for field in PROOF_FIELDS),
        "E558 did not prove every behavior boundary",
    )
    _require(witness["grants_admission"] is False, "E558 granted admission")

    contract = build_worldbridge_e538_shared_contracts(
        cross_lane_behavior_witness=witness
    )
    _require(
        contract["admissions"]["cross_lane_behavior_admitted"] is True,
        "E538 rejected behavior routing",
    )
    _require(
        contract["admissions"]["behavior_routing_admitted"] is True,
        "E538 rejected behavior routing admission",
    )
    _require(
        contract["admissions"]["behavior_equivalence_admitted"] is False,
        "behavior equivalence opened",
    )
    _require(
        contract["admissions"]["lossless"] is False,
        "behavior witness opened lossless",
    )
    _require(
        contract["admissions"]["tick_merge_admitted"] is False,
        "behavior witness opened tick merge",
    )

    admission = build_worldbridge_tick_replay_admission(
        cross_lane_behavior_witness=witness
    )
    _require(
        admission["cross_lane_behavior_admitted"] is True,
        "tick admission rejected behavior routing",
    )
    _require(
        admission["behavior_routing_admitted"] is True,
        "tick admission omitted behavior routing",
    )
    _require(admission["lossless"] is False, "tick admission opened lossless")
    _require(
        admission["tick_merge_admitted"] is False,
        "tick admission opened tick merge",
    )

    audit = build_worldbridge_mapping_audit(
        field_witness,
        witness,
    )
    _require(
        audit["cross_lane_behavior_admitted"] is True,
        "mapping audit rejected behavior routing",
    )
    _require(audit["lossless"] is False, "mapping audit opened lossless")
    _require(
        audit["behavior_authority_evidence"]["witness_digest"]
        == witness["witness_digest"],
        "mapping audit changed E558 digest",
    )

    status = build_runtime_worldbridge_status(
        field_roundtrip_witness=field_witness,
        cross_lane_behavior_witness=witness,
    )
    _require(
        status["tick_replay_admission"]["cross_lane_behavior_admitted"]
        is True,
        "runtime status rejected behavior routing",
    )
    _require(
        status["mapping_audit"]["cross_lane_behavior_admitted"] is True,
        "runtime mapping audit rejected behavior routing",
    )
    _require(status["default_ready"] is False, "status opened default readiness")

    tampered = copy.deepcopy(witness)
    tampered["lane_local_roundtrip_evidence"]["sr"]["fields"][
        "membrane_attach"
    ]["state"] = "mismatch"
    tampered = _reseal_witness(tampered)
    tampered_validation = (
        validate_worldbridge_e558_cross_lane_behavior_authority(tampered)
    )
    _require(tampered_validation["valid"] is False, "tampered E558 accepted")
    _require(
        "lane_local_admission_mismatch" in tampered_validation["errors"],
        "E558 did not diagnose lane behavior tamper",
    )

    return {
        "schema_version": 1,
        "status": "worldbridge_e558_cross_lane_behavior_authority",
        "real_game_viewport": True,
        "real_ps_membrane_producer": True,
        "read_only": True,
        "behavior_routing": witness["behavior_routing"],
        "proof": {field: witness[field] for field in PROOF_FIELDS},
        "remaining_behavior_blockers": witness[
            "remaining_behavior_blockers"
        ],
        "witness_validated": True,
        "witness_digest": witness["witness_digest"],
        "field_witness_digest": witness["field_witness_digest"],
        "lane_local_digest": witness["lane_local_digest"],
        "membrane_audit_digest": witness["membrane_audit_digest"],
        "cross_lane_behavior_admitted": admission[
            "cross_lane_behavior_admitted"
        ],
        "behavior_routing_admitted": admission[
            "behavior_routing_admitted"
        ],
        "behavior_equivalence_admitted": False,
        "lossless": admission["lossless"],
        "tick_merge_admitted": admission["tick_merge_admitted"],
        "default_ready": admission["default_ready"],
        "tampered_lane_behavior_rejected": True,
        "tampered_errors": tampered_validation["errors"],
        "witness": witness,
        "contract_valid": True,
        "errors": [],
        "ok": True,
    }


def verify() -> dict[str, object]:
    with _trusted_sample_project(ROOT) as e554_project:
        with patch.object(
            e557_tool,
            "_trusted_sample_project",
            lambda _root: nullcontext(e554_project),
        ), patch(
            "tools.check_worldbridge_e554_shared_randomness_authority."
            "_trusted_sample_project",
            lambda _root: nullcontext(e554_project),
        ):
            e557 = e557_tool.verify()
            return _verify_behavior(e557["witness"])


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
