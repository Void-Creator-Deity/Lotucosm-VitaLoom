# -*- coding: utf-8 -*-
"""Verify E546 shared frame-clock delta evidence on a real viewport."""
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
from core.Lotucosm.runtime.world_bridge_tick_authority import (
    validate_worldbridge_tick_receipt,
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


def _reseal_receipt(receipt: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(receipt)
    consumers = sealed.get("clock_consumers")
    if isinstance(consumers, list):
        for row in consumers:
            if not isinstance(row, dict):
                continue
            row["consumer_digest"] = ""
            row["consumer_digest"] = _digest(
                {
                    key: value
                    for key, value in row.items()
                    if key != "consumer_digest"
                }
            )
    sealed["receipt_digest"] = ""
    sealed["receipt_digest"] = _digest(sealed)
    return sealed


def _reseal_witness(witness: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(witness)
    sealed["witness_digest"] = ""
    sealed["witness_digest"] = _digest(sealed)
    return sealed


def _tampered_witness(witness: dict[str, object]) -> dict[str, object]:
    candidate = copy.deepcopy(witness)
    receipt = candidate["completed_tick_receipt"]
    _require(isinstance(receipt, dict), "witness receipt is not mutable mapping")
    decision = receipt.get("clock_decision")
    _require(isinstance(decision, dict), "witness receipt decision missing")
    decision["decision_digest"] = "0" * 64
    receipt["clock_decision_digest"] = "0" * 64
    consumers = receipt.get("clock_consumers")
    _require(isinstance(consumers, list), "witness receipt consumers missing")
    for row in consumers:
        _require(isinstance(row, dict), "witness consumer is not mapping")
        row["decision_digest"] = "0" * 64
    candidate["completed_tick_receipt"] = _reseal_receipt(receipt)
    candidate["decision_digest"] = "0" * 64
    return _reseal_witness(candidate)


def _clock_receipt_summary(receipt: dict[str, object]) -> dict[str, object]:
    decision = receipt["clock_decision"]
    consumers = receipt["clock_consumers"]
    return {
        "tick_sequence": receipt["tick_sequence"],
        "decision_sequence": decision["decision_sequence"],
        "decision_digest": decision["decision_digest"],
        "delta_time": receipt["delta_time"],
        "bridge_handoff_requested": decision["bridge_handoff_requested"],
        "consumer_order": [row["consumer"] for row in consumers],
        "receipt_digest": receipt["receipt_digest"],
    }


def verify() -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    scene = project / "scenes" / "challenge_scene.pond"
    viewport = _new_viewport(project, scene, "e546-shared-clock-root-seed")
    try:
        viewport._update_simulation()
        first_receipt = viewport._worldbridge_last_tick_receipt
        _require(isinstance(first_receipt, dict), "first real tick receipt missing")
        _require(
            all(
                field in first_receipt
                for field in (
                    "clock_decision",
                    "clock_decision_digest",
                    "clock_consumers",
                )
            ),
            "first real tick has no frame clock decision",
        )
        _require(
            validate_worldbridge_tick_receipt(first_receipt)
            == {"valid": True, "errors": []},
            "first real tick receipt did not validate",
        )

        viewport._update_simulation()
        second_receipt = viewport._worldbridge_last_tick_receipt
        _require(
            isinstance(second_receipt, dict),
            "second real tick receipt missing",
        )
        _require(
            all(
                field in second_receipt
                for field in (
                    "clock_decision",
                    "clock_decision_digest",
                    "clock_consumers",
                )
            ),
            "second real tick has no frame clock decision",
        )
        _require(
            validate_worldbridge_tick_receipt(second_receipt)
            == {"valid": True, "errors": []},
            "second real tick receipt did not validate",
        )

        first_summary = _clock_receipt_summary(first_receipt)
        second_summary = _clock_receipt_summary(second_receipt)
        _require(
            int(second_summary["tick_sequence"])
            > int(first_summary["tick_sequence"]),
            "real tick sequence did not advance",
        )
        _require(
            second_summary["decision_sequence"]
            > first_summary["decision_sequence"],
            "real clock decision sequence did not advance",
        )
        _require(
            second_summary["decision_digest"]
            != first_summary["decision_digest"],
            "real clock decision digest was reused",
        )
        _require(
            first_summary["consumer_order"] == ["sr", "ps"],
            "first real frame did not consume the delta SR then PS",
        )
        _require(
            second_summary["consumer_order"] == ["sr", "ps"],
            "second real frame did not consume the delta SR then PS",
        )

        witness = build_worldbridge_e546_shared_clock_delta_authority(
            completed_tick_receipt=second_receipt,
            previous_completed_tick_receipt=first_receipt,
            owner_token=str(viewport._worldbridge_clock_owner_token),
            runtime_epoch=str(viewport._sr_runtime_epoch),
        )
        _require(
            validate_worldbridge_e546_shared_clock_delta_authority(witness)
            == {"valid": True, "errors": []},
            "E546 witness did not validate",
        )
        _require(witness["sequence_scope"] == "adjacent_receipt_chain", "witness did not seal a chain")
        _require(witness["sequence_strictly_increasing"] is True, "clock sequence was not strict")
        _require(witness["decision_digest_not_reused"] is True, "clock digest was reused")
        _require(witness["grants_admission"] is False, "witness granted admission")
        _require(witness["admission_effect"] == "none", "witness changed admission effect")

        baseline = build_worldbridge_tick_replay_admission()
        admission = build_worldbridge_tick_replay_admission(
            shared_clock_delta_witness=witness
        )
        evidence = admission["shared_clock_delta_evidence"]
        _require(evidence["validated"] is True, "admission did not validate witness")
        _require(evidence["grants_admission"] is False, "evidence granted admission")
        _require(evidence["admission_effect"] == "none", "evidence changed effect")
        _require(admission["tick_merge_admitted"] is False, "tick merge opened")
        _require(
            admission["full_unified_replay_admitted"] is False,
            "full unified replay opened",
        )
        _require(admission["default_ready"] is False, "default readiness opened")
        _require(
            admission["remaining_admission_blockers"]
            == baseline["remaining_admission_blockers"],
            "E546 evidence changed admission blockers",
        )
        _require(
            admission["do_not_claim"] == baseline["do_not_claim"],
            "E546 evidence changed do-not-claim list",
        )

        status = build_runtime_worldbridge_status(
            project,
            shared_clock_delta_witness=witness,
        )
        status_admission = status["tick_replay_admission"]
        status_evidence = status_admission["shared_clock_delta_evidence"]
        _require(status_evidence["validated"] is True, "runtime status dropped evidence")
        _require(
            status_evidence["witness_digest"] == witness["witness_digest"],
            "runtime status changed witness digest",
        )
        _require(status_admission["default_ready"] is False, "runtime status opened readiness")

        tampered = _tampered_witness(witness)
        tampered_validation = (
            validate_worldbridge_e546_shared_clock_delta_authority(tampered)
        )
        _require(tampered_validation["valid"] is False, "tampered witness was accepted")
        _require(
            any("decision_digest" in error for error in tampered_validation["errors"]),
            "tampered decision digest was not diagnosed",
        )

        return {
            "schema_version": 1,
            "status": "worldbridge_e546_shared_clock_delta_authority",
            "real_game_viewport": True,
            "read_only": True,
            "first_tick": first_summary,
            "second_tick": second_summary,
            "sequence_scope": witness["sequence_scope"],
            "witness_validated": True,
            "witness_digest": witness["witness_digest"],
            "admission_evidence": evidence,
            "runtime_status_evidence_validated": status_evidence["validated"],
            "tampered_decision_rejected": True,
            "tampered_decision_errors": tampered_validation["errors"],
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
            raise AssertionError("E546 viewport cleanup incomplete")


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
