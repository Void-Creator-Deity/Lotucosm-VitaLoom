# -*- coding: utf-8 -*-
"""Qt-free production tick authority for the opt-in WorldBridge boundary.

One tick owns exactly one delta, one ordered input batch and one RNG stream
snapshot boundary.  This module is the single place where those three are bound
together, so the SR script phase and the PS bridge read the same immutable
batch instead of re-deriving it independently.

The authority never touches module-global RNGs, never restores live state and
never admits replay.  Every admission flag stays ``False``; the value of the
module is fail-closed binding evidence, not a checkpoint.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .world_bridge_deterministic_randomness_context import (
    WorldBridgeDeterministicRandomnessContext,
    validate_worldbridge_deterministic_randomness_snapshot,
)
from .world_bridge_clock_ordering_authority import (
    validate_worldbridge_frame_clock_decision,
)
from .world_bridge_input_sequence import (
    LIFECYCLE_ACTIONS,
    WorldBridgeInputSequence,
    validate_worldbridge_input_events,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_tick_authority"
CONTEXT_STATUS = "worldbridge_tick_context"
RECEIPT_STATUS = "worldbridge_tick_receipt"
CLOCK_DOMAIN = "worldbridge_authority_tick_v1"
RNG_PHASE_ORDER = ("sr.start", "sr.complete", "ps.start", "ps.complete")
CLOCK_CONSUMER_ORDER = ("sr", "ps")
ADMISSION_KEYS = ("atomic_checkpoint", "lossless", "replay_admitted", "default_ready")

_CONTEXT_KEYS = {
    "schema_version",
    "status",
    "tick_sequence",
    "delta_time",
    "paused",
    "lifecycle_action",
    "pause_reset_epoch",
    "input_events",
    "clock_domain",
    "source",
    "rng_context_id",
    "rng_snapshot_digest",
    "rng_context_snapshot",
    "admissions",
    "context_digest",
}

_CLOCK_CONTEXT_KEYS = {
    "clock_decision",
    "clock_decision_digest",
    "clock_consumers",
}

_SNAPSHOT_KEYS = {
    "schema_version",
    "status",
    "tick_sequence",
    "last_input_sequence",
    "pause_reset_epoch",
    "input_sequence_snapshot",
    "current_tick",
    "rng_phases",
    "rng_context_id",
    "last_receipt",
}

_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _context_digest(context: Mapping[str, Any]) -> str:
    clean = dict(context)
    clean["context_digest"] = ""
    return _digest(clean)


def _receipt_digest(receipt: Mapping[str, Any]) -> str:
    clean = dict(receipt)
    clean["receipt_digest"] = ""
    return _digest(clean)


def _validate_rng_phase_records(
    records: object,
    *,
    tick_sequence: int | None,
    expected_phase_count: int | None = None,
    error_prefix: str = "rng_phases",
) -> list[str]:
    """Validate ordered phase evidence shared by receipts and snapshots."""
    errors: list[str] = []
    if not isinstance(records, list) or len(records) > len(RNG_PHASE_ORDER):
        return [f"{error_prefix}_invalid"]
    if expected_phase_count is not None and len(records) != expected_phase_count:
        errors.append(f"{error_prefix}_count_mismatch")
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"{error_prefix}_record_invalid")
            continue
        if set(record) != {
            "phase", "order", "tick_sequence", "draw_counts", "record_digest"
        }:
            errors.append(f"{error_prefix}_keys_invalid")
            continue
        if record.get("phase") != RNG_PHASE_ORDER[index] or record.get("order") != index:
            errors.append(f"{error_prefix}_order_invalid")
        if tick_sequence is not None and record.get("tick_sequence") != tick_sequence:
            errors.append(f"{error_prefix}_tick_sequence_mismatch")
        draw_counts = record.get("draw_counts")
        if not isinstance(draw_counts, Mapping):
            errors.append(f"{error_prefix}_draw_counts_invalid")
        else:
            for name, value in draw_counts.items():
                if (
                    not isinstance(name, str)
                    or _TOKEN_RE.fullmatch(name) is None
                    or isinstance(value, bool)
                    or not isinstance(value, int)
                    or value < 0
                ):
                    errors.append(f"{error_prefix}_draw_counts_invalid")
                    break
        record_digest = record.get("record_digest")
        if not isinstance(record_digest, str) or len(record_digest) != 64:
            errors.append(f"{error_prefix}_record_digest_invalid")
            continue
        payload = dict(record)
        payload.pop("record_digest")
        try:
            expected_digest = _digest(payload)
        except (TypeError, ValueError, OverflowError):
            errors.append(f"{error_prefix}_record_not_canonical_json")
        else:
            if record_digest != expected_digest:
                # Keep the historical singular phase-digest code used by
                # existing restore diagnostics while sharing validation.
                errors.append(
                    f"{error_prefix.removesuffix('_phases')}_phase_digest_mismatch"
                )
    return errors


def _clock_consumer_digest(consumer: Mapping[str, Any]) -> str:
    payload = dict(consumer)
    payload["consumer_digest"] = ""
    return _digest(payload)


def _validate_clock_consumers(
    consumers: object,
    *,
    tick_sequence: int | None,
    decision_digest: str | None,
    require_sr: bool,
    require_ps: bool,
    error_prefix: str,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(consumers, list) or len(consumers) > len(CLOCK_CONSUMER_ORDER):
        return [f"{error_prefix}_invalid"]
    seen: list[str] = []
    for index, consumer in enumerate(consumers):
        if not isinstance(consumer, Mapping):
            errors.append(f"{error_prefix}_record_invalid")
            continue
        if set(consumer) != {
            "consumer", "decision_digest", "tick_sequence", "consumer_digest"
        }:
            errors.append(f"{error_prefix}_keys_invalid")
            continue
        name = consumer.get("consumer")
        if name not in CLOCK_CONSUMER_ORDER:
            errors.append(f"{error_prefix}_name_invalid")
            continue
        if index >= len(CLOCK_CONSUMER_ORDER) or name != CLOCK_CONSUMER_ORDER[index]:
            errors.append(f"{error_prefix}_order_invalid")
        if name in seen:
            errors.append(f"{error_prefix}_duplicate")
        seen.append(name)
        if decision_digest is not None and consumer.get("decision_digest") != decision_digest:
            errors.append(f"{error_prefix}_decision_digest_mismatch")
        if tick_sequence is not None and consumer.get("tick_sequence") != tick_sequence:
            errors.append(f"{error_prefix}_tick_sequence_mismatch")
        digest = consumer.get("consumer_digest")
        if not isinstance(digest, str) or len(digest) != 64:
            errors.append(f"{error_prefix}_digest_invalid")
        else:
            payload = dict(consumer)
            payload.pop("consumer_digest")
            if digest != _digest(payload):
                errors.append(f"{error_prefix}_digest_mismatch")
    if require_sr and "sr" not in seen:
        errors.append(f"{error_prefix}_sr_missing")
    if require_ps and "ps" not in seen:
        errors.append(f"{error_prefix}_ps_missing")
    return errors


def validate_worldbridge_tick_receipt(receipt: object) -> dict[str, Any]:
    """Validate one detached completed-tick receipt without owned state."""
    errors: list[str] = []
    if not isinstance(receipt, Mapping):
        return {"valid": False, "errors": ["receipt_not_mapping"]}
    if receipt.get("schema_version") != SCHEMA_VERSION:
        errors.append("receipt_version_mismatch")
    if receipt.get("status") != RECEIPT_STATUS:
        errors.append("receipt_status_mismatch")
    tick_sequence = receipt.get("tick_sequence")
    if (
        isinstance(tick_sequence, bool)
        or not isinstance(tick_sequence, int)
        or tick_sequence < 1
    ):
        errors.append("receipt_tick_sequence_invalid")
        clean_tick_sequence = None
    else:
        clean_tick_sequence = tick_sequence
    epoch = receipt.get("pause_reset_epoch")
    if isinstance(epoch, bool) or not isinstance(epoch, int) or epoch < 0:
        errors.append("receipt_pause_reset_epoch_invalid")
    for field in ("input_digest", "context_digest"):
        digest = receipt.get(field)
        if not isinstance(digest, str) or len(digest) != 64:
            errors.append(f"receipt_{field}_invalid")
    rng_context_id = receipt.get("rng_context_id")
    if rng_context_id is not None and (
        not isinstance(rng_context_id, str)
        or _TOKEN_RE.fullmatch(rng_context_id) is None
    ):
        errors.append("receipt_rng_context_id_invalid")
    rng_start_digest = receipt.get("rng_start_digest")
    rng_end_digest = receipt.get("rng_end_digest")
    for field, digest in (
        ("rng_start_digest", rng_start_digest),
        ("rng_end_digest", rng_end_digest),
    ):
        if digest is not None and (
            not isinstance(digest, str) or len(digest) != 64
        ):
            errors.append(f"receipt_{field}_invalid")
    if rng_context_id is None:
        if rng_start_digest is not None or rng_end_digest is not None:
            errors.append("receipt_rng_binding_inconsistent")
    elif not all(
        isinstance(digest, str) and len(digest) == 64
        for digest in (rng_start_digest, rng_end_digest)
    ):
        errors.append("receipt_rng_binding_incomplete")
    phase_count = receipt.get("rng_phase_count")
    if (
        isinstance(phase_count, bool)
        or not isinstance(phase_count, int)
        or phase_count < 0
        or phase_count > len(RNG_PHASE_ORDER)
    ):
        errors.append("receipt_rng_phase_count_invalid")
        clean_phase_count = None
    else:
        clean_phase_count = phase_count
    errors.extend(
        _validate_rng_phase_records(
            receipt.get("rng_phases"),
            tick_sequence=clean_tick_sequence,
            expected_phase_count=clean_phase_count,
            error_prefix="receipt_rng_phases",
        )
    )
    has_clock = all(field in receipt for field in _CLOCK_CONTEXT_KEYS)
    if any(field in receipt for field in _CLOCK_CONTEXT_KEYS) and not has_clock:
        errors.append("receipt_clock_fields_incomplete")
    if has_clock:
        decision = receipt.get("clock_decision")
        digest = receipt.get("clock_decision_digest")
        consumers = receipt.get("clock_consumers")
        validation = validate_worldbridge_frame_clock_decision(decision)
        if validation != {"valid": True, "errors": []}:
            errors.extend(
                f"receipt_clock_decision_{item.removeprefix('decision_')}"
                for item in validation["errors"]
            )
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or not isinstance(decision, Mapping)
            or digest != decision.get("decision_digest")
        ):
            errors.append("receipt_clock_decision_digest_mismatch")
        if isinstance(decision, Mapping):
            if receipt.get("delta_time") != decision.get("sr_delta_seconds"):
                errors.append("receipt_clock_delta_mismatch")
            if receipt.get("paused") != decision.get("paused"):
                errors.append("receipt_clock_paused_mismatch")
        errors.extend(_validate_clock_consumers(
            consumers,
            tick_sequence=clean_tick_sequence,
            decision_digest=digest if isinstance(digest, str) else None,
            require_sr=True,
            require_ps=(
                isinstance(decision, Mapping)
                and decision.get("bridge_handoff_requested") is True
            ),
            error_prefix="receipt_clock_consumers",
        ))
    admissions = receipt.get("admissions")
    if (
        not isinstance(admissions, Mapping)
        or set(admissions) != set(ADMISSION_KEYS)
    ):
        errors.append("receipt_admissions_keys_invalid")
    elif any(value is not False for value in admissions.values()):
        errors.append("receipt_admissions_must_be_false")
    digest = receipt.get("receipt_digest")
    if not isinstance(digest, str) or len(digest) != 64:
        errors.append("receipt_digest_invalid")
    else:
        try:
            expected_digest = _receipt_digest(receipt)
        except (TypeError, ValueError, OverflowError):
            errors.append("receipt_not_canonical_json")
        else:
            if digest != expected_digest:
                errors.append("receipt_digest_mismatch")
    return {"valid": not errors, "errors": errors}

def _clean_token(value: object, field: str) -> str:
    if not isinstance(value, str) or _TOKEN_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a clean identifier")
    return value


def _finite_non_negative(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a finite non-negative number")
    number = float(value)
    if not math.isfinite(number) or number < 0.0:
        raise TypeError(f"{field} must be a finite non-negative number")
    return number


def _non_negative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TypeError(f"{field} must be a non-negative integer")
    return value


def _batch_digest(events: Sequence[Mapping[str, Any]]) -> str:
    return _digest(
        [
            {
                "event_id": event["event_id"],
                "sequence": event["sequence"],
                "pause_reset_epoch": event["pause_reset_epoch"],
                "kind": event["kind"],
                "payload": event["payload"],
                "event_digest": event["event_digest"],
            }
            for event in events
        ]
    )


def _admissions() -> dict[str, bool]:
    return {key: False for key in ADMISSION_KEYS}


class WorldBridgeTickAuthority:
    """Own one ordered delta/input/RNG binding per opt-in runtime tick."""

    def __init__(
        self,
        *,
        input_sequence: WorldBridgeInputSequence | None = None,
        clock_domain: str = CLOCK_DOMAIN,
    ) -> None:
        if input_sequence is None:
            input_sequence = WorldBridgeInputSequence()
        if not isinstance(input_sequence, WorldBridgeInputSequence):
            raise TypeError("input_sequence must be a WorldBridgeInputSequence")
        self.input_sequence = input_sequence
        self.clock_domain = _clean_token(clock_domain, "clock_domain")
        self._tick_sequence = 0
        self._last_input_sequence = 0
        self._current: dict[str, Any] | None = None
        self._rng_context: WorldBridgeDeterministicRandomnessContext | None = None
        self._rng_phases: list[dict[str, Any]] = []
        self._clock_consumers: list[dict[str, Any]] = []
        self._last_receipt: dict[str, Any] | None = None

    @property
    def tick_sequence(self) -> int:
        return self._tick_sequence

    @property
    def admissions(self) -> dict[str, bool]:
        return _admissions()

    @property
    def rng_context_id(self) -> str | None:
        return None if self._rng_context is None else self._rng_context.context_id

    @property
    def rng_phases(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._rng_phases)

    @property
    def last_receipt(self) -> dict[str, Any] | None:
        return None if self._last_receipt is None else copy.deepcopy(self._last_receipt)

    def bind_randomness_context(self, context: object | None) -> dict[str, Any] | None:
        """Bind the caller-owned named-stream context used for tick boundaries."""
        if context is None:
            self._rng_context = None
            return None
        if not isinstance(context, WorldBridgeDeterministicRandomnessContext):
            raise TypeError(
                "context must be a WorldBridgeDeterministicRandomnessContext"
            )
        snapshot = context.snapshot()
        validation = validate_worldbridge_deterministic_randomness_snapshot(snapshot)
        if validation != {"valid": True, "errors": []}:
            raise ValueError(
                "deterministic context failed tick authority validation: "
                + ",".join(validation["errors"])
            )
        self._rng_context = context
        return snapshot

    def begin_tick(
        self,
        delta_time: float,
        *,
        paused: bool = False,
        lifecycle_action: str = "tick",
        source: str = "viewport_tick",
        clock_decision: Mapping[str, Any] | None = None,
        clock_owner_token: str | None = None,
        clock_runtime_epoch: str | None = None,
    ) -> dict[str, Any]:
        """Consume the current input batch and seal one immutable tick context."""
        if self._current is not None:
            raise RuntimeError("worldbridge tick authority already owns an active tick")
        if not isinstance(paused, bool):
            raise TypeError("paused must be bool")
        delta = _finite_non_negative(delta_time, "delta_time")
        if paused and delta != 0.0:
            raise ValueError("paused tick must carry a zero delta")
        if lifecycle_action not in LIFECYCLE_ACTIONS:
            raise ValueError("unsupported lifecycle_action")
        clean_source = _clean_token(source, "source")
        decision: dict[str, Any] | None = None
        decision_digest: str | None = None
        if clock_decision is not None:
            validation = validate_worldbridge_frame_clock_decision(clock_decision)
            if validation != {"valid": True, "errors": []}:
                raise ValueError(
                    "worldbridge frame clock decision rejected: "
                    + ",".join(validation["errors"])
                )
            decision = copy.deepcopy(dict(clock_decision))
            decision_digest = str(decision["decision_digest"])
            if paused != decision["paused"]:
                raise ValueError("clock decision paused state mismatch")
            if delta != float(decision["sr_delta_seconds"]):
                raise ValueError("clock decision delta mismatch")
            if clock_owner_token != decision["owner_token"]:
                raise ValueError("clock decision owner token mismatch")
            if clock_runtime_epoch != decision["runtime_epoch"]:
                raise ValueError("clock decision runtime epoch mismatch")
            if (
                self._last_receipt is not None
                and self._last_receipt.get("clock_decision_digest") == decision_digest
            ):
                raise ValueError("clock decision is stale")
        epoch = self.input_sequence.pause_reset_epoch
        pending = self.input_sequence.snapshot()["pending"]
        validation = validate_worldbridge_input_events(
            pending,
            last_sequence=self._last_input_sequence,
            pause_reset_epoch=epoch,
        )
        if not validation["valid"]:
            raise ValueError(
                "worldbridge tick input batch rejected: "
                + ",".join(validation["errors"])
            )
        rng_snapshot: dict[str, Any] | None = None
        rng_context_id: str | None = None
        rng_digest: str | None = None
        if self._rng_context is not None:
            rng_snapshot = self._rng_context.snapshot()
            check = validate_worldbridge_deterministic_randomness_snapshot(rng_snapshot)
            if check != {"valid": True, "errors": []}:
                raise ValueError("worldbridge tick rng snapshot rejected")
            rng_context_id = rng_snapshot["context_id"]
            rng_digest = rng_snapshot["snapshot_digest"]

        events = self.input_sequence.consume()
        if events:
            self._last_input_sequence = int(events[-1]["sequence"])
        self._tick_sequence += 1
        context: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "status": CONTEXT_STATUS,
            "tick_sequence": self._tick_sequence,
            "delta_time": delta,
            "paused": paused,
            "lifecycle_action": lifecycle_action,
            "pause_reset_epoch": epoch,
            "input_events": events,
            "clock_domain": self.clock_domain,
            "source": clean_source,
            "rng_context_id": rng_context_id,
            "rng_snapshot_digest": rng_digest,
            "rng_context_snapshot": rng_snapshot,
            "admissions": _admissions(),
            "context_digest": "",
        }
        if decision is not None:
            context["clock_decision"] = decision
            context["clock_decision_digest"] = decision_digest
            context["clock_consumers"] = []
        context["context_digest"] = _context_digest(context)
        self._rng_phases = []
        self._clock_consumers = []
        self._current = context
        return copy.deepcopy(context)

    def current_tick(self) -> dict[str, Any] | None:
        return None if self._current is None else copy.deepcopy(self._current)

    def consume_inputs(self) -> list[dict[str, Any]]:
        """Return the active tick batch, or fall back to the raw input cursor."""
        if self._current is not None:
            return copy.deepcopy(self._current["input_events"])
        events = self.input_sequence.consume()
        if events:
            self._last_input_sequence = int(events[-1]["sequence"])
        return events

    def record_rng_phase(
        self,
        phase: str,
        *,
        draw_counts: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record one ordered RNG boundary inside the active tick."""
        if self._current is None:
            raise RuntimeError("worldbridge tick authority has no active tick")
        if phase not in RNG_PHASE_ORDER:
            raise ValueError("unsupported rng phase")
        if len(self._rng_phases) >= len(RNG_PHASE_ORDER):
            raise ValueError("rng phase order violation: all phases already recorded")
        expected = RNG_PHASE_ORDER[len(self._rng_phases)]
        if phase != expected:
            raise ValueError(
                f"rng phase order violation: expected {expected}, got {phase}"
            )
        counts: dict[str, int] = {}
        if draw_counts is not None:
            if not isinstance(draw_counts, Mapping):
                raise TypeError("draw_counts must be a mapping")
            for name, value in draw_counts.items():
                counts[_clean_token(name, "draw stream name")] = _non_negative_int(
                    value, "draw count"
                )
        record: dict[str, Any] = {
            "phase": phase,
            "order": len(self._rng_phases),
            "tick_sequence": self._current["tick_sequence"],
            "draw_counts": counts,
        }
        record["record_digest"] = _digest(record)
        self._rng_phases.append(record)
        return copy.deepcopy(record)

    def record_clock_consumer(self, consumer: str) -> dict[str, Any]:
        """Append SR then PS evidence for the active clock decision.

        SR is the first consumer of every decision-bound tick. PS may appear
        only when the viewport requested a real bridge handoff, and completion
        additionally requires that the Pond bridge actually succeeded.
        """
        if self._current is None:
            raise RuntimeError("worldbridge tick authority has no active tick")
        decision = self._current.get("clock_decision")
        if not isinstance(decision, Mapping):
            raise RuntimeError("no clock decision is bound to the active tick")
        if consumer not in CLOCK_CONSUMER_ORDER:
            raise ValueError("unsupported clock consumer")
        expected = CLOCK_CONSUMER_ORDER[len(self._clock_consumers)]
        if consumer != expected:
            if consumer in ("sr", "ps") and any(
                row.get("consumer") == consumer for row in self._clock_consumers
            ):
                raise ValueError(f"clock consumer already recorded: {consumer}")
            raise ValueError(
                f"clock consumer order violation: expected {expected}, got {consumer}"
            )
        if consumer == "ps" and decision.get("bridge_handoff_requested") is not True:
            raise ValueError("PS consumer requires a requested bridge handoff")
        record: dict[str, Any] = {
            "consumer": consumer,
            "decision_digest": decision["decision_digest"],
            "tick_sequence": self._current["tick_sequence"],
            "consumer_digest": "",
        }
        record["consumer_digest"] = _digest(
            {key: value for key, value in record.items() if key != "consumer_digest"}
        )
        self._clock_consumers.append(record)
        self._current["clock_consumers"] = copy.deepcopy(self._clock_consumers)
        self._current["context_digest"] = ""
        self._current["context_digest"] = _context_digest(self._current)
        return copy.deepcopy(record)

    def complete_tick(self) -> dict[str, Any]:
        """Seal the tick with an end-of-tick RNG boundary and a detached receipt."""
        if self._current is None:
            raise RuntimeError("worldbridge tick authority has no active tick")
        context = self._current
        context_validation = self.validate_tick_context(context)
        if not context_validation["valid"]:
            self.clear_active_tick()
            raise ValueError(
                "worldbridge tick context rejected: "
                + ",".join(context_validation["errors"])
            )
        decision = context.get("clock_decision")
        if isinstance(decision, Mapping):
            consumers = context.get("clock_consumers")
            consumer_names = (
                [row.get("consumer") for row in consumers]
                if isinstance(consumers, list)
                else []
            )
            if "sr" not in consumer_names:
                self.clear_active_tick()
                raise ValueError("clock decision tick requires SR consumption")
            handoff_requested = decision.get("bridge_handoff_requested") is True
            if handoff_requested and "ps" not in consumer_names:
                self.clear_active_tick()
                raise ValueError("clock decision tick requires PS handoff consumption")
            if not handoff_requested and "ps" in consumer_names:
                self.clear_active_tick()
                raise ValueError("clock decision tick forbids PS without handoff")
        rng_end: dict[str, Any] | None = None
        if self._rng_context is not None:
            rng_end = self._rng_context.snapshot()
        receipt: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "status": RECEIPT_STATUS,
            "tick_sequence": context["tick_sequence"],
            "delta_time": context["delta_time"],
            "paused": context["paused"],
            "lifecycle_action": context["lifecycle_action"],
            "pause_reset_epoch": context["pause_reset_epoch"],
            "clock_domain": context["clock_domain"],
            "source": context["source"],
            "input_event_count": len(context["input_events"]),
            "input_digest": _batch_digest(context["input_events"]),
            "context_digest": context["context_digest"],
            "rng_context_id": context["rng_context_id"],
            "rng_start_digest": context["rng_snapshot_digest"],
            "rng_end_digest": None if rng_end is None else rng_end["snapshot_digest"],
            "rng_phase_count": len(self._rng_phases),
            "rng_phases": copy.deepcopy(self._rng_phases),
            "admissions": _admissions(),
            "receipt_digest": "",
        }
        if isinstance(decision, Mapping):
            receipt["clock_decision"] = copy.deepcopy(dict(decision))
            receipt["clock_decision_digest"] = context["clock_decision_digest"]
            receipt["clock_consumers"] = copy.deepcopy(context["clock_consumers"])
        receipt["receipt_digest"] = _receipt_digest(receipt)
        self._last_receipt = receipt
        # Completion closes the transient binding but keeps the just-sealed RNG
        # phases available to the published snapshot contract.
        self._current = None
        self._clock_consumers = []
        return copy.deepcopy(receipt)

    def clear_active_tick(self) -> None:
        """Drop the transient tick binding without advancing the input epoch."""
        self._current = None
        self._rng_phases = []
        self._clock_consumers = []

    def reset(self, *, lifecycle_action: str = "reset") -> dict[str, Any]:
        """Advance the input lifecycle epoch and drop the transient tick binding."""
        if lifecycle_action not in LIFECYCLE_ACTIONS:
            raise ValueError("unsupported lifecycle_action")
        result = self.input_sequence.lifecycle(lifecycle_action)
        self.clear_active_tick()
        # A lifecycle boundary intentionally discards the pending batch; the
        # cursor pointer must follow the sequence counter so the discarded
        # events are not later reported as a continuity gap.
        self._last_input_sequence = self.input_sequence.snapshot()["next_sequence"] - 1
        return {
            "lifecycle_action": lifecycle_action,
            "pause_reset_epoch": result["pause_reset_epoch"],
            "tick_sequence": self._tick_sequence,
        }

    def check_tick_binding(
        self,
        *,
        delta_time: float | None = None,
        input_events: Sequence[Mapping[str, Any]] | None = None,
        tick_sequence: int | None = None,
        clock_decision_digest: str | None = None,
    ) -> dict[str, Any]:
        """Fail-closed check that a consumer uses the active tick binding."""
        context = self._current
        if context is None:
            return {"valid": False, "errors": ["no_active_tick"]}
        errors = list(self.validate_tick_context(context)["errors"])
        if delta_time is not None:
            try:
                candidate_delta = float(delta_time)
            except (TypeError, ValueError):
                candidate_delta = None
            if candidate_delta is None or candidate_delta != float(context["delta_time"]):
                errors.append("delta_time_mismatch")
        if tick_sequence is not None:
            if tick_sequence != context["tick_sequence"]:
                errors.append("tick_sequence_mismatch")
        if input_events is not None:
            try:
                candidate_digest = _batch_digest(input_events)
            except (KeyError, TypeError):
                candidate_digest = None
            if candidate_digest != _batch_digest(context["input_events"]):
                errors.append("input_batch_mismatch")
        if clock_decision_digest is not None:
            if clock_decision_digest != context.get("clock_decision_digest"):
                errors.append("clock_decision_digest_mismatch")
        return {"valid": not errors, "errors": errors}

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS,
            "tick_sequence": self._tick_sequence,
            "last_input_sequence": self._last_input_sequence,
            "pause_reset_epoch": self.input_sequence.pause_reset_epoch,
            "input_sequence_snapshot": self.input_sequence.snapshot(),
            "current_tick": copy.deepcopy(self._current),
            "rng_phases": copy.deepcopy(self._rng_phases),
            "rng_context_id": self.rng_context_id,
            "last_receipt": copy.deepcopy(self._last_receipt),
        }

    def restore_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        """Restore the authority cursor atomically after full validation."""
        validation = validate_worldbridge_tick_authority_snapshot(snapshot)
        if not validation["valid"]:
            raise ValueError(
                "invalid tick authority snapshot: "
                + ",".join(validation["errors"])
            )

        # The context object itself is process-owned and is never replaced by a
        # checkpoint. Refuse a snapshot from another named-stream context before
        # touching the input cursor so restore remains atomic.
        if self.rng_context_id != snapshot["rng_context_id"]:
            raise ValueError("tick authority snapshot rng context mismatch")

        restored_sequence = self.input_sequence
        restored_sequence.restore_snapshot(snapshot["input_sequence_snapshot"])
        self._tick_sequence = snapshot["tick_sequence"]
        self._last_input_sequence = snapshot["last_input_sequence"]
        self._current = copy.deepcopy(snapshot["current_tick"])
        self._rng_phases = copy.deepcopy(snapshot["rng_phases"])
        current = self._current
        self._clock_consumers = (
            copy.deepcopy(current["clock_consumers"])
            if isinstance(current, Mapping)
            and isinstance(current.get("clock_consumers"), list)
            else []
        )
        self._last_receipt = copy.deepcopy(snapshot["last_receipt"])

    @staticmethod
    def validate_tick_context(context: object) -> dict[str, Any]:
        """Validate a sealed tick context without touching live authority state."""
        errors: list[str] = []
        if not isinstance(context, Mapping):
            return {"valid": False, "errors": ["context_not_mapping"]}
        try:
            keys = set(context)
        except Exception:
            return {"valid": False, "errors": ["context_keys_invalid"]}
        legacy_shape = keys == _CONTEXT_KEYS
        clock_shape = keys == (_CONTEXT_KEYS | _CLOCK_CONTEXT_KEYS)
        if not legacy_shape and not clock_shape:
            errors.append("context_keys_mismatch")
        if context.get("schema_version") != SCHEMA_VERSION:
            errors.append("context_version_mismatch")
        if context.get("status") != CONTEXT_STATUS:
            errors.append("context_status_mismatch")
        tick_sequence = context.get("tick_sequence")
        if isinstance(tick_sequence, bool) or not isinstance(tick_sequence, int) or tick_sequence < 1:
            errors.append("context_tick_sequence_invalid")
        delta = context.get("delta_time")
        if (
            isinstance(delta, bool)
            or not isinstance(delta, (int, float))
            or not math.isfinite(float(delta))
            or float(delta) < 0.0
        ):
            errors.append("context_delta_invalid")
        paused = context.get("paused")
        if not isinstance(paused, bool):
            errors.append("context_paused_invalid")
        elif paused and float(delta or 0.0) != 0.0:
            errors.append("context_paused_delta_nonzero")
        if context.get("lifecycle_action") not in LIFECYCLE_ACTIONS:
            errors.append("context_lifecycle_action_invalid")
        epoch = context.get("pause_reset_epoch")
        if isinstance(epoch, bool) or not isinstance(epoch, int) or epoch < 0:
            errors.append("context_pause_reset_epoch_invalid")
        clock_domain = context.get("clock_domain")
        if not isinstance(clock_domain, str) or _TOKEN_RE.fullmatch(clock_domain) is None:
            errors.append("context_clock_domain_invalid")
        source = context.get("source")
        if not isinstance(source, str) or _TOKEN_RE.fullmatch(source) is None:
            errors.append("context_source_invalid")
        events = context.get("input_events")
        if not isinstance(events, list):
            errors.append("context_input_events_invalid")
        else:
            first_sequence = (
                int(events[0]["sequence"]) - 1
                if events and isinstance(events[0], Mapping) and isinstance(events[0].get("sequence"), int)
                else 0
            )
            batch = validate_worldbridge_input_events(
                events,
                last_sequence=first_sequence,
                pause_reset_epoch=epoch if isinstance(epoch, int) else 0,
            )
            if not batch["valid"]:
                errors.extend(f"context_{error}" for error in batch["errors"])
        admissions = context.get("admissions")
        if not isinstance(admissions, Mapping) or set(admissions) != set(ADMISSION_KEYS):
            errors.append("context_admissions_keys_invalid")
        elif any(bool(value) for value in admissions.values()):
            errors.append("context_admissions_must_be_false")
        rng_snapshot = context.get("rng_context_snapshot")
        rng_digest = context.get("rng_snapshot_digest")
        rng_context_id = context.get("rng_context_id")
        if rng_snapshot is None:
            if rng_digest is not None or rng_context_id is not None:
                errors.append("context_rng_binding_inconsistent")
        else:
            rng_validation = validate_worldbridge_deterministic_randomness_snapshot(rng_snapshot)
            if rng_validation != {"valid": True, "errors": []}:
                errors.append("context_rng_snapshot_invalid")
            else:
                if rng_digest != rng_snapshot["snapshot_digest"]:
                    errors.append("context_rng_digest_mismatch")
                if rng_context_id != rng_snapshot["context_id"]:
                    errors.append("context_rng_context_id_mismatch")
        digest = context.get("context_digest")
        if not isinstance(digest, str) or len(digest) != 64:
            errors.append("context_digest_invalid")
        elif digest != _context_digest(context):
            errors.append("context_digest_mismatch")
        if clock_shape:
            decision = context.get("clock_decision")
            consumed = context.get("clock_consumers")
            consumed_names = (
                [row.get("consumer") for row in consumed]
                if isinstance(consumed, list)
                else []
            )
            decision_validation = validate_worldbridge_frame_clock_decision(decision)
            if decision_validation != {"valid": True, "errors": []}:
                errors.extend(
                    f"context_clock_decision_{item.removeprefix('decision_')}"
                    for item in decision_validation["errors"]
                )
            decision_digest = context.get("clock_decision_digest")
            if (
                not isinstance(decision_digest, str)
                or len(decision_digest) != 64
                or not isinstance(decision, Mapping)
                or decision_digest != decision.get("decision_digest")
            ):
                errors.append("context_clock_decision_digest_mismatch")
            if isinstance(decision, Mapping):
                if delta != decision.get("sr_delta_seconds"):
                    errors.append("context_clock_delta_mismatch")
                if paused != decision.get("paused"):
                    errors.append("context_clock_paused_mismatch")
                requested = decision.get("bridge_handoff_requested") is True
            else:
                requested = False
            errors.extend(
                _validate_clock_consumers(
                    consumed,
                    tick_sequence=tick_sequence if isinstance(tick_sequence, int) else None,
                    decision_digest=decision_digest if isinstance(decision_digest, str) else None,
                    require_sr=False,
                    require_ps=False,
                    error_prefix="context_clock_consumers",
                )
            )
            if not requested and "ps" in consumed_names:
                errors.append("context_clock_consumers_ps_without_handoff")
        return {"valid": not errors, "errors": errors}


