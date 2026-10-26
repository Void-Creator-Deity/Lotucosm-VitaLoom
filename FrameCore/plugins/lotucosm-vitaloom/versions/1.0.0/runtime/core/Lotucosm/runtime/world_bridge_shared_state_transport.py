# -*- coding: utf-8 -*-
"""Qt-free, opt-in SR/PS shared-state transport contract.

This module transports an immutable JSON envelope for evidence and future
experiments only.  It deliberately does not restore live objects, attach to
``Pond.update``/``unified_pond_step``, or change any default runtime authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from collections import deque
from collections.abc import Mapping, Sequence
from typing import Any

from .world_bridge_deterministic_randomness_context import (
    validate_worldbridge_deterministic_randomness_snapshot,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_shared_state_transport"
TRANSPORT_MODE = "opt_in_quarantine_only"
DO_NOT_CLAIM = (
    "shared_live_state_restore",
    "atomic_sr_ps_checkpoint",
    "cross_lane_replay",
    "lossless_worldbridge_mapping",
    "live_adapter_admitted",
    "unified_pond_default_ready",
)
_ENVELOPE_KEYS = {
    "schema_version", "status", "transport_mode", "envelope_id", "capture_epoch",
    "sequence", "input_events", "lifecycle", "clock_provenance", "bridge_identity_links",
    "rng_context_snapshot", "atomicity", "failure", "quarantine", "lossless",
    "replay_admitted", "default_ready", "envelope_digest",
}
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_EVENT_KEYS = {"event_id", "kind", "payload"}
_LINK_KEYS = {"sr_entity_id", "ps_organism_id", "relation"}
_CLOCK_KEYS = {"domain", "tick", "delta", "time", "source"}
_LIFECYCLE_KEYS = {"pause_reset_epoch", "action", "playing", "paused"}
_FAILURE_KEYS = {"code", "stage", "message"}
MAX_RETAINED_RECEIPTS = 128


def build_worldbridge_shared_state_envelope(
    *,
    envelope_id: str,
    capture_epoch: int,
    sequence: int,
    input_events: Sequence[Mapping[str, Any]],
    pause_reset_epoch: int,
    clock_provenance: Mapping[str, Mapping[str, Any]],
    bridge_identity_links: Sequence[Mapping[str, Any]],
    rng_context_snapshot: Mapping[str, Any] | None = None,
    lifecycle_action: str = "tick",
    playing: bool = True,
    paused: bool = False,
    atomicity: str = "ordered_non_atomic",
    failure: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a copied, digest-sealed transport envelope; no live authority is attached."""
    envelope_id = _clean_id(envelope_id, "envelope_id")
    capture_epoch = _non_negative_int(capture_epoch, "capture_epoch")
    sequence = _non_negative_int(sequence, "sequence")
    pause_reset_epoch = _non_negative_int(pause_reset_epoch, "pause_reset_epoch")
    if not isinstance(playing, bool) or not isinstance(paused, bool):
        raise TypeError("playing and paused must be bool")
    if lifecycle_action not in {"start", "pause", "resume", "stop", "reset", "tick"}:
        raise ValueError("unsupported lifecycle_action")
    if atomicity not in {"ordered_non_atomic", "atomic"}:
        raise ValueError("unsupported atomicity")
    events = _normalize_events(input_events)
    clocks = _normalize_clocks(clock_provenance)
    links = _normalize_links(bridge_identity_links)
    rng = None if rng_context_snapshot is None else _json_copy(rng_context_snapshot, "rng_context_snapshot")
    if rng is not None and not validate_worldbridge_deterministic_randomness_snapshot(rng)["valid"]:
        raise ValueError("rng_context_snapshot failed deterministic randomness validation")
    failure_value = None if failure is None else _normalize_failure(failure)
    quarantine = failure_value is not None
    envelope: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "transport_mode": TRANSPORT_MODE,
        "envelope_id": envelope_id,
        "capture_epoch": capture_epoch,
        "sequence": sequence,
        "input_events": events,
        "lifecycle": {
            "pause_reset_epoch": pause_reset_epoch,
            "action": lifecycle_action,
            "playing": playing,
            "paused": paused,
        },
        "clock_provenance": clocks,
        "bridge_identity_links": links,
        "rng_context_snapshot": rng,
        "atomicity": atomicity,
        "failure": failure_value,
        "quarantine": quarantine,
        "lossless": False,
        "replay_admitted": False,
        "default_ready": False,
        "envelope_digest": "",
    }
    envelope["envelope_digest"] = _digest(envelope)
    return copy.deepcopy(envelope)


