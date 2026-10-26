# -*- coding: utf-8 -*-
"""Qt-free, evidence-gated contracts for the five E538 replay preconditions.

This module composes the existing clock, input/lifecycle, RNG, pause/reset and
checkpoint boundaries into one machine-checkable contract. It exercises real
producer APIs where they exist. Sealed E550-E554 witnesses may admit only the
capability they prove; replay, atomic cross-process and default-runtime
authority remain closed.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from collections.abc import Mapping
from typing import Any

from .world_bridge_checkpoint_restore_feasibility import (
    build_worldbridge_checkpoint_restore_feasibility_contract,
    validate_worldbridge_checkpoint_restore_feasibility_contract,
)
from .world_bridge_clock_ordering_authority import (
    build_worldbridge_clock_ordering_authority_contract,
    observe_worldbridge_clock_ordering,
    validate_worldbridge_clock_ordering_authority_contract,
)
from .world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
    restore_worldbridge_deterministic_randomness_context,
    validate_worldbridge_deterministic_randomness_snapshot,
)
from .world_bridge_input_pause_authority import (
    build_worldbridge_input_pause_authority_contract,
    observe_worldbridge_sr_input_lifecycle,
    validate_worldbridge_input_pause_authority_contract,
)
from .world_bridge_e550_pause_reset_error_isolation_authority import (
    validate_worldbridge_e550_pause_reset_error_isolation_authority,
)
from .world_bridge_e551_scene_pond_checkpoint_authority import (
    validate_worldbridge_e551_scene_pond_checkpoint_authority,
)
from .world_bridge_e552_shared_clock_delta_authority import (
    validate_worldbridge_e552_shared_clock_delta_authority,
)
from .world_bridge_e553_scheduler_input_queue_authority import (
    validate_worldbridge_e553_scheduler_input_queue_authority,
)
from .world_bridge_e554_shared_randomness_authority import (
    validate_worldbridge_e554_shared_randomness_authority,
)
from .world_bridge_shared_state_transport import (
    WorldBridgeSharedStateReceiver,
    build_worldbridge_shared_state_envelope,
    copy_worldbridge_shared_state_envelope,
    quarantine_worldbridge_shared_state_transport,
    validate_worldbridge_shared_state_envelope,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e538_shared_contracts"
RUNTIME_MODE = "dual"
AUTHORITY_SCOPE = "evidence_gated_shared_contract_boundary"
REQUIREMENT_IDS = (
    "shared_clock_and_delta",
    "shared_queued_input_ordering",
    "shared_random_seed_contract",
    "shared_pause_reset_error_isolation",
    "shared_scene_pond_checkpoint",
)
REMAINING_ADMISSION_BLOCKERS = (
    "shared_clock_and_delta_contract_missing",
    "shared_queued_input_ordering_missing",
    "shared_random_seed_contract_missing",
    "shared_pause_reset_error_isolation_contract_missing",
    "shared_scene_pond_checkpoint_contract_missing",
    "full_unified_runtime_replay_not_proven",
    "unified_default_runtime_readiness_not_proven",
)
PAUSE_RESET_ERROR_ISOLATION_BLOCKER = (
    "shared_pause_reset_error_isolation_contract_missing"
)
SCENE_POND_CHECKPOINT_BLOCKER = (
    "shared_scene_pond_checkpoint_contract_missing"
)
SHARED_CLOCK_DELTA_BLOCKER = "shared_clock_and_delta_contract_missing"
SHARED_QUEUED_INPUT_BLOCKER = "shared_queued_input_ordering_missing"
SHARED_RANDOMNESS_BLOCKER = "shared_random_seed_contract_missing"
FULL_REPLAY_BLOCKER = "full_unified_runtime_replay_not_proven"
DEFAULT_READINESS_BLOCKER = "unified_default_runtime_readiness_not_proven"
DO_NOT_CLAIM = (
    "shared_sr_ps_clock",
    "shared_queued_input_ordering",
    "shared_rng_seed_contract",
    "shared_pause_reset_authority",
    "shared_scene_pond_checkpoint",
    "atomic_sr_ps_checkpoint",
    "full_unified_runtime_replay",
    "sr_ps_tick_merge",
    "cross_lane_behavior_equivalence",
    "cross_lane_behavior_equivalence_outside_declared_scope",
    "lossless_worldbridge_mapping",
    "portable_sr_executable_script_checkpoint",
    "cross_session_script_rehydration",
    "unified_pond_default_ready",
)
_FALSE_ADMISSIONS = (
    "cross_lane_behavior_admitted",
    "behavior_equivalence_admitted",
    "behavior_routing_admitted",
    "tick_merge_admitted",
    "replay_admitted",
    "full_unified_replay_admitted",
    "lossless",
    "default_ready",
    "shared_clock",
    "shared_queued_input_ordering",
    "shared_random_seed_contract",
    "cross_lane_rng_draw_order_admitted",
    "dynamic_entropy_boundary_admitted",
    "native_entropy_boundary_admitted",
    "process_global_entropy_admitted",
    "shared_pause_reset_authority",
    "cross_lane_error_isolation_admitted",
    "partial_failure_compensation_admitted",
    "atomic_capture_admitted",
    "cross_lane_checkpoint_available",
    "cross_lane_restore_available",
    "time_conversion_admitted",
    "cross_call_ordering_admitted",
    "scheduler_owned",
    "backpressure_admitted",
    "dropped_event_policy_admitted",
    "cross_lane_input_ordering_admitted",
    "shared_scene_pond_checkpoint",
    "script_checkpoint_admitted",
    "cross_session_script_rehydration_admitted",
    "atomic_sr_ps_checkpoint_admitted",
)
_MISSING_BY_REQUIREMENT = {
    "shared_clock_and_delta": (
        "shared_sr_ps_clock",
        "sr_seconds_to_ps_ticks_conversion",
        "cross_call_or_cross_thread_ordering",
    ),
    "shared_queued_input_ordering": (
        "scheduler_owner_and_canonical_input_event_schema",
        "monotonic_sequence_and_lane_phase_routing",
        "admission_backpressure_and_dropped_event_policy",
    ),
    "shared_random_seed_contract": (
        "cross_lane_rng_draw_order",
        "dynamic_entropy_boundary_closed",
        "native_entropy_boundary_closed",
    ),
    "shared_pause_reset_error_isolation": (
        "shared_pause_reset_authority",
        "restore_order_and_partial_failure_compensation",
        "cross_lane_error_isolation",
    ),
    "shared_scene_pond_checkpoint": (
        "versioned_complete_sr_runtime_state",
        "versioned_complete_ps_pond_and_system_state",
        "bridge_link_and_identity_restoration",
        "same_instant_atomic_capture",
    ),
}

def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _canonical_event(
    sequence: int, epoch: int, data: Mapping[str, Any], kind: str = "input"
) -> dict[str, Any]:
    payload = {
        "canonical_sequence": sequence,
        "pause_reset_epoch": epoch,
        "event_digest": _digest(dict(data)),
        "data": dict(data),
    }
    return {"event_id": f"e538-input-{sequence}", "kind": kind, "payload": payload}


def _clock_provenance(
    *, sequence: int, sr_delta: float = 0.05, ps_delta: float = 1.0
) -> dict[str, dict[str, Any]]:
    return {
        "sr": {
            "domain": "sr",
            "tick": sequence,
            "delta": sr_delta,
            "time": sequence * sr_delta,
            "source": "e538_probe",
        },
        "ps": {
            "domain": "ps",
            "tick": sequence,
            "delta": ps_delta,
            "time": sequence * ps_delta,
            "source": "e538_probe",
        },
    }


def _envelope(
    *,
    sequence: int,
    capture_epoch: int,
    pause_reset_epoch: int,
    input_events: list[Mapping[str, Any]] | None = None,
    rng_context_snapshot: Mapping[str, Any] | None = None,
    lifecycle_action: str = "tick",
    playing: bool = True,
    paused: bool = False,
) -> dict[str, Any]:
    return build_worldbridge_shared_state_envelope(
        envelope_id=f"e538-shared-{sequence}",
        capture_epoch=capture_epoch,
        sequence=sequence,
        input_events=[] if input_events is None else input_events,
        pause_reset_epoch=pause_reset_epoch,
        clock_provenance=_clock_provenance(sequence=sequence),
        bridge_identity_links=[
            {"sr_entity_id": f"e538-sr-{sequence}", "ps_organism_id": f"e538-ps-{sequence}"}
        ],
        rng_context_snapshot=rng_context_snapshot,
        lifecycle_action=lifecycle_action,
        playing=playing,
        paused=paused,
    )


def _clock_evidence() -> dict[str, Any]:
    contract = build_worldbridge_clock_ordering_authority_contract()
    validation = validate_worldbridge_clock_ordering_authority_contract(contract)
    paused = observe_worldbridge_clock_ordering(4.0, paused=True, bridge_handoff_invoked=True)
    slow = observe_worldbridge_clock_ordering(0.01, paused=False, bridge_handoff_invoked=True)
    fast = observe_worldbridge_clock_ordering(3.0, paused=False, bridge_handoff_invoked=True)
    missed = observe_worldbridge_clock_ordering(1.0, paused=False, bridge_handoff_invoked=False)
    checks = {
        "authority_contract_valid": validation == {"valid": True, "errors": []},
        "paused_non_advance": paused["sr_delta_seconds"] == 0.0
        and paused["ps_ticks_advanced"] == 0,
        "slow_speed_handoff": math.isclose(
            slow["sr_delta_seconds"], 0.01, rel_tol=0.0, abs_tol=1e-12
        )
        and slow["ps_ticks_advanced"] == 1,
        "fast_speed_handoff": math.isclose(
            fast["sr_delta_seconds"], 0.15, rel_tol=0.0, abs_tol=1e-12
        )
        and fast["ps_ticks_advanced"] == 1,
        "missed_handoff": math.isclose(
            missed["sr_delta_seconds"], 0.05, rel_tol=0.0, abs_tol=1e-12
        )
        and missed["ps_ticks_advanced"] == 0,
        "no_time_conversion": all(
            item["time_conversion_admitted"] is False
            for item in (paused, slow, fast, missed)
        ),
    }
    return {
        "source_contract_valid": checks["authority_contract_valid"],
        "checks": checks,
        "observations": {
            "paused": paused,
            "slow_speed_handoff": slow,
            "fast_speed_handoff": fast,
            "missed_handoff": missed,
        },
    }


def _input_evidence() -> dict[str, Any]:
    contract = build_worldbridge_input_pause_authority_contract()
    validation = validate_worldbridge_input_pause_authority_contract(contract)
    not_playing = observe_worldbridge_sr_input_lifecycle(
        playing=False, paused=False, bridge_handoff_invoked=True
    )
    paused = observe_worldbridge_sr_input_lifecycle(
        playing=True, paused=True, bridge_handoff_invoked=True
    )
    playing_sr_only = observe_worldbridge_sr_input_lifecycle(
        playing=True, paused=False, bridge_handoff_invoked=False
    )
    handoff = observe_worldbridge_sr_input_lifecycle(
        playing=True, paused=False, bridge_handoff_invoked=True
    )
    resume_discards = observe_worldbridge_sr_input_lifecycle(
        playing=True, paused=True, bridge_handoff_invoked=True, lifecycle_action="resume"
    )
    checks = {
        "authority_contract_valid": validation == {"valid": True, "errors": []},
        "not_playing_has_no_snapshot": not_playing["sr_snapshot_admitted"] is False
        and not_playing["bridge_handoff_admitted"] is False,
        "paused_has_no_snapshot": paused["sr_snapshot_admitted"] is False
        and paused["bridge_handoff_admitted"] is False,
        "playing_sr_only_has_snapshot": playing_sr_only["sr_snapshot_admitted"] is True
        and playing_sr_only["bridge_handoff_admitted"] is False,
        "handoff_does_not_route_input": handoff["bridge_handoff_admitted"] is True
        and handoff["ps_received_input"] is False,
        "resume_discards_buffer": resume_discards["sr_input_buffer_discarded"] is True
        and resume_discards["sr_snapshot_admitted"] is False,
    }
    return {
        "source_contract_valid": checks["authority_contract_valid"],
        "checks": checks,
        "observations": {
            "not_playing": not_playing,
            "paused": paused,
            "playing_sr_only": playing_sr_only,
            "handoff": handoff,
            "resume_discards": resume_discards,
        },
    }


def _canonical_input_evidence() -> dict[str, Any]:
    receiver = WorldBridgeSharedStateReceiver()
    first = _envelope(
        sequence=0,
        capture_epoch=0,
        pause_reset_epoch=1,
        input_events=[_canonical_event(0, 1, {"key": "A"})],
        lifecycle_action="start",
    )
    second = _envelope(
        sequence=1,
        capture_epoch=1,
        pause_reset_epoch=1,
        input_events=[_canonical_event(1, 1, {"key": "B"})],
    )
    receiver.accept(first)
    receiver.accept(second)
    accepted_fingerprint = receiver.state_fingerprint()
    gap = _envelope(
        sequence=2,
        capture_epoch=2,
        pause_reset_epoch=1,
        input_events=[_canonical_event(3, 1, {"key": "C"})],
    )
    gap_rejected = False
    try:
        receiver.accept(gap)
    except ValueError:
        gap_rejected = True
    return {
        "accepted_count": receiver.accepted_count,
        "last_input_sequence": receiver.last_input_sequence,
        "continuity_valid": receiver.accepted_count == 2 and receiver.last_input_sequence == 1,
        "gap_rejected": gap_rejected,
        "gap_rejected_without_mutation": receiver.state_fingerprint() == accepted_fingerprint,
    }


def _rng_evidence() -> tuple[dict[str, Any], dict[str, Any]]:
    context = create_worldbridge_deterministic_randomness_context("e538-shared-rng", "e538-fixed-root-seed")
    python_stream = register_worldbridge_deterministic_random_stream(context, "sr.script", "python_random")
    numpy_stream = register_worldbridge_deterministic_random_stream(context, "ps.resource", "numpy_pcg64_generator")
    python_stream.random()
    numpy_stream.random()
    baseline = context.snapshot()
    validation = validate_worldbridge_deterministic_randomness_snapshot(baseline)
    python_stream.random()
    numpy_stream.random()
    restore_worldbridge_deterministic_randomness_context(context, baseline)
    restored = context.snapshot()
    checks = {
        "snapshot_valid": validation == {"valid": True, "errors": []},
        "restore_roundtrip_matches": restored == baseline,
        "global_python_random_touched": baseline["global_python_random_touched"],
        "global_numpy_random_touched": baseline["global_numpy_random_touched"],
    }
    return checks, baseline


def _pause_reset_evidence() -> dict[str, Any]:
    receiver = WorldBridgeSharedStateReceiver()
    start = _envelope(sequence=0, capture_epoch=0, pause_reset_epoch=0, lifecycle_action="start")
    paused = _envelope(
        sequence=1, capture_epoch=1, pause_reset_epoch=1, lifecycle_action="pause", paused=True
    )
    resumed = _envelope(sequence=2, capture_epoch=2, pause_reset_epoch=2, lifecycle_action="resume")
    receiver.accept(start)
    receiver.accept(paused)
    receiver.accept(resumed)
    before = receiver.state_fingerprint()
    regressed = _envelope(sequence=3, capture_epoch=3, pause_reset_epoch=1)
    regression_rejected = False
    try:
        receiver.accept(regressed)
    except ValueError:
        regression_rejected = True
    quarantine = quarantine_worldbridge_shared_state_transport(
        envelope_id="e538-quarantine",
        sequence=3,
        code="bridge_failure",
        stage="snapshot_phase",
        message="isolated bridge failure",
    )
    quarantine_validation = validate_worldbridge_shared_state_envelope(quarantine)
    return {
        "epoch_advanced": receiver.last_pause_reset_epoch == 2,
        "regression_rejected": regression_rejected,
        "regression_rejected_without_mutation": receiver.state_fingerprint() == before,
        "quarantine_valid": quarantine_validation == {"valid": True, "errors": []},
        "quarantine_denies_replay": quarantine["replay_admitted"] is False,
    }


def _checkpoint_evidence(rng_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    feasibility = build_worldbridge_checkpoint_restore_feasibility_contract()
    feasibility_validation = validate_worldbridge_checkpoint_restore_feasibility_contract(feasibility)
    envelope = _envelope(
        sequence=0,
        capture_epoch=0,
        pause_reset_epoch=0,
        rng_context_snapshot=rng_snapshot,
        lifecycle_action="start",
    )
    transport_validation = validate_worldbridge_shared_state_envelope(envelope)
    copied = copy_worldbridge_shared_state_envelope(envelope)
    tampered = copy.deepcopy(envelope)
    tampered["sequence"] = 1
    tampered_validation = validate_worldbridge_shared_state_envelope(tampered)
    receiver = WorldBridgeSharedStateReceiver()
    receiver.accept(envelope)
    return {
        "feasibility_contract_valid": feasibility_validation == {"valid": True, "errors": []},
        "cross_lane_checkpoint_available": feasibility["decision"]["cross_lane_checkpoint_available"],
        "transport_envelope_valid": transport_validation == {"valid": True, "errors": []},
        "transport_copy_isolated": copied is not envelope and copied == envelope,
        "transport_tamper_rejected": tampered_validation["valid"] is False
        and "envelope_digest_mismatch" in tampered_validation["errors"],
        "receiver_accepted": receiver.accepted_count == 1,
    }


def _requirements(evidence: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    validators = {
        "shared_clock_and_delta": all(evidence["clock"]["checks"].values()),
        "shared_queued_input_ordering": all(
            evidence["input"]["checks"].values()
        )
        and all(evidence["canonical_input"].values()),
        "shared_random_seed_contract": (
            evidence["rng"]["checks"]["snapshot_valid"] is True
            and evidence["rng"]["checks"]["restore_roundtrip_matches"] is True
            and evidence["rng"]["checks"]["global_python_random_touched"] is False
            and evidence["rng"]["checks"]["global_numpy_random_touched"] is False
        ),
        "shared_pause_reset_error_isolation": all(evidence["pause_reset"].values()),
        "shared_scene_pond_checkpoint": all(
            value is True
            for key, value in evidence["checkpoint"].items()
            if key != "cross_lane_checkpoint_available"
        )
        and evidence["checkpoint"]["cross_lane_checkpoint_available"] is False,
    }
    source_authority = {
        "shared_clock_and_delta": "worldbridge_clock_ordering_authority",
        "shared_queued_input_ordering": "worldbridge_input_pause_authority",
        "shared_random_seed_contract": "worldbridge_e554_shared_randomness_authority",
        "shared_pause_reset_error_isolation": "worldbridge_shared_state_transport",
        "shared_scene_pond_checkpoint": "worldbridge_checkpoint_restore_feasibility",
    }
    pause_reset_admitted = (
        evidence.get("pause_reset_error_isolation", {}).get("validated") is True
    )
    checkpoint_admitted = (
        evidence.get("scene_pond_checkpoint", {}).get("validated") is True
    )
    clock_admitted = (
        evidence.get("shared_clock_delta", {}).get("validated") is True
    )
    input_admitted = (
        evidence.get("scheduler_input_queue", {}).get("validated") is True
    )
    randomness_admitted = (
        evidence.get("shared_randomness_authority", {}).get("validated")
        is True
    )
    requirements = {}
    for requirement_id in REQUIREMENT_IDS:
        if requirement_id == "shared_clock_and_delta":
            capability_admitted = clock_admitted
        elif requirement_id == "shared_queued_input_ordering":
            capability_admitted = input_admitted
        elif requirement_id == "shared_pause_reset_error_isolation":
            capability_admitted = pause_reset_admitted
        elif requirement_id == "shared_scene_pond_checkpoint":
            capability_admitted = checkpoint_admitted
        elif requirement_id == "shared_random_seed_contract":
            capability_admitted = randomness_admitted
        else:
            capability_admitted = False
        requirements[requirement_id] = {
            "declared": True,
            "validated": bool(validators[requirement_id]),
            "capability_admitted": capability_admitted,
            "blocking": not capability_admitted,
            "source_authority": source_authority[requirement_id],
            "missing_requirements": (
                []
                if capability_admitted
                else list(_MISSING_BY_REQUIREMENT[requirement_id])
            ),
        }
    return requirements


def _pause_reset_error_isolation_evidence(witness: object) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "witness_digest": None,
            "errors": [],
        }
    validation = validate_worldbridge_e550_pause_reset_error_isolation_authority(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness, Mapping)
            and isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "errors": list(validation["errors"]),
    }


def _scene_pond_checkpoint_evidence(witness: object) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "witness_digest": None,
            "errors": [],
        }
    validation = validate_worldbridge_e551_scene_pond_checkpoint_authority(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness, Mapping)
            and isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "errors": list(validation["errors"]),
    }


def _shared_clock_delta_evidence(witness: object) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "witness_digest": None,
            "errors": [],
        }
    validation = validate_worldbridge_e552_shared_clock_delta_authority(witness)
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness, Mapping)
            and isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "errors": list(validation["errors"]),
    }


def _scheduler_input_queue_evidence(witness: object) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "witness_digest": None,
            "errors": [],
        }
    validation = validate_worldbridge_e553_scheduler_input_queue_authority(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness, Mapping)
            and isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "errors": list(validation["errors"]),
    }


def _shared_randomness_authority_evidence(witness: object) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "witness_digest": None,
            "errors": [],
        }
    validation = validate_worldbridge_e554_shared_randomness_authority(witness)
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness, Mapping)
            and isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "errors": list(validation["errors"]),
    }


def _full_unified_replay_evidence(witness: object) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "witness_digest": None,
            "errors": [],
        }
    from .world_bridge_e555_full_unified_runtime_replay_authority import (
        validate_worldbridge_e555_full_unified_runtime_replay_authority,
    )

    validation = validate_worldbridge_e555_full_unified_runtime_replay_authority(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness, Mapping)
            and isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "errors": list(validation["errors"]),
    }


def _unified_default_runtime_readiness_evidence(witness: object) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "witness_digest": None,
            "errors": [],
        }
    from .world_bridge_e556_unified_default_runtime_readiness import (
        validate_worldbridge_e556_unified_default_runtime_readiness,
    )

    validation = validate_worldbridge_e556_unified_default_runtime_readiness(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness, Mapping)
            and isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "errors": list(validation["errors"]),
    }


def _cross_lane_behavior_evidence(witness: object) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "witness_digest": None,
            "errors": [],
        }
    from .world_bridge_e558_cross_lane_behavior_authority import (
        validate_worldbridge_e558_cross_lane_behavior_authority,
    )

    validation = validate_worldbridge_e558_cross_lane_behavior_authority(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness, Mapping)
            and isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "errors": list(validation["errors"]),
    }


def _behavior_equivalence_evidence(witness: object) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "witness_digest": None,
            "routing_witness_digest": None,
            "scope": None,
            "equivalence_policy": None,
            "errors": [],
        }
    from .world_bridge_e560_behavior_equivalence_authority import (
        validate_worldbridge_e560_behavior_equivalence_authority,
    )

    validation = validate_worldbridge_e560_behavior_equivalence_authority(
        witness
    )
    is_mapping = isinstance(witness, Mapping)
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "witness_digest": (
            witness.get("witness_digest") if is_mapping else None
        ),
        "routing_witness_digest": (
            witness.get("routing_witness_digest") if is_mapping else None
        ),
        "scope": witness.get("scope") if is_mapping else None,
        "equivalence_policy": (
            witness.get("equivalence_policy") if is_mapping else None
        ),
        "errors": list(validation["errors"]),
    }


def _serialized_tick_merge_evidence(witness: object) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "witness_digest": None,
            "errors": [],
        }
    from .world_bridge_e559_serialized_tick_merge_authority import (
        validate_worldbridge_e559_serialized_tick_merge_authority,
    )

    validation = validate_worldbridge_e559_serialized_tick_merge_authority(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness, Mapping)
            and isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "errors": list(validation["errors"]),
    }


def _lossless_mapping_evidence(witness: object) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "witness_digest": None,
            "lossless_policy": None,
            "scope": None,
            "portable_checkpoint_lossless": False,
            "errors": [],
        }
    from .world_bridge_e561_lossless_mapping_authority import (
        validate_worldbridge_e561_lossless_mapping_authority,
    )

    validation = validate_worldbridge_e561_lossless_mapping_authority(witness)
    is_mapping = isinstance(witness, Mapping)
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "witness_digest": (
            witness.get("witness_digest") if is_mapping else None
        ),
        "lossless_policy": (
            witness.get("lossless_policy") if is_mapping else None
        ),
        "scope": witness.get("scope") if is_mapping else None,
        "portable_checkpoint_lossless": (
            witness.get("portable_checkpoint_lossless") is True
            if is_mapping
            else False
        ),
        "errors": list(validation["errors"]),
    }


def _script_checkpoint_evidence(witness: object) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "witness_digest": None,
            "scope": None,
            "policy": None,
            "remaining_script_blockers": [],
            "errors": [],
        }
    from .world_bridge_e562_script_checkpoint_authority import (
        validate_worldbridge_e562_script_checkpoint_authority,
    )

    validation = validate_worldbridge_e562_script_checkpoint_authority(witness)
    is_mapping = isinstance(witness, Mapping)
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "witness_digest": (
            witness.get("witness_digest") if is_mapping else None
        ),
        "scope": witness.get("scope") if is_mapping else None,
        "policy": witness.get("policy") if is_mapping else None,
        "remaining_script_blockers": (
            list(witness.get("remaining_script_blockers", ()))
            if is_mapping
            else []
        ),
        "errors": list(validation["errors"]),
    }


def _cross_session_script_evidence(witness: object) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "witness_digest": None,
            "scope": None,
            "policy": None,
            "runtime_contract_version": None,
            "remaining_script_blockers": [],
            "errors": [],
        }
    from .world_bridge_e563_cross_session_script_rehydration import (
        validate_worldbridge_e563_cross_session_script_rehydration_authority,
    )

    validation = (
        validate_worldbridge_e563_cross_session_script_rehydration_authority(
            witness
        )
    )
    is_mapping = isinstance(witness, Mapping)
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "witness_digest": (
            witness.get("witness_digest") if is_mapping else None
        ),
        "scope": witness.get("scope") if is_mapping else None,
        "policy": witness.get("policy") if is_mapping else None,
        "runtime_contract_version": (
            witness.get("runtime_contract_version") if is_mapping else None
        ),
        "remaining_script_blockers": (
            list(witness.get("remaining_script_blockers", ()))
            if is_mapping
            else []
        ),
        "errors": list(validation["errors"]),
    }


def _cross_lane_atomic_checkpoint_evidence(witness: object) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "witness_digest": None,
            "scope": None,
            "policy": None,
            "errors": [],
        }
    from .world_bridge_e565_cross_lane_atomic_checkpoint import (
        validate_worldbridge_e565_cross_lane_atomic_checkpoint_authority,
    )

    validation = (
        validate_worldbridge_e565_cross_lane_atomic_checkpoint_authority(
            witness
        )
    )
    is_mapping = isinstance(witness, Mapping)
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "witness_digest": (
            witness.get("witness_digest") if is_mapping else None
        ),
        "scope": witness.get("scope") if is_mapping else None,
        "policy": witness.get("policy") if is_mapping else None,
        "errors": list(validation["errors"]),
    }


def _build_payload(
    *,
    pause_reset_error_isolation_witness: object = None,
    scene_pond_checkpoint_witness: object = None,
    shared_clock_delta_witness: object = None,
    scheduler_input_queue_witness: object = None,
    shared_randomness_authority_witness: object = None,
    full_unified_replay_witness: object = None,
    unified_default_runtime_readiness_witness: object = None,
    cross_lane_behavior_witness: object = None,
    behavior_equivalence_witness: object = None,
    serialized_tick_merge_witness: object = None,
    lossless_mapping_witness: object = None,
    script_checkpoint_witness: object = None,
    cross_session_script_witness: object = None,
    cross_lane_atomic_checkpoint_witness: object = None,
) -> dict[str, Any]:
    clock = _clock_evidence()
    input_evidence = _input_evidence()
    canonical_input = _canonical_input_evidence()
    rng_checks, rng_snapshot = _rng_evidence()
    pause_reset = _pause_reset_evidence()
    checkpoint = _checkpoint_evidence(rng_snapshot)
    pause_reset_admission = _pause_reset_error_isolation_evidence(
        pause_reset_error_isolation_witness
    )
    checkpoint_admission = _scene_pond_checkpoint_evidence(
        scene_pond_checkpoint_witness
    )
    clock_admission = _shared_clock_delta_evidence(shared_clock_delta_witness)
    input_admission = _scheduler_input_queue_evidence(
        scheduler_input_queue_witness
    )
    randomness_admission = _shared_randomness_authority_evidence(
        shared_randomness_authority_witness
    )
    replay_admission = _full_unified_replay_evidence(
        full_unified_replay_witness
    )
    readiness_admission = _unified_default_runtime_readiness_evidence(
        unified_default_runtime_readiness_witness
    )
    behavior_admission = _cross_lane_behavior_evidence(
        cross_lane_behavior_witness
    )
    behavior_equivalence_admission = _behavior_equivalence_evidence(
        behavior_equivalence_witness
    )
    tick_merge_admission = _serialized_tick_merge_evidence(
        serialized_tick_merge_witness
    )
    lossless_mapping_admission = _lossless_mapping_evidence(
        lossless_mapping_witness
    )
    script_checkpoint_admission = _script_checkpoint_evidence(
        script_checkpoint_witness
    )
    cross_session_script_admission = _cross_session_script_evidence(
        cross_session_script_witness
    )
    cross_lane_atomic_checkpoint_admission = (
        _cross_lane_atomic_checkpoint_evidence(
            cross_lane_atomic_checkpoint_witness
        )
    )
    pause_reset_admitted = pause_reset_admission["validated"] is True
    checkpoint_admitted = checkpoint_admission["validated"] is True
    clock_admitted = clock_admission["validated"] is True
    input_admitted = input_admission["validated"] is True
    randomness_admitted = randomness_admission["validated"] is True
    replay_evidence_validated = replay_admission["validated"] is True
    replay_prerequisites_admitted = all(
        (
            clock_admitted,
            input_admitted,
            randomness_admitted,
            pause_reset_admitted,
            checkpoint_admitted,
        )
    )
    replay_admitted = replay_evidence_validated and replay_prerequisites_admitted
    readiness_evidence_validated = readiness_admission["validated"] is True
    default_ready = readiness_evidence_validated and replay_admitted
    behavior_admitted = behavior_admission["validated"] is True
    behavior_equivalence_admitted = (
        behavior_admitted
        and behavior_equivalence_admission["validated"] is True
        and behavior_equivalence_admission["routing_witness_digest"]
        == behavior_admission["witness_digest"]
    )
    tick_merge_admitted = tick_merge_admission["validated"] is True
    lossless_admitted = lossless_mapping_admission["validated"] is True
    script_checkpoint_admitted = (
        script_checkpoint_admission["validated"] is True
    )
    cross_session_script_admitted = (
        cross_session_script_admission["validated"] is True
    )
    cross_lane_atomic_checkpoint_admitted = (
        cross_lane_atomic_checkpoint_admission["validated"] is True
    )
    evidence = {
        "clock": clock,
        "input": input_evidence,
        "canonical_input": canonical_input,
        "rng": {"checks": rng_checks},
        "pause_reset": pause_reset,
        "pause_reset_error_isolation": pause_reset_admission,
        "scene_pond_checkpoint": checkpoint_admission,
        "shared_clock_delta": clock_admission,
        "scheduler_input_queue": input_admission,
        "shared_randomness_authority": randomness_admission,
        "full_unified_replay": replay_admission,
        "unified_default_runtime_readiness": readiness_admission,
        "cross_lane_behavior": behavior_admission,
        "behavior_equivalence": behavior_equivalence_admission,
        "serialized_tick_merge": tick_merge_admission,
        "lossless_mapping": lossless_mapping_admission,
        "script_checkpoint": script_checkpoint_admission,
        "cross_session_script": cross_session_script_admission,
        "cross_lane_atomic_checkpoint": (
            cross_lane_atomic_checkpoint_admission
        ),
        "checkpoint": checkpoint,
    }
    admissions = {field: False for field in _FALSE_ADMISSIONS}
    admissions["shared_pause_reset_authority"] = pause_reset_admitted
    admissions["cross_lane_error_isolation_admitted"] = pause_reset_admitted
    admissions["partial_failure_compensation_admitted"] = pause_reset_admitted
    admissions["atomic_capture_admitted"] = checkpoint_admitted
    admissions["cross_lane_checkpoint_available"] = checkpoint_admitted
    admissions["cross_lane_restore_available"] = checkpoint_admitted
    admissions["shared_scene_pond_checkpoint"] = checkpoint_admitted
    admissions["shared_clock"] = clock_admitted
    admissions["time_conversion_admitted"] = clock_admitted
    admissions["cross_call_ordering_admitted"] = clock_admitted
    admissions["scheduler_owned"] = input_admitted
    admissions["backpressure_admitted"] = input_admitted
    admissions["dropped_event_policy_admitted"] = input_admitted
    admissions["cross_lane_input_ordering_admitted"] = input_admitted
    admissions["shared_queued_input_ordering"] = input_admitted
    admissions["shared_random_seed_contract"] = randomness_admitted
    admissions["cross_lane_rng_draw_order_admitted"] = randomness_admitted
    admissions["dynamic_entropy_boundary_admitted"] = randomness_admitted
    admissions["native_entropy_boundary_admitted"] = randomness_admitted
    admissions["process_global_entropy_admitted"] = randomness_admitted
    admissions["replay_admitted"] = replay_admitted
    admissions["full_unified_replay_admitted"] = replay_admitted
    admissions["default_ready"] = default_ready
    admissions["cross_lane_behavior_admitted"] = behavior_admitted
    admissions["behavior_routing_admitted"] = behavior_admitted
    admissions["behavior_equivalence_admitted"] = (
        behavior_equivalence_admitted
    )
    admissions["tick_merge_admitted"] = tick_merge_admitted
    admissions["lossless"] = lossless_admitted
    admissions["script_checkpoint_admitted"] = script_checkpoint_admitted
    admissions["cross_session_script_rehydration_admitted"] = (
        cross_session_script_admitted
    )
    admissions["atomic_sr_ps_checkpoint_admitted"] = (
        cross_lane_atomic_checkpoint_admitted
    )
    remaining_blockers = [
        blocker
        for blocker in REMAINING_ADMISSION_BLOCKERS
        if not (
            (
                pause_reset_admitted
                and blocker == PAUSE_RESET_ERROR_ISOLATION_BLOCKER
            )
            or (
                checkpoint_admitted
                and blocker == SCENE_POND_CHECKPOINT_BLOCKER
            )
            or (
                clock_admitted
                and blocker == SHARED_CLOCK_DELTA_BLOCKER
            )
            or (
                input_admitted
                and blocker == SHARED_QUEUED_INPUT_BLOCKER
            )
            or (
                randomness_admitted
                and blocker == SHARED_RANDOMNESS_BLOCKER
            )
            or (
                replay_admitted
                and blocker == FULL_REPLAY_BLOCKER
            )
            or (
                default_ready
                and blocker == DEFAULT_READINESS_BLOCKER
            )
        )
    ]
    do_not_claim = [
        claim
        for claim in DO_NOT_CLAIM
        if not (
            pause_reset_admitted and claim == "shared_pause_reset_authority"
        )
        and not (
            checkpoint_admitted and claim == "shared_scene_pond_checkpoint"
        )
        and not (
            clock_admitted
            and claim
            in {
                "shared_sr_ps_clock",
                "sr_seconds_to_ps_ticks_conversion",
                "cross_call_or_cross_thread_ordering",
            }
        )
        and not (
            input_admitted and claim == "shared_queued_input_ordering"
        )
        and not (
            randomness_admitted and claim == "shared_rng_seed_contract"
        )
        and not (
            replay_admitted and claim == "full_unified_runtime_replay"
        )
        and not (
            default_ready and claim == "unified_pond_default_ready"
        )
        and not (
            tick_merge_admitted and claim == "sr_ps_tick_merge"
        )
        and not (
            behavior_equivalence_admitted
            and claim == "cross_lane_behavior_equivalence"
        )
        and not (
            lossless_admitted
            and claim == "lossless_worldbridge_mapping"
        )
        and not (
            cross_session_script_admitted
            and claim == "cross_session_script_rehydration"
        )
        and not (
            cross_lane_atomic_checkpoint_admitted
            and claim == "atomic_sr_ps_checkpoint"
        )
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "runtime_mode": RUNTIME_MODE,
        "authority_scope": AUTHORITY_SCOPE,
        "requirements": _requirements(evidence),
        "pause_reset_error_isolation_witness": copy.deepcopy(
            pause_reset_error_isolation_witness
        ),
        "pause_reset_error_isolation_evidence": pause_reset_admission,
        "scene_pond_checkpoint_witness": copy.deepcopy(
            scene_pond_checkpoint_witness
        ),
        "scene_pond_checkpoint_evidence": checkpoint_admission,
        "shared_clock_delta_witness": copy.deepcopy(shared_clock_delta_witness),
        "shared_clock_delta_evidence": clock_admission,
        "scheduler_input_queue_witness": copy.deepcopy(
            scheduler_input_queue_witness
        ),
        "scheduler_input_queue_evidence": input_admission,
        "shared_randomness_authority_witness": copy.deepcopy(
            shared_randomness_authority_witness
        ),
        "shared_randomness_authority_evidence": randomness_admission,
        "full_unified_replay_witness": copy.deepcopy(
            full_unified_replay_witness
        ),
        "full_unified_replay_evidence": replay_admission,
        "unified_default_runtime_readiness_witness": copy.deepcopy(
            unified_default_runtime_readiness_witness
        ),
        "unified_default_runtime_readiness_evidence": readiness_admission,
        "cross_lane_behavior_witness": copy.deepcopy(
            cross_lane_behavior_witness
        ),
        "cross_lane_behavior_evidence": behavior_admission,
        "behavior_equivalence_witness": copy.deepcopy(
            behavior_equivalence_witness
        ),
        "behavior_equivalence_evidence": behavior_equivalence_admission,
        "serialized_tick_merge_witness": copy.deepcopy(
            serialized_tick_merge_witness
        ),
        "serialized_tick_merge_evidence": tick_merge_admission,
        "lossless_mapping_witness": copy.deepcopy(
            lossless_mapping_witness
        ),
        "lossless_mapping_evidence": lossless_mapping_admission,
        "script_checkpoint_witness": copy.deepcopy(
            script_checkpoint_witness
        ),
        "script_checkpoint_evidence": script_checkpoint_admission,
        "cross_session_script_witness": copy.deepcopy(
            cross_session_script_witness
        ),
        "cross_session_script_evidence": cross_session_script_admission,
        "cross_lane_atomic_checkpoint_witness": copy.deepcopy(
            cross_lane_atomic_checkpoint_witness
        ),
        "cross_lane_atomic_checkpoint_evidence": (
            cross_lane_atomic_checkpoint_admission
        ),
        "source_evidence": {
            "clock": clock,
            "input": input_evidence,
            "canonical_input": canonical_input,
            "rng": rng_checks,
            "pause_reset": pause_reset,
            "pause_reset_error_isolation": pause_reset_admission,
            "scene_pond_checkpoint": checkpoint_admission,
            "shared_clock_delta": clock_admission,
            "scheduler_input_queue": input_admission,
            "shared_randomness_authority": randomness_admission,
            "full_unified_replay": replay_admission,
            "unified_default_runtime_readiness": readiness_admission,
            "cross_lane_behavior": behavior_admission,
            "behavior_equivalence": behavior_equivalence_admission,
            "serialized_tick_merge": tick_merge_admission,
            "lossless_mapping": lossless_mapping_admission,
            "script_checkpoint": script_checkpoint_admission,
            "cross_session_script": cross_session_script_admission,
            "cross_lane_atomic_checkpoint": (
                cross_lane_atomic_checkpoint_admission
            ),
            "checkpoint": checkpoint,
        },
        "admissions": admissions,
        "remaining_admission_blockers": remaining_blockers,
        "do_not_claim": do_not_claim,
    }


def build_worldbridge_e538_shared_contracts(
    *,
    pause_reset_error_isolation_witness: Mapping[str, Any] | None = None,
    scene_pond_checkpoint_witness: Mapping[str, Any] | None = None,
    shared_clock_delta_witness: Mapping[str, Any] | None = None,
    scheduler_input_queue_witness: Mapping[str, Any] | None = None,
    shared_randomness_authority_witness: Mapping[str, Any] | None = None,
    full_unified_replay_witness: Mapping[str, Any] | None = None,
    unified_default_runtime_readiness_witness: Mapping[str, Any] | None = None,
    cross_lane_behavior_witness: Mapping[str, Any] | None = None,
    behavior_equivalence_witness: Mapping[str, Any] | None = None,
    serialized_tick_merge_witness: Mapping[str, Any] | None = None,
    lossless_mapping_witness: Mapping[str, Any] | None = None,
    script_checkpoint_witness: Mapping[str, Any] | None = None,
    cross_session_script_witness: Mapping[str, Any] | None = None,
    cross_lane_atomic_checkpoint_witness: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build shared contracts, admitting only validated capability witnesses."""
    result = _build_payload(
        pause_reset_error_isolation_witness=pause_reset_error_isolation_witness,
        scene_pond_checkpoint_witness=scene_pond_checkpoint_witness,
        shared_clock_delta_witness=shared_clock_delta_witness,
        scheduler_input_queue_witness=scheduler_input_queue_witness,
        shared_randomness_authority_witness=shared_randomness_authority_witness,
        full_unified_replay_witness=full_unified_replay_witness,
        unified_default_runtime_readiness_witness=(
            unified_default_runtime_readiness_witness
        ),
        cross_lane_behavior_witness=cross_lane_behavior_witness,
        behavior_equivalence_witness=behavior_equivalence_witness,
        serialized_tick_merge_witness=serialized_tick_merge_witness,
        lossless_mapping_witness=lossless_mapping_witness,
        script_checkpoint_witness=script_checkpoint_witness,
        cross_session_script_witness=cross_session_script_witness,
        cross_lane_atomic_checkpoint_witness=(
            cross_lane_atomic_checkpoint_witness
        ),
    )
    result["contract_valid"] = True
    validation = validate_worldbridge_e538_shared_contract(result)
    result["contract_valid"] = validation["valid"]
    return result


