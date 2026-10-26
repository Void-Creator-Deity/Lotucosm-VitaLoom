# -*- coding: utf-8 -*-
"""Read-only evidence for WorldBridge tick/replay admission boundaries."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .world_bridge_e545_completed_tick_transaction_witness import (
    validate_worldbridge_e545_completed_tick_transaction_witness,
)
from .world_bridge_e546_shared_clock_delta_authority import (
    validate_worldbridge_e546_shared_clock_delta_authority,
)
from .world_bridge_e547_queued_input_handoff_authority import (
    validate_worldbridge_e547_queued_input_handoff_authority,
)
from .world_bridge_e548_rng_draw_order_authority import (
    validate_worldbridge_e548_rng_draw_order_authority,
)
from .world_bridge_e549_pause_reset_lifecycle_authority import (
    validate_worldbridge_e549_pause_reset_lifecycle_authority,
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
from .world_bridge_e555_full_unified_runtime_replay_authority import (
    validate_worldbridge_e555_full_unified_runtime_replay_authority,
)
from .world_bridge_e556_unified_default_runtime_readiness import (
    validate_worldbridge_e556_unified_default_runtime_readiness,
)
from .world_bridge_e558_cross_lane_behavior_authority import (
    validate_worldbridge_e558_cross_lane_behavior_authority,
)
from .world_bridge_e559_serialized_tick_merge_authority import (
    validate_worldbridge_e559_serialized_tick_merge_authority,
)
from .world_bridge_e560_behavior_equivalence_authority import (
    validate_worldbridge_e560_behavior_equivalence_authority,
)
from .world_bridge_e561_lossless_mapping_authority import (
    validate_worldbridge_e561_lossless_mapping_authority,
)
from .world_bridge_e562_script_checkpoint_authority import (
    validate_worldbridge_e562_script_checkpoint_authority,
)
from .world_bridge_e563_cross_session_script_rehydration import (
    validate_worldbridge_e563_cross_session_script_rehydration_authority,
)
from .world_bridge_e565_cross_lane_atomic_checkpoint import (
    validate_worldbridge_e565_cross_lane_atomic_checkpoint_authority,
)
from .world_bridge_e538_shared_contracts import (
    build_worldbridge_e538_shared_contracts,
)


DO_NOT_CLAIM = (
    "sr_ps_tick_merge",
    "full_unified_runtime_replay",
    "cross_lane_behavior_equivalence_outside_declared_scope",
    "lossless_worldbridge_mapping",
    "portable_sr_executable_script_checkpoint",
    "cross_session_script_rehydration",
    "unified_pond_default_ready",
)


def _completed_tick_transaction_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e545_completed_tick_transaction_witness(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }


def _shared_clock_delta_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e546_shared_clock_delta_authority(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }

def _queued_input_handoff_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e547_queued_input_handoff_authority(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }

def _rng_draw_order_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e548_rng_draw_order_authority(witness)
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }


def _pause_reset_lifecycle_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e549_pause_reset_lifecycle_authority(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }


def _pause_reset_error_isolation_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = (
        validate_worldbridge_e550_pause_reset_error_isolation_authority(witness)
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }


def _scene_pond_checkpoint_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e551_scene_pond_checkpoint_authority(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }


def _shared_clock_delta_authority_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e552_shared_clock_delta_authority(witness)
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }


def _scheduler_input_queue_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e553_scheduler_input_queue_authority(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }


def _shared_randomness_authority_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e554_shared_randomness_authority(witness)
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }


def _full_unified_replay_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e555_full_unified_runtime_replay_authority(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }


def _unified_default_runtime_readiness_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e556_unified_default_runtime_readiness(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }


def _cross_lane_behavior_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e558_cross_lane_behavior_authority(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }


def _serialized_tick_merge_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e559_serialized_tick_merge_authority(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }


def _behavior_equivalence_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "routing_witness_digest": None,
            "scope": None,
            "equivalence_policy": None,
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e560_behavior_equivalence_authority(
        witness
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "routing_witness_digest": (
            witness.get("routing_witness_digest")
            if isinstance(witness.get("routing_witness_digest"), str)
            else None
        ),
        "scope": witness.get("scope"),
        "equivalence_policy": witness.get("equivalence_policy"),
        "grants_admission": False,
        "admission_effect": "none",
    }


def _lossless_mapping_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "lossless_policy": None,
            "scope": None,
            "portable_checkpoint_lossless": False,
            "silent_loss_cells": [],
            "nonportable_owner_boundaries": [],
            "remaining_lossless_blockers": [],
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e561_lossless_mapping_authority(witness)
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "lossless_policy": witness.get("lossless_policy"),
        "scope": witness.get("scope"),
        "portable_checkpoint_lossless": (
            witness.get("portable_checkpoint_lossless") is True
        ),
        "silent_loss_cells": list(witness.get("silent_loss_cells", ())),
        "nonportable_owner_boundaries": list(
            witness.get("nonportable_owner_boundaries", ())
        ),
        "remaining_lossless_blockers": list(
            witness.get("remaining_lossless_blockers", ())
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }


def _script_checkpoint_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "scope": None,
            "policy": None,
            "remaining_script_blockers": [],
            "grants_admission": False,
            "admission_effect": "none",
        }
    validation = validate_worldbridge_e562_script_checkpoint_authority(witness)
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": (
            witness.get("witness_digest")
            if isinstance(witness.get("witness_digest"), str)
            else None
        ),
        "scope": witness.get("scope"),
        "policy": witness.get("policy"),
        "remaining_script_blockers": list(
            witness.get("remaining_script_blockers", ())
        ),
        "grants_admission": False,
        "admission_effect": "none",
    }


def _cross_session_script_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "scope": None,
            "policy": None,
            "runtime_contract_version": None,
            "remaining_script_blockers": [],
            "grants_admission": False,
        }
    validation = (
        validate_worldbridge_e563_cross_session_script_rehydration_authority(
            witness
        )
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": witness.get("witness_digest"),
        "scope": witness.get("scope"),
        "policy": witness.get("policy"),
        "runtime_contract_version": witness.get("runtime_contract_version"),
        "remaining_script_blockers": list(
            witness.get("remaining_script_blockers", ())
        ),
        "grants_admission": witness.get("grants_admission") is True,
    }


def _cross_lane_atomic_checkpoint_evidence(
    witness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if witness is None:
        return {
            "evidence_available": False,
            "validated": False,
            "errors": [],
            "witness_digest": None,
            "scope": None,
            "policy": None,
        }
    validation = (
        validate_worldbridge_e565_cross_lane_atomic_checkpoint_authority(
            witness
        )
    )
    return {
        "evidence_available": True,
        "validated": validation["valid"],
        "errors": list(validation["errors"]),
        "witness_digest": witness.get("witness_digest"),
        "scope": witness.get("scope"),
        "policy": witness.get("policy"),
    }


def build_worldbridge_tick_replay_admission(
    *,
    completed_tick_transaction_witness: Mapping[str, Any] | None = None,
    shared_clock_delta_witness: Mapping[str, Any] | None = None,
    queued_input_handoff_witness: Mapping[str, Any] | None = None,
    rng_draw_order_witness: Mapping[str, Any] | None = None,
    pause_reset_lifecycle_witness: Mapping[str, Any] | None = None,
    pause_reset_error_isolation_witness: Mapping[str, Any] | None = None,
    scene_pond_checkpoint_witness: Mapping[str, Any] | None = None,
    shared_clock_delta_authority_witness: Mapping[str, Any] | None = None,
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
    """Describe dual-lane tick evidence without mutating either lane.

    Valid E545 transaction and E546 shared-clock-delta witnesses are retained
    as independently validated evidence only. Neither can remove blockers or
    turn any admission flag on.
    """
    shared_contracts = build_worldbridge_e538_shared_contracts(
        pause_reset_error_isolation_witness=(
            pause_reset_error_isolation_witness
        ),
        scene_pond_checkpoint_witness=scene_pond_checkpoint_witness,
        shared_clock_delta_witness=shared_clock_delta_authority_witness,
        scheduler_input_queue_witness=scheduler_input_queue_witness,
        shared_randomness_authority_witness=(
            shared_randomness_authority_witness
        ),
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
    replay_evidence = _full_unified_replay_evidence(
        full_unified_replay_witness
    )
    replay_admitted = (
        shared_contracts["contract_valid"] is True
        and replay_evidence["validated"] is True
        and shared_contracts["admissions"]["replay_admitted"] is True
    )
    readiness_evidence = _unified_default_runtime_readiness_evidence(
        unified_default_runtime_readiness_witness
    )
    default_ready = (
        replay_admitted
        and readiness_evidence["validated"] is True
        and shared_contracts["admissions"]["default_ready"] is True
    )
    behavior_evidence = _cross_lane_behavior_evidence(
        cross_lane_behavior_witness
    )
    cross_lane_behavior_admitted = (
        behavior_evidence["validated"] is True
        and shared_contracts["admissions"]["cross_lane_behavior_admitted"]
        is True
    )
    behavior_equivalence_evidence = _behavior_equivalence_evidence(
        behavior_equivalence_witness
    )
    behavior_equivalence_admitted = (
        behavior_equivalence_evidence["validated"] is True
        and shared_contracts["admissions"]["behavior_equivalence_admitted"]
        is True
    )
    lossless_mapping_evidence = _lossless_mapping_evidence(
        lossless_mapping_witness
    )
    lossless_admitted = (
        lossless_mapping_evidence["validated"] is True
        and shared_contracts["admissions"]["lossless"] is True
    )
    script_checkpoint_evidence = _script_checkpoint_evidence(
        script_checkpoint_witness
    )
    script_checkpoint_admitted = (
        script_checkpoint_evidence["validated"] is True
        and shared_contracts["admissions"]["script_checkpoint_admitted"] is True
    )
    cross_session_script_evidence = _cross_session_script_evidence(
        cross_session_script_witness
    )
    cross_session_script_admitted = (
        cross_session_script_evidence["validated"] is True
        and shared_contracts["admissions"][
            "cross_session_script_rehydration_admitted"
        ]
        is True
    )
    cross_lane_atomic_checkpoint_evidence = (
        _cross_lane_atomic_checkpoint_evidence(
            cross_lane_atomic_checkpoint_witness
        )
    )
    atomic_sr_ps_checkpoint_admitted = (
        cross_lane_atomic_checkpoint_evidence["validated"] is True
        and shared_contracts["admissions"][
            "atomic_sr_ps_checkpoint_admitted"
        ]
        is True
    )
    tick_merge_evidence = _serialized_tick_merge_evidence(
        serialized_tick_merge_witness
    )
    tick_merge_admitted = (
        tick_merge_evidence["validated"] is True
        and shared_contracts["admissions"]["tick_merge_admitted"] is True
    )
    return {
        "schema_version": 1,
        "status": "worldbridge_tick_replay_admission",
        "read_only": True,
        "runtime_mode": "dual",
        "tick_merge_admitted": tick_merge_admitted,
        "replay_admitted": replay_admitted,
        "full_unified_replay_admitted": replay_admitted,
        "behavior_routing_admitted": cross_lane_behavior_admitted,
        "behavior_equivalence_admitted": behavior_equivalence_admitted,
        "lossless": lossless_admitted,
        "script_checkpoint_admitted": script_checkpoint_admitted,
        "cross_session_script_rehydration_admitted": (
            cross_session_script_admitted
        ),
        "atomic_sr_ps_checkpoint_admitted": (
            atomic_sr_ps_checkpoint_admitted
        ),
        "default_ready": default_ready,
        "cross_lane_behavior_admitted": cross_lane_behavior_admitted,
        "sr_lane": {
            "entrypoint": "GameViewport._update_simulation",
            "clock": {
                "delta_expression": "0.05 * max(0.2, simulation_speed)",
                "scene_time_owner": "GameViewport._scene_runtime_time",
            },
            "phase_order": [
                "script",
                "spawn",
                "actuator",
                "fluid",
                "physics",
                "survival",
                "snapshot",
            ],
            "input_contract": "SrInputState.snapshot is captured during SR tick preparation",
        },
        "ps_lane": {
            "entrypoint": "world_bridge.unified_pond_step -> Pond.update",
            "clock": {
                "bridge_delta_consumed_by_pond": False,
                "pond_time_increment": 1,
                "root_entity_update_delta": 1.0,
            },
            "input_contract": "no shared SR/PS queued-input contract",
        },
        "bridge_handoff": {
            "location": "GameViewport.run_snapshot_phase",
            "order": [
                "complete_SR_phases",
                "refresh_SR_HUD",
                "sync_SR_to_PS",
                "Pond.update",
                "sync_PS_to_SR_display",
                "publish_SR_snapshots",
            ],
            "failure_isolation": "bridge exceptions are logged and do not merge scheduler authority",
        },
        "persistence_and_replay": {
            "sr_scene_contract": ".pond scene descriptor/runtime path",
            "ps_pond_contract": "Pond.save_pond/load_pond and OrganismSerializer",
            "shared_checkpoint_contract": False,
            "shared_input_log_contract": False,
            "shared_random_seed_contract": False,
            "full_replay_contract": False,
        },
        "completed_tick_transaction_evidence": (
            _completed_tick_transaction_evidence(
                completed_tick_transaction_witness
            )
        ),
        "shared_clock_delta_evidence": (
            _shared_clock_delta_evidence(shared_clock_delta_witness)
        ),
        "queued_input_handoff_evidence": (
            _queued_input_handoff_evidence(queued_input_handoff_witness)
        ),
        "rng_draw_order_evidence": (
            _rng_draw_order_evidence(rng_draw_order_witness)
        ),
        "pause_reset_lifecycle_evidence": (
            _pause_reset_lifecycle_evidence(pause_reset_lifecycle_witness)
        ),
        "pause_reset_error_isolation_evidence": (
            _pause_reset_error_isolation_evidence(
                pause_reset_error_isolation_witness
            )
        ),
        "scene_pond_checkpoint_evidence": (
            _scene_pond_checkpoint_evidence(scene_pond_checkpoint_witness)
        ),
        "shared_clock_delta_authority_evidence": (
            _shared_clock_delta_authority_evidence(
                shared_clock_delta_authority_witness
            )
        ),
        "scheduler_input_queue_evidence": (
            _scheduler_input_queue_evidence(scheduler_input_queue_witness)
        ),
        "shared_randomness_authority_evidence": (
            _shared_randomness_authority_evidence(
                shared_randomness_authority_witness
            )
        ),
        "full_unified_replay_evidence": replay_evidence,
        "unified_default_runtime_readiness_evidence": readiness_evidence,
        "cross_lane_behavior_evidence": behavior_evidence,
        "behavior_equivalence_evidence": behavior_equivalence_evidence,
        "lossless_mapping_evidence": lossless_mapping_evidence,
        "script_checkpoint_evidence": script_checkpoint_evidence,
        "cross_session_script_evidence": cross_session_script_evidence,
        "cross_lane_atomic_checkpoint_evidence": (
            cross_lane_atomic_checkpoint_evidence
        ),
        "serialized_tick_merge_evidence": tick_merge_evidence,
        "shared_contracts": shared_contracts,
        "shared_contracts_valid": shared_contracts["contract_valid"],
        "remaining_admission_blockers": list(
            shared_contracts["remaining_admission_blockers"]
        ),
        "do_not_claim": [
            claim
            for claim in DO_NOT_CLAIM
            if not (
                lossless_admitted
                and claim == "lossless_worldbridge_mapping"
            )
            and not (
                cross_session_script_admitted
                and claim == "cross_session_script_rehydration"
            )
        ],
    }


__all__ = ["build_worldbridge_tick_replay_admission", "DO_NOT_CLAIM"]
