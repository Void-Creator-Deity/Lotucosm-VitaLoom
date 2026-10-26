"""Qt-free E503 witness for post-restore RNG continuation parity."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

SCHEMA_VERSION = 1
STATUS = "worldbridge_e503_live_restore_parity"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: Mapping[str, Any]) -> str:
    clean = dict(value)
    clean["witness_digest"] = ""
    return hashlib.sha256(_canonical(clean)).hexdigest()


def build_worldbridge_e503_live_restore_parity(
    *,
    checkpoint_snapshot: Mapping[str, Any],
    baseline_next_snapshot: Mapping[str, Any],
    restored_next_snapshot: Mapping[str, Any],
    restore_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Build parity evidence from two independently captured next-tick states."""
    for name, value in (
        ("checkpoint_snapshot", checkpoint_snapshot),
        ("baseline_next_snapshot", baseline_next_snapshot),
        ("restored_next_snapshot", restored_next_snapshot),
        ("restore_result", restore_result),
    ):
        if not isinstance(value, Mapping):
            raise TypeError(f"{name} must be a mapping")
    if not checkpoint_snapshot.get("snapshot_digest"):
        raise ValueError("checkpoint RNG snapshot digest is missing")
    if baseline_next_snapshot.get("context_id") != restored_next_snapshot.get("context_id"):
        raise ValueError("restored context identity mismatch")
    if baseline_next_snapshot.get("streams") != restored_next_snapshot.get("streams"):
        raise ValueError("post-restore stream states are not equal")
    if restore_result.get("restored") is not True:
        raise ValueError("live restore result is not successful")
    if restore_result.get("rollback_performed") is not False:
        raise ValueError("successful restore carries rollback evidence")
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "checkpoint_snapshot_digest": str(checkpoint_snapshot["snapshot_digest"]),
        "baseline_next_snapshot": copy.deepcopy(dict(baseline_next_snapshot)),
        "restored_next_snapshot": copy.deepcopy(dict(restored_next_snapshot)),
        "restore_result": copy.deepcopy(dict(restore_result)),
        "context_identity_equal": True,
        "next_draw_state_equal": True,
        "restore_successful": True,
        "live_restore_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "witness_digest": "",
    }
    witness["witness_digest"] = _digest(witness)
    return copy.deepcopy(witness)


def validate_worldbridge_e503_live_restore_parity(value: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("identity_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_mismatch")
    if not isinstance(value.get("checkpoint_snapshot_digest"), str) or len(value.get("checkpoint_snapshot_digest", "")) != 64:
        errors.append("checkpoint_digest_invalid")
    baseline = value.get("baseline_next_snapshot")
    restored = value.get("restored_next_snapshot")
    if not isinstance(baseline, Mapping) or not isinstance(restored, Mapping):
        errors.append("next_snapshot_invalid")
    elif baseline != restored:
        errors.append("next_snapshot_mismatch")
    result = value.get("restore_result")
    if not isinstance(result, Mapping) or result.get("restored") is not True:
        errors.append("restore_result_invalid")
    if value.get("context_identity_equal") is not True or value.get("next_draw_state_equal") is not True:
        errors.append("parity_not_proven")
    if value.get("live_restore_admitted") is not False or value.get("replay_admitted") is not False or value.get("default_ready") is not False:
        errors.append("admission_overclaim")
    if value.get("witness_digest") != _digest(value):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "build_worldbridge_e503_live_restore_parity",
    "validate_worldbridge_e503_live_restore_parity",
]