def validate_worldbridge_shared_state_envelope(envelope: object) -> dict[str, Any]:
    """Validate schema, digest and isolation-safe JSON shape without restoring state."""
    errors: list[str] = []
    if not isinstance(envelope, Mapping):
        return {"valid": False, "errors": ["envelope_not_mapping"]}
    try:
        if set(envelope) != _ENVELOPE_KEYS:
            errors.append("envelope_keys_mismatch")
    except Exception:
        return {"valid": False, "errors": ["envelope_keys_invalid"]}
    if envelope.get("schema_version") != SCHEMA_VERSION: errors.append("schema_version_mismatch")
    if envelope.get("status") != STATUS: errors.append("status_mismatch")
    if envelope.get("transport_mode") != TRANSPORT_MODE: errors.append("transport_mode_mismatch")
    for field in ("envelope_id",):
        try: _clean_id(envelope.get(field), field)
        except (TypeError, ValueError): errors.append(f"{field}_invalid")
    for field in ("capture_epoch", "sequence"):
        if not _is_non_negative_int(envelope.get(field)): errors.append(f"{field}_invalid")
    events = envelope.get("input_events")
    if not isinstance(events, list): errors.append("input_events_not_list")
    else: _validate_events(events, errors)
    lifecycle = envelope.get("lifecycle")
    if not isinstance(lifecycle, Mapping) or set(lifecycle) != _LIFECYCLE_KEYS:
        errors.append("lifecycle_invalid")
    else:
        if not _is_non_negative_int(lifecycle.get("pause_reset_epoch")): errors.append("pause_reset_epoch_invalid")
        if lifecycle.get("action") not in {"start", "pause", "resume", "stop", "reset", "tick"}: errors.append("lifecycle_action_invalid")
        if not isinstance(lifecycle.get("playing"), bool) or not isinstance(lifecycle.get("paused"), bool): errors.append("lifecycle_flags_invalid")
    clocks = envelope.get("clock_provenance")
    if not isinstance(clocks, Mapping): errors.append("clock_provenance_not_mapping")
    else: _validate_clocks(clocks, errors)
    links = envelope.get("bridge_identity_links")
    if not isinstance(links, list): errors.append("bridge_identity_links_not_list")
    else: _validate_links(links, errors)
    rng = envelope.get("rng_context_snapshot")
    if rng is not None:
        result = validate_worldbridge_deterministic_randomness_snapshot(rng)
        if not result["valid"]: errors.extend(f"rng_{e}" for e in result["errors"])
    if envelope.get("atomicity") not in {"ordered_non_atomic", "atomic"}: errors.append("atomicity_invalid")
    failure = envelope.get("failure")
    if failure is not None and (not isinstance(failure, Mapping) or set(failure) != _FAILURE_KEYS): errors.append("failure_invalid")
    if envelope.get("quarantine") is not (failure is not None): errors.append("quarantine_mismatch")
    for field in ("lossless", "replay_admitted", "default_ready"):
        if envelope.get(field) is not False: errors.append(f"{field}_must_remain_false")
    try: expected = _digest(envelope)
    except (TypeError, ValueError, OverflowError): expected = None; errors.append("envelope_not_canonical_json")
    if not _is_sha256(envelope.get("envelope_digest")): errors.append("envelope_digest_invalid")
    elif expected != envelope.get("envelope_digest"): errors.append("envelope_digest_mismatch")
    return {"valid": not errors, "errors": errors}