def validate_worldbridge_tick_authority_snapshot(snapshot: object) -> dict[str, Any]:
    """Validate a full tick-authority cursor snapshot without restoring it."""
    errors: list[str] = []
    if not isinstance(snapshot, Mapping):
        return {"valid": False, "errors": ["snapshot_not_mapping"]}
    try:
        if set(snapshot) != _SNAPSHOT_KEYS:
            errors.append("snapshot_keys_mismatch")
    except Exception:
        return {"valid": False, "errors": ["snapshot_keys_invalid"]}
    if snapshot.get("schema_version") != SCHEMA_VERSION or snapshot.get("status") != STATUS:
        errors.append("snapshot_version_mismatch")
    tick_sequence = snapshot.get("tick_sequence")
    tick_sequence_valid = (
        not isinstance(tick_sequence, bool)
        and isinstance(tick_sequence, int)
        and tick_sequence >= 0
    )
    if not tick_sequence_valid:
        errors.append("snapshot_tick_sequence_invalid")
    last_input_sequence = snapshot.get("last_input_sequence")
    last_input_valid = (
        not isinstance(last_input_sequence, bool)
        and isinstance(last_input_sequence, int)
        and last_input_sequence >= 0
    )
    if not last_input_valid:
        errors.append("snapshot_last_input_sequence_invalid")
    sequence_snapshot: Mapping[str, Any] | None = None
    try:
        WorldBridgeInputSequence.validate_snapshot(snapshot.get("input_sequence_snapshot"))
    except Exception:
        errors.append("snapshot_input_sequence_invalid")
    else:
        candidate_sequence = snapshot["input_sequence_snapshot"]
        if isinstance(candidate_sequence, Mapping):
            sequence_snapshot = candidate_sequence
            epoch = sequence_snapshot["pause_reset_epoch"]
            if snapshot.get("pause_reset_epoch") != epoch:
                errors.append("snapshot_pause_reset_epoch_mismatch")
            if (
                last_input_valid
                and last_input_sequence > sequence_snapshot["next_sequence"] - 1
            ):
                errors.append("snapshot_last_input_sequence_ahead_of_cursor")
    current = snapshot.get("current_tick")
    if current is not None:
        context_validation = WorldBridgeTickAuthority.validate_tick_context(current)
        if not context_validation["valid"]:
            errors.extend(f"snapshot_{error}" for error in context_validation["errors"])
        else:
            if current.get("tick_sequence") != tick_sequence:
                errors.append("snapshot_tick_sequence_mismatch")
            if sequence_snapshot is not None and (
                current.get("pause_reset_epoch")
                != sequence_snapshot.get("pause_reset_epoch")
            ):
                errors.append("snapshot_current_tick_pause_reset_epoch_mismatch")
    phases = snapshot.get("rng_phases")
    errors.extend(
        _validate_rng_phase_records(
            phases,
            tick_sequence=tick_sequence if tick_sequence_valid else None,
            error_prefix="snapshot_rng_phases",
        )
    )
    rng_context_id = snapshot.get("rng_context_id")
    if rng_context_id is not None and (
        not isinstance(rng_context_id, str)
        or _TOKEN_RE.fullmatch(rng_context_id) is None
    ):
        errors.append("snapshot_rng_context_id_invalid")
    last_receipt = snapshot.get("last_receipt")
    if last_receipt is not None:
        receipt_validation = validate_worldbridge_tick_receipt(last_receipt)
        if not receipt_validation["valid"]:
            errors.extend(
                f"snapshot_last_receipt_{error.removeprefix('receipt_')}"
                for error in receipt_validation["errors"]
            )
        else:
            receipt_sequence = last_receipt["tick_sequence"]
            if current is None:
                if receipt_sequence != tick_sequence:
                    errors.append("snapshot_tick_sequence_mismatch")
            elif receipt_sequence != tick_sequence - 1:
                errors.append("snapshot_active_last_receipt_sequence_mismatch")
            if last_receipt.get("rng_context_id") != rng_context_id:
                errors.append("snapshot_rng_context_id_mismatch")
            if current is None:
                receipt_phase_evidence = {
                    "count": last_receipt.get("rng_phase_count"),
                    "phases": last_receipt.get("rng_phases"),
                }
                snapshot_phase_evidence = {
                    "count": len(phases) if isinstance(phases, list) else None,
                    "phases": phases,
                }
                if receipt_phase_evidence != snapshot_phase_evidence:
                    errors.append("snapshot_last_receipt_rng_phases_mismatch")
            elif phases and (
                not isinstance(phases, list)
                or any(
                    not isinstance(phase, Mapping)
                    or phase.get("tick_sequence") != tick_sequence
                    for phase in phases
                )
            ):
                errors.append("snapshot_active_rng_phases_inconsistent")
    else:
        if tick_sequence_valid and tick_sequence > (0 if current is None else 1):
            if current is None:
                errors.append("snapshot_last_receipt_unavailable")
        if current is not None and phases:
            pass
        elif phases:
            errors.append("snapshot_rng_phases_without_active_tick")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}

__all__ = [
    "ADMISSION_KEYS",
    "CLOCK_CONSUMER_ORDER",
    "CLOCK_DOMAIN",
    "CONTEXT_STATUS",
    "RECEIPT_STATUS",
    "RNG_PHASE_ORDER",
    "SCHEMA_VERSION",
    "STATUS",
    "WorldBridgeTickAuthority",
    "validate_worldbridge_tick_authority_snapshot",
    "validate_worldbridge_tick_receipt",
]
