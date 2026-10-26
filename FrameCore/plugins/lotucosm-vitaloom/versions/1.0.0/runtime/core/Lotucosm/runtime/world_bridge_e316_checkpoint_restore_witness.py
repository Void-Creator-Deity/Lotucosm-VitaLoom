# -*- coding: utf-8 -*-
"""E316 opt-in checkpoint/restore and rollback witness.

This deliberately uses the bounded E313 harness as an isolated seam.  It proves
transaction ordering and failure isolation for a complete synthetic checkpoint,
not restoration of production SR/PS objects or admission of a live adapter.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_e313_bounded_replay_corpus import (
    _apply_tick,
    _finish,
    _input_log,
    _new_run,
    _restore,
    _snapshot,
    validate_e313_checkpoint,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_e316_checkpoint_restore_witness"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["checkpoint_digest"] = ""
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _fingerprint(run: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(_finish(run))).hexdigest()


def _build_shared_checkpoint(source: Mapping[str, Any]) -> dict[str, Any]:
    checkpoint = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "phase_order": list(source["phase_order"]),
        "capture_epoch": 1,
        "sequence": 0,
        "input_cursor": source["input_cursor"],
        "sr_lane": {"tick": source["tick"], "position": source["sr_position"]},
        "ps_lane": {"tick": source["tick"], "energy": source["ps_energy"]},
        "randomness_snapshot": copy.deepcopy(source["randomness_snapshot"]),
        "lifecycle": {"pause_reset_epoch": 0, "action": "tick", "playing": True, "paused": False},
        "bridge_identity_links": [{"sr_entity_id": "sr:e316", "ps_organism_id": "ps:e316", "relation": "observation_link"}],
        "checkpoint_digest": "",
    }
    checkpoint["checkpoint_digest"] = _digest(checkpoint)
    return checkpoint


def validate_e316_checkpoint(checkpoint: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(checkpoint, Mapping):
        return {"valid": False, "errors": ["checkpoint_not_mapping"]}
    required = {"schema_version", "status", "phase_order", "capture_epoch", "sequence", "input_cursor", "sr_lane", "ps_lane", "randomness_snapshot", "lifecycle", "bridge_identity_links", "checkpoint_digest"}
    if set(checkpoint) != required: errors.append("checkpoint_keys_mismatch")
    if checkpoint.get("schema_version") != SCHEMA_VERSION: errors.append("schema_version_mismatch")
    if checkpoint.get("status") != STATUS: errors.append("status_mismatch")
    if checkpoint.get("phase_order") != ["input_ingest", "sr_tick", "sr_to_ps_sync", "ps_tick", "trace_capture"]: errors.append("phase_order_mismatch")
    sr_lane = checkpoint.get("sr_lane")
    ps_lane = checkpoint.get("ps_lane")
    if not isinstance(sr_lane, Mapping) or not isinstance(ps_lane, Mapping):
        errors.append("lane_state_missing")
    else:
        source = {
            "schema_version": 1,
            "status": "worldbridge_e313_bounded_cross_lane_replay_corpus",
            "phase_order": checkpoint.get("phase_order"),
            "tick": sr_lane.get("tick"),
            "input_cursor": checkpoint.get("input_cursor"),
            "sr_position": sr_lane.get("position"),
            "ps_energy": ps_lane.get("energy"),
            "randomness_snapshot": checkpoint.get("randomness_snapshot"),
            "checkpoint_digest": "",
        }
        try:
            source["checkpoint_digest"] = _digest_e313(source)
            if validate_e313_checkpoint(source)["valid"] is not True:
                errors.append("embedded_e313_state_invalid")
        except (TypeError, ValueError, OverflowError):
            errors.append("embedded_e313_state_invalid")
    try:
        if checkpoint.get("checkpoint_digest") != _digest(checkpoint): errors.append("checkpoint_digest_mismatch")
    except (TypeError, ValueError, OverflowError): errors.append("checkpoint_not_canonical_json")
    lifecycle = checkpoint.get("lifecycle")
    if lifecycle != {"pause_reset_epoch": 0, "action": "tick", "playing": True, "paused": False}:
        errors.append("lifecycle_invalid")
    links = checkpoint.get("bridge_identity_links")
    if not isinstance(links, list) or len(links) != 1 or not isinstance(links[0], Mapping) or links[0].get("relation") != "observation_link":
        errors.append("identity_link_invalid")
    if isinstance(sr_lane, Mapping) and isinstance(ps_lane, Mapping) and sr_lane.get("tick") != ps_lane.get("tick"):
        errors.append("lane_tick_mismatch")
    return {"valid": not errors, "errors": errors}


def _restore_transaction(
    checkpoint: Mapping[str, Any], target: dict[str, Any], *, fail_stage: str | None = None
) -> str | None:
    """Prepare a fresh run and replace the target only after every stage succeeds."""
    validation = validate_e316_checkpoint(checkpoint)
    if not validation["valid"]:
        return "checkpoint_validation_failed"
    embedded = {
        "schema_version": 1,
        "status": "worldbridge_e313_bounded_cross_lane_replay_corpus",
        "phase_order": checkpoint["phase_order"],
        "tick": checkpoint["sr_lane"]["tick"],
        "input_cursor": checkpoint["input_cursor"],
        "sr_position": checkpoint["sr_lane"]["position"],
        "ps_energy": checkpoint["ps_lane"]["energy"],
        "randomness_snapshot": checkpoint["randomness_snapshot"],
        "checkpoint_digest": "",
    }
    embedded["checkpoint_digest"] = _digest_e313(embedded)
    try:
        candidate = _restore(embedded)
        if fail_stage == "ps_lane_apply": raise RuntimeError("injected ps lane apply failure")
        if fail_stage == "bridge_commit": raise RuntimeError("injected bridge commit failure")
    except (ValueError, RuntimeError) as exc:
        return str(exc)
    target.clear()
    target.update(candidate)
    return None


def _digest_e313(value: Mapping[str, Any]) -> str:
    payload = dict(value); payload["checkpoint_digest"] = ""
    return hashlib.sha256(_canonical(payload)).hexdigest()


def run_e316_checkpoint_restore_witness() -> dict[str, Any]:
    events = _input_log()
    baseline = _new_run()
    for event in events[:3]: _apply_tick(baseline, event)
    source = _snapshot(baseline)
    checkpoint = _build_shared_checkpoint(source)
    checkpoint_validation = validate_e316_checkpoint(checkpoint)
    restored = _new_run()
    restore_error = _restore_transaction(checkpoint, restored)
    if restore_error is not None:
        raise RuntimeError(f"valid checkpoint restore failed: {restore_error}")
    for event in events[3:]: _apply_tick(baseline, event)
    for event in events[3:]: _apply_tick(restored, event)
    baseline_final, restored_final = _finish(baseline), _finish(restored)
    target = _new_run()
    for event in events[:2]: _apply_tick(target, event)
    target_before = _fingerprint(target)
    failure_error = _restore_transaction(checkpoint, target, fail_stage="ps_lane_apply")
    target_after = _fingerprint(target)
    tampered = copy.deepcopy(checkpoint); tampered["ps_lane"]["energy"] += 1.0
    tamper_error = _restore_transaction(tampered, target)
    tamper_state_preserved = _fingerprint(target) == target_before
    return {
        "schema_version": SCHEMA_VERSION, "status": STATUS, "witness_only": True,
        "checkpoint": checkpoint, "checkpoint_validation": checkpoint_validation,
        "restore": {
            "fresh_instances": True,
            "error": restore_error,
            "post_checkpoint_trace_equal": baseline_final["trace"][3:] == restored_final["trace"],
            "final_state_equal": all(
                baseline_final[field] == restored_final[field]
                for field in ("tick", "input_cursor", "sr_position", "ps_energy")
            ),
        },
        "rollback": {"injected_failure_rejected": bool(failure_error), "target_state_preserved": target_before == target_after, "failure_error": failure_error},
        "tamper_rejection": {"rejected": bool(tamper_error), "target_state_preserved": tamper_state_preserved, "error": tamper_error},
        "boundaries": {"shared_live_state_restore": False, "full_unified_replay_admitted": False, "cross_lane_replay": False, "lossless": False, "default_ready": False, "live_adapter_admitted": False},
    }


def build_worldbridge_e316_checkpoint_restore_witness() -> dict[str, Any]:
    result = run_e316_checkpoint_restore_witness()
    result["protocol_valid"] = bool(result["checkpoint_validation"]["valid"] and result["restore"]["fresh_instances"] and result["restore"]["post_checkpoint_trace_equal"] and result["restore"]["final_state_equal"] and result["rollback"]["injected_failure_rejected"] and result["rollback"]["target_state_preserved"] and result["tamper_rejection"]["rejected"] and result["tamper_rejection"]["target_state_preserved"] and all(value is False for value in result["boundaries"].values()))
    return result


__all__ = ["build_worldbridge_e316_checkpoint_restore_witness", "run_e316_checkpoint_restore_witness", "validate_e316_checkpoint"]
