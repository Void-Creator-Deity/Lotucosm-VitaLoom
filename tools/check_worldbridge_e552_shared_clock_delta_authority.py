# -*- coding: utf-8 -*-
"""Verify E552 shared SR/PS delta consumption across real viewport speeds."""
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

from PyQt6 import sip
from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtWidgets import QApplication

from core.Lotucosm.pond import Pond
from core.Lotucosm.runtime.world_bridge_e552_shared_clock_delta_authority import (
    PROOF_FIELDS,
    build_worldbridge_e552_shared_clock_delta_authority,
    validate_worldbridge_e552_shared_clock_delta_authority,
)
from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    SHARED_CLOCK_DELTA_BLOCKER,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from tools.check_worldbridge_e505_fresh_host_reconstruction import _new_viewport


SPEEDS = (0.5, 1.0, 3.0)


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
    app = QApplication.instance() or QApplication([])
    project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    scene = project / "scenes" / "challenge_scene.pond"
    viewport = _new_viewport(project, scene, "e552-shared-clock-root")
    original_pond_update = Pond.update
    pond_calls: list[dict[str, object]] = []
    try:
        viewport._update_simulation()
        _require(
            isinstance(viewport._worldbridge_last_tick_receipt, dict),
            "E552 initial tick missing",
        )

        def observed_update(pond, delta_time=1.0):
            before = {
                "time": pond.time,
                "simulation_time": pond.simulation_time,
            }
            gate_snapshot = viewport.worldbridge_owner_gate_snapshot()
            original_pond_update(pond, delta_time)
            pond_calls.append(
                {
                    "before": before,
                    "after": {
                        "time": pond.time,
                        "simulation_time": pond.simulation_time,
                    },
                    "gate_snapshot": gate_snapshot,
                }
            )

        Pond.update = observed_update
        samples = []
        for speed in SPEEDS:
            viewport._apply_speed(speed)
            pond_calls.clear()
            viewport._update_simulation()
            receipt = copy.deepcopy(viewport._worldbridge_last_tick_receipt)
            envelope = copy.deepcopy(
                viewport._worldbridge_last_shared_state_envelope
            )
            _require(isinstance(receipt, dict), f"E552 tick missing at {speed}")
            _require(isinstance(envelope, dict), f"E552 envelope missing at {speed}")
            _require(len(pond_calls) == 1, f"E552 Pond call count at {speed}")
            call = pond_calls[0]
            samples.append(
                {
                    "simulation_speed": speed,
                    "decision": copy.deepcopy(receipt["clock_decision"]),
                    "receipt": receipt,
                    "envelope": envelope,
                    "pond_before": call["before"],
                    "pond_after": call["after"],
                    "gate_snapshot": call["gate_snapshot"],
                }
            )
        Pond.update = original_pond_update

        witness = build_worldbridge_e552_shared_clock_delta_authority(
            clock_samples=samples
        )
        _require(
            validate_worldbridge_e552_shared_clock_delta_authority(witness)
            == {"valid": True, "errors": []},
            "E552 witness invalid",
        )
        _require(
            all(witness[field] is True for field in PROOF_FIELDS),
            "E552 did not prove every clock boundary",
        )
        _require(witness["grants_admission"] is False, "E552 granted admission")
        _require(witness["admission_effect"] == "none", "E552 changed effect")

        baseline = build_worldbridge_tick_replay_admission()
        admission = build_worldbridge_tick_replay_admission(
            shared_clock_delta_authority_witness=witness
        )
        evidence = admission["shared_clock_delta_authority_evidence"]
        _require(evidence["validated"] is True, "admission rejected E552")
        expected_blockers = [
            blocker
            for blocker in baseline["remaining_admission_blockers"]
            if blocker != SHARED_CLOCK_DELTA_BLOCKER
        ]
        _require(
            admission["remaining_admission_blockers"] == expected_blockers,
            "E552 did not clear exactly the shared-clock blocker",
        )
        clock_requirement = admission["shared_contracts"]["requirements"][
            "shared_clock_and_delta"
        ]
        _require(
            clock_requirement["capability_admitted"] is True,
            "E552 clock capability not admitted",
        )
        _require(
            clock_requirement["blocking"] is False,
            "E552 clock requirement remains blocking",
        )
        clock_admissions = admission["shared_contracts"]["admissions"]
        _require(
            clock_admissions["shared_clock"] is True,
            "E552 shared clock remains closed",
        )
        _require(
            clock_admissions["time_conversion_admitted"] is True,
            "E552 time conversion remains closed",
        )
        _require(
            clock_admissions["cross_call_ordering_admitted"] is True,
            "E552 cross-call ordering remains closed",
        )
        _require(admission["tick_merge_admitted"] is False, "tick merge opened")
        _require(
            admission["full_unified_replay_admitted"] is False,
            "full replay opened",
        )
        _require(admission["default_ready"] is False, "default readiness opened")

        status = build_runtime_worldbridge_status(
            shared_clock_delta_authority_witness=witness
        )
        status_evidence = status["tick_replay_admission"][
            "shared_clock_delta_authority_evidence"
        ]
        _require(status_evidence["validated"] is True, "status dropped E552")
        _require(
            status_evidence["witness_digest"] == witness["witness_digest"],
            "status changed E552 digest",
        )
        _require(
            status["tick_replay_admission"]["default_ready"] is False,
            "status opened readiness",
        )

        tampered = copy.deepcopy(witness)
        tampered["clock_samples"][1]["pond_after"]["simulation_time"] += 0.01
        tampered = _reseal_witness(tampered)
        tampered_validation = (
            validate_worldbridge_e552_shared_clock_delta_authority(tampered)
        )
        _require(
            tampered_validation["valid"] is False,
            "E552 tampered PS time was accepted",
        )

        return {
            "schema_version": 1,
            "status": "worldbridge_e552_shared_clock_delta_authority",
            "real_game_viewport": True,
            "read_only": True,
            "conversion_policy": witness["conversion_policy"],
            "speeds": list(SPEEDS),
            "deltas": [
                sample["decision"]["sr_delta_seconds"] for sample in samples
            ],
            "ps_ticks_advanced": [
                sample["pond_after"]["time"] - sample["pond_before"]["time"]
                for sample in samples
            ],
            "ps_simulation_time_deltas": [
                sample["pond_after"]["simulation_time"]
                - sample["pond_before"]["simulation_time"]
                for sample in samples
            ],
            "gate_depths": [
                sample["gate_snapshot"]["depth"] for sample in samples
            ],
            "proof": {field: witness[field] for field in PROOF_FIELDS},
            "witness_validated": True,
            "witness_digest": witness["witness_digest"],
            "admission_evidence": evidence,
            "runtime_status_evidence_validated": status_evidence["validated"],
            "remaining_admission_blockers": admission[
                "remaining_admission_blockers"
            ],
            "shared_clock_admitted": True,
            "time_conversion_admitted": True,
            "cross_call_ordering_admitted": True,
            "witness": witness,
            "clock_samples": samples,
            "tampered_clock_rejected": True,
            "tampered_errors": tampered_validation["errors"],
            "atomic_checkpoint": False,
            "scheduler_owned": False,
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
    finally:
        Pond.update = original_pond_update
        viewport.deleteLater()
        QCoreApplication.sendPostedEvents(viewport, QEvent.Type.DeferredDelete)
        app.processEvents()
        if not sip.isdeleted(viewport):
            raise AssertionError("E552 viewport cleanup incomplete")


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
