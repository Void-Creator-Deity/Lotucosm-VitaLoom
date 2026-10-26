"""Read-only witness for post-restore dual-lane next-tick parity."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

SCHEMA_VERSION = 1
STATUS = "worldbridge_e507_next_tick_replay_witness"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["witness_digest"] = ""
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _state(checkpoint: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "sr_state": copy.deepcopy(checkpoint.get("sr_state")),
        "ps_state": copy.deepcopy(checkpoint.get("ps_state")),
        "bridge_identity_links": copy.deepcopy(checkpoint.get("bridge_identity_links")),
        "input_state": copy.deepcopy(checkpoint.get("input_state")),
        "randomness_state": copy.deepcopy(checkpoint.get("randomness_state")),
        "lifecycle": copy.deepcopy(checkpoint.get("lifecycle")),
    }


def build_worldbridge_e507_next_tick_replay_witness(
    *,
    checkpoint: Mapping[str, Any],
    baseline_next: Mapping[str, Any],
    restored_next: Mapping[str, Any],
    restore_result: Mapping[str, Any],
) -> dict[str, Any]:
    for name, value in (("checkpoint", checkpoint), ("baseline_next", baseline_next), ("restored_next", restored_next), ("restore_result", restore_result)):
        if not isinstance(value, Mapping):
            raise TypeError(f"{name} must be a mapping")
    baseline = _state(baseline_next)
    restored = _state(restored_next)
    parity = baseline == restored
    fields = {field: baseline[field] == restored[field] for field in baseline}
    transport = (
        baseline["input_state"].get("shared_transport")
        == restored["input_state"].get("shared_transport")
    ) if isinstance(baseline["input_state"], Mapping) and isinstance(restored["input_state"], Mapping) else False
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "checkpoint_digest": checkpoint.get("digest"),
        "restore_result": copy.deepcopy(dict(restore_result)),
        "field_parity": fields,
        "sr_ps_next_tick_parity": parity,
        "transport_continuity_parity": transport,
        "next_rng_parity": fields["randomness_state"],
        "bridge_continuity_parity": fields["bridge_identity_links"],
        "input_order_parity": fields["input_state"],
        "atomic_checkpoint": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
        "witness_digest": "",
    }
    witness["witness_digest"] = _digest(witness)
    return copy.deepcopy(witness)


def validate_worldbridge_e507_next_tick_replay_witness(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("identity_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_mismatch")
    if not isinstance(value.get("checkpoint_digest"), str) or len(value.get("checkpoint_digest", "")) != 64:
        errors.append("checkpoint_digest_invalid")
    result = value.get("restore_result")
    if not isinstance(result, Mapping) or result.get("restored") is not True or result.get("rollback_performed") is not False:
        errors.append("restore_result_invalid")
    fields = value.get("field_parity")
    if not isinstance(fields, Mapping) or any(not isinstance(fields.get(field), bool) for field in ("sr_state", "ps_state", "bridge_identity_links", "input_state", "randomness_state", "lifecycle")):
        errors.append("field_parity_invalid")
    else:
        expected = all(fields.values())
        if value.get("sr_ps_next_tick_parity") is not expected:
            errors.append("parity_mismatch")
        if value.get("transport_continuity_parity") is not fields["input_state"]:
            errors.append("transport_parity_mismatch")
        if value.get("next_rng_parity") is not fields["randomness_state"]:
            errors.append("rng_parity_mismatch")
        if value.get("bridge_continuity_parity") is not fields["bridge_identity_links"]:
            errors.append("bridge_parity_mismatch")
        if value.get("input_order_parity") is not fields["input_state"]:
            errors.append("input_parity_mismatch")
    for field in ("atomic_checkpoint", "replay_admitted", "default_ready", "lossless"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    if value.get("witness_digest") != _digest(value):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": errors}


__all__ = ["build_worldbridge_e507_next_tick_replay_witness", "validate_worldbridge_e507_next_tick_replay_witness"]