def validate_worldbridge_e538_shared_contract(contract: object) -> dict[str, Any]:
    """Validate exact contract shape and reject every unearned admission."""
    errors: list[str] = []
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_must_be_mapping"]}
    if contract.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if contract.get("status") != STATUS:
        errors.append("status_mismatch")
    if contract.get("read_only") is not True:
        errors.append("read_only_required")
    if contract.get("runtime_mode") != RUNTIME_MODE:
        errors.append("runtime_mode_mismatch")
    if contract.get("authority_scope") != AUTHORITY_SCOPE:
        errors.append("authority_scope_overclaim")
    if contract.get("contract_valid") is not True:
        errors.append("contract_valid_required")
    pause_reset_witness = contract.get(
        "pause_reset_error_isolation_witness"
    )
    pause_reset_evidence = _pause_reset_error_isolation_evidence(
        pause_reset_witness
    )
    if (
        pause_reset_evidence["evidence_available"] is True
        and pause_reset_evidence["validated"] is not True
    ):
        errors.append("pause_reset_error_isolation_witness_invalid")
    checkpoint_witness = contract.get("scene_pond_checkpoint_witness")
    checkpoint_evidence = _scene_pond_checkpoint_evidence(checkpoint_witness)
    if (
        checkpoint_evidence["evidence_available"] is True
        and checkpoint_evidence["validated"] is not True
    ):
        errors.append("scene_pond_checkpoint_witness_invalid")
    clock_witness = contract.get("shared_clock_delta_witness")
    clock_evidence = _shared_clock_delta_evidence(clock_witness)
    if (
        clock_evidence["evidence_available"] is True
        and clock_evidence["validated"] is not True
    ):
        errors.append("shared_clock_delta_witness_invalid")
    input_witness = contract.get("scheduler_input_queue_witness")
    input_evidence = _scheduler_input_queue_evidence(input_witness)
    if (
        input_evidence["evidence_available"] is True
        and input_evidence["validated"] is not True
    ):
        errors.append("scheduler_input_queue_witness_invalid")
    randomness_witness = contract.get("shared_randomness_authority_witness")
    randomness_evidence = _shared_randomness_authority_evidence(
        randomness_witness
    )
    if (
        randomness_evidence["evidence_available"] is True
        and randomness_evidence["validated"] is not True
    ):
        errors.append("shared_randomness_authority_witness_invalid")
    replay_witness = contract.get("full_unified_replay_witness")
    replay_evidence = _full_unified_replay_evidence(replay_witness)
    if (
        replay_evidence["evidence_available"] is True
        and replay_evidence["validated"] is not True
    ):
        errors.append("full_unified_replay_witness_invalid")
    readiness_witness = contract.get(
        "unified_default_runtime_readiness_witness"
    )
    readiness_evidence = _unified_default_runtime_readiness_evidence(
        readiness_witness
    )
    if (
        readiness_evidence["evidence_available"] is True
        and readiness_evidence["validated"] is not True
    ):
        errors.append("unified_default_runtime_readiness_witness_invalid")
    behavior_witness = contract.get("cross_lane_behavior_witness")
    behavior_evidence = _cross_lane_behavior_evidence(behavior_witness)
    if (
        behavior_evidence["evidence_available"] is True
        and behavior_evidence["validated"] is not True
    ):
        errors.append("cross_lane_behavior_witness_invalid")
    behavior_equivalence_witness = contract.get(
        "behavior_equivalence_witness"
    )
    behavior_equivalence_evidence = _behavior_equivalence_evidence(
        behavior_equivalence_witness
    )
    if (
        behavior_equivalence_evidence["evidence_available"] is True
        and behavior_equivalence_evidence["validated"] is not True
    ):
        errors.append("behavior_equivalence_witness_invalid")
    tick_merge_witness = contract.get("serialized_tick_merge_witness")
    tick_merge_evidence = _serialized_tick_merge_evidence(
        tick_merge_witness
    )
    if (
        tick_merge_evidence["evidence_available"] is True
        and tick_merge_evidence["validated"] is not True
    ):
        errors.append("serialized_tick_merge_witness_invalid")
    lossless_mapping_witness = contract.get("lossless_mapping_witness")
    lossless_mapping_evidence = _lossless_mapping_evidence(
        lossless_mapping_witness
    )
    if (
        lossless_mapping_evidence["evidence_available"] is True
        and lossless_mapping_evidence["validated"] is not True
    ):
        errors.append("lossless_mapping_witness_invalid")
    script_checkpoint_witness = contract.get("script_checkpoint_witness")
    script_checkpoint_evidence = _script_checkpoint_evidence(
        script_checkpoint_witness
    )
    if (
        script_checkpoint_evidence["evidence_available"] is True
        and script_checkpoint_evidence["validated"] is not True
    ):
        errors.append("script_checkpoint_witness_invalid")
    cross_session_script_witness = contract.get(
        "cross_session_script_witness"
    )
    cross_session_script_evidence = _cross_session_script_evidence(
        cross_session_script_witness
    )
    if (
        cross_session_script_evidence["evidence_available"] is True
        and cross_session_script_evidence["validated"] is not True
    ):
        errors.append("cross_session_script_witness_invalid")
    cross_lane_atomic_checkpoint_witness = contract.get(
        "cross_lane_atomic_checkpoint_witness"
    )
    cross_lane_atomic_checkpoint_evidence = (
        _cross_lane_atomic_checkpoint_evidence(
            cross_lane_atomic_checkpoint_witness
        )
    )
    if (
        cross_lane_atomic_checkpoint_evidence["evidence_available"] is True
        and cross_lane_atomic_checkpoint_evidence["validated"] is not True
    ):
        errors.append("cross_lane_atomic_checkpoint_witness_invalid")
    try:
        expected = _build_payload(
            pause_reset_error_isolation_witness=pause_reset_witness,
            scene_pond_checkpoint_witness=checkpoint_witness,
            shared_clock_delta_witness=clock_witness,
            scheduler_input_queue_witness=input_witness,
            shared_randomness_authority_witness=randomness_witness,
            full_unified_replay_witness=replay_witness,
            unified_default_runtime_readiness_witness=readiness_witness,
            cross_lane_behavior_witness=behavior_witness,
            behavior_equivalence_witness=behavior_equivalence_witness,
            serialized_tick_merge_witness=tick_merge_witness,
            lossless_mapping_witness=lossless_mapping_witness,
            script_checkpoint_witness=script_checkpoint_witness,
            cross_session_script_witness=cross_session_script_witness,
            cross_lane_atomic_checkpoint_witness=(
                cross_lane_atomic_checkpoint_witness
            ),
        )
    except Exception:
        return {"valid": False, "errors": ["source_producer_failed"]}
    actual = dict(contract)
    actual.pop("contract_valid", None)
    if actual != expected:
        errors.append("contract_payload_mismatch")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "AUTHORITY_SCOPE",
    "DO_NOT_CLAIM",
    "DEFAULT_READINESS_BLOCKER",
    "FULL_REPLAY_BLOCKER",
    "PAUSE_RESET_ERROR_ISOLATION_BLOCKER",
    "REMAINING_ADMISSION_BLOCKERS",
    "REQUIREMENT_IDS",
    "SCENE_POND_CHECKPOINT_BLOCKER",
    "SHARED_CLOCK_DELTA_BLOCKER",
    "SHARED_QUEUED_INPUT_BLOCKER",
    "SHARED_RANDOMNESS_BLOCKER",
    "build_worldbridge_e538_shared_contracts",
    "validate_worldbridge_e538_shared_contract",
]
