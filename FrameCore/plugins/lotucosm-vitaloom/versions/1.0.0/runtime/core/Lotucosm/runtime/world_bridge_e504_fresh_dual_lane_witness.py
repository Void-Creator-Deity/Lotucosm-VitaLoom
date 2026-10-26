"""Qt-free E504 composite witness for a fresh dual-lane runtime pair."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

SCHEMA_VERSION = 1
STATUS = "worldbridge_e504_fresh_dual_lane_witness"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: Mapping[str, Any]) -> str:
    clean = dict(value)
    clean["witness_digest"] = ""
    return hashlib.sha256(_canonical(clean)).hexdigest()


def _canonical_input_state(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_input_state(child)
            for key, child in value.items()
            if key not in {"runtime_epoch"}
        }
    if isinstance(value, list):
        return [_canonical_input_state(child) for child in value]
    return copy.deepcopy(value)


def build_worldbridge_e504_fresh_dual_lane_witness(
    *,
    source_checkpoint: Mapping[str, Any],
    fresh_checkpoint: Mapping[str, Any],
    fresh_sr_restore: Mapping[str, Any],
    fresh_ps_restore: Mapping[str, Any],
    source_next_rng_snapshot: Mapping[str, Any],
    fresh_next_rng_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    values = {
        "source_checkpoint": source_checkpoint,
        "fresh_checkpoint": fresh_checkpoint,
        "fresh_sr_restore": fresh_sr_restore,
        "fresh_ps_restore": fresh_ps_restore,
        "source_next_rng_snapshot": source_next_rng_snapshot,
        "fresh_next_rng_snapshot": fresh_next_rng_snapshot,
    }
    if any(not isinstance(value, Mapping) for value in values.values()):
        raise TypeError("E504 inputs must be mappings")
    if source_checkpoint is fresh_checkpoint:
        raise ValueError("E504 requires distinct source and fresh checkpoints")
    if source_checkpoint.get("runtime_mode") != "dual" or fresh_checkpoint.get("runtime_mode") != "dual":
        raise ValueError("E504 checkpoint runtime mode must be dual")
    sr_parity = fresh_sr_restore.get("dynamic_state_equal") is True and fresh_sr_restore.get("fresh_instance") is True
    ps_parity = fresh_ps_restore.get("canonical_state_equal") is True and fresh_ps_restore.get("fresh_instance_created") is True
    bridge_equal = source_checkpoint.get("bridge_identity_links") == fresh_checkpoint.get("bridge_identity_links")
    source_input = _canonical_input_state(source_checkpoint.get("input_state"))
    fresh_input = _canonical_input_state(fresh_checkpoint.get("input_state"))
    input_equal = source_input == fresh_input
    rng_equal = source_next_rng_snapshot == fresh_next_rng_snapshot
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "source_checkpoint_digest": str(source_checkpoint.get("digest", "")),
        "fresh_checkpoint_digest": str(fresh_checkpoint.get("digest", "")),
        "fresh_sr_restore": copy.deepcopy(dict(fresh_sr_restore)),
        "fresh_ps_restore": copy.deepcopy(dict(fresh_ps_restore)),
        "sr_parity": sr_parity,
        "ps_parity": ps_parity,
        "bridge_identity_equal": bridge_equal,
        "input_continuity_equal": input_equal,
        "source_input_digest": hashlib.sha256(_canonical(source_input)).hexdigest(),
        "fresh_input_digest": hashlib.sha256(_canonical(fresh_input)).hexdigest(),
        "next_rng_state_equal": rng_equal,
        "fresh_dual_lane_parity": bool(sr_parity and ps_parity and bridge_equal and input_equal and rng_equal),
        "live_restore_admitted": False,
        "atomic_checkpoint": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
        "witness_digest": "",
    }
    witness["witness_digest"] = _digest(witness)
    return copy.deepcopy(witness)


def validate_worldbridge_e504_fresh_dual_lane_witness(value: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("identity_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_mismatch")
    for field in ("source_checkpoint_digest", "fresh_checkpoint_digest"):
        if not isinstance(value.get(field), str) or len(value.get(field, "")) != 64:
            errors.append(f"{field}_invalid")
    for field in ("source_input_digest", "fresh_input_digest"):
        if not isinstance(value.get(field), str) or len(value.get(field, "")) != 64:
            errors.append(f"{field}_invalid")
    expected = all(value.get(field) is True for field in (
        "sr_parity", "ps_parity", "bridge_identity_equal", "input_continuity_equal", "next_rng_state_equal",
    ))
    if value.get("fresh_dual_lane_parity") is not expected:
        errors.append("parity_admission_mismatch")
    if value.get("live_restore_admitted") is not False or value.get("atomic_checkpoint") is not False or value.get("replay_admitted") is not False or value.get("default_ready") is not False or value.get("lossless") is not False:
        errors.append("admission_overclaim")
    if value.get("witness_digest") != _digest(value):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "build_worldbridge_e504_fresh_dual_lane_witness",
    "validate_worldbridge_e504_fresh_dual_lane_witness",
]
