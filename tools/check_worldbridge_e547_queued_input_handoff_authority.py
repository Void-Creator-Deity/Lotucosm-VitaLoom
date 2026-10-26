# -*- coding: utf-8 -*-
"""Verify E547 queued-input handoff evidence on a real viewport."""
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
    validate_worldbridge_e546_shared_clock_delta_authority,
)
from core.Lotucosm.runtime.world_bridge_e547_queued_input_handoff_authority import (
    build_worldbridge_e547_queued_input_handoff_authority,
    validate_worldbridge_e547_queued_input_handoff_authority,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.Lotucosm.runtime.world_bridge_tick_authority import (
    validate_worldbridge_tick_receipt,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from tools.check_worldbridge_e505_fresh_host_reconstruction import _new_viewport


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


def verify() -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    scene = project / "scenes" / "challenge_scene.pond"
    viewport = _new_viewport(project, scene, "e547-queued-input-root-seed")
    try:
        viewport._update_simulation()
        previous_receipt = viewport._worldbridge_last_tick_receipt
        _require(
            isinstance(previous_receipt, dict),
            "E547 previous tick receipt missing",
        )
        _require(
            validate_worldbridge_tick_receipt(previous_receipt)
            == {"valid": True, "errors": []},
            "E547 previous tick receipt invalid",
        )

        viewport._sr_input_press("W")
        viewport._sr_input_release("W")
        viewport._update_simulation()
        receipt = viewport._worldbridge_last_tick_receipt
        envelope = viewport._worldbridge_last_shared_state_envelope
        events = copy.deepcopy(viewport._worldbridge_input_events_last_tick)
        authority = viewport._worldbridge_tick_authority
        snapshot = authority.input_sequence.snapshot()
        pond = viewport._unified_pond
        ps_events = pond.worldbridge_input_events_last_tick

        _require(isinstance(receipt, dict), "E547 current tick receipt missing")
        _require(
            validate_worldbridge_tick_receipt(receipt)
            == {"valid": True, "errors": []},
            "E547 current tick receipt invalid",
        )
        _require(isinstance(envelope, dict), "E547 shared-state envelope missing")
        _require(
            len(events) == 2,
            f"E547 real viewport retained {len(events)} events",
        )
        _require(
            [event["sequence"] for event in events] == [1, 2],
            "E547 canonical input sequence unexpected",
        )
        _require(
            [event["event_id"] for event in ps_events]
            == [event["event_id"] for event in events],
            "E547 PS did not retain the canonical input batch",
        )

        clock_witness = build_worldbridge_e546_shared_clock_delta_authority(
            completed_tick_receipt=receipt,
            previous_completed_tick_receipt=previous_receipt,
            owner_token=str(viewport._worldbridge_clock_owner_token),
            runtime_epoch=str(viewport._sr_runtime_epoch),
        )
        _require(
            validate_worldbridge_e546_shared_clock_delta_authority(clock_witness)
            == {"valid": True, "errors": []},
            "E547 E546 clock evidence invalid",
        )

        witness = build_worldbridge_e547_queued_input_handoff_authority(
            completed_tick_receipt=receipt,
            shared_clock_delta_witness=clock_witness,
            canonical_input_events=events,
            input_sequence_snapshot=snapshot,
            shared_state_envelope=envelope,
            ps_received_input_events=ps_events,
        )
        _require(
            validate_worldbridge_e547_queued_input_handoff_authority(witness)
            == {"valid": True, "errors": []},
            "E547 queued-input witness invalid",
        )
        for field in (
            "batch_contiguous",
            "receipt_batch_bound",
            "envelope_batch_bound",
            "sr_pending_empty_after_tick",
            "canonical_event_ids_consumed",
            "ps_received_batch_identical",
            "same_tick_delta_observed",
        ):
            _require(witness[field] is True, f"E547 evidence false: {field}")
        _require(witness["grants_admission"] is False, "E547 granted admission")
        _require(witness["admission_effect"] == "none", "E547 changed effect")

        baseline = build_worldbridge_tick_replay_admission()
        admission = build_worldbridge_tick_replay_admission(
            queued_input_handoff_witness=witness
        )
        evidence = admission["queued_input_handoff_evidence"]
        _require(evidence["validated"] is True, "admission rejected E547 evidence")
        _require(evidence["grants_admission"] is False, "admission granted from E547")
        _require(admission["tick_merge_admitted"] is False, "tick merge opened")
        _require(
            admission["full_unified_replay_admitted"] is False,
            "full replay opened",
        )
        _require(admission["default_ready"] is False, "default readiness opened")
        _require(
            admission["remaining_admission_blockers"]
            == baseline["remaining_admission_blockers"],
            "E547 changed admission blockers",
        )

        status = build_runtime_worldbridge_status(
            project,
            queued_input_handoff_witness=witness,
        )
        status_admission = status["tick_replay_admission"]
        status_evidence = status_admission["queued_input_handoff_evidence"]
        _require(status_evidence["validated"] is True, "runtime status dropped E547")
        _require(
            status_evidence["witness_digest"] == witness["witness_digest"],
            "runtime status changed E547 digest",
        )
        _require(status_admission["default_ready"] is False, "status opened readiness")

        tampered = copy.deepcopy(witness)
        tampered["ps_received_input_events"][0]["event_id"] = "input-reordered"
        tampered = _reseal_witness(tampered)
        tampered_validation = (
            validate_worldbridge_e547_queued_input_handoff_authority(tampered)
        )
        _require(tampered_validation["valid"] is False, "tampered PS batch accepted")
        _require(
            "ps_received_batch_mismatch" in tampered_validation["errors"],
            "tampered PS batch was not diagnosed",
        )
        _require(
            pond.worldbridge_input_events_last_tick == events,
            "tamper check mutated the live PS evidence",
        )

        return {
            "schema_version": 1,
            "status": "worldbridge_e547_queued_input_handoff_authority",
            "real_game_viewport": True,
            "read_only": True,
            "previous_tick_sequence": previous_receipt["tick_sequence"],
            "tick_sequence": receipt["tick_sequence"],
            "decision_digest": receipt["clock_decision"]["decision_digest"],
            "pause_reset_epoch": witness["pause_reset_epoch"],
            "event_count": witness["event_count"],
            "input_digest": witness["input_digest"],
            "first_input_sequence": witness["first_input_sequence"],
            "last_input_sequence": witness["last_input_sequence"],
            "canonical_event_ids": [event["event_id"] for event in events],
            "evidence": {
                field: witness[field]
                for field in (
                    "batch_contiguous",
                    "receipt_batch_bound",
                    "envelope_batch_bound",
                    "sr_pending_empty_after_tick",
                    "canonical_event_ids_consumed",
                    "ps_received_batch_identical",
                    "same_tick_delta_observed",
                )
            },
            "witness_validated": True,
            "witness_digest": witness["witness_digest"],
            "admission_evidence": evidence,
            "runtime_status_evidence_validated": status_evidence["validated"],
            "tampered_ps_batch_rejected": True,
            "tampered_errors": tampered_validation["errors"],
            "shared_queued_input_ordering": False,
            "scheduler_owned": False,
            "input_replay_admitted": False,
            "tick_merge_admitted": admission["tick_merge_admitted"],
            "full_unified_replay_admitted": admission[
                "full_unified_replay_admitted"
            ],
            "default_ready": admission["default_ready"],
            "remaining_admission_blockers": admission[
                "remaining_admission_blockers"
            ],
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
            raise AssertionError("E547 viewport cleanup incomplete")


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
