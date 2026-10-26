# -*- coding: utf-8 -*-
"""Read-only WorldBridge/unified Pond gate evidence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from collections.abc import Mapping

from core.Lotucosm.runtime.world_bridge_mapping_audit import build_worldbridge_mapping_audit
from core.Lotucosm.runtime.world_bridge_checkpoint_mapping_audit import (
    build_worldbridge_checkpoint_mapping_audit,
)
from core.Lotucosm.runtime.world_bridge_script_mapping_audit import (
    build_worldbridge_script_mapping_audit,
)
from core.Lotucosm.runtime.world_bridge_render_identity_audit import (
    build_worldbridge_render_identity_audit,
)
from core.Lotucosm.runtime.world_bridge_topology_mapping_audit import (
    build_worldbridge_topology_mapping_audit,
)
from core.Lotucosm.runtime.world_bridge_membrane_behavior_audit import (
    build_worldbridge_membrane_behavior_audit,
)
from core.Lotucosm.runtime.world_bridge_lane_local_roundtrip import (
    build_worldbridge_lane_local_roundtrip_ps_contract,
    build_worldbridge_lane_local_roundtrip_sr_contract,
)
from core.Lotucosm.runtime.world_bridge_topology_corpus_artifact import (
    validate_worldbridge_topology_corpus_artifact,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    build_worldbridge_e538_shared_contracts,
)
from core.Lotucosm.runtime.world_bridge_clock_ordering_authority import (
    build_worldbridge_clock_ordering_authority_contract,
)
from core.Lotucosm.runtime.world_bridge_input_pause_authority import (
    build_worldbridge_input_pause_authority_contract,
)
from core.Lotucosm.runtime.world_bridge_dual_lane_trace import (
    build_worldbridge_dual_lane_trace_contract,
)
from core.Lotucosm.runtime.world_bridge_live_trace_producer import (
    build_worldbridge_live_trace_producer_contract,
)
from core.Lotucosm.runtime.world_bridge_live_trace_comparability import (
    build_worldbridge_live_trace_comparability_contract,
)
from core.Lotucosm.runtime.world_bridge_live_trace_time_series import (
    build_worldbridge_live_trace_time_series_contract,
)
from core.Lotucosm.runtime.world_bridge_live_capture_session import (
    build_worldbridge_live_capture_session_contract,
)
from core.Lotucosm.runtime.world_bridge_live_capture_artifact import (
    build_worldbridge_live_capture_artifact_contract,
)
from core.Lotucosm.runtime.world_bridge_randomness_authority import (
    build_worldbridge_randomness_authority_contract,
)
from core.Lotucosm.runtime.world_bridge_sr_runtime_randomness import (
    build_worldbridge_sr_runtime_randomness_contract,
)
from core.Lotucosm.runtime.world_bridge_transaction_authority import (
    build_worldbridge_transaction_failure_isolation_contract,
)
from core.Lotucosm.runtime.world_bridge_checkpoint_restore_feasibility import (
    build_worldbridge_checkpoint_restore_feasibility_contract,
)
from core.Lotucosm.runtime.world_bridge_e313_bounded_replay_corpus import (
    build_worldbridge_e313_bounded_replay_corpus,
)
from core.Lotucosm.runtime.world_bridge_e313_live_capture_binding import (
    build_worldbridge_e313_live_capture_binding,
)
from core.Lotucosm.runtime.world_bridge_recovery_authority import (
    build_worldbridge_recovery_compensation_controlled_restart_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_readmission_authority import (
    build_worldbridge_failure_quarantine_readmission_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_diagnostic_provenance import (
    build_worldbridge_quarantine_diagnostic_provenance_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_lifecycle_correlation import (
    build_worldbridge_quarantine_lifecycle_correlation_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
    build_worldbridge_quarantine_operator_presentation_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export import (
    build_worldbridge_quarantine_operator_presentation_export_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export_audit import (
    build_worldbridge_quarantine_operator_presentation_export_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_evidence_bundle import (
    build_worldbridge_quarantine_operator_evidence_bundle_contract,
)
from core.Lotucosm.runtime.world_bridge_e512_provenance_receipt import (
    build_worldbridge_e512_provenance_receipt_contract,
    build_worldbridge_e512_provenance_receipt_status,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_surface_audit import (
    build_worldbridge_quarantine_operator_presentation_surface_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_surface_receipt import (
    build_worldbridge_quarantine_operator_presentation_surface_receipt_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_receipt_consumer import (
    build_worldbridge_quarantine_operator_presentation_receipt_consumer_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_consumer_non_consumption_audit import (
    build_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_e263_aggregate_provenance_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_e264_envelope_consistency_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_e265_portable_witness_attestation import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_random_state_observation_binding import (
    build_worldbridge_random_state_observation_binding_contract,
)
from core.Lotucosm.runtime.world_bridge_e266_cross_record_attestation_matrix_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix_contract,
)
from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    build_worldbridge_deterministic_randomness_context_contract,
)
from core.Lotucosm.runtime.world_bridge_shared_state_transport import (
    build_worldbridge_shared_state_transport_contract,
)
from core.Lotucosm.runtime.world_bridge_e315_shared_state_transport_binding import (
    build_worldbridge_e315_shared_state_transport_binding,
)
from core.Lotucosm.runtime.world_bridge_e316_checkpoint_restore_witness import (
    build_worldbridge_e316_checkpoint_restore_witness,
)
from core.Lotucosm.runtime.world_bridge_e317_live_checkpoint_gap_audit import (
    build_worldbridge_e317_live_checkpoint_gap_audit,
)
from core.Lotucosm.runtime.world_bridge_e366_live_checkpoint_admission import (
    build_worldbridge_e366_live_checkpoint_admission_contract,
)
from core.Lotucosm.runtime.world_bridge_e367_live_viewport_witness import (
    build_worldbridge_e367_live_viewport_witness_contract,
)
from core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter import (
    build_game_viewport_live_checkpoint_adapter_contract,
)
from core.Lotucosm.script_entropy_audit import (
    build_script_entropy_admission_contract,
)
from core.Lotucosm.runtime.world_bridge_fresh_restore_parity import (
    build_worldbridge_fresh_restore_parity_contract,
)
from core.Lotucosm.runtime.world_bridge_fresh_sr_restore import (
    build_worldbridge_fresh_sr_restore_contract,
)
from core.Lotucosm.runtime.world_bridge_e382_restore_receipt import (
    validate_e382_receipt,
)
from core.Lotucosm.runtime.world_bridge_e384_receipt_ledger import (
    consume_e382_receipt_durable,
)
from core.VitaLoom.simulation.sr_runtime_structure_parity import (
    SCHEMA_VERSION as SR_STRUCTURE_PARITY_SCHEMA_VERSION,
    STATUS as SR_STRUCTURE_PARITY_STATUS,
)
from core.Lotucosm.runtime.world_bridge_named_stream_adapter import (
    build_worldbridge_named_stream_adapter_contract,
    build_worldbridge_respawn_two_stream_handoff_contract,
)
from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import (
    build_worldbridge_respawn_two_stream_artifact_contract,
)
from core.Lotucosm.runtime.world_bridge_respawn_artifact_inspection import (
    build_worldbridge_respawn_artifact_inspection_contract,
)
from core.Lotucosm.runtime.world_bridge_respawn_artifact_diagnostics import (
    build_worldbridge_respawn_artifact_diagnostic_projection_contract,
)
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_consumer import (
    build_worldbridge_respawn_diagnostic_consumer_contract,
)
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_presentation import (
    build_worldbridge_respawn_diagnostic_presentation_contract,
)
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_export import (
    build_worldbridge_respawn_diagnostic_export_contract,
)
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_export_audit import (
    build_worldbridge_respawn_diagnostic_export_audit_contract,
)


DO_NOT_CLAIM = (
    "unified_pond_default_ready",
    "lossless_worldbridge_mapping",
    "portable_sr_executable_script_checkpoint",
    "cross_session_script_rehydration",
    "sr_ps_tick_merge",
    "full_unified_runtime_replay",
    "cross_lane_behavior_equivalence_outside_declared_scope",
    "branching_history_conflict_resolution",
    "opengl_default_ready",
    "sr2d_native_acceleration",
)

KNOWN_GAPS = (
    "lossless_mapping",
    "membrane_script_component_roundtrip",
    "full_unified_runtime_replay",
    "default_readiness",
)


def _load_project_config(project_path: Path | None) -> dict[str, Any]:
    if project_path is None:
        return {}
    config_path = project_path / "project.json"
    if not config_path.is_file():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _world_bridge_import_state() -> tuple[bool, str, str, bool]:
    try:
        from core.Lotucosm.runtime import world_bridge

        return (
            True,
            str(world_bridge.RUNTIME_MODE_DUAL),
            str(world_bridge.RUNTIME_MODE_UNIFIED),
            callable(getattr(world_bridge, "unified_pond_step", None)),
        )
    except Exception:
        return False, "dual", "unified_pond", False


def build_runtime_worldbridge_status(
    project_path: Path | None = None,
    *,
    live_checkpoint_witness: Mapping[str, Any] | None = None,
    live_checkpoint_cleanup: Mapping[str, Any] | None = None,
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
    field_roundtrip_witness: Mapping[str, Any] | None = None,
    cross_lane_behavior_witness: Mapping[str, Any] | None = None,
    behavior_equivalence_witness: Mapping[str, Any] | None = None,
    serialized_tick_merge_witness: Mapping[str, Any] | None = None,
    lossless_mapping_witness: Mapping[str, Any] | None = None,
    script_checkpoint_witness: Mapping[str, Any] | None = None,
    cross_session_script_witness: Mapping[str, Any] | None = None,
    cross_lane_atomic_checkpoint_witness: Mapping[str, Any] | None = None,
    project_write_authority_witness: Mapping[str, Any] | None = None,
    script_portability_boundary_witness: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    project_config = _load_project_config(project_path)
    importable, dual_mode, unified_mode, step_available = _world_bridge_import_state()

    runtime_mode = dual_mode
    unified_enabled = False
    if importable:
        from core.Lotucosm.runtime.world_bridge import resolve_runtime_mode, unified_pond_enabled

        runtime_mode = resolve_runtime_mode(project_config)
        unified_enabled = unified_pond_enabled(project_config)

    cross_session_script_evidence: dict[str, Any] = {
        "evidence_available": False,
        "validated": False,
        "witness_digest": None,
        "scope": None,
        "policy": None,
        "runtime_contract_version": None,
        "remaining_script_blockers": [],
        "errors": [],
    }
    if cross_session_script_witness is not None:
        from core.Lotucosm.runtime.world_bridge_e563_cross_session_script_rehydration import (
            validate_worldbridge_e563_cross_session_script_rehydration_authority,
        )

        validation = (
            validate_worldbridge_e563_cross_session_script_rehydration_authority(
                cross_session_script_witness
            )
        )
        cross_session_script_evidence = {
            "evidence_available": True,
            "validated": validation["valid"],
            "witness_digest": cross_session_script_witness.get(
                "witness_digest"
            ),
            "scope": cross_session_script_witness.get("scope"),
            "policy": cross_session_script_witness.get("policy"),
            "runtime_contract_version": cross_session_script_witness.get(
                "runtime_contract_version"
            ),
            "remaining_script_blockers": list(
                cross_session_script_witness.get(
                    "remaining_script_blockers", ()
                )
            ),
            "errors": list(validation["errors"]),
        }
    cross_session_script_admitted = (
        cross_session_script_evidence["validated"] is True
    )
    cross_lane_atomic_checkpoint_evidence: dict[str, Any] = {
        "evidence_available": False,
        "validated": False,
        "witness_digest": None,
        "scope": None,
        "policy": None,
        "errors": [],
    }
    if cross_lane_atomic_checkpoint_witness is not None:
        from core.Lotucosm.runtime.world_bridge_e565_cross_lane_atomic_checkpoint import (
            validate_worldbridge_e565_cross_lane_atomic_checkpoint_authority,
        )

        validation = (
            validate_worldbridge_e565_cross_lane_atomic_checkpoint_authority(
                cross_lane_atomic_checkpoint_witness
            )
        )
        cross_lane_atomic_checkpoint_evidence = {
            "evidence_available": True,
            "validated": validation["valid"],
            "witness_digest": cross_lane_atomic_checkpoint_witness.get(
                "witness_digest"
            ),
            "scope": cross_lane_atomic_checkpoint_witness.get("scope"),
            "policy": cross_lane_atomic_checkpoint_witness.get("policy"),
            "errors": list(validation["errors"]),
        }
    atomic_sr_ps_checkpoint_admitted = (
        cross_lane_atomic_checkpoint_evidence["validated"] is True
    )
    project_write_authority_evidence: dict[str, Any] = {
        "evidence_available": False,
        "validated": False,
        "witness_digest": None,
        "scope": None,
        "errors": [],
    }
    if project_write_authority_witness is not None:
        from core.VitaLoom.project.project_write_authority import (
            validate_project_write_authority_witness,
        )

        validation = validate_project_write_authority_witness(
            project_write_authority_witness
        )
        project_write_authority_evidence = {
            "evidence_available": True,
            "validated": validation["valid"],
            "witness_digest": project_write_authority_witness.get(
                "witness_digest"
            ),
            "scope": project_write_authority_witness.get("scope"),
            "errors": list(validation["errors"]),
        }
    global_cross_process_atomicity_admitted = (
        project_write_authority_evidence["validated"] is True
    )
    script_portability_boundary_evidence: dict[str, Any] = {
        "evidence_available": False,
        "validated": False,
        "witness_digest": None,
        "scope": None,
        "policy": None,
        "errors": [],
    }
    if script_portability_boundary_witness is not None:
        from core.Lotucosm.runtime.world_bridge_e567_script_portability_boundary import (
            validate_worldbridge_e567_script_portability_boundary,
        )

        validation = validate_worldbridge_e567_script_portability_boundary(
            script_portability_boundary_witness
        )
        script_portability_boundary_evidence = {
            "evidence_available": True,
            "validated": validation["valid"],
            "witness_digest": script_portability_boundary_witness.get(
                "witness_digest"
            ),
            "scope": script_portability_boundary_witness.get("scope"),
            "policy": script_portability_boundary_witness.get("policy"),
            "errors": list(validation["errors"]),
        }
    executable_source_portability_boundary_closed = (
        script_portability_boundary_evidence["validated"] is True
    )
    do_not_claim = list(DO_NOT_CLAIM)
    if cross_session_script_admitted:
        do_not_claim.remove("cross_session_script_rehydration")
    if (
        atomic_sr_ps_checkpoint_admitted
        and "atomic_sr_ps_checkpoint" in do_not_claim
    ):
        do_not_claim.remove("atomic_sr_ps_checkpoint")

    return {
        "schema_version": 1,
        "status": "worldbridge_gate_evidence",
        "read_only": True,
        "project_path": str(project_path) if project_path else None,
        "runtime_mode": runtime_mode,
        "unified_pond_enabled": bool(unified_enabled),
        "default_ready": False,
        "world_bridge_importable": bool(importable),
        "pilot_modules": [
            "world_bridge_module",
            "game_viewport_opt_in_hooks",
            "comparability_module",
            "time_series_aggregation_module",
            "bounded_capture_session_module",
            "sealed_capture_artifact_module",
            "randomness_authority_module",
            "sr_runtime_randomness_ownership_module",
            "cross_lane_transaction_failure_isolation_module",
            "cross_lane_checkpoint_restore_feasibility_module",
            "e313_bounded_replay_corpus_module",
            "e313_live_capture_binding_module",
            "shared_state_transport_module",
            "e315_shared_state_transport_binding_module",
            "e316_checkpoint_restore_witness_module",
            "e317_live_checkpoint_gap_audit_module",
            "e366_live_checkpoint_admission_module",
            "e367_live_viewport_witness_module",
            "e319_game_viewport_live_checkpoint_adapter_module",
            "script_entropy_admission_module",
            "fresh_ps_restore_parity_module",
            "fresh_sr_restore_parity_module",
            "sr_runtime_structure_parity_module",
            "e379_tick_envelope_module",
            "e380_tick_execution_module",
            "e381_tick_sequence_module",
            "e382_restore_receipt_module",
            "cross_lane_recovery_compensation_controlled_restart_module",
            "failure_quarantine_opt_in_handoff_readmission_module",
            "quarantine_diagnostic_provenance_module",
            "quarantine_diagnostic_query_host_module",
            "quarantine_lifecycle_correlation_module",
            "quarantine_operator_presentation_module",
            "quarantine_operator_presentation_export_module",
            "quarantine_operator_presentation_export_audit_module",
            "quarantine_operator_evidence_bundle_module",
            "e512_provenance_receipt_module",
            "quarantine_operator_presentation_surface_audit_module",
            "quarantine_operator_presentation_surface_receipt_module",
            "quarantine_operator_presentation_receipt_consumer_module",
            "quarantine_operator_presentation_consumer_non_consumption_audit_module",
            "quarantine_operator_presentation_status_projection_audit_module",
            "quarantine_operator_presentation_status_projection_boundary_audit_module",
            "quarantine_operator_presentation_status_projection_boundary_compatibility_audit_module",
            "quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_module",
            "quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_module",
            "quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit_module",
            "quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_module",
            "quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_module",
            "quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_module",
            "quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit_module",
            "quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit_module",
            "quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit_module",
            "quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit_module",
            "quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit_module",
            "quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit_module",
            "quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_module",
            "quarantine_operator_presentation_status_projection_boundary_portable_witness_attestation_cross_record_attestation_matrix_audit_module",
            "random_state_observation_binding_module",
            "deterministic_randomness_context_module",
            "named_stream_sr_mind_adapter_module",
            "respawn_two_stream_handoff_module",
            "respawn_two_stream_artifact_module",
            "respawn_artifact_inspection_module",
            "respawn_artifact_diagnostic_projection_module",
            "respawn_diagnostic_consumer_module",
            "respawn_diagnostic_presentation_module",
            "respawn_diagnostic_export_module",
            "respawn_diagnostic_export_audit_module",
        ],
        "evidence": {
            "explicit_project_flag": runtime_mode == unified_mode,
            "world_bridge_step_available": bool(step_available),
            "focused_tests": [
                "tests/test_plasticity_and_world_bridge.py",
                "tests/test_game_viewport_unified_bridge.py",
                "tests/test_comparability.py",
            ],
            "comparability_smoke": {
                "command": "python -B tools/run_dual_comparability.py --ticks 20 --checkpoint 10 --checkpoint 20",
                "ticks": 20,
                "checkpoints": [10, 20],
            },
        },
        "known_gaps": list(KNOWN_GAPS),
        "mapping_audit": build_worldbridge_mapping_audit(
            field_roundtrip_witness,
            cross_lane_behavior_witness,
            serialized_tick_merge_witness,
            behavior_equivalence_witness,
            lossless_mapping_witness,
            script_checkpoint_witness,
            cross_session_script_witness,
        ),
        "checkpoint_mapping_audit": build_worldbridge_checkpoint_mapping_audit(),
        "script_mapping_audit": build_worldbridge_script_mapping_audit(),
        "render_identity_audit": build_worldbridge_render_identity_audit(),
        "topology_mapping_audit": build_worldbridge_topology_mapping_audit(),
        "membrane_behavior_audit": build_worldbridge_membrane_behavior_audit(),
        "lane_local_roundtrip_sr_contract": build_worldbridge_lane_local_roundtrip_sr_contract(),
        "lane_local_roundtrip_ps_contract": build_worldbridge_lane_local_roundtrip_ps_contract(),
        "tick_replay_admission": build_worldbridge_tick_replay_admission(
            completed_tick_transaction_witness=completed_tick_transaction_witness,
            shared_clock_delta_witness=shared_clock_delta_witness,
            queued_input_handoff_witness=queued_input_handoff_witness,
            rng_draw_order_witness=rng_draw_order_witness,
            pause_reset_lifecycle_witness=pause_reset_lifecycle_witness,
            pause_reset_error_isolation_witness=(
                pause_reset_error_isolation_witness
            ),
            scene_pond_checkpoint_witness=scene_pond_checkpoint_witness,
            shared_clock_delta_authority_witness=(
                shared_clock_delta_authority_witness
            ),
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
        ),
        "e538_shared_contracts": build_worldbridge_e538_shared_contracts(
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
        ),
        "common_clock_cross_lane_ordering_authority_contract": build_worldbridge_clock_ordering_authority_contract(),
        "shared_queued_input_pause_reset_authority_contract": build_worldbridge_input_pause_authority_contract(),
        "dual_lane_trace_contract": build_worldbridge_dual_lane_trace_contract(),
        "live_dual_lane_trace_producer_contract": build_worldbridge_live_trace_producer_contract(),
        "live_dual_lane_field_comparability_contract": build_worldbridge_live_trace_comparability_contract(),
        "live_dual_lane_comparability_time_series_contract": build_worldbridge_live_trace_time_series_contract(),
        "bounded_live_comparability_capture_session_contract": build_worldbridge_live_capture_session_contract(),
        "sealed_live_comparability_capture_artifact_contract": build_worldbridge_live_capture_artifact_contract(),
        "cross_lane_randomness_authority_contract": build_worldbridge_randomness_authority_contract(),
        "sr_runtime_randomness_ownership_contract": build_worldbridge_sr_runtime_randomness_contract(),
        "cross_lane_transaction_failure_isolation_contract": build_worldbridge_transaction_failure_isolation_contract(),
        "cross_lane_checkpoint_restore_feasibility_contract": build_worldbridge_checkpoint_restore_feasibility_contract(),
        "e313_bounded_replay_corpus": build_worldbridge_e313_bounded_replay_corpus(),
        "e313_live_capture_binding": build_worldbridge_e313_live_capture_binding(),
        "shared_state_transport": build_worldbridge_shared_state_transport_contract(),
        "e315_shared_state_transport_binding": build_worldbridge_e315_shared_state_transport_binding(),
        "e316_checkpoint_restore_witness": build_worldbridge_e316_checkpoint_restore_witness(),
        "e317_live_checkpoint_gap_audit": build_worldbridge_e317_live_checkpoint_gap_audit(),
        "e366_live_checkpoint_admission": build_worldbridge_e366_live_checkpoint_admission_contract(),
        "e367_live_viewport_witness": build_worldbridge_e367_live_viewport_witness_contract(
            live_checkpoint_witness,
            live_checkpoint_cleanup,
        ),
        "e319_game_viewport_live_checkpoint_adapter": build_game_viewport_live_checkpoint_adapter_contract(),
        "script_entropy_admission": build_script_entropy_admission_contract(),
        "fresh_ps_restore_parity": build_worldbridge_fresh_restore_parity_contract(),
        "fresh_sr_restore_parity": build_worldbridge_fresh_sr_restore_contract(),
        "e379_tick_envelope": {
            "schema_version": 1,
            "status": "worldbridge_e379_tick_envelope",
            "opt_in_only": True,
            "shared_clock_admitted": False,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
            "real_game_viewport_witness": False,
            "contract_valid": True,
        },
        "e380_tick_execution": {
            "schema_version": 1,
            "status": "worldbridge_e380_tick_execution",
            "opt_in_only": True,
            "real_game_viewport_witness": False,
            "execution_invoked": False,
            "input_consumption_observed": False,
            "rng_consumption_observed": False,
            "shared_clock_admitted": False,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
            "contract_valid": True,
        },
        "e381_tick_sequence": {
            "schema_version": 1,
            "status": "worldbridge_e381_tick_sequence",
            "opt_in_only": True,
            "continuous_execution_observed": False,
            "input_boundaries_observed": False,
            "dynamic_spawn_observed": False,
            "dynamic_despawn_observed": False,
            "shared_clock_admitted": False,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
            "contract_valid": True,
        },
        "e382_restore_receipt": {
            "schema_version": 1,
            "status": "worldbridge_e382_restore_receipt",
            "receipt_validation_available": callable(validate_e382_receipt),
            "fresh_sequence_restore": False,
            "failure_abort_observed": False,
            "compensation_preserved_target": False,
            "cross_process_receipt_revalidated": False,
            "canonical_bytes_roundtrip": False,
            "duplicate_consumption_rejected": False,
            "child_identity_binding": True,
            "durable_ledger_available": callable(consume_e382_receipt_durable),
            "cross_process_lock_rejected": False,
            "project_identity_binding": True,
            "ledger_digest_binding": True,
            "manifest_scene_identity_source": True,
            "arbitrary_identity_only": False,
            "complete_child_result_digest_binding": True,
            "tampered_checkpoint_rejected": False,
            "component_digest_matrix": {
                "sr_state": False,
                "ps_state": False,
                "randomness_state": False,
                "input_state": False,
                "lifecycle": False,
            },
            "durable_component_matrix": {
                "consumer_prewrite_validation": True,
                "incomplete_component_rejected": False,
                "tampered_component_rejected": False,
            },
            "ledger_provenance": {
                "component_provenance_recorded": False,
                "ledger_digest_bound": True,
                "cross_process_reread_equal": False,
                "tampered_ledger_rejected": False,
            },
            "project_identity_provenance": {
                "manifest_scene_snapshot_recorded": False,
                "changed_project_world_rejected": False,
            },
            "project_identity_change_matrix": {
                "manifest_change_rejected": False,
                "scene_change_rejected": False,
                "scene_path_change_rejected": False,
            },
            "identity_cross_process": {
                "path_normalization_stable": False,
                "cross_process_snapshot_equal": False,
                "duplicate_consumption_rejected": False,
            },
            "ledger_schema_boundary": {
                "unknown_top_level_rejected": False,
                "old_schema_version_rejected": False,
                "unknown_provenance_fields_rejected": False,
            },
            "receipt_encoding_boundary": {
                "unknown_field_rejected": False,
                "duplicate_key_rejected": False,
                "noncanonical_bytes_rejected": False,
            },
            "atomic_write_failure": {
                "replace_failure_rejected": False,
                "fsync_failure_rejected": False,
                "ledger_preserved": False,
                "temporary_files_cleaned": False,
            },
            "concurrent_consumption": {
                "different_receipts_both_consumed": False,
                "same_receipt_second_attempt_rejected": False,
                "ledger_count_matches_provenance": False,
            },
            "end_to_end_chain": {
                "real_e381_child": False,
                "real_project_identity": False,
                "component_digest_binding": False,
                "ledger_provenance_recorded": False,
                "cross_process_snapshot_equal": False,
                "component_tamper_rejected": False,
            },
            "shared_delta_contract": {
                "pond_accepts_delta": True,
                "pond_tick_counter_preserved": True,
                "root_entity_receives_shared_delta": True,
                "default_ready": False,
            },
            "delta_lifecycle": {
                "paused_delta_zero": True,
                "invalid_delta_rejected": True,
                "dropped_time_accumulation": False,
            },
            "input_sequence": {
                "canonical_sequence": False,
                "pause_epoch": False,
                "dropped_event_policy": "reject_sequence_gap",
                "shared_queued_input_ordering": False,
                "input_replay_admitted": False,
            },
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
            "contract_valid": True,
        },
        "sr_runtime_structure_parity": {
            "schema_version": SR_STRUCTURE_PARITY_SCHEMA_VERSION,
            "status": SR_STRUCTURE_PARITY_STATUS,
            "dynamic_restore_requires_exact_structure_digest": True,
            "fresh_scene_reconstruction": False,
            "cross_lane_parity": False,
            "default_ready": False,
        },
        "cross_lane_recovery_compensation_controlled_restart_contract": build_worldbridge_recovery_compensation_controlled_restart_contract(),
        "failure_quarantine_opt_in_handoff_readmission_contract": build_worldbridge_failure_quarantine_readmission_contract(),
        "failure_quarantine_diagnostic_provenance_contract": build_worldbridge_quarantine_diagnostic_provenance_contract(),
        "failure_quarantine_lifecycle_correlation_contract": build_worldbridge_quarantine_lifecycle_correlation_contract(),
        "failure_quarantine_operator_presentation_contract": build_worldbridge_quarantine_operator_presentation_contract(),
        "failure_quarantine_operator_presentation_export_contract": build_worldbridge_quarantine_operator_presentation_export_contract(),
        "failure_quarantine_operator_presentation_export_audit_contract": build_worldbridge_quarantine_operator_presentation_export_audit_contract(),
        "failure_quarantine_operator_evidence_bundle_contract": build_worldbridge_quarantine_operator_evidence_bundle_contract(),
        "failure_e512_provenance_receipt_contract": build_worldbridge_e512_provenance_receipt_contract(),
        "provenance_receipt": build_worldbridge_e512_provenance_receipt_status(),
        "failure_quarantine_operator_presentation_surface_audit_contract": build_worldbridge_quarantine_operator_presentation_surface_audit_contract(),
        "failure_quarantine_operator_presentation_surface_receipt_contract": build_worldbridge_quarantine_operator_presentation_surface_receipt_contract(),
        "failure_quarantine_operator_presentation_receipt_consumer_contract": build_worldbridge_quarantine_operator_presentation_receipt_consumer_contract(),
        "failure_quarantine_operator_presentation_consumer_non_consumption_audit_contract": build_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract(),
        "failure_quarantine_operator_presentation_status_projection_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit_contract(),
        "failure_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix_audit_contract": build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix_contract(),
        "pre_post_random_state_observation_binding_contract": build_worldbridge_random_state_observation_binding_contract(),
        "opt_in_deterministic_randomness_context_contract": build_worldbridge_deterministic_randomness_context_contract(),
        "opt_in_named_stream_sr_mind_adapter_contract": build_worldbridge_named_stream_adapter_contract(),
        "opt_in_respawn_two_stream_handoff_contract": build_worldbridge_respawn_two_stream_handoff_contract(),
        "opt_in_respawn_two_stream_artifact_contract": build_worldbridge_respawn_two_stream_artifact_contract(),
        "opt_in_respawn_artifact_inspection_contract": build_worldbridge_respawn_artifact_inspection_contract(),
        "opt_in_respawn_artifact_diagnostic_projection_contract": build_worldbridge_respawn_artifact_diagnostic_projection_contract(),
        "opt_in_respawn_diagnostic_consumer_contract": build_worldbridge_respawn_diagnostic_consumer_contract(),
        "opt_in_respawn_diagnostic_presentation_contract": build_worldbridge_respawn_diagnostic_presentation_contract(),
        "opt_in_respawn_diagnostic_export_contract": build_worldbridge_respawn_diagnostic_export_contract(),
        "opt_in_respawn_diagnostic_export_audit_contract": build_worldbridge_respawn_diagnostic_export_audit_contract(),
        "cross_session_script_rehydration_admitted": (
            cross_session_script_admitted
        ),
        "cross_session_script_evidence": cross_session_script_evidence,
        "atomic_sr_ps_checkpoint_admitted": (
            atomic_sr_ps_checkpoint_admitted
        ),
        "cross_lane_atomic_checkpoint_evidence": (
            cross_lane_atomic_checkpoint_evidence
        ),
        "global_cross_process_atomicity_admitted": (
            global_cross_process_atomicity_admitted
        ),
        "project_write_authority_evidence": project_write_authority_evidence,
        "executable_source_portability_boundary_closed": (
            executable_source_portability_boundary_closed
        ),
        "script_portability_boundary_evidence": (
            script_portability_boundary_evidence
        ),
        "do_not_claim": do_not_claim,
    }














