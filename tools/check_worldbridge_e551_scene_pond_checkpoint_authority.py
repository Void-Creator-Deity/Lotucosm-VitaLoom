# -*- coding: utf-8 -*-
"""Verify E551 atomic checkpoint capture and fresh-host parity."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import threading
import time
from pathlib import Path

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

from core.Lotucosm.runtime.world_bridge_e551_scene_pond_checkpoint_authority import (
    PROOF_FIELDS,
    build_worldbridge_e551_scene_pond_checkpoint_authority,
    validate_worldbridge_e551_scene_pond_checkpoint_authority,
)
from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    SCENE_POND_CHECKPOINT_BLOCKER,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from tools.check_worldbridge_e505_fresh_host_reconstruction import (
    _new_viewport,
    verify as verify_e505,
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


def _atomic_capture_probe(project: Path, scene: Path) -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    viewport = _new_viewport(project, scene, "e551-atomic-probe")
    try:
        viewport._update_simulation()
        gate = viewport._worldbridge_gate_handle()
        original_locked = viewport._capture_worldbridge_live_checkpoint_locked
        first_entered = threading.Event()
        second_entered = threading.Event()
        release_first = threading.Event()
        results: dict[str, object] = {}
        errors: dict[str, BaseException] = {}

        def blocking_capture(checkpoint_id=None):
            if checkpoint_id == "e551-held":
                first_entered.set()
                if not release_first.wait(5.0):
                    raise TimeoutError("E551 held capture was not released")
            else:
                second_entered.set()
            return original_locked(checkpoint_id)

        viewport._capture_worldbridge_live_checkpoint_locked = blocking_capture

        def capture(name: str) -> None:
            try:
                results[name] = viewport.capture_worldbridge_live_checkpoint(name)
            except BaseException as exc:
                errors[name] = exc

        first = threading.Thread(target=capture, args=("e551-held",))
        first.start()
        _require(first_entered.wait(2.0), "E551 held capture did not start")
        held_gate = gate.snapshot()
        blocked_before = held_gate["blocked_attempts"]

        second = threading.Thread(target=capture, args=("e551-competing",))
        second.start()
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            if gate.snapshot()["blocked_attempts"] > blocked_before:
                break
            time.sleep(0.005)
        blocked_after = gate.snapshot()["blocked_attempts"]
        _require(
            blocked_after > blocked_before,
            "E551 competing capture was not blocked",
        )
        _require(
            second_entered.is_set() is False,
            "E551 competing capture entered owner scope",
        )
        competing_entered_before_release = second_entered.is_set()
        release_first.set()
        first.join(timeout=5.0)
        second.join(timeout=5.0)
        _require(not first.is_alive(), "E551 held capture thread remained alive")
        _require(
            not second.is_alive(),
            "E551 competing capture thread remained alive",
        )
        _require(not errors, f"E551 capture probe failed: {errors}")
        _require(
            set(results) == {"e551-held", "e551-competing"},
            "E551 capture probe lost a checkpoint",
        )
        live_gate = gate.snapshot()
        _require(live_gate["locked"] is False, "E551 gate remained locked")
        return {
            "checkpoint_gate_snapshot": held_gate,
            "live_gate_after": live_gate,
            "competing_operation": "capture_live_checkpoint",
            "competing_blocked": True,
            "competing_entered_before_release": competing_entered_before_release,
            "blocked_attempts_before": blocked_before,
            "blocked_attempts_after": blocked_after,
            "holder_completed": True,
        }
    finally:
        viewport.deleteLater()
        QCoreApplication.sendPostedEvents(viewport, QEvent.Type.DeferredDelete)
        app.processEvents()
        if not sip.isdeleted(viewport):
            raise AssertionError("E551 probe viewport cleanup incomplete")


def verify() -> dict[str, object]:
    fresh_host = verify_e505()
    project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    scene = project / "scenes" / "challenge_scene.pond"
    atomic = _atomic_capture_probe(project, scene)
    witness = build_worldbridge_e551_scene_pond_checkpoint_authority(
        checkpoint=fresh_host["source_checkpoint"],
        fresh_dual_lane_witness=fresh_host["witness"],
        atomic_capture_evidence=atomic,
    )
    _require(
        validate_worldbridge_e551_scene_pond_checkpoint_authority(witness)
        == {"valid": True, "errors": []},
        "E551 witness invalid",
    )
    _require(
        all(witness[field] is True for field in PROOF_FIELDS),
        "E551 did not prove every checkpoint boundary",
    )
    _require(witness["grants_admission"] is False, "E551 granted admission")
    _require(witness["admission_effect"] == "none", "E551 changed effect")

    baseline = build_worldbridge_tick_replay_admission()
    admission = build_worldbridge_tick_replay_admission(
        scene_pond_checkpoint_witness=witness
    )
    evidence = admission["scene_pond_checkpoint_evidence"]
    _require(evidence["validated"] is True, "admission rejected E551")
    _require(evidence["grants_admission"] is False, "E551 granted evidence")
    expected_blockers = [
        blocker
        for blocker in baseline["remaining_admission_blockers"]
        if blocker != SCENE_POND_CHECKPOINT_BLOCKER
    ]
    _require(
        admission["remaining_admission_blockers"] == expected_blockers,
        "E551 did not clear exactly the checkpoint blocker",
    )
    checkpoint_requirement = admission["shared_contracts"]["requirements"][
        "shared_scene_pond_checkpoint"
    ]
    _require(
        checkpoint_requirement["capability_admitted"] is True,
        "E551 checkpoint capability not admitted",
    )
    _require(
        checkpoint_requirement["blocking"] is False,
        "E551 checkpoint requirement remains blocking",
    )
    checkpoint_admissions = admission["shared_contracts"]["admissions"]
    _require(
        checkpoint_admissions["shared_scene_pond_checkpoint"] is True,
        "E551 checkpoint admission remains closed",
    )
    _require(
        checkpoint_admissions["atomic_capture_admitted"] is True,
        "E551 atomic capture admission remains closed",
    )
    _require(
        checkpoint_admissions["cross_lane_checkpoint_available"] is True,
        "E551 checkpoint availability remains closed",
    )
    _require(
        checkpoint_admissions["cross_lane_restore_available"] is True,
        "E551 restore availability remains closed",
    )
    _require(admission["tick_merge_admitted"] is False, "tick merge opened")
    _require(
        admission["full_unified_replay_admitted"] is False,
        "full replay opened",
    )
    _require(admission["default_ready"] is False, "default readiness opened")

    status = build_runtime_worldbridge_status(
        scene_pond_checkpoint_witness=witness
    )
    status_evidence = status["tick_replay_admission"][
        "scene_pond_checkpoint_evidence"
    ]
    _require(status_evidence["validated"] is True, "status dropped E551")
    _require(
        status_evidence["witness_digest"] == witness["witness_digest"],
        "status changed E551 digest",
    )
    _require(
        status["tick_replay_admission"]["default_ready"] is False,
        "status opened readiness",
    )

    tampered = copy.deepcopy(witness)
    tampered["atomic_capture_evidence"]["competing_entered_before_release"] = True
    tampered = _reseal_witness(tampered)
    tampered_validation = (
        validate_worldbridge_e551_scene_pond_checkpoint_authority(tampered)
    )
    _require(
        tampered_validation["valid"] is False,
        "E551 tampered atomic capture was accepted",
    )

    return {
        "schema_version": 1,
        "status": "worldbridge_e551_scene_pond_checkpoint_authority",
        "real_game_viewport": True,
        "read_only": True,
        "checkpoint_digest": witness["checkpoint"]["digest"],
        "fresh_checkpoint_digest": witness["fresh_dual_lane_witness"][
            "fresh_checkpoint_digest"
        ],
        "blocked_attempts_before": atomic["blocked_attempts_before"],
        "blocked_attempts_after": atomic["blocked_attempts_after"],
        "proof": {field: witness[field] for field in PROOF_FIELDS},
        "witness_validated": True,
        "witness_digest": witness["witness_digest"],
        "witness": witness,
        "admission_evidence": evidence,
        "runtime_status_evidence_validated": status_evidence["validated"],
        "remaining_admission_blockers": admission[
            "remaining_admission_blockers"
        ],
        "shared_scene_pond_checkpoint_admitted": True,
        "atomic_capture_admitted": True,
        "tampered_atomic_capture_rejected": True,
        "tampered_errors": tampered_validation["errors"],
        "atomic_checkpoint": False,
        "cross_process_atomicity": False,
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