class WorldBridgeSharedStateReceiver:
    """Receiver-side continuity guard; it stores envelopes, never live lane objects."""

    __slots__ = (
        "_last_sequence",
        "_last_capture_epoch",
        "_last_pause_reset_epoch",
        "_last_input_sequence",
        "_last_input_pause_reset_epoch",
        "_rng_context_id",
        "_rng_snapshot_digest",
        "_accepted",
        "_accepted_count",
    )

    def __init__(self) -> None:
        self._last_sequence: int | None = None
        self._last_capture_epoch: int | None = None
        self._last_pause_reset_epoch: int | None = None
        self._last_input_sequence: int | None = None
        self._last_input_pause_reset_epoch: int | None = None
        self._rng_context_id: str | None = None
        self._rng_snapshot_digest: str | None = None
        self._accepted: deque[dict[str, Any]] = deque(maxlen=MAX_RETAINED_RECEIPTS)
        self._accepted_count = 0

    @property
    def accepted_count(self) -> int:
        """Return total accepted envelopes, independent of bounded retention."""
        return self._accepted_count

    @property
    def last_sequence(self) -> int | None:
        return self._last_sequence

    @property
    def last_capture_epoch(self) -> int | None:
        return self._last_capture_epoch

    @property
    def last_pause_reset_epoch(self) -> int | None:
        """Return the last accepted lifecycle epoch without exposing storage."""
        return self._last_pause_reset_epoch

    @property
    def last_input_sequence(self) -> int | None:
        """Return the last canonical input sequence accepted by this receiver."""
        return self._last_input_sequence

    @property
    def accepted_envelopes(self) -> list[dict[str, Any]]:
        """Return the bounded detached receipt window, never a live-state API."""
        return copy.deepcopy(list(self._accepted))

    def continuity_snapshot(self) -> dict[str, Any]:
        """Return detached receiver continuity, including its bounded receipts."""
        return {
            "last_sequence": self._last_sequence,
            "last_capture_epoch": self._last_capture_epoch,
            "last_pause_reset_epoch": self._last_pause_reset_epoch,
            "last_input_sequence": self._last_input_sequence,
            "last_input_pause_reset_epoch": self._last_input_pause_reset_epoch,
            "rng_context_id": self._rng_context_id,
            "rng_snapshot_digest": self._rng_snapshot_digest,
            "accepted_count": self._accepted_count,
            "accepted_envelopes": self.accepted_envelopes,
        }

    def restore_continuity(self, snapshot: Mapping[str, Any]) -> None:
        """Restore a validated detached cursor without applying live lane state."""
        if not isinstance(snapshot, Mapping):
            raise TypeError("receiver continuity snapshot must be a mapping")
        required = {"last_sequence", "last_capture_epoch", "last_pause_reset_epoch", "last_input_sequence", "last_input_pause_reset_epoch", "rng_context_id", "rng_snapshot_digest", "accepted_count", "accepted_envelopes"}
        if set(snapshot) != required:
            raise ValueError("receiver continuity schema mismatch")
        envelopes = snapshot["accepted_envelopes"]
        if not isinstance(envelopes, list) or len(envelopes) > MAX_RETAINED_RECEIPTS:
            raise ValueError("receiver continuity receipts invalid")
        count = snapshot["accepted_count"]
        if isinstance(count, bool) or not isinstance(count, int) or count < len(envelopes):
            raise ValueError("receiver continuity count invalid")
        previous_sequence = None
        previous_capture_epoch = None
        for envelope in envelopes:
            validation = validate_worldbridge_shared_state_envelope(envelope)
            if validation != {"valid": True, "errors": []}:
                raise ValueError("receiver continuity envelope invalid")
            sequence = envelope["sequence"]
            capture_epoch = envelope["capture_epoch"]
            if previous_sequence is not None and sequence != previous_sequence + 1:
                raise ValueError("receiver continuity window sequence mismatch")
            if previous_capture_epoch is not None and capture_epoch < previous_capture_epoch:
                raise ValueError("receiver continuity window epoch regression")
            previous_sequence = sequence
            previous_capture_epoch = capture_epoch
        if envelopes and envelopes[-1]["sequence"] != snapshot["last_sequence"]:
            raise ValueError("receiver continuity count mismatch")
        rng_snapshots = [item["rng_context_snapshot"] for item in envelopes]
        expected_rng_id = None
        expected_rng_digest = None
        if rng_snapshots and any(item is not None for item in rng_snapshots):
            # A transport-only checkpoint may legitimately contain no RNG
            # context at all. Once one snapshot is present, however, a gap is
            # ambiguous and must remain fail-closed.
            if any(item is None for item in rng_snapshots):
                raise ValueError("receiver continuity RNG snapshot gap")
            expected_rng_id = rng_snapshots[-1]["context_id"]
            expected_rng_digest = rng_snapshots[-1]["snapshot_digest"]
            if any(item["context_id"] != expected_rng_id for item in rng_snapshots):
                raise ValueError("receiver continuity RNG context mismatch")
        if snapshot["rng_context_id"] != expected_rng_id:
            raise ValueError("receiver continuity RNG context cursor mismatch")
        if snapshot["rng_snapshot_digest"] != expected_rng_digest:
            raise ValueError("receiver continuity RNG snapshot cursor mismatch")
        self._last_sequence = snapshot["last_sequence"]
        self._last_capture_epoch = snapshot["last_capture_epoch"]
        self._last_pause_reset_epoch = snapshot["last_pause_reset_epoch"]
        self._last_input_sequence = snapshot["last_input_sequence"]
        self._last_input_pause_reset_epoch = snapshot["last_input_pause_reset_epoch"]
        self._rng_context_id = snapshot["rng_context_id"]
        self._rng_snapshot_digest = snapshot["rng_snapshot_digest"]
        self._accepted = deque(copy.deepcopy(envelopes), maxlen=MAX_RETAINED_RECEIPTS)
        self._accepted_count = count

    def state_fingerprint(self) -> tuple[int, int | None, int | None, int | None, tuple[str, ...]]:
        """Expose continuity state for rollback evidence without exposing mutable storage."""
        return (
            self._accepted_count,
            self._last_sequence,
            self._last_capture_epoch,
            self._last_pause_reset_epoch,
            self._last_input_sequence,
            self._last_input_pause_reset_epoch,
            self._rng_context_id,
            self._rng_snapshot_digest,
            tuple(item["envelope_digest"] for item in self._accepted),
        )

    def accept(self, envelope: Mapping[str, Any]) -> dict[str, Any]:
        """Accept exactly the next sequence/epoch, or reject without mutation."""
        copied = copy_worldbridge_shared_state_envelope(envelope)
        sequence = copied["sequence"]
        capture_epoch = copied["capture_epoch"]
        pause_epoch = copied["lifecycle"]["pause_reset_epoch"]
        expected = 0 if self._last_sequence is None else self._last_sequence + 1
        if sequence != expected:
            raise ValueError(f"sequence continuity failure: expected {expected}, got {sequence}")
        if self._last_capture_epoch is not None and capture_epoch < self._last_capture_epoch:
            raise ValueError("capture_epoch regression")
        if self._last_pause_reset_epoch is not None and pause_epoch < self._last_pause_reset_epoch:
            raise ValueError("pause_reset_epoch regression")
        rng_snapshot = copied["rng_context_snapshot"]
        if self._rng_context_id is not None and rng_snapshot is None:
            raise ValueError("RNG snapshot continuity gap")
        if rng_snapshot is not None:
            context_id = rng_snapshot["context_id"]
            if self._rng_context_id is not None and context_id != self._rng_context_id:
                raise ValueError("RNG context mismatch")
        input_sequence, input_epoch = _validate_canonical_input_batch(
            copied["input_events"],
            last_sequence=self._last_input_sequence,
            last_pause_reset_epoch=self._last_input_pause_reset_epoch,
            envelope_pause_reset_epoch=pause_epoch,
        )
        self._accepted.append(copied)
        self._accepted_count += 1
        self._last_sequence = sequence
        self._last_capture_epoch = capture_epoch
        self._last_pause_reset_epoch = pause_epoch
        if input_sequence is not None:
            self._last_input_sequence = input_sequence
            self._last_input_pause_reset_epoch = input_epoch
        if rng_snapshot is not None:
            self._rng_context_id = rng_snapshot["context_id"]
            self._rng_snapshot_digest = rng_snapshot["snapshot_digest"]
        return copy.deepcopy(copied)

    def quarantine(self, *, sequence: int, code: str, stage: str, message: str) -> dict[str, Any]:
        """Return a failure artifact while preserving the last accepted receiver state."""
        return quarantine_worldbridge_shared_state_transport(
            envelope_id=f"receiver-quarantine-{sequence}", sequence=sequence,
            code=code, stage=stage, message=message,
        )


