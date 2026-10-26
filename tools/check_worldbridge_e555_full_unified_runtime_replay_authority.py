#!/usr/bin/env python3
"""Verify E555 full unified runtime replay on real GameViewport evidence."""
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
from core.Lotucosm.runtime.world_bridge_e555_full_unified_runtime_replay_authority import (
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
from tools.check_worldbridge_e550_pause_reset_error_isolation_authority import (
    verify as verify_e550,
)
from tools.check_worldbridge_e551_scene_pond_checkpoint_authority import (
    verify as verify_e551,
)
from tools.check_worldbridge_e552_shared_clock_delta_authority import (
    verify as verify_e552,
)
from tools.check_worldbridge_e553_scheduler_input_queue_authority import (
    verify as verify_e553,
)
from tools.check_worldbridge_e554_shared_randomness_authority import (
    _trusted_sample_project as _e554_trusted_sample_project,
)
from tools.check_worldbridge_e554_shared_randomness_authority import (
    verify as verify_e554,
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


def _verify_after_e554(e554: dict[str, object]) -> dict[str, object]:
    e550 = verify_e550()
    e551 = verify_e551()
    e552 = verify_e552()
    e553 = verify_e553()
    e533 = verify_e533()
    for label, result in (
        ("E550", e550),
        ("E551", e551),
        ("E552", e552),
        ("E553", e553),
        ("E554", e554),
        ("E533", e533),
    ):
        _require(result["ok"] is True if "ok" in result else result["contract_valid"] is True, f"{label} prerequisite failed")

    prerequisites = build_worldbridge_e538_shared_contracts(
        pause_reset_error_isolation_witness=e550["witness"],
        scene_pond_checkpoint_witness=e551["witness"],
        shared_clock_delta_witness=e552["witness"],
        scheduler_input_queue_witness=e553["witness"],
        shared_randomness_authority_witness=e554["witness"],
    )
    _require(
        prerequisites["remaining_admission_blockers"]
        == [
            "full_unified_runtime_replay_not_proven",
            "unified_default_runtime_readiness_not_proven",
        ],
        "E555 prerequisite blockers are not exact: "
        + repr(prerequisites["remaining_admission_blockers"]),
    )

    witness = build_worldbridge_e555_full_unified_runtime_replay_authority(
        e533_artifact=e533["artifact"],
        shared_contract=prerequisites,
    )
    validation = (
        validate_worldbridge_e555_full_unified_runtime_replay_authority(witness)
    )
    _require(
        validation == {"valid": True, "errors": []},
        "E555 witness invalid",
    )
    _require(
        all(witness[field] is True for field in PROOF_FIELDS),
        "E555 did not prove every replay boundary",
    )
    _require(witness["trace_count"] >= 3, "E555 trace is too short")
    _require(witness["grants_admission"] is False, "E555 granted admission")

    full_contract = build_worldbridge_e538_shared_contracts(
        pause_reset_error_isolation_witness=e550["witness"],
        scene_pond_checkpoint_witness=e551["witness"],
        shared_clock_delta_witness=e552["witness"],
        scheduler_input_queue_witness=e553["witness"],
        shared_randomness_authority_witness=e554["witness"],
        full_unified_replay_witness=witness,
    )
    _require(
        full_contract["admissions"]["replay_admitted"] is True,
        "E555 did not admit replay",
    )
    _require(
        full_contract["admissions"]["full_unified_replay_admitted"] is True,
        "E555 did not admit full replay",
    )
    _require(
        full_contract["remaining_admission_blockers"]
        == ["unified_default_runtime_readiness_not_proven"],
        "E555 removed more than the replay blocker",
    )
    _require(
        full_contract["admissions"]["default_ready"] is False,
        "E555 opened default readiness",
    )

    admission = build_worldbridge_tick_replay_admission(
        pause_reset_error_isolation_witness=e550["witness"],
        scene_pond_checkpoint_witness=e551["witness"],
        shared_clock_delta_authority_witness=e552["witness"],
        scheduler_input_queue_witness=e553["witness"],
        shared_randomness_authority_witness=e554["witness"],
        full_unified_replay_witness=witness,
    )
    _require(admission["replay_admitted"] is True, "tick admission rejected replay")
    _require(
        admission["full_unified_replay_admitted"] is True,
        "tick admission rejected full replay",
    )
    _require(admission["tick_merge_admitted"] is False, "tick merge opened")
    _require(admission["default_ready"] is False, "default readiness opened")

    status = build_runtime_worldbridge_status(
        pause_reset_error_isolation_witness=e550["witness"],
        scene_pond_checkpoint_witness=e551["witness"],
        shared_clock_delta_authority_witness=e552["witness"],
        scheduler_input_queue_witness=e553["witness"],
        shared_randomness_authority_witness=e554["witness"],
        full_unified_replay_witness=witness,
    )
    status_admission = status["tick_replay_admission"]
    _require(status_admission["replay_admitted"] is True, "status rejected replay")
    _require(
        status_admission["full_unified_replay_evidence"]["witness_digest"]
        == witness["witness_digest"],
        "status changed E555 digest",
    )
    _require(status_admission["default_ready"] is False, "status opened readiness")

    tampered = copy.deepcopy(witness)
    tampered["e539_trace"]["trace_count"] += 1
    tampered = _reseal_witness(tampered)
    tampered_validation = (
        validate_worldbridge_e555_full_unified_runtime_replay_authority(tampered)
    )
    _require(tampered_validation["valid"] is False, "tampered E555 accepted")
    _require(
        "e539_trace_recompute_mismatch" in tampered_validation["errors"],
        "E555 did not diagnose trace tamper",
    )

    return {
        "schema_version": 1,
        "status": "worldbridge_e555_full_unified_runtime_replay_authority",
        "real_game_viewport_pair": True,
        "read_only": True,
        "trace_count": witness["trace_count"],
        "pair_id": witness["e533_artifact"]["pair_id"],
        "artifact_digest": witness["artifact_digest"],
        "shared_contract_digest": witness["shared_contract_digest"],
        "trace_digest": witness["trace_digest"],
        "source_runtime_epoch": witness["source_runtime_epoch"],
        "fresh_runtime_epoch": witness["fresh_runtime_epoch"],
        "relative_ticks": [
            [record["source_relative_tick"], record["fresh_relative_tick"]]
            for record in witness["e539_trace"]["tick_records"]
        ],
        "proof": {field: witness[field] for field in PROOF_FIELDS},
        "witness_validated": True,
        "witness_digest": witness["witness_digest"],
        "witness": witness,
        "prerequisites": {
            "pause_reset_error_isolation_witness": e550["witness"],
            "scene_pond_checkpoint_witness": e551["witness"],
            "shared_clock_delta_witness": e552["witness"],
            "scheduler_input_queue_witness": e553["witness"],
            "shared_randomness_authority_witness": e554["witness"],
        },
        "replay_admitted": admission["replay_admitted"],
        "full_unified_replay_admitted": admission[
            "full_unified_replay_admitted"
        ],
        "tick_merge_admitted": admission["tick_merge_admitted"],
        "default_ready": admission["default_ready"],
        "remaining_admission_blockers": admission[
            "remaining_admission_blockers"
        ],
        "tampered_trace_rejected": True,
        "tampered_errors": tampered_validation["errors"],
        "contract_valid": True,
        "errors": [],
        "ok": True,
    }


def verify() -> dict[str, object]:
    # E554 revalidates the dynamic-script source corpus. Keep its trusted
    # project alive until the composed E555 witness has been validated.
    with _e554_trusted_sample_project(ROOT) as project:
        with patch(
            "tools.check_worldbridge_e554_shared_randomness_authority."
            "_trusted_sample_project",
            lambda _root: nullcontext(project),
        ):
            e554 = verify_e554()
        return _verify_after_e554(e554)


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
