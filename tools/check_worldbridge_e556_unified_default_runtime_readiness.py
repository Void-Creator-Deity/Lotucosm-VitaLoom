#!/usr/bin/env python3
"""Verify E556 explicit-unified runtime readiness on a real GameViewport."""
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

from PyQt6 import sip
from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtWidgets import QApplication

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
)
from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    build_worldbridge_e538_shared_contracts,
)
from core.Lotucosm.runtime.world_bridge_e556_unified_default_runtime_readiness import (
    PROOF_FIELDS,
    build_worldbridge_e556_unified_default_runtime_readiness,
    validate_worldbridge_e556_unified_default_runtime_readiness,
)
from core.Lotucosm.runtime.world_bridge_native_entropy_audit import (
    build_native_backend_selection_evidence,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.scene import get_scene_manager
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from core.VitaLoom.viewports.game_viewport import GameViewport
from tools.check_worldbridge_e554_shared_randomness_authority import (
    _trusted_sample_project,
)
from tools.check_worldbridge_e533_capture_binding import _project_binding
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


def _new_explicit_unified_viewport(project: Path, scene: Path) -> GameViewport:
    scene_manager = get_scene_manager()
    scene_manager.clear_scene(notify=False)
    viewport = GameViewport()
    viewport.editor_context.current_project_path = str(project)
    _require(scene_manager.load_scene(str(scene)), "E556 scene load failed")
    viewport._using_scene_runtime = True
    viewport._sr_runtime_scene_path = str(scene)
    _require(
        isinstance(viewport._begin_sr_snapshot_lifetime(), str),
        "E556 SR runtime epoch missing",
    )
    _require(
        viewport._load_scene_runtime_entities(),
        "E556 SR runtime load failed",
    )
    viewport._refresh_unified_pond_mode({"runtime_mode": "unified_pond"})
    _require(
        viewport._unified_pond_mode is True,
        "E556 explicit unified mode did not enter",
    )
    viewport.set_worldbridge_opt_in_deterministic_randomness_context(
        create_worldbridge_deterministic_randomness_context(
            "e556-unified-readiness-context",
            "e556-unified-readiness-root",
        )
    )
    viewport._ensure_unified_pond()
    viewport.is_playing = True
    viewport.is_paused = False
    return viewport


def _capture_unified_mode(
    project: Path,
    scene: Path,
    replay_witness: dict[str, object],
) -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    viewport = _new_explicit_unified_viewport(project, scene)
    try:
        viewport._sr_input_press("W")
        viewport._sr_input_release("W")
        receipts: list[dict[str, object]] = []
        for _ in range(3):
            before = int(viewport._unified_pond.time)
            viewport._update_simulation()
            receipt = viewport._worldbridge_last_tick_receipt
            _require(isinstance(receipt, dict), "E556 receipt missing")
            _require(receipt.get("tick_sequence") == len(receipts) + 1, "E556 tick gap")
            after = int(viewport._unified_pond.time)
            receipts.append(
                {
                    "tick_sequence": receipt["tick_sequence"],
                    "decision_digest": receipt["clock_decision"][
                        "decision_digest"
                    ],
                    "receipt_digest": receipt["receipt_digest"],
                    "rng_context_id": receipt["rng_context_id"],
                    "pond_time_before": before,
                    "pond_time_after": after,
                }
            )
        authority = viewport._worldbridge_tick_authority
        queue = viewport._worldbridge_input_sequence
        scheduler = queue.scheduler_snapshot()
        rng_context = viewport._worldbridge_opt_in_deterministic_randomness_context
        physics = viewport._sr_physics_world
        _require(physics is not None, "E556 physics backend missing")
        backend_selection = build_native_backend_selection_evidence(
            physics.backend_capability(),
            requested_backend=str(viewport._sr2d_backend_request),
        )
        project_binding = _project_binding(project, scene)
        evidence = {
            "project_binding": copy.deepcopy(project_binding),
            "resolved_runtime_mode": "unified_pond",
            "unified_pond_enabled": viewport._unified_pond_mode,
            "tick_authority_sequence": authority.tick_sequence,
            "scheduler_snapshot": scheduler,
            "rng_context_id": rng_context.context_id,
            "native_backend_selection": backend_selection,
            "tick_receipts": receipts,
            "fallback_used": False,
            "duplicate_tick_authority_detected": False,
        }
        _require(
            authority.tick_sequence == receipts[-1]["tick_sequence"],
            "E556 duplicate tick authority observed",
        )
        _require(
            all(
                row["pond_time_after"] == row["pond_time_before"] + 1
                for row in receipts
            ),
            "E556 Pond did not advance once per tick",
        )
        return evidence
    finally:
        viewport.deleteLater()
        QCoreApplication.sendPostedEvents(viewport, QEvent.Type.DeferredDelete)
        app.processEvents()
        if not sip.isdeleted(viewport):
            raise AssertionError("E556 viewport cleanup incomplete")


def _verify_readiness(
    e555: dict[str, object],
    project: Path,
    scene: Path,
) -> dict[str, object]:
    replay_witness = e555["witness"]
    unified_mode = _capture_unified_mode(project, scene, replay_witness)
    witness = build_worldbridge_e556_unified_default_runtime_readiness(
        full_unified_replay_witness=replay_witness,
        unified_mode_evidence=unified_mode,
    )
    validation = (
        validate_worldbridge_e556_unified_default_runtime_readiness(witness)
    )
    _require(
        validation == {"valid": True, "errors": []},
        "E556 witness invalid",
    )
    _require(
        all(witness[field] is True for field in PROOF_FIELDS),
        "E556 did not prove every readiness boundary",
    )
    _require(witness["grants_admission"] is False, "E556 granted admission")

    prerequisites = e555["prerequisites"]
    contract = build_worldbridge_e538_shared_contracts(
        **prerequisites,
        full_unified_replay_witness=replay_witness,
        unified_default_runtime_readiness_witness=witness,
    )
    _require(contract["admissions"]["default_ready"] is True, "E556 did not admit default readiness")
    _require(contract["remaining_admission_blockers"] == [], "E556 left admission blockers")
    _require(contract["admissions"]["lossless"] is False, "E556 opened lossless")
    _require(contract["admissions"]["tick_merge_admitted"] is False, "E556 opened tick merge")

    admission = build_worldbridge_tick_replay_admission(
        pause_reset_error_isolation_witness=prerequisites[
            "pause_reset_error_isolation_witness"
        ],
        scene_pond_checkpoint_witness=prerequisites[
            "scene_pond_checkpoint_witness"
        ],
        shared_clock_delta_authority_witness=prerequisites[
            "shared_clock_delta_witness"
        ],
        scheduler_input_queue_witness=prerequisites[
            "scheduler_input_queue_witness"
        ],
        shared_randomness_authority_witness=prerequisites[
            "shared_randomness_authority_witness"
        ],
        full_unified_replay_witness=replay_witness,
        unified_default_runtime_readiness_witness=witness,
    )
    _require(admission["default_ready"] is True, "tick admission rejected readiness")
    _require(admission["replay_admitted"] is True, "tick admission rejected replay")
    _require(admission["tick_merge_admitted"] is False, "tick merge opened")

    status = build_runtime_worldbridge_status(
        pause_reset_error_isolation_witness=prerequisites[
            "pause_reset_error_isolation_witness"
        ],
        scene_pond_checkpoint_witness=prerequisites[
            "scene_pond_checkpoint_witness"
        ],
        shared_clock_delta_authority_witness=prerequisites[
            "shared_clock_delta_witness"
        ],
        scheduler_input_queue_witness=prerequisites[
            "scheduler_input_queue_witness"
        ],
        shared_randomness_authority_witness=prerequisites[
            "shared_randomness_authority_witness"
        ],
        full_unified_replay_witness=replay_witness,
        unified_default_runtime_readiness_witness=witness,
    )
    status_admission = status["tick_replay_admission"]
    _require(status_admission["default_ready"] is True, "status rejected readiness")
    _require(
        status_admission["unified_default_runtime_readiness_evidence"][
            "witness_digest"
        ]
        == witness["witness_digest"],
        "status changed E556 digest",
    )

    tampered = copy.deepcopy(witness)
    tampered["unified_mode_evidence"]["tick_receipts"][1][
        "tick_sequence"
    ] = 9
    tampered = _reseal_witness(tampered)
    tampered_validation = (
        validate_worldbridge_e556_unified_default_runtime_readiness(tampered)
    )
    _require(tampered_validation["valid"] is False, "tampered E556 accepted")
    _require(
        "tick_sequence_not_continuous" in tampered_validation["errors"],
        "E556 did not diagnose tick tamper",
    )

    return {
        "schema_version": 1,
        "status": "worldbridge_e556_unified_default_runtime_readiness",
        "real_game_viewport": True,
        "read_only": True,
        "live_tick_count": witness["live_tick_count"],
        "tick_sequences": witness["tick_sequences"],
        "project_binding_digest": witness["project_binding_digest"],
        "policy_samples": witness["runtime_mode_policy"]["samples"],
        "proof": {field: witness[field] for field in PROOF_FIELDS},
        "witness_validated": True,
        "witness_digest": witness["witness_digest"],
        "replay_witness_digest": replay_witness["witness_digest"],
        "default_ready": admission["default_ready"],
        "replay_admitted": admission["replay_admitted"],
        "tick_merge_admitted": admission["tick_merge_admitted"],
        "lossless": contract["admissions"]["lossless"],
        "remaining_admission_blockers": admission[
            "remaining_admission_blockers"
        ],
        "tampered_tick_rejected": True,
        "tampered_errors": tampered_validation["errors"],
        "witness": witness,
        "contract_valid": True,
        "errors": [],
        "ok": True,
    }


def verify() -> dict[str, object]:
    project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    scene = project / "scenes" / "challenge_scene.pond"
    # Keep the E554 script corpus alive while E555 and E556 revalidate it.
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
        return _verify_readiness(e555, project, scene)


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
