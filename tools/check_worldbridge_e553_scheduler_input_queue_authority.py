# -*- coding: utf-8 -*-
"""Verify E553 scheduler-owned bounded input queue on a real viewport."""
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

from core.Lotucosm.runtime.world_bridge_e546_shared_clock_delta_authority import (
    build_worldbridge_e546_shared_clock_delta_authority,
)
from core.Lotucosm.runtime.world_bridge_e547_queued_input_handoff_authority import (
    build_worldbridge_e547_queued_input_handoff_authority,
)
from core.Lotucosm.runtime.world_bridge_e553_scheduler_input_queue_authority import (
    PROOF_FIELDS,
    build_worldbridge_e553_scheduler_input_queue_authority,
    validate_worldbridge_e553_scheduler_input_queue_authority,
)
from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    SHARED_QUEUED_INPUT_BLOCKER,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from tools.check_worldbridge_e505_fresh_host_reconstruction import _new_viewport


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
    viewport = _new_viewport(project, scene, "e553-scheduler-input-root")
    try:
        queue = viewport._worldbridge_input_sequence
        queue.configure_policy(max_pending=2, overflow_policy="reject_newest")
        scheduler_before = queue.scheduler_snapshot()

        viewport._sr_input_press("W")
        viewport._sr_input_release("W")
        attempt_before = queue.scheduler_snapshot()
        viewport._sr_input_press("A")
        rejection = copy.deepcopy(viewport._worldbridge_last_input_backpressure)
        _require(isinstance(rejection, dict), "E553 backpressure receipt missing")
        attempt_after = queue.scheduler_snapshot()
        _require(
            attempt_before["next_sequence"] == attempt_after["next_sequence"],
            "E553 rejected event advanced sequence",
        )

        viewport._update_simulation()
        receipt = copy.deepcopy(viewport._worldbridge_last_tick_receipt)
        envelope = copy.deepcopy(viewport._worldbridge_last_shared_state_envelope)
        events = copy.deepcopy(viewport._worldbridge_input_events_last_tick)
        ps_events = copy.deepcopy(
            viewport._unified_pond.worldbridge_input_events_last_tick
        )
        _require(isinstance(receipt, dict), "E553 completed receipt missing")
        _require(isinstance(envelope, dict), "E553 envelope missing")
        _require(len(events) == 2, "E553 accepted batch missing")
        clock = build_worldbridge_e546_shared_clock_delta_authority(
            completed_tick_receipt=receipt,
            owner_token=str(viewport._worldbridge_clock_owner_token),
            runtime_epoch=str(viewport._sr_runtime_epoch),
        )
        handoff = build_worldbridge_e547_queued_input_handoff_authority(
            completed_tick_receipt=receipt,
            shared_clock_delta_witness=clock,
            canonical_input_events=events,
            input_sequence_snapshot=queue.snapshot(),
            shared_state_envelope=envelope,
            ps_received_input_events=ps_events,
        )
        scheduler_after_dispatch = queue.scheduler_snapshot()
        dispatch_receipt = copy.deepcopy(
            scheduler_after_dispatch["dispatch_receipts"][-1]
        )

        viewport._sr_input_press("D")
        viewport._sr_input_release("D")
        drop_before = queue.scheduler_snapshot()
        viewport._sr_input_clear(lifecycle_action="pause")
        drop_after = queue.scheduler_snapshot()
        drop_receipt = copy.deepcopy(drop_after["drop_receipts"][-1])
        drop_attempt = {
            "before": drop_before,
            "drop_receipt": drop_receipt,
            "after": drop_after,
        }
        backpressure_attempt = {
            "before": attempt_before,
            "rejected_receipt": rejection,
            "after": attempt_after,
        }

        witness = build_worldbridge_e553_scheduler_input_queue_authority(
            queued_input_handoff_witness=handoff,
            scheduler_before=scheduler_before,
            backpressure_attempt=backpressure_attempt,
            scheduler_after_dispatch=scheduler_after_dispatch,
            dispatch_receipt=dispatch_receipt,
            drop_attempt=drop_attempt,
        )
        _require(
            validate_worldbridge_e553_scheduler_input_queue_authority(witness)
            == {"valid": True, "errors": []},
            "E553 witness invalid",
        )
        _require(
            all(witness[field] is True for field in PROOF_FIELDS),
            "E553 did not prove every queue boundary",
        )
        _require(witness["grants_admission"] is False, "E553 granted admission")
        _require(witness["admission_effect"] == "none", "E553 changed effect")

        baseline = build_worldbridge_tick_replay_admission()
        admission = build_worldbridge_tick_replay_admission(
            scheduler_input_queue_witness=witness
        )
        evidence = admission["scheduler_input_queue_evidence"]
        _require(evidence["validated"] is True, "admission rejected E553")
        expected_blockers = [
            blocker
            for blocker in baseline["remaining_admission_blockers"]
            if blocker != SHARED_QUEUED_INPUT_BLOCKER
        ]
        _require(
            admission["remaining_admission_blockers"] == expected_blockers,
            "E553 did not clear exactly the queued-input blocker",
        )
        input_requirement = admission["shared_contracts"]["requirements"][
            "shared_queued_input_ordering"
        ]
        _require(
            input_requirement["capability_admitted"] is True,
            "E553 input capability not admitted",
        )
        _require(
            input_requirement["blocking"] is False,
            "E553 input requirement remains blocking",
        )
        input_admissions = admission["shared_contracts"]["admissions"]
        for field in (
            "scheduler_owned",
            "shared_queued_input_ordering",
            "cross_lane_input_ordering_admitted",
            "backpressure_admitted",
            "dropped_event_policy_admitted",
        ):
            _require(
                input_admissions[field] is True,
                f"E553 admission remains closed: {field}",
            )
        _require(admission["tick_merge_admitted"] is False, "tick merge opened")
        _require(
            admission["full_unified_replay_admitted"] is False,
            "full replay opened",
        )
        _require(admission["default_ready"] is False, "default readiness opened")

        status = build_runtime_worldbridge_status(
            scheduler_input_queue_witness=witness
        )
        status_evidence = status["tick_replay_admission"][
            "scheduler_input_queue_evidence"
        ]
        _require(status_evidence["validated"] is True, "status dropped E553")
        _require(
            status_evidence["witness_digest"] == witness["witness_digest"],
            "status changed E553 digest",
        )
        _require(
            status["tick_replay_admission"]["default_ready"] is False,
            "status opened readiness",
        )

        tampered = copy.deepcopy(witness)
        tampered["backpressure_attempt"]["after"]["next_sequence"] += 1
        tampered = _reseal_witness(tampered)
        tampered_validation = (
            validate_worldbridge_e553_scheduler_input_queue_authority(tampered)
        )
        _require(
            tampered_validation["valid"] is False,
            "E553 tampered backpressure was accepted",
        )

        return {
            "schema_version": 1,
            "status": "worldbridge_e553_scheduler_input_queue_authority",
            "real_game_viewport": True,
            "read_only": True,
            "scheduler_owner_id": scheduler_after_dispatch[
                "scheduler_owner_id"
            ],
            "max_pending": scheduler_after_dispatch["max_pending"],
            "overflow_policy": scheduler_after_dispatch["overflow_policy"],
            "accepted_count": scheduler_after_dispatch["accepted_count"],
            "rejected_count": scheduler_after_dispatch["rejected_count"],
            "dispatch_event_ids": dispatch_receipt["event_ids"],
            "dropped_event_ids": drop_receipt["dropped_event_ids"],
            "proof": {field: witness[field] for field in PROOF_FIELDS},
            "witness_validated": True,
            "witness_digest": witness["witness_digest"],
            "witness": witness,
            "admission_evidence": evidence,
            "runtime_status_evidence_validated": status_evidence["validated"],
            "remaining_admission_blockers": admission[
                "remaining_admission_blockers"
            ],
            "scheduler_owned_admitted": True,
            "backpressure_admitted": True,
            "dropped_event_policy_admitted": True,
            "tampered_backpressure_rejected": True,
            "tampered_errors": tampered_validation["errors"],
            "scheduler_owned": False,
            "backpressure_admitted": False,
            "dropped_event_policy_admitted": False,
            "input_replay_admitted": False,
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
        viewport.deleteLater()
        QCoreApplication.sendPostedEvents(viewport, QEvent.Type.DeferredDelete)
        app.processEvents()
        if not sip.isdeleted(viewport):
            raise AssertionError("E553 viewport cleanup incomplete")


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