def copy_worldbridge_shared_state_envelope(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Validate then return a deep copy; invalid transport is rejected, never applied."""
    result = validate_worldbridge_shared_state_envelope(envelope)
    if not result["valid"]:
        raise ValueError("invalid shared state envelope: " + ", ".join(result["errors"]))
    return copy.deepcopy(dict(envelope))


def quarantine_worldbridge_shared_state_transport(*, envelope_id: str, sequence: int, code: str, stage: str, message: str) -> dict[str, Any]:
    """Create an explicit fallback artifact for partial transport failure."""
    return build_worldbridge_shared_state_envelope(
        envelope_id=envelope_id, capture_epoch=0, sequence=sequence, input_events=[],
        pause_reset_epoch=0, clock_provenance={"sr": _clock("sr", 0, 0.0, 0.0, "quarantine"), "ps": _clock("ps", 0, 0.0, 0.0, "quarantine")},
        bridge_identity_links=[], failure={"code": code, "stage": stage, "message": message},
    )


def build_worldbridge_shared_state_transport_contract() -> dict[str, Any]:
    sample = build_worldbridge_shared_state_envelope(
        envelope_id="e314-contract", capture_epoch=1, sequence=1, input_events=[], pause_reset_epoch=1,
        clock_provenance={"sr": _clock("sr", 1, 0.05, 0.05, "sr_runtime"), "ps": _clock("ps", 1, 1.0, 1.0, "pond_update")}, bridge_identity_links=[])
    validation = validate_worldbridge_shared_state_envelope(sample)
    return {"schema_version": SCHEMA_VERSION, "status": STATUS, "qt_free": True, "opt_in": True, "quarantine_only": True, "contract_valid": validation["valid"], "envelope": sample, "copy_isolated": copy_worldbridge_shared_state_envelope(sample) is not sample, "shared_live_restore": False, "replay_admitted": False, "lossless": False, "default_ready": False, "do_not_claim": list(DO_NOT_CLAIM)}


def _normalize_events(value: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence): raise TypeError("input_events must be a sequence")
    result=[]; seen=set()
    for index, raw in enumerate(value):
        if not isinstance(raw, Mapping) or set(raw) != _EVENT_KEYS: raise ValueError(f"input_events[{index}] keys mismatch")
        event_id = _clean_id(raw.get("event_id"), f"input_events[{index}].event_id")
        if event_id in seen: raise ValueError("duplicate input event_id")
        seen.add(event_id); kind = _clean_id(raw.get("kind"), f"input_events[{index}].kind")
        payload = _json_copy(raw.get("payload"), f"input_events[{index}].payload")
        if not isinstance(payload, dict): raise TypeError("event payload must be mapping")
        event = {"event_id": event_id, "kind": kind, "payload": payload}
        result.append(event)
    return result


def _normalize_clocks(value: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    if not isinstance(value, Mapping) or set(value) != {"sr", "ps"}: raise ValueError("clock_provenance must contain sr and ps")
    result={}
    for lane, raw in value.items():
        if not isinstance(raw, Mapping) or set(raw) != _CLOCK_KEYS: raise ValueError(f"clock {lane} keys mismatch")
        domain = _clean_id(raw.get("domain"), f"clock.{lane}.domain")
        if domain != lane: raise ValueError(f"clock domain mismatch for {lane}")
        tick = _non_negative_int(raw.get("tick"), f"clock.{lane}.tick")
        delta = _finite_non_negative(raw.get("delta"), f"clock.{lane}.delta")
        time = _finite_non_negative(raw.get("time"), f"clock.{lane}.time")
        source = _clean_id(raw.get("source"), f"clock.{lane}.source")
        result[lane] = {"domain": domain, "tick": tick, "delta": delta, "time": time, "source": source}
    return result


def _clock(domain: str, tick: int, delta: float, time: float, source: str) -> dict[str, Any]: return {"domain": domain, "tick": tick, "delta": delta, "time": time, "source": source}


def _normalize_links(value: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence): raise TypeError("bridge_identity_links must be a sequence")
    result=[]; seen_sr=set(); seen_ps=set()
    for index, raw in enumerate(value):
        if not isinstance(raw, Mapping): raise TypeError(f"bridge_identity_links[{index}] must be mapping")
        sr = _clean_id(raw.get("sr_entity_id"), f"bridge_identity_links[{index}].sr_entity_id")
        ps = _clean_id(raw.get("ps_organism_id"), f"bridge_identity_links[{index}].ps_organism_id")
        relation = raw.get("relation", "observation_link")
        if set(raw) not in ({"sr_entity_id", "ps_organism_id"}, _LINK_KEYS): raise ValueError("identity link keys mismatch")
        if relation != "observation_link": raise ValueError("unsupported identity relation")
        if sr in seen_sr or ps in seen_ps: raise ValueError("duplicate bridge identity")
        seen_sr.add(sr); seen_ps.add(ps); result.append({"sr_entity_id": sr, "ps_organism_id": ps, "relation": relation})
    return sorted(result, key=lambda item: (item["sr_entity_id"], item["ps_organism_id"]))


def _normalize_failure(value: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != _FAILURE_KEYS: raise ValueError("failure keys mismatch")
    return {key: _clean_id(value[key], f"failure.{key}") if key != "message" else _required_string(value[key], "failure.message") for key in _FAILURE_KEYS}


def _validate_events(events: list[Any], errors: list[str]) -> None:
    seen=set()
    for i, raw in enumerate(events):
        if not isinstance(raw, Mapping) or set(raw) != _EVENT_KEYS: errors.append(f"input_event_{i}_invalid"); continue
        if not isinstance(raw.get("event_id"), str) or raw["event_id"] in seen: errors.append(f"input_event_{i}_id_invalid")
        seen.add(raw.get("event_id"));
        if not isinstance(raw.get("kind"), str) or not isinstance(raw.get("payload"), Mapping): errors.append(f"input_event_{i}_fields_invalid")


def _validate_clocks(clocks: Mapping[str, Any], errors: list[str]) -> None:
    if set(clocks) != {"sr", "ps"}: errors.append("clock_domains_mismatch"); return
    for lane, raw in clocks.items():
        if not isinstance(raw, Mapping) or set(raw) != _CLOCK_KEYS: errors.append(f"clock_{lane}_invalid"); continue
        if raw.get("domain") != lane: errors.append(f"clock_{lane}_domain_invalid")
        if not _is_non_negative_int(raw.get("tick")): errors.append(f"clock_{lane}_tick_invalid")
        if not _is_finite_non_negative(raw.get("delta")) or not _is_finite_non_negative(raw.get("time")): errors.append(f"clock_{lane}_value_invalid")
        if not isinstance(raw.get("source"), str) or not raw["source"]: errors.append(f"clock_{lane}_source_invalid")


def _validate_links(links: list[Any], errors: list[str]) -> None:
    seen_sr=set(); seen_ps=set()
    for i, raw in enumerate(links):
        if not isinstance(raw, Mapping) or set(raw) != _LINK_KEYS: errors.append(f"identity_link_{i}_invalid"); continue
        sr, ps = raw.get("sr_entity_id"), raw.get("ps_organism_id")
        if not isinstance(sr, str) or sr in seen_sr or not isinstance(ps, str) or ps in seen_ps: errors.append(f"identity_link_{i}_duplicate_or_invalid")
        seen_sr.add(sr); seen_ps.add(ps)
        if raw.get("relation") != "observation_link": errors.append(f"identity_link_{i}_relation_invalid")


def _validate_canonical_input_batch(
    events: list[Any],
    *,
    last_sequence: int | None,
    last_pause_reset_epoch: int | None,
    envelope_pause_reset_epoch: int,
) -> tuple[int | None, int | None]:
    """Reject dropped canonical input events before receiver state mutation.

    Legacy diagnostic envelopes may contain arbitrary event payloads and remain
    accepted.  Once the viewport canonical shape is present, every event in
    that envelope must carry a contiguous input sequence and matching epoch.
    """
    canonical_flags = [
        isinstance(event, Mapping)
        and isinstance(event.get("payload"), Mapping)
        and "canonical_sequence" in event["payload"]
        for event in events
    ]
    if not any(canonical_flags):
        return None, None
    if not all(canonical_flags):
        raise ValueError("canonical input batch mixes canonical and legacy events")
    expected = None if last_sequence is None else last_sequence + 1
    current_sequence = last_sequence
    current_epoch = last_pause_reset_epoch
    for index, event in enumerate(events):
        payload = event["payload"]
        required = {"canonical_sequence", "pause_reset_epoch", "event_digest", "data"}
        if set(payload) != required:
            raise ValueError(f"canonical input event {index} schema invalid")
        sequence = payload["canonical_sequence"]
        epoch = payload["pause_reset_epoch"]
        if not _is_non_negative_int(sequence):
            raise ValueError(f"canonical input event {index} sequence invalid")
        if not _is_non_negative_int(epoch):
            raise ValueError(f"canonical input event {index} epoch invalid")
        if not _is_sha256(payload["event_digest"]):
            raise ValueError(f"canonical input event {index} digest invalid")
        if epoch != envelope_pause_reset_epoch:
            raise ValueError(f"canonical input event {index} epoch mismatch")
        if expected is not None and sequence != expected:
            raise ValueError(
                f"canonical input sequence continuity failure: expected {expected}, got {sequence}"
            )
        expected = sequence + 1
        current_sequence = sequence
        current_epoch = epoch
    return current_sequence, current_epoch


def _json_copy(value: Any, field: str) -> Any:
    try: return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))
    except (TypeError, ValueError) as exc: raise TypeError(f"{field} must be finite JSON") from exc


def _digest(value: Mapping[str, Any]) -> str:
    clean = dict(value); clean["envelope_digest"] = ""
    return hashlib.sha256(json.dumps(clean, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _clean_id(value: object, field: str) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None: raise ValueError(f"{field} must be a clean identifier")
    return value


def _required_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip(): raise ValueError(f"{field} must be non-empty string")
    return value.strip()


def _is_non_negative_int(value: object) -> bool: return isinstance(value, int) and not isinstance(value, bool) and value >= 0

def _non_negative_int(value: object, field: str) -> int:
    if not _is_non_negative_int(value): raise TypeError(f"{field} must be non-negative integer")
    return value


def _is_finite_non_negative(value: object) -> bool: return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and float(value) >= 0

def _finite_non_negative(value: object, field: str) -> float:
    if not _is_finite_non_negative(value): raise TypeError(f"{field} must be finite non-negative number")
    return float(value)


def _is_sha256(value: object) -> bool: return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


__all__ = [
    "SCHEMA_VERSION", "STATUS", "TRANSPORT_MODE", "DO_NOT_CLAIM", "MAX_RETAINED_RECEIPTS",
    "build_worldbridge_shared_state_envelope", "validate_worldbridge_shared_state_envelope",
    "copy_worldbridge_shared_state_envelope", "quarantine_worldbridge_shared_state_transport",
    "build_worldbridge_shared_state_transport_contract",
]
