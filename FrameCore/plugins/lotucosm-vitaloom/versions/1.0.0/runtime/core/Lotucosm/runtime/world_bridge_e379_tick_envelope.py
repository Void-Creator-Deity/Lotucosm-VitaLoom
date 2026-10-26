"""Opt-in shared tick envelope for WorldBridge parity evidence.

This is a caller-owned envelope, not a scheduler.  It makes the temporal and
input claims explicit while preserving the production dual-lane boundary.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_e379_tick_envelope"


def build_worldbridge_e379_tick_envelope(
    *,
    sequence: int,
    sr_delta_seconds: float,
    ps_ticks: int,
    input_events: Sequence[Mapping[str, Any]],
    sr_state_digest: str,
    ps_state_digest: str,
    randomness_digest: str,
) -> dict[str, Any]:
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        raise ValueError("sequence must be a non-negative integer")
    if isinstance(sr_delta_seconds, bool) or not isinstance(sr_delta_seconds, (int, float)):
        raise ValueError("sr_delta_seconds must be numeric")
    delta = float(sr_delta_seconds)
    if delta < 0 or delta != delta or delta in (float("inf"), float("-inf")):
        raise ValueError("sr_delta_seconds must be finite and non-negative")
    if isinstance(ps_ticks, bool) or not isinstance(ps_ticks, int) or ps_ticks < 0:
        raise ValueError("ps_ticks must be a non-negative integer")
    events = [dict(event) for event in input_events]
    for index, event in enumerate(events):
        if not isinstance(event, Mapping):
            raise ValueError(f"input_events[{index}] must be a mapping")
        if set(event) != {"sequence", "tick", "action", "payload"}:
            raise ValueError("input event shape is invalid")
        if event["sequence"] != index:
            raise ValueError("input event sequence must be contiguous")
    for name, digest in (("sr_state_digest", sr_state_digest), ("ps_state_digest", ps_state_digest), ("randomness_digest", randomness_digest)):
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"{name} must be a sha256 digest")
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "sequence": sequence,
        "sr_delta_seconds": delta,
        "ps_ticks": ps_ticks,
        "input_events": events,
        "sr_state_digest": sr_state_digest,
        "ps_state_digest": ps_state_digest,
        "randomness_digest": randomness_digest,
        "shared_tick_identity": f"e379:{sequence}",
        "opt_in_only": True,
        "shared_clock_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    envelope["envelope_digest"] = _digest(envelope)
    return envelope


def validate_worldbridge_e379_tick_envelope(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["envelope_must_be_mapping"]}
    errors: list[str] = []
    required = {
        "schema_version", "status", "sequence", "sr_delta_seconds", "ps_ticks",
        "input_events", "sr_state_digest", "ps_state_digest", "randomness_digest",
        "shared_tick_identity", "opt_in_only", "shared_clock_admitted",
        "replay_admitted", "default_ready", "lossless", "envelope_digest",
    }
    if set(value) != required:
        errors.append("envelope_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("schema_mismatch")
    if value.get("shared_tick_identity") != f"e379:{value.get('sequence')}":
        errors.append("tick_identity_mismatch")
    if value.get("opt_in_only") is not True:
        errors.append("opt_in_required")
    for field in ("shared_clock_admitted", "replay_admitted", "default_ready", "lossless"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    try:
        expected = _digest(value)
    except (TypeError, ValueError):
        expected = None
        errors.append("envelope_not_canonical")
    if value.get("envelope_digest") != expected:
        errors.append("envelope_digest_mismatch")
    try:
        candidate = build_worldbridge_e379_tick_envelope(
            sequence=value.get("sequence"),
            sr_delta_seconds=value.get("sr_delta_seconds"),
            ps_ticks=value.get("ps_ticks"),
            input_events=value.get("input_events"),
            sr_state_digest=value.get("sr_state_digest"),
            ps_state_digest=value.get("ps_state_digest"),
            randomness_digest=value.get("randomness_digest"),
        )
        if dict(candidate) != dict(value):
            errors.append("envelope_content_invalid")
    except (TypeError, ValueError):
        errors.append("envelope_content_invalid")
    return {"valid": not errors, "errors": errors}


def compare_worldbridge_e379_tick_envelopes(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    left_result = validate_worldbridge_e379_tick_envelope(left)
    right_result = validate_worldbridge_e379_tick_envelope(right)
    if not left_result["valid"] or not right_result["valid"]:
        return {"equal": False, "reason": "invalid_envelope", "left": left_result, "right": right_result}
    equal = dict(left) == dict(right)
    return {"equal": equal, "reason": "canonical_match" if equal else "tick_state_mismatch"}


def digest_worldbridge_e379_state(value: object) -> str:
    """Digest one JSON-safe lane state for the envelope producer."""
    encoded = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _digest(value: Mapping[str, Any]) -> str:
    unsigned = dict(value)
    unsigned.pop("envelope_digest", None)
    encoded = json.dumps(unsigned, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "build_worldbridge_e379_tick_envelope",
    "compare_worldbridge_e379_tick_envelopes",
    "digest_worldbridge_e379_state",
    "validate_worldbridge_e379_tick_envelope",
]
