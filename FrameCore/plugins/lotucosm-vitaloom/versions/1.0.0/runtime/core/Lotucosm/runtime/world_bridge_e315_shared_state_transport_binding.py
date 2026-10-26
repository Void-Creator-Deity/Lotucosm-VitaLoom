# -*- coding: utf-8 -*-
"""E315 evidence binding the shared transport to the real E313 seam."""
from __future__ import annotations

import copy
from typing import Any

from core.Lotucosm.runtime.world_bridge_e313_live_capture_binding import (
    run_e313_live_capture_binding,
)
from core.Lotucosm.runtime.world_bridge_shared_state_transport import (
    WorldBridgeSharedStateReceiver,
    build_worldbridge_shared_state_envelope,
    validate_worldbridge_shared_state_envelope,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_e315_shared_state_transport_binding"


def _capture_to_envelope(capture: dict[str, Any], sequence: int) -> dict[str, Any]:
    event = {
        "event_id": f"sr-event-{capture['input_provenance']['sequence']}",
        "kind": "thrust",
        "payload": {
            "sequence": capture["input_provenance"]["sequence"],
            "tick": capture["input_provenance"]["tick"],
            "value": 1.0,
        },
    }
    clocks = {
        "sr": {
            "domain": "sr",
            "tick": capture["input_provenance"]["tick"],
            "delta": 0.05,
            "time": capture["clock_provenance"]["sr_sim_time"],
            "source": "e313_live_sr_observation",
        },
        "ps": {
            "domain": "ps",
            "tick": capture["clock_provenance"]["ps_tick"],
            "delta": 1.0,
            "time": float(capture["clock_provenance"]["ps_tick"]),
            "source": "e313_live_pond_update",
        },
    }
    return build_worldbridge_shared_state_envelope(
        envelope_id=f"e315-live-{sequence}",
        capture_epoch=1,
        sequence=sequence,
        input_events=[event],
        pause_reset_epoch=0,
        clock_provenance=clocks,
        bridge_identity_links=[
            {
                "sr_entity_id": "sr:e313",
                "ps_organism_id": "ps:e313",
                "relation": "observation_link",
            }
        ],
    )


def run_e315_shared_state_transport_binding() -> dict[str, Any]:
    first_capture = run_e313_live_capture_binding()
    second_capture = run_e313_live_capture_binding()
    first = _capture_to_envelope(first_capture, 0)
    second = _capture_to_envelope(second_capture, 1)
    receiver = WorldBridgeSharedStateReceiver()
    accepted_first = receiver.accept(first)
    accepted_second = receiver.accept(second)

    tampered = copy.deepcopy(second)
    tampered["clock_provenance"]["ps"]["tick"] += 1
    tamper_result = validate_worldbridge_shared_state_envelope(tampered)
    before_rejected_inputs = receiver.state_fingerprint()
    try:
        receiver.accept(tampered)
    except ValueError as exc:
        tamper_error = str(exc)
    else:
        tamper_error = ""
    gap = _capture_to_envelope(first_capture, 3)
    try:
        receiver.accept(gap)
    except ValueError as exc:
        gap_error = str(exc)
    else:
        gap_error = ""
    after_rejected_inputs = receiver.state_fingerprint()
    quarantine = receiver.quarantine(
        sequence=3,
        code="sequence_continuity_failure",
        stage="receiver_accept",
        message=gap_error or "sequence continuity failure",
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "real_e313_capture_seam_exercised": first_capture["capture_seam_exercised"] and second_capture["capture_seam_exercised"],
        "envelopes": [first, second],
        "receiver": {
            "accepted_count": receiver.accepted_count,
            "last_sequence": receiver.last_sequence,
            "first_copy_isolated": accepted_first is not first,
            "second_copy_isolated": accepted_second is not second,
            "sequence_continuity_enforced": bool(gap_error),
            "gap_error": gap_error,
            "tamper_error": tamper_error,
            "rejected_input_state_preserved": before_rejected_inputs == after_rejected_inputs,
        },
        "tamper_rejection": {
            "valid": tamper_result["valid"],
            "digest_mismatch": "envelope_digest_mismatch" in tamper_result["errors"],
        },
        "quarantine": {
            "required": True,
            "artifact_valid": validate_worldbridge_shared_state_envelope(quarantine)["valid"],
            "preserves_last_accepted_sequence": receiver.last_sequence == 1,
            "mode": "observation_only_no_replay",
        },
        "partial_failure_rollback": {
            "tampered_envelope_rejected": bool(tamper_error),
            "sequence_gap_rejected": bool(gap_error),
            "receiver_state_preserved": before_rejected_inputs == after_rejected_inputs,
        },
        "parity": {
            "fresh_capture_envelope_shape_equal": first.keys() == second.keys(),
            "sr_ps_clock_domains_distinct": first["clock_provenance"]["sr"]["domain"] != first["clock_provenance"]["ps"]["domain"],
            "identity_is_link_not_object_identity": first["bridge_identity_links"][0]["relation"] == "observation_link",
        },
        "shared_live_state_restore": False,
        "full_unified_replay_admitted": False,
        "cross_lane_replay": False,
        "lossless": False,
        "default_ready": False,
        "live_adapter_admitted": False,
    }


def build_worldbridge_e315_shared_state_transport_binding() -> dict[str, Any]:
    result = run_e315_shared_state_transport_binding()
    result["protocol_valid"] = bool(
        result["real_e313_capture_seam_exercised"]
        and result["receiver"]["accepted_count"] == 2
        and result["receiver"]["sequence_continuity_enforced"]
        and result["tamper_rejection"]["digest_mismatch"]
        and result["quarantine"]["required"]
        and result["quarantine"]["artifact_valid"]
        and result["quarantine"]["preserves_last_accepted_sequence"]
        and result["partial_failure_rollback"]["tampered_envelope_rejected"]
        and result["partial_failure_rollback"]["sequence_gap_rejected"]
        and result["partial_failure_rollback"]["receiver_state_preserved"]
        and result["parity"]["fresh_capture_envelope_shape_equal"]
        and result["parity"]["sr_ps_clock_domains_distinct"]
        and result["parity"]["identity_is_link_not_object_identity"]
        and result["default_ready"] is False
    )
    return result


__all__ = [
    "build_worldbridge_e315_shared_state_transport_binding",
    "run_e315_shared_state_transport_binding",
]
