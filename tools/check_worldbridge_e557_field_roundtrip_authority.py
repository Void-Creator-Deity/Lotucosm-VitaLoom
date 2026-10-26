#!/usr/bin/env python3
"""Verify E557 field round-trip authority on a real GameViewport."""
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

from core.Lotucosm.runtime.world_bridge_e557_field_roundtrip_authority import (
    PROOF_FIELDS,
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
from tools.check_worldbridge_e554_shared_randomness_authority import (
    _trusted_sample_project,
)
import tools.check_worldbridge_e555_full_unified_runtime_replay_authority as e555_tool


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


def _verify_with_replay(
    replay_witness: dict[str, object],
) -> dict[str, object]:
    field_result = verify_e537()
    _require(field_result["ok"] is True, "E537 field round-trip failed")
    witness = build_worldbridge_e557_field_roundtrip_authority(
        field_roundtrip_result=field_result,
        full_unified_replay_witness=replay_witness,
    )
    validation = validate_worldbridge_e557_field_roundtrip_authority(witness)
    _require(
        validation == {"valid": True, "errors": []},
        "E557 witness invalid",
    )
    _require(
        all(witness[field] is True for field in PROOF_FIELDS),
        "E557 did not prove every field boundary",
    )
    _require(witness["grants_admission"] is False, "E557 granted admission")

    audit = build_worldbridge_mapping_audit(witness)
    evidence = audit["field_roundtrip_evidence"]
    _require(
        audit["available_field_cells_closed"] is True,
        "mapping audit rejected E557",
    )
    _require(audit["lossless"] is False, "mapping audit opened lossless")
    _require(
        evidence["witness_digest"] == witness["witness_digest"],
        "mapping audit changed E557 digest",
    )

    status = build_runtime_worldbridge_status(
        field_roundtrip_witness=witness
    )
    status_audit = status["mapping_audit"]
    _require(
        status_audit["available_field_cells_closed"] is True,
        "runtime status rejected E557",
    )
    _require(status["default_ready"] is False, "status opened default readiness")

    tampered = copy.deepcopy(witness)
    tampered["field_roundtrip_result"]["restored_cells"] = 26
    tampered = _reseal_witness(tampered)
    tampered_validation = (
        validate_worldbridge_e557_field_roundtrip_authority(tampered)
    )
    _require(tampered_validation["valid"] is False, "tampered E557 accepted")
    _require(
        "field_aggregate_mismatch" in tampered_validation["errors"],
        "E557 did not diagnose aggregate tamper",
    )

    return {
        "schema_version": 1,
        "status": "worldbridge_e557_field_roundtrip_authority",
        "real_game_viewport": True,
        "read_only": True,
        "restored_cell_count": witness["restored_cell_count"],
        "owner_absent_cells": witness["owner_absent_cells"],
        "fail_closed_cells": witness["fail_closed_cells"],
        "capture_required_cells": field_result["capture_required_cells"],
        "capture_restored_cells": field_result["capture_restored_cells"],
        "proof": {field: witness[field] for field in PROOF_FIELDS},
        "remaining_mapping_blockers": witness[
            "remaining_mapping_blockers"
        ],
        "witness_validated": True,
        "witness_digest": witness["witness_digest"],
        "witness": witness,
        "field_result_digest": witness["field_result_digest"],
        "replay_witness_digest": witness["replay_witness_digest"],
        "mapping_audit_closed": audit["available_field_cells_closed"],
        "runtime_status_closed": status_audit[
            "available_field_cells_closed"
        ],
        "lossless": False,
        "cross_lane_behavior_admitted": False,
        "tick_merge_admitted": False,
        "tampered_field_result_rejected": True,
        "tampered_errors": tampered_validation["errors"],
        "contract_valid": True,
        "errors": [],
        "ok": True,
    }


def verify() -> dict[str, object]:
    # Keep the E554 script corpus alive while E555 and E557 revalidate it.
    with _trusted_sample_project(ROOT) as e554_project:
        with patch.object(
            e555_tool,
            "_e554_trusted_sample_project",
            lambda _root: nullcontext(e554_project),
        ), patch(
            "tools.check_worldbridge_e554_shared_randomness_authority."
            "_trusted_sample_project",
            lambda _root: nullcontext(e554_project),
        ):
            e555 = e555_tool.verify()
        return _verify_with_replay(e555["witness"])


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
