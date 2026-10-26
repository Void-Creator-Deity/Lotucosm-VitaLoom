"""Qt-free E502 evidence for ordered SR/PS RNG consumption boundaries."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from .world_bridge_deterministic_randomness_context import (
    WorldBridgeDeterministicRandomnessContext,
    validate_worldbridge_deterministic_randomness_snapshot,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_e502_rng_draw_order_witness"
PHASE_ORDER = ("sr.start", "sr.complete", "ps.start", "ps.complete")


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: Mapping[str, Any]) -> str:
    clean = dict(value)
    clean["witness_digest"] = ""
    return hashlib.sha256(_canonical(clean)).hexdigest()


def _stream_cursor(stream: Mapping[str, Any]) -> str:
    state = stream["state"]
    if stream["family"] == "python_random":
        return str(state["internal_state"][-1])
    return str(state["state"]["state"])


def _observation(
    context: WorldBridgeDeterministicRandomnessContext,
    phase: str,
    order: int,
    draw_counts: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    snapshot = context.snapshot()
    streams = []
    for stream in snapshot["streams"]:
        streams.append({
            "stream_name": stream["stream_name"],
            "family": stream["family"],
            "registration_index": stream["registration_index"],
            "cursor": _stream_cursor(stream),
            "state_digest": hashlib.sha256(_canonical(stream["state"])).hexdigest(),
            "draw_count": int((draw_counts or {}).get(stream["stream_name"], 0)),
        })
    return {
        "phase": phase,
        "order": order,
        "context_id": snapshot["context_id"],
        "registration": [stream["stream_name"] for stream in snapshot["streams"]],
        "streams": streams,
        "snapshot_digest": snapshot["snapshot_digest"],
    }


def capture_worldbridge_e502_rng_phase_boundary(
    context: WorldBridgeDeterministicRandomnessContext,
    phase: str,
    order: int,
    *,
    draw_counts: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    """Capture one real phase boundary without advancing any stream."""
    if phase not in PHASE_ORDER:
        raise ValueError(f"unsupported E502 phase: {phase}")
    if isinstance(order, bool) or not isinstance(order, int) or order < 0:
        raise ValueError("order must be a non-negative integer")
    return _observation(context, phase, order, draw_counts)


def build_worldbridge_e502_rng_draw_order_witness(
    envelopes: Sequence[Mapping[str, Any]],
    observations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if isinstance(envelopes, (str, bytes)) or not isinstance(envelopes, Sequence) or not envelopes:
        raise ValueError("E502 requires at least one shared-state envelope")
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence) or not observations:
        raise ValueError("E502 requires phase observations")
    copied = [copy.deepcopy(dict(item)) for item in observations]
    _validate_observations(copied)
    registration = copied[0]["registration"]
    stream_names = set(registration)
    if not {"sr.runtime", "ps.pond"}.issubset(stream_names):
        raise ValueError("E502 requires sr.runtime and ps.pond streams")
    changes = []
    for before, after in zip(copied, copied[1:]):
        if before["order"] == 3:
            continue
        before_by_name = {item["stream_name"]: item for item in before["streams"]}
        for stream in after["streams"]:
            prior = before_by_name.get(stream["stream_name"])
            if prior is not None:
                changes.append({
                    "from_phase": before["phase"],
                    "to_phase": after["phase"],
                    "stream_name": stream["stream_name"],
                    "cursor_changed": stream["cursor"] != prior["cursor"],
                    "state_changed": stream["state_digest"] != prior["state_digest"],
                    "draw_count_changed": stream["draw_count"] != prior["draw_count"],
                })
    sr_changes = [item for item in changes if item["stream_name"] == "sr.runtime" and item["to_phase"] == "sr.complete"]
    ps_changes = [item for item in changes if item["stream_name"] == "ps.pond" and item["to_phase"] == "ps.complete"]
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "phase_order": list(PHASE_ORDER),
        "envelope_digests": [str(item["envelope_digest"]) for item in envelopes],
        "observations": copied,
        "registration_order": registration,
        "stream_changes": changes,
        "sr_consumption_observed": any(
            item["draw_count_changed"] and item["cursor_changed"] and item["state_changed"]
            for item in sr_changes
        ),
        "ps_consumption_observed": any(
            item["draw_count_changed"] and item["cursor_changed"] and item["state_changed"]
            for item in ps_changes
        ),
        "registration_order_stable": all(item["registration"] == registration for item in copied),
        "phase_order_proven": all(
            [item["phase"] for item in copied[start : start + len(PHASE_ORDER)]] == list(PHASE_ORDER)
            for start in range(0, len(copied), len(PHASE_ORDER))
        ),
        "consumption_order_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "witness_digest": "",
    }
    witness["consumption_order_admitted"] = bool(
        witness["sr_consumption_observed"]
        and witness["ps_consumption_observed"]
        and witness["registration_order_stable"]
        and witness["phase_order_proven"]
    )
    witness["witness_digest"] = _digest(witness)
    return copy.deepcopy(witness)


def validate_worldbridge_e502_rng_draw_order_witness(value: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("identity_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_mismatch")
    if value.get("phase_order") != list(PHASE_ORDER):
        errors.append("phase_order_mismatch")
    observations = value.get("observations")
    if not isinstance(observations, list):
        errors.append("observations_not_list")
    else:
        try:
            _validate_observations(observations)
        except ValueError as exc:
            errors.append(str(exc))
    registration = value.get("registration_order")
    if not isinstance(registration, list) or len(registration) != len(set(registration)):
        errors.append("registration_order_invalid")
    if value.get("registration_order_stable") is not True or value.get("phase_order_proven") is not True:
        errors.append("order_not_proven")
    if value.get("consumption_order_admitted") is not (
        value.get("sr_consumption_observed") is True
        and value.get("ps_consumption_observed") is True
        and value.get("registration_order_stable") is True
        and value.get("phase_order_proven") is True
    ):
        errors.append("admission_mismatch")
    if value.get("replay_admitted") is not False or value.get("default_ready") is not False:
        errors.append("admission_overclaim")
    if not isinstance(value.get("witness_digest"), str) or value.get("witness_digest") != _digest(value):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def _validate_observations(observations: Sequence[Mapping[str, Any]]) -> None:
    if len(observations) < len(PHASE_ORDER) or len(observations) % len(PHASE_ORDER):
        raise ValueError("observation_batch_size_invalid")
    for start in range(0, len(observations), len(PHASE_ORDER)):
        batch = observations[start : start + len(PHASE_ORDER)]
        if [item.get("phase") for item in batch] != list(PHASE_ORDER):
            raise ValueError("observation_phase_order_invalid")
        if [item.get("order") for item in batch] != list(range(len(PHASE_ORDER))):
            raise ValueError("observation_order_invalid")
    expected_registration: list[str] | None = None
    for index, item in enumerate(observations):
        registration = item.get("registration")
        streams = item.get("streams")
        if not isinstance(registration, list) or not isinstance(streams, list):
            raise ValueError("observation_streams_invalid")
        if expected_registration is None:
            expected_registration = registration
        elif registration != expected_registration:
            raise ValueError("registration_order_changed")
        if [stream.get("stream_name") for stream in streams] != registration:
            raise ValueError("stream_registration_mismatch")
        for stream in streams:
            if (
                not isinstance(stream.get("cursor"), str)
                or len(stream.get("state_digest", "")) != 64
                or isinstance(stream.get("draw_count"), bool)
                or not isinstance(stream.get("draw_count"), int)
                or stream.get("draw_count") < 0
            ):
                raise ValueError("stream_cursor_invalid")


__all__ = [
    "PHASE_ORDER",
    "build_worldbridge_e502_rng_draw_order_witness",
    "capture_worldbridge_e502_rng_phase_boundary",
    "validate_worldbridge_e502_rng_draw_order_witness",
]
