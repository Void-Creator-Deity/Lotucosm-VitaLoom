#!/usr/bin/env python3
"""Verify E561 declared-no-silent-loss mapping on a real GameViewport."""
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
    build_worldbridge_e560_behavior_equivalence_authority,
)
from core.Lotucosm.runtime.world_bridge_e561_lossless_mapping_authority import (
    PROOF_FIELDS,
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


def _verify_lossless(
    behavior_witness: dict[str, object],
) -> dict[str, object]:
    field_witness = behavior_witness["field_roundtrip_witness"]
    behavior_equivalence = (
        build_worldbridge_e560_behavior_equivalence_authority(
            cross_lane_behavior_witness=behavior_witness,
        )
    )
    witness = build_worldbridge_e561_lossless_mapping_authority(
        field_roundtrip_witness=field_witness,
        behavior_equivalence_witness=behavior_equivalence,
    )
    validation = validate_worldbridge_e561_lossless_mapping_authority(witness)
    _require(
        validation == {"valid": True, "errors": []},
        "E561 witness invalid",
    )
    _require(
        all(witness[field] is True for field in PROOF_FIELDS),
        "E561 did not prove every mapping disposition",
    )
    _require(witness["grants_admission"] is False, "E561 granted admission")
    _require(witness["silent_loss_cells"] == [], "E561 found silent loss")
    _require(
        witness["portable_checkpoint_lossless"] is False,
        "E561 overclaimed portable script checkpoint losslessness",
    )

    contract = build_worldbridge_e538_shared_contracts(
        cross_lane_behavior_witness=behavior_witness,
        behavior_equivalence_witness=behavior_equivalence,
        lossless_mapping_witness=witness,
    )
    _require(
        contract["contract_valid"] is True,
        "E538 rejected the E561 contract",
    )
    _require(
        contract["admissions"]["lossless"] is True,
        "E538 rejected lossless mapping",
    )
    _require(
        contract["admissions"]["behavior_equivalence_admitted"] is True,
        "E538 lost the prerequisite behavior authority",
    )
    _require(
        contract["admissions"]["tick_merge_admitted"] is False,
        "E561 opened tick merge",
    )
    _require(
        contract["admissions"]["default_ready"] is False,
        "E561 opened default readiness",
    )
    _require(
        "lossless_worldbridge_mapping" not in contract["do_not_claim"],
        "E538 retained the lossless mapping exclusion",
    )
    _require(
        "portable_sr_executable_script_checkpoint"
        in contract["do_not_claim"],
        "E538 lost the nonportable script boundary",
    )

    admission = build_worldbridge_tick_replay_admission(
        cross_lane_behavior_witness=behavior_witness,
        behavior_equivalence_witness=behavior_equivalence,
        lossless_mapping_witness=witness,
    )
    _require(admission["lossless"] is True, "tick admission rejected E561")
    _require(
        admission["lossless_mapping_evidence"]["portable_checkpoint_lossless"]
        is False,
        "tick admission overclaimed script portability",
    )

    audit = build_worldbridge_mapping_audit(
        field_witness,
        behavior_witness,
        None,
        behavior_equivalence,
        witness,
    )
    _require(
        audit["lossless"] is True,
        "mapping audit rejected E561",
    )
    _require(
        audit["lossless_mapping_evidence"]["witness_digest"]
        == witness["witness_digest"],
        "mapping audit changed the E561 digest",
    )

    status = build_runtime_worldbridge_status(
        field_roundtrip_witness=field_witness,
        cross_lane_behavior_witness=behavior_witness,
        behavior_equivalence_witness=behavior_equivalence,
        lossless_mapping_witness=witness,
    )
    _require(
        status["tick_replay_admission"]["lossless"] is True,
        "runtime status rejected E561",
    )
    _require(
        status["default_ready"] is False,
        "runtime status opened default readiness",
    )

    tampered = copy.deepcopy(witness)
    tampered["field_disposition_matrix"][0]["disposition"] = "silent_drop"
    tampered = _reseal_witness(tampered)
    tampered_validation = (
        validate_worldbridge_e561_lossless_mapping_authority(tampered)
    )
    _require(tampered_validation["valid"] is False, "tampered E561 accepted")
    _require(
        "field_disposition_matrix_mismatch" in tampered_validation["errors"],
        "E561 did not diagnose disposition tamper",
    )

    return {
        "schema_version": 1,
        "status": "worldbridge_e561_lossless_mapping_authority",
        "real_game_viewport": True,
        "read_only": True,
        "scope": witness["scope"],
        "lossless_policy": witness["lossless_policy"],
        "field_disposition_matrix": witness["field_disposition_matrix"],
        "silent_loss_cells": witness["silent_loss_cells"],
        "nonportable_owner_boundaries": witness[
            "nonportable_owner_boundaries"
        ],
        "portable_checkpoint_lossless": witness[
            "portable_checkpoint_lossless"
        ],
        "proof": {field: witness[field] for field in PROOF_FIELDS},
        "remaining_lossless_blockers": witness[
            "remaining_lossless_blockers"
        ],
        "witness_validated": True,
        "witness_digest": witness["witness_digest"],
        "field_witness_digest": witness["field_witness_digest"],
        "behavior_witness_digest": witness["behavior_witness_digest"],
        "lossless_mapping_result_digest": witness[
            "lossless_mapping_result_digest"
        ],
        "lossless": admission["lossless"],
        "tick_merge_admitted": admission["tick_merge_admitted"],
        "default_ready": admission["default_ready"],
        "tampered_disposition_rejected": True,
        "tampered_errors": tampered_validation["errors"],
        "witness": witness,
        "contract_valid": True,
        "errors": [],
        "ok": True,
    }


def verify() -> dict[str, object]:
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
            return _verify_lossless(e558["witness"])


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
