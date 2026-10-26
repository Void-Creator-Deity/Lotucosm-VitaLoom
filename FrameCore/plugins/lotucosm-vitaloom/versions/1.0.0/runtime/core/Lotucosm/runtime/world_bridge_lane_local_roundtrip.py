# -*- coding: utf-8 -*-
"""E538 lane-local round-trip evidence for SR membrane and PS membrane behavior.

This module proves two separate, non-authoritative facts without opening a
cross-lane behavior authority:

* the SR membrane topology owner round-trips through its own capture/restore
  contract, and the restored edges/attachments still drive the SR channel
  consumer;
* the PS ``Membrane`` behavior round-trips through its real producer contract
  (``get_inspectable_properties`` / ``get_status``), and its forbidden
  behaviors remain lane-local.

Every field is reported as ``aligned`` or ``mismatch``; the helper is
deliberately fail-closed on empty or malformed evidence. The contract never
admits cross-lane behavior, tick merge, full unified replay, lossless mapping,
or default readiness.
"""
from __future__ import annotations

import copy
from typing import Any, Callable, Mapping, Sequence

SCHEMA_VERSION = 1
_BEHAVIOR_FIELDS = ("auto_ingest", "is_inside")
_SR_FIELD_NAMES = (
    "membrane_template",
    "membrane_attach",
    "structural_edges",
    "signal_edges",
    "aggregate_chemosignal",
)


def validate_lane_local_roundtrip_evidence(
    *,
    lane: str,
    fields: Mapping[str, Any],
    required_fields: Sequence[str],
    restored_source_digest: str,
    restored_state_digest: str,
) -> dict[str, Any]:
    """Validate one lane-local round-trip report.

    A report is aligned only when every required field explicitly reports
    ``aligned``, both restored digests are non-empty, and the source and
    restored digests match. Missing or malformed evidence is a mismatch, never
    a silent pass.
    """
    errors: list[str] = []
    normalized: dict[str, str] = {}

    if not isinstance(lane, str) or not lane.strip():
        errors.append("lane_missing")
    if not isinstance(fields, Mapping):
        errors.append("fields_missing")
        fields = {}
    if not isinstance(required_fields, Sequence) or isinstance(required_fields, str):
        errors.append("required_fields_invalid")
        required_fields = ()
    if not isinstance(restored_source_digest, str) or not restored_source_digest:
        errors.append("restored_source_digest_missing")
    if not isinstance(restored_state_digest, str) or not restored_state_digest:
        errors.append("restored_state_digest_missing")
    if restored_source_digest != restored_state_digest:
        errors.append("restored_digest_mismatch")

    seen: set[str] = set()
    for raw_name in required_fields or ():
        name = str(raw_name)
        if not name or name in seen:
            errors.append("required_field_invalid")
            continue
        seen.add(name)
        item = fields.get(name)
        if not isinstance(item, Mapping):
            normalized[name] = "mismatch"
            errors.append(f"field_missing:{name}")
            continue
        state = str(item.get("state", "mismatch"))
        normalized[name] = state
        if state != "aligned":
            errors.append(f"field_not_aligned:{name}")

    aligned = not errors and bool(required_fields) and all(
        normalized.get(str(name)) == "aligned" for name in required_fields
    )
    return {
        "lane": lane,
        "aligned": aligned,
        "field_states": normalized,
        "errors": errors,
    }


def build_worldbridge_lane_local_roundtrip_sr_contract() -> dict[str, Any]:
    """Descriptor for the SR membrane topology round-trip boundary."""
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_lane_local_roundtrip_sr_contract",
        "lane": "sr",
        "read_only": True,
        "owner": "GameViewport.capture_sr_topology_owner_state/restore_sr_topology_owner_state",
        "roundtrip_fields": [
            "membrane_template",
            "membrane_attach",
            "structural_edges",
            "signal_edges",
            "aggregate_chemosignal",
        ],
        "mode": "lane_local_roundtrip",
        "cross_lane_behavior_admitted": False,
        "tick_merge_admitted": False,
        "full_unified_replay_admitted": False,
        "lossless": False,
        "default_ready": False,
        "do_not_claim": [
            "cross_lane_membrane_behavior_authority",
            "unified_runtime_replay",
            "lossless_worldbridge_mapping",
        ],
    }


def build_worldbridge_lane_local_roundtrip_ps_contract() -> dict[str, Any]:
    """Descriptor for the PS Membrane behavior round-trip boundary."""
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_lane_local_roundtrip_ps_contract",
        "lane": "ps",
        "read_only": True,
        "owner": "builtin.components.membrane.Membrane",
        "roundtrip_fields": [
            "radius",
            "ingest_threshold",
            "efficiency",
            "auto_ingest",
            "is_inside",
        ],
        "mode": "lane_local_roundtrip",
        "cross_lane_behavior_admitted": False,
        "tick_merge_admitted": False,
        "full_unified_replay_admitted": False,
        "lossless": False,
        "default_ready": False,
        "do_not_claim": [
            "cross_lane_membrane_behavior_authority",
            "unified_runtime_replay",
            "lossless_worldbridge_mapping",
        ],
    }


def build_worldbridge_lane_local_roundtrip_admission(
    *,
    sr_evidence: Mapping[str, Any],
    ps_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Combine SR/PS lane-local evidence without granting authority."""
    sr_validation = _validate_evidence(sr_evidence, _SR_FIELD_NAMES)
    ps_validation = _validate_evidence(ps_evidence, _BEHAVIOR_FIELDS)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_lane_local_roundtrip_admission",
        "read_only": True,
        "sr_aligned": bool(sr_validation["aligned"]),
        "ps_aligned": bool(ps_validation["aligned"]),
        "sr_validation": sr_validation,
        "ps_validation": ps_validation,
        "cross_lane_behavior_admitted": False,
        "tick_merge_admitted": False,
        "full_unified_replay_admitted": False,
        "lossless": False,
        "default_ready": False,
        "blockers": [
            "cross_lane_membrane_behavior_authority",
            "shared_clock_and_delta_contract",
            "shared_queued_input_ordering",
            "shared_random_seed_contract",
            "shared_pause_reset_error_isolation_contract",
            "shared_scene_pond_checkpoint_contract",
            "full_unified_runtime_replay_not_proven",
        ],
        "do_not_claim": [
            "cross_lane_membrane_behavior_authority",
            "unified_runtime_replay",
            "lossless_worldbridge_mapping",
        ],
    }


def _validate_evidence(evidence: Mapping[str, Any], required_fields: Sequence[str]) -> dict[str, Any]:
    if not isinstance(evidence, Mapping):
        return {
            "lane": None,
            "aligned": False,
            "field_states": {},
            "errors": ["evidence_missing"],
        }
    fields = evidence.get("fields")
    if not isinstance(fields, Mapping):
        fields = {}
    return validate_lane_local_roundtrip_evidence(
        lane=str(evidence.get("lane", "")),
        fields=fields,
        required_fields=required_fields,
        restored_source_digest=str(evidence.get("restored_source_digest", "")),
        restored_state_digest=str(evidence.get("restored_state_digest", "")),
    )


__all__ = [
    "SCHEMA_VERSION",
    "build_worldbridge_lane_local_roundtrip_admission",
    "build_worldbridge_lane_local_roundtrip_ps_contract",
    "build_worldbridge_lane_local_roundtrip_sr_contract",
    "validate_lane_local_roundtrip_evidence",
]
