# -*- coding: utf-8
"""Opt-in live SR/PS checkpoint composition and compensating restore.

The coordinator owns ordering and failure compensation.  Concrete lane
adapters remain responsible for restoring their own live objects.  Nothing in
this module is attached to the default tick loop or claims replay admission.
"""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
import re
from collections import OrderedDict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from secrets import token_bytes
from threading import RLock
from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_live_checkpoint"
_CHECKPOINT_KEYS = {
    "schema_version",
    "status",
    "checkpoint_id",
    "sequence",
    "runtime_mode",
    "topology_owner_state",
    "sr_state",
    "ps_state",
    "bridge_identity_links",
    "input_state",
    "randomness_state",
    "lifecycle",
    "digest",
}
_RESTORE_ORDER = (
    "lifecycle",
    "input",
    "tick_authority",
    "randomness",
    "ps",
    "sr",
    "topology",
    "bridge",
)
_TOPOLOGY_RESTORE_PHASE = "topology"
_PROCESS_OWNER_BINDINGS: OrderedDict[str, dict[str, Any]] = OrderedDict()
_PROCESS_OWNER_CHECKPOINTS: OrderedDict[tuple[str, str], None] = OrderedDict()
_PROCESS_OWNER_BINDINGS_LOCK = RLock()
# These are ephemeral in-process capabilities, not durable checkpoint data.
# Evicted checkpoint bindings fail closed instead of growing without bound.
_MAX_PROCESS_OWNER_BINDINGS = 512
_MAX_PROCESS_OWNER_CHECKPOINTS = 4096
_PROCESS_OWNER_BINDING_KEY = token_bytes(32)
_TICK_BINDING_KEYS = {
    "tick_sequence",
    "pause_reset_epoch",
    "input_digest",
    "context_digest",
    "rng_context_id",
    "rng_start_digest",
    "rng_end_digest",
    "receipt_digest",
}
_TICK_SCOPE_KEYS = {
    "schema_version",
    "status",
    "authority_id",
    "tick_sequence",
    "pause_reset_epoch",
    "context_digest",
}
_TICK_SCOPE_STATUS = "worldbridge_active_tick_scope"
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def _checkpoint_portable_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(dict(value))
    payload["digest"] = ""
    lifecycle = payload.get("lifecycle")
    if isinstance(lifecycle, Mapping):
        portable_lifecycle = dict(lifecycle)
        portable_lifecycle.pop("process_owner_binding", None)
        # Gate hold/acquisition counters are process-local capture evidence,
        # not state restored by the checkpoint transaction.
        portable_lifecycle.pop("owner_gate_snapshot", None)
        payload["lifecycle"] = portable_lifecycle
    return payload


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _json_copy(value: Any, field: str) -> Any:
    try:
        return json.loads(_canonical(value).decode("utf-8"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be finite canonical JSON") from exc


def _digest(value: Mapping[str, Any]) -> str:
    """Digest portable checkpoint state, excluding process-local owner handles.

    The owner binding is validated against live roots during restore and is not
    portable simulation state. Excluding it keeps cross-host parity receipts
    stable without weakening the restore-time owner-drift check.
    """
    return hashlib.sha256(_canonical(_checkpoint_portable_payload(value))).hexdigest()


def _state_digest(checkpoint: Mapping[str, Any]) -> str:
    """Digest live state while ignoring checkpoint identity metadata."""
    payload = {
        key: copy.deepcopy(checkpoint[key])
        for key in _CHECKPOINT_KEYS
        if key not in {"checkpoint_id", "sequence", "digest"} and key in checkpoint
    }
    lifecycle = payload.get("lifecycle")
    if isinstance(lifecycle, Mapping):
        portable_lifecycle = dict(lifecycle)
        portable_lifecycle.pop("process_owner_binding", None)
        portable_lifecycle.pop("owner_gate_snapshot", None)
        payload["lifecycle"] = portable_lifecycle
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _register_process_owner_binding(
    checkpoint: dict[str, Any], binding: Mapping[str, Any]
) -> None:
    lifecycle = checkpoint.get("lifecycle")
    if not isinstance(lifecycle, dict):
        raise WorldBridgeOwnerBindingDrift(["checkpoint_lifecycle_invalid"])
    binding_payload = _canonical(dict(binding))
    token = hmac.new(
        _PROCESS_OWNER_BINDING_KEY, binding_payload, hashlib.sha256
    ).hexdigest()
    lifecycle["process_owner_binding"] = token
    checkpoint["digest"] = _digest(checkpoint)
    with _PROCESS_OWNER_BINDINGS_LOCK:
        record = _PROCESS_OWNER_BINDINGS.get(token)
        if record is None:
            record = {"binding": copy.deepcopy(dict(binding))}
            _PROCESS_OWNER_BINDINGS[token] = record
        elif record["binding"] != dict(binding):
            raise WorldBridgeOwnerBindingDrift(["process_owner_binding_collision"])
        _PROCESS_OWNER_BINDINGS.move_to_end(token)
        checkpoint_key = (token, checkpoint["digest"])
        _PROCESS_OWNER_CHECKPOINTS[checkpoint_key] = None
        _PROCESS_OWNER_CHECKPOINTS.move_to_end(checkpoint_key)
        while len(_PROCESS_OWNER_CHECKPOINTS) > _MAX_PROCESS_OWNER_CHECKPOINTS:
            _PROCESS_OWNER_CHECKPOINTS.popitem(last=False)
        while len(_PROCESS_OWNER_BINDINGS) > _MAX_PROCESS_OWNER_BINDINGS:
            oldest, _ = _PROCESS_OWNER_BINDINGS.popitem(last=False)
            for key in tuple(_PROCESS_OWNER_CHECKPOINTS):
                if key[0] == oldest:
                    del _PROCESS_OWNER_CHECKPOINTS[key]


def _resolve_process_owner_binding(checkpoint: Mapping[str, Any]) -> Mapping[str, Any] | None:
    lifecycle = checkpoint.get("lifecycle")
    token = lifecycle.get("process_owner_binding") if isinstance(lifecycle, Mapping) else None
    if not isinstance(token, str) or not token:
        return None
    with _PROCESS_OWNER_BINDINGS_LOCK:
        record = _PROCESS_OWNER_BINDINGS.get(token)
        checkpoint_key = (token, checkpoint.get("digest"))
        if record is None or checkpoint_key not in _PROCESS_OWNER_CHECKPOINTS:
            return None
        _PROCESS_OWNER_BINDINGS.move_to_end(token)
        _PROCESS_OWNER_CHECKPOINTS.move_to_end(checkpoint_key)
        return copy.deepcopy(record["binding"])


def _validate_cross_lane_binding(checkpoint: Mapping[str, Any]) -> None:
    """Validate that checkpoint lanes belong to one runtime/input epoch."""
    lifecycle = checkpoint["lifecycle"]
    input_state = checkpoint["input_state"]
    randomness = checkpoint.get("randomness_state")
    if not isinstance(lifecycle, Mapping) or not isinstance(input_state, Mapping):
        raise ValueError("cross-lane checkpoint binding is incomplete")
    runtime_epoch = lifecycle.get("runtime_epoch")
    if runtime_epoch is None:
        # Checkpoints produced before the cross-lane epoch contract remain
        # readable; modern checkpoints carry the complete binding below.
        return
    if not isinstance(runtime_epoch, str) or not runtime_epoch:
        raise ValueError("cross-lane runtime epoch is invalid")

    canonical = input_state.get("canonical_sequence")
    # Checkpoints created before canonical input/transport capture remain
    # readable. Once either modern cursor is present, however, the complete
    # cross-lane binding is mandatory and cannot be partially supplied.
    transport = input_state.get("shared_transport")
    if canonical is None:
        if transport is not None and (
            not isinstance(transport, Mapping)
            or transport.get("runtime_epoch") != runtime_epoch
        ):
            raise ValueError("cross-lane shared transport runtime epoch mismatch")
        # Legacy checkpoints may carry the transport envelope but predate the
        # canonical input cursor. They retain their existing compatibility
        # semantics; modern checkpoints are fully checked below.
        return
    if not isinstance(canonical, Mapping):
        raise ValueError("cross-lane canonical input cursor is missing")
    input_epoch = canonical.get("pause_reset_epoch")
    next_sequence = canonical.get("next_sequence")
    if isinstance(input_epoch, bool) or not isinstance(input_epoch, int) or input_epoch < 0:
        raise ValueError("cross-lane input epoch is invalid")
    if isinstance(next_sequence, bool) or not isinstance(next_sequence, int) or next_sequence < 1:
        raise ValueError("cross-lane input cursor is invalid")
    lifecycle_input_epoch = lifecycle.get("input_pause_reset_epoch")
    if lifecycle_input_epoch is not None and lifecycle_input_epoch != input_epoch:
        raise ValueError("cross-lane lifecycle input epoch mismatch")

    if not isinstance(transport, Mapping) or transport.get("runtime_epoch") != runtime_epoch:
        raise ValueError("cross-lane shared transport runtime epoch mismatch")
    receiver = transport.get("receiver")
    if receiver is not None:
        if not isinstance(receiver, Mapping):
            raise ValueError("cross-lane receiver cursor is invalid")
        receiver_epoch = receiver.get("last_pause_reset_epoch")
        receiver_input_epoch = receiver.get("last_input_pause_reset_epoch")
        receiver_input_sequence = receiver.get("last_input_sequence")
        if receiver_epoch is not None and receiver_epoch != input_epoch:
            raise ValueError("cross-lane receiver pause epoch mismatch")
        if receiver_input_epoch is not None and receiver_input_epoch != input_epoch:
            raise ValueError("cross-lane receiver input epoch mismatch")
        if receiver_input_sequence is not None and (
            isinstance(receiver_input_sequence, bool)
            or not isinstance(receiver_input_sequence, int)
            or receiver_input_sequence >= next_sequence
        ):
            raise ValueError("cross-lane receiver input cursor mismatch")

    if randomness is not None:
        if not isinstance(randomness, Mapping) or randomness.get("runtime_epoch") != runtime_epoch:
            raise ValueError("cross-lane randomness runtime epoch mismatch")

    ps_events = input_state.get("ps_handoff_input_events", [])
    if not isinstance(ps_events, list):
        raise ValueError("cross-lane PS input batch is invalid")
    for event in ps_events:
        if not isinstance(event, Mapping) or event.get("pause_reset_epoch") != input_epoch:
            raise ValueError("cross-lane PS input epoch mismatch")
        sequence = event.get("sequence")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence >= next_sequence:
            raise ValueError("cross-lane PS input cursor mismatch")


def _non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _required_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def build_worldbridge_live_checkpoint(
    *,
    checkpoint_id: str,
    sequence: int,
    sr_state: Mapping[str, Any],
    ps_state: Mapping[str, Any],
    bridge_identity_links: Sequence[Mapping[str, Any]],
    input_state: Mapping[str, Any],
    randomness_state: Mapping[str, Any] | None,
    lifecycle: Mapping[str, Any],
    topology_owner_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an isolated, digest-sealed checkpoint from live adapter output.

    ``topology_owner_state`` is the authoritative SR topology/membrane owner
    slice.  It is stored as a separate owner so a restore failure cannot hide
    behind the SR entity envelope.  Omitting it remains readable for legacy
    adapters that do not expose the topology owner contract.
    """
    checkpoint: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "checkpoint_id": _required_id(checkpoint_id, "checkpoint_id"),
        "sequence": _non_negative_int(sequence, "sequence"),
        "runtime_mode": "dual",
        "topology_owner_state": (
            {}
            if topology_owner_state is None
            else _json_mapping_copy(topology_owner_state, "topology_owner_state")
        ),
        "sr_state": _json_mapping_copy(sr_state, "sr_state"),
        "ps_state": _json_mapping_copy(ps_state, "ps_state"),
        "bridge_identity_links": _json_sequence_copy(bridge_identity_links, "bridge_identity_links"),
        "input_state": _json_mapping_copy(input_state, "input_state"),
        "randomness_state": None if randomness_state is None else _json_mapping_copy(randomness_state, "randomness_state"),
        "lifecycle": _json_mapping_copy(lifecycle, "lifecycle"),
        "digest": "",
    }
    checkpoint["digest"] = _digest(checkpoint)
    return copy.deepcopy(checkpoint)


def validate_worldbridge_live_checkpoint(checkpoint: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(checkpoint, Mapping):
        return {"valid": False, "errors": ["checkpoint_must_be_mapping"]}
    checkpoint_keys = set(checkpoint)
    if checkpoint_keys != _CHECKPOINT_KEYS:
        legacy_keys = _CHECKPOINT_KEYS - {"topology_owner_state"}
        if checkpoint_keys != legacy_keys:
            errors.append("checkpoint_keys_mismatch")
    if checkpoint.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if checkpoint.get("status") != STATUS:
        errors.append("status_mismatch")
    try:
        _required_id(checkpoint.get("checkpoint_id"), "checkpoint_id")
    except ValueError:
        errors.append("checkpoint_id_invalid")
    try:
        _non_negative_int(checkpoint.get("sequence"), "sequence")
    except ValueError:
        errors.append("sequence_invalid")
    if checkpoint.get("runtime_mode") != "dual":
        errors.append("runtime_mode_mismatch")
    for field in ("sr_state", "ps_state", "input_state", "lifecycle"):
        if not isinstance(checkpoint.get(field), Mapping):
            errors.append(f"{field}_invalid")
    if not isinstance(checkpoint.get("bridge_identity_links"), list):
        errors.append("bridge_identity_links_invalid")
    randomness = checkpoint.get("randomness_state")
    if randomness is not None and not isinstance(randomness, Mapping):
        errors.append("randomness_state_invalid")
    topology_owner = checkpoint.get("topology_owner_state")
    if topology_owner is not None and not isinstance(topology_owner, Mapping):
        errors.append("topology_owner_state_invalid")
    elif isinstance(topology_owner, Mapping) and topology_owner:
        sr_state = checkpoint.get("sr_state")
        envelope = sr_state.get("runtime_restore_envelope") if isinstance(sr_state, Mapping) else None
        envelope_topology = (
            envelope.get("topology") if isinstance(envelope, Mapping) else None
        )
        if envelope_topology is not None:
            try:
                owner_equal = _canonical(topology_owner) == _canonical(envelope_topology)
            except (TypeError, ValueError, OverflowError):
                owner_equal = False
            if not owner_equal:
                errors.append("topology_owner_state_envelope_mismatch")
    digest = checkpoint.get("digest")
    if not isinstance(digest, str) or digest != _digest(checkpoint):
        errors.append("digest_mismatch")
    try:
        _canonical(checkpoint)
    except (TypeError, ValueError, OverflowError):
        errors.append("checkpoint_not_canonical_json")
    return {"valid": not errors, "errors": errors}


def _validate_tick_binding_value(binding: object) -> list[str]:
    """Validate the portable, eight-field completed-tick binding."""

    if binding is None:
        return []
    if not isinstance(binding, Mapping):
        return ["tick_binding_not_mapping"]
    errors: list[str] = []
    if set(binding) != _TICK_BINDING_KEYS:
        errors.append("tick_binding_keys_mismatch")
    tick_sequence = binding.get("tick_sequence")
    if (
        isinstance(tick_sequence, bool)
        or not isinstance(tick_sequence, int)
        or tick_sequence < 1
    ):
        errors.append("tick_binding_tick_sequence_invalid")
    pause_epoch = binding.get("pause_reset_epoch")
    if (
        isinstance(pause_epoch, bool)
        or not isinstance(pause_epoch, int)
        or pause_epoch < 0
    ):
        errors.append("tick_binding_pause_reset_epoch_invalid")
    for field in ("input_digest", "context_digest", "receipt_digest"):
        value = binding.get(field)
        if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
            errors.append(f"tick_binding_{field}_invalid")
    rng_context_id = binding.get("rng_context_id")
    if rng_context_id is not None and (
        not isinstance(rng_context_id, str)
        or _TOKEN_RE.fullmatch(rng_context_id) is None
    ):
        errors.append("tick_binding_rng_context_id_invalid")
    for field in ("rng_start_digest", "rng_end_digest"):
        value = binding.get(field)
        if value is not None and (
            not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None
        ):
            errors.append(f"tick_binding_{field}_invalid")
    try:
        _canonical(binding)
    except (TypeError, ValueError, OverflowError):
        errors.append("tick_binding_not_canonical_json")
    return errors


def _validate_tick_scope_value(scope: object) -> list[str]:
    """Validate process-local active-tick evidence without claiming completion."""

    if scope is None:
        return []
    if not isinstance(scope, Mapping):
        return ["tick_scope_not_mapping"]
    errors: list[str] = []
    if set(scope) != _TICK_SCOPE_KEYS:
        errors.append("tick_scope_keys_mismatch")
    if scope.get("schema_version") != 1:
        errors.append("tick_scope_schema_version_mismatch")
    if scope.get("status") != _TICK_SCOPE_STATUS:
        errors.append("tick_scope_status_mismatch")
    authority_id = scope.get("authority_id")
    if (
        isinstance(authority_id, bool)
        or not isinstance(authority_id, int)
        or authority_id < 1
    ):
        errors.append("tick_scope_authority_id_invalid")
    tick_sequence = scope.get("tick_sequence")
    if (
        isinstance(tick_sequence, bool)
        or not isinstance(tick_sequence, int)
        or tick_sequence < 1
    ):
        errors.append("tick_scope_tick_sequence_invalid")
    pause_epoch = scope.get("pause_reset_epoch")
    if (
        isinstance(pause_epoch, bool)
        or not isinstance(pause_epoch, int)
        or pause_epoch < 0
    ):
        errors.append("tick_scope_pause_reset_epoch_invalid")
    context_digest = scope.get("context_digest")
    if (
        not isinstance(context_digest, str)
        or _DIGEST_RE.fullmatch(context_digest) is None
    ):
        errors.append("tick_scope_context_digest_invalid")
    try:
        _canonical(scope)
    except (TypeError, ValueError, OverflowError):
        errors.append("tick_scope_not_canonical_json")
    return errors


def _tick_evidence_mismatches(
    expected_binding: Mapping[str, Any] | None,
    expected_scope: Mapping[str, Any] | None,
    actual_binding: Mapping[str, Any] | None,
    actual_scope: Mapping[str, Any] | None,
) -> list[str]:
    """Return exact drift errors for completed binding and active scope."""

    errors: list[str] = []
    if expected_scope is None and expected_binding is None:
        if actual_binding is not None:
            errors.append("completed_tick_binding_appeared")
        if actual_scope is not None:
            errors.append("active_tick_scope_appeared")
        return errors
    if expected_scope is not None:
        if expected_binding is not None:
            errors.append("tick_binding_and_scope_both_present")
        if actual_scope is None:
            errors.append("active_tick_scope_unavailable")
        elif expected_scope != actual_scope:
            errors.append("active_tick_scope_mismatch")
        if actual_binding is not None:
            errors.append("completed_tick_binding_replaced_active_scope")
        return errors
    if actual_binding is None:
        errors.append("completed_tick_binding_unavailable")
    elif expected_binding != actual_binding:
        errors.append("completed_tick_binding_mismatch")
    if actual_scope is not None:
        errors.append("active_tick_scope_replaced_completed_binding")
    return errors


def _json_mapping_copy(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a mapping")
    copied = _json_copy(dict(value), field)
    if not isinstance(copied, dict):
        raise TypeError(f"{field} must be a mapping")
    return copied


def _json_sequence_copy(value: Sequence[Mapping[str, Any]], field: str) -> list[dict[str, Any]]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field} must be a sequence")
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        result.append(_json_mapping_copy(item, f"{field}[{index}]"))
    return result


@dataclass(frozen=True)
class LiveCheckpointAdapters:
    """Explicit owner functions for one live checkpoint participant set."""

    capture_sr: Callable[[], Mapping[str, Any]]
    restore_sr: Callable[[Mapping[str, Any]], None]
    capture_ps: Callable[[], Mapping[str, Any]]
    restore_ps: Callable[[Mapping[str, Any]], None]
    capture_bridge: Callable[[], Sequence[Mapping[str, Any]]]
    restore_bridge: Callable[[Sequence[Mapping[str, Any]]], None]
    capture_input: Callable[[], Mapping[str, Any]]
    restore_input: Callable[[Mapping[str, Any]], None]
    capture_randomness: Callable[[], Mapping[str, Any] | None]
    restore_randomness: Callable[[Mapping[str, Any] | None], None]
    capture_lifecycle: Callable[[], Mapping[str, Any]]
    restore_lifecycle: Callable[[Mapping[str, Any]], None]
    # The SR topology/membrane graph is its own live owner.  It is captured
    # separately from the SR entity envelope so restore and compensation can
    # address it as a distinct phase instead of a nested side effect.
    capture_topology: Callable[[], Mapping[str, Any]] | None = None
    restore_topology: Callable[[Mapping[str, Any]], None] | None = None
    # A transactional handoff may need an identity-preserving PS snapshot in
    # addition to the portable checkpoint representation above.  The hooks
    # are opt-in and deliberately absent from ordinary checkpoint restore.
    capture_live_ps: Callable[[], Any] | None = None
    restore_live_ps: Callable[[Any], None] | None = None
    # Transaction callers must capture the portable PS representation and the
    # identity-preserving live PS state at one owner-controlled boundary.
    # The first result is portable JSON state, the second is the live snapshot.
    capture_transaction_state: Callable[[], tuple[Mapping[str, Any], Any]] | None = None
    # Preferred for an identity-preserving transaction: capture every owner
    # once behind an owner-controlled boundary and return one detached
    # snapshot. When omitted, the coordinator retains its legacy composition
    # path for backward compatibility.
    capture_transaction_snapshot: (
        Callable[[], WorldBridgeTransactionCapture] | None
    ) = None
    # Handoff rollback may run while the authority still owns the current
    # tick. This callback captures identity/sequence/context evidence for that
    # active scope; it must never manufacture a completed-tick receipt.
    capture_handoff_transaction_snapshot: (
        Callable[[], WorldBridgeTransactionCapture] | None
    ) = None
    # Checkpoint-only capture may run before the first authoritative tick. This
    # callback is deliberately weaker than the strict transaction callback and
    # still rejects an active tick.
    capture_legacy_transaction_snapshot: (
        Callable[[], WorldBridgeTransactionCapture] | None
    ) = None
    # Restore paths need a cheap, owner-provided probe of the current completed
    # binding or active handoff scope. The result is a detached pair.
    capture_tick_evidence: (
        Callable[[], tuple[Mapping[str, Any] | None, Mapping[str, Any] | None]]
        | None
    ) = None
    # Compensation owners are separate from forward restore callables so a
    # post-mutation failure injection cannot replace the inverse operation.
    compensate_sr: Callable[[Mapping[str, Any]], None] | None = None
    compensate_ps: Callable[[Mapping[str, Any]], None] | None = None
    compensate_bridge: Callable[[Sequence[Mapping[str, Any]]], None] | None = None
    compensate_input: Callable[[Mapping[str, Any]], None] | None = None
    compensate_randomness: Callable[[Mapping[str, Any] | None], None] | None = None
    compensate_lifecycle: Callable[[Mapping[str, Any]], None] | None = None
    compensate_topology: Callable[[Mapping[str, Any]], None] | None = None
    # Tick authority is process-local simulation state. It is captured beside
    # the portable checkpoint, never inside it, and is restored between the
    # input cursor and randomness owners.
    capture_tick_authority: Callable[[], Mapping[str, Any] | None] | None = None
    restore_tick_authority: Callable[[Mapping[str, Any]], None] | None = None
    compensate_tick_authority: Callable[[Mapping[str, Any]], None] | None = None
    validate_tick_authority: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None
    # Process-local owner identities are included in the live checkpoint and
    # revalidated before and through restore. They are not portable replay data.
    capture_owner_binding: Callable[[], Mapping[str, Any]] | None = None
    validate_owner_binding: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None


@dataclass(frozen=True)
class WorldBridgeTransactionCapture:
    """One coherent snapshot of every checkpointed live owner.

    ``ps_state`` is the portable PS representation; ``live_ps_state`` keeps
    process-local identity where an identity-preserving restore requires it.
    A coordinator may build a checkpoint from this detached result without
    invoking any individual ``capture_*`` callback again.
    """

    sr_state: Mapping[str, Any]
    ps_state: Mapping[str, Any]
    live_ps_state: Any
    bridge_identity_links: Sequence[Mapping[str, Any]]
    input_state: Mapping[str, Any]
    randomness_state: Mapping[str, Any] | None
    lifecycle: Mapping[str, Any]
    topology_owner_state: Mapping[str, Any] | None = None
    tick_binding: Mapping[str, Any] | None = None
    tick_scope: Mapping[str, Any] | None = None
    tick_authority_state: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class WorldBridgeLiveTransactionCheckpoint:
    """Pre-mutation checkpoint for an opt-in identity-preserving handoff."""

    checkpoint: Mapping[str, Any]
    live_ps_state: Any
    live_ps_state_digest: str
    tick_binding: Mapping[str, Any] | None = None
    tick_scope: Mapping[str, Any] | None = None
    tick_authority_state: Mapping[str, Any] | None = None


class WorldBridgeOwnerBindingDrift(RuntimeError):
    """Raised when a live checkpoint operation changes owner roots."""

    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("live checkpoint owner binding drift: " + ", ".join(self.errors))


class WorldBridgeTransactionCaptureError(RuntimeError):
    """Raised when a transaction snapshot cannot prove one coherent state."""

    def __init__(self, reason: str, *, details: Mapping[str, Any] | None = None) -> None:
        if not isinstance(reason, str) or not reason:
            raise ValueError("transaction capture reason must be non-empty")
        self.reason = reason
        self.details = copy.deepcopy(dict(details or {}))
        super().__init__(f"transaction capture failed: {reason}")


class WorldBridgeTickBindingDrift(RuntimeError):
    """Raised when live tick evidence changes across a checkpoint operation."""

    def __init__(
        self,
        errors: Sequence[str],
        *,
        expected: Mapping[str, Any] | None = None,
        actual: Mapping[str, Any] | None = None,
        actual_binding: Mapping[str, Any] | None = None,
        actual_scope: Mapping[str, Any] | None = None,
    ) -> None:
        self.errors = tuple(errors)
        self.expected = copy.deepcopy(None if expected is None else dict(expected))
        self.actual = copy.deepcopy(None if actual is None else dict(actual))
        self.actual_binding = copy.deepcopy(
            None if actual_binding is None else dict(actual_binding)
        )
        self.actual_scope = copy.deepcopy(
            None if actual_scope is None else dict(actual_scope)
        )
        super().__init__("live checkpoint tick binding drift: " + ", ".join(self.errors))


class WorldBridgeLiveCheckpointError(RuntimeError):
    """A failed restore with structured phase and compensation evidence."""

    def __init__(self, phase: str, cause: BaseException, report: Mapping[str, Any]) -> None:
        self.phase = phase
        self.cause = cause
        self.report = copy.deepcopy(dict(report))
        super().__init__(f"live checkpoint restore failed in {phase}: {cause}")


class WorldBridgeLiveCheckpointCoordinator:
    """Capture and restore a live checkpoint through explicit owner adapters."""

    def __init__(self, adapters: LiveCheckpointAdapters) -> None:
        self._adapters = adapters

    def _owner_binding_errors(
        self,
        expected: Mapping[str, Any] | None,
        *,
        ignored_errors: Sequence[str] = (),
    ) -> list[str]:
        capture = self._adapters.capture_owner_binding
        validator = self._adapters.validate_owner_binding
        if capture is None and validator is None:
            return []
        if capture is None or validator is None:
            return ["owner_binding_adapter_incomplete"]
        if expected is None:
            return ["checkpoint_owner_binding_missing"]
        try:
            result = validator(expected)
        except Exception as exc:
            return [f"owner_binding_validator_failed:{type(exc).__name__}"]
        if not isinstance(result, Mapping):
            return ["owner_binding_validator_result_invalid"]
        errors = result.get("errors")
        if result.get("valid") is True and errors == []:
            return []
        if not isinstance(errors, (list, tuple)) or any(
            not isinstance(item, str) or not item for item in errors
        ):
            return ["owner_binding_validator_errors_invalid"]
        ignored = set(ignored_errors)
        return [
            error for error in dict.fromkeys(errors) if error not in ignored
        ] or ([] if errors and all(error in ignored for error in errors) else ["owner_binding_invalid"])

    def _require_owner_binding(
        self,
        expected: Mapping[str, Any] | None,
        *,
        ignored_errors: Sequence[str] = (),
    ) -> None:
        errors = self._owner_binding_errors(expected, ignored_errors=ignored_errors)
        if errors:
            raise WorldBridgeOwnerBindingDrift(errors)

    @staticmethod
    def _snapshot_is_detached(snapshot: WorldBridgeTransactionCapture) -> bool:
        """Reject malformed callbacks before they can be treated as a fence."""
        if not isinstance(snapshot, WorldBridgeTransactionCapture):
            return False
        return (
            isinstance(snapshot.sr_state, Mapping)
            and isinstance(snapshot.ps_state, Mapping)
            and isinstance(snapshot.input_state, Mapping)
            and isinstance(snapshot.lifecycle, Mapping)
            and isinstance(snapshot.bridge_identity_links, Sequence)
            and not isinstance(snapshot.bridge_identity_links, (str, bytes))
            and all(
                isinstance(item, Mapping)
                for item in snapshot.bridge_identity_links
            )
            and (
                snapshot.randomness_state is None
                or isinstance(snapshot.randomness_state, Mapping)
            )
            and (
                snapshot.topology_owner_state is None
                or isinstance(snapshot.topology_owner_state, Mapping)
            )
            and (
                snapshot.tick_binding is None
                or isinstance(snapshot.tick_binding, Mapping)
            )
            and (
                snapshot.tick_scope is None
                or isinstance(snapshot.tick_scope, Mapping)
            )
            and (
                snapshot.tick_authority_state is None
                or isinstance(snapshot.tick_authority_state, Mapping)
            )
        )

    def _build_checkpoint(
        self,
        *,
        checkpoint_id: str,
        sequence: int,
        ps_state: Mapping[str, Any],
        transaction_snapshot: WorldBridgeTransactionCapture | None = None,
    ) -> dict[str, Any]:
        a = self._adapters
        if transaction_snapshot is not None:
            if not self._snapshot_is_detached(transaction_snapshot):
                raise WorldBridgeTransactionCaptureError(
                    "transaction_capture_snapshot_invalid"
                )
            return build_worldbridge_live_checkpoint(
                checkpoint_id=checkpoint_id,
                sequence=sequence,
                sr_state=transaction_snapshot.sr_state,
                ps_state=ps_state,
                bridge_identity_links=transaction_snapshot.bridge_identity_links,
                input_state=transaction_snapshot.input_state,
                randomness_state=transaction_snapshot.randomness_state,
                lifecycle=transaction_snapshot.lifecycle,
                topology_owner_state=transaction_snapshot.topology_owner_state,
            )
        return build_worldbridge_live_checkpoint(
            checkpoint_id=checkpoint_id,
            sequence=sequence,
            sr_state=a.capture_sr(),
            ps_state=ps_state,
            bridge_identity_links=a.capture_bridge(),
            input_state=a.capture_input(),
            randomness_state=a.capture_randomness(),
            lifecycle=a.capture_lifecycle(),
            topology_owner_state=(
                a.capture_topology() if a.capture_topology is not None else None
            ),
        )

    def _capture_owner_binding(self) -> dict[str, Any] | None:
        capture = self._adapters.capture_owner_binding
        return dict(capture()) if capture is not None else None

    def _capture_owner_evidence(self) -> dict[str, str]:
        """Return detached evidence for every owner used by a transaction.

        The fallback composition path still invokes each owner adapter once at
        the authoritative capture point. These probes run before and after
        that point so callers without a combined owner callback can detect a
        moving owner window instead of accepting a mixed snapshot.
        """
        a = self._adapters
        states = {
            "sr": a.capture_sr(),
            "live_ps": a.capture_live_ps() if a.capture_live_ps is not None else None,
            "bridge": a.capture_bridge(),
            "input": a.capture_input(),
            "randomness": a.capture_randomness(),
            "lifecycle": a.capture_lifecycle(),
            "topology": a.capture_topology() if a.capture_topology is not None else None,
            "tick_authority": (
                a.capture_tick_authority()
                if a.capture_tick_authority is not None
                else None
            ),
        }
        evidence: dict[str, str] = {}
        for owner, state in states.items():
            if owner == "live_ps" and state is not None:
                evidence[owner] = _live_state_digest(state)
            else:
                evidence[owner] = hashlib.sha256(_canonical(state)).hexdigest()
        return evidence

    def _capture_transaction_snapshot(
        self,
        *,
        handoff_scope: bool = False,
    ) -> tuple[WorldBridgeTransactionCapture, Mapping[str, Any] | None]:
        """Capture all owners through the strongest available transaction fence.

        ``handoff_scope`` opts into active-tick evidence without relaxing the
        ordinary completed-tick transaction path.
        """
        a = self._adapters
        owner_binding_before = self._capture_owner_binding()
        capture_snapshot = (
            a.capture_handoff_transaction_snapshot
            if handoff_scope
            else a.capture_transaction_snapshot
        )
        if capture_snapshot is not None:
            try:
                result = capture_snapshot()
            except WorldBridgeTransactionCaptureError:
                # A combined callback may report PS drift before the
                # coordinator observes owner replacement.  Root drift is the
                # stronger failure and must remain visible.
                if owner_binding_before is not None:
                    self._require_owner_binding(owner_binding_before)
                raise
            if not self._snapshot_is_detached(result):
                raise WorldBridgeTransactionCaptureError(
                    "transaction_capture_snapshot_invalid"
                )
            snapshot = result
        else:
            if a.capture_live_ps is None or a.restore_live_ps is None:
                raise RuntimeError(
                    "transactional live PS capture/restore owners are unavailable"
                )
            before_evidence = self._capture_owner_evidence()
            tick_authority_before = (
                a.capture_tick_authority()
                if a.capture_tick_authority is not None
                else None
            )
            if tick_authority_before is not None and not isinstance(
                tick_authority_before, Mapping
            ):
                raise WorldBridgeTransactionCaptureError(
                    "transaction_tick_authority_snapshot_invalid"
                )
            if a.capture_transaction_state is not None:
                result = a.capture_transaction_state()
                if (
                    not isinstance(result, tuple)
                    or len(result) != 2
                    or not isinstance(result[0], Mapping)
                ):
                    raise WorldBridgeTransactionCaptureError(
                        "transaction_capture_result_invalid"
                    )
                portable_ps_state, live_ps_state = result
            else:
                portable_ps_state = a.capture_ps()
                live_ps_state = a.capture_live_ps()
            snapshot = WorldBridgeTransactionCapture(
                sr_state=a.capture_sr(),
                ps_state=portable_ps_state,
                live_ps_state=live_ps_state,
                bridge_identity_links=a.capture_bridge(),
                input_state=a.capture_input(),
                randomness_state=a.capture_randomness(),
                lifecycle=a.capture_lifecycle(),
                topology_owner_state=(
                    a.capture_topology() if a.capture_topology is not None else None
                ),
                tick_authority_state=(
                    copy.deepcopy(dict(tick_authority_before))
                    if tick_authority_before is not None
                    else None
                ),
            )
            after_evidence = self._capture_owner_evidence()
            if owner_binding_before is not None:
                self._require_owner_binding(owner_binding_before)
            changed_owners = [
                owner
                for owner in before_evidence
                if before_evidence[owner] != after_evidence[owner]
            ]
            if changed_owners:
                raise WorldBridgeTransactionCaptureError(
                    (
                        "live_ps_changed_during_capture"
                        if changed_owners == ["live_ps"]
                        else "transaction_owner_changed_during_capture"
                    ),
                    details={
                        "owners": changed_owners,
                        "before": before_evidence,
                        "after": after_evidence,
                    },
                )
        if owner_binding_before is not None:
            self._require_owner_binding(owner_binding_before)
        _live_state_digest(snapshot.live_ps_state)
        return snapshot, owner_binding_before

    def _capture_current_tick_evidence(
        self,
    ) -> tuple[Mapping[str, Any] | None, Mapping[str, Any] | None]:
        """Return detached evidence for the current live tick scope."""

        callback = self._adapters.capture_tick_evidence
        if callback is None:
            return None, None
        result = callback()
        if (
            not isinstance(result, tuple)
            or len(result) != 2
            or (result[0] is not None and not isinstance(result[0], Mapping))
            or (result[1] is not None and not isinstance(result[1], Mapping))
        ):
            raise WorldBridgeTickBindingDrift(["tick_evidence_callback_invalid"])
        binding = None if result[0] is None else copy.deepcopy(dict(result[0]))
        scope = None if result[1] is None else copy.deepcopy(dict(result[1]))
        errors = _validate_tick_binding_value(binding)
        errors.extend(_validate_tick_scope_value(scope))
        if errors:
            raise WorldBridgeTickBindingDrift(
                errors,
                expected=binding or scope,
                actual=scope or binding,
                actual_binding=binding,
                actual_scope=scope,
            )
        return binding, scope

    def _require_tick_evidence(
        self,
        expected_binding: Mapping[str, Any] | None,
        expected_scope: Mapping[str, Any] | None,
    ) -> tuple[Mapping[str, Any] | None, Mapping[str, Any] | None]:
        """Return detached evidence or fail when either tick owner drifts."""

        try:
            actual_binding, actual_scope = self._capture_current_tick_evidence()
        except Exception as exc:
            raise WorldBridgeTickBindingDrift(
                [f"tick_evidence_capture_failed:{type(exc).__name__}"],
                expected=expected_binding or expected_scope,
                actual=None,
            ) from exc
        errors = _tick_evidence_mismatches(
            expected_binding,
            expected_scope,
            actual_binding,
            actual_scope,
        )
        if errors:
            raise WorldBridgeTickBindingDrift(
                errors,
                expected=expected_binding or expected_scope,
                actual=actual_binding or actual_scope,
                actual_binding=actual_binding,
                actual_scope=actual_scope,
            )
        return actual_binding, actual_scope

    def _capture_transaction_state(self) -> tuple[Mapping[str, Any], Any, Any]:
        """Legacy tuple view of one coherent transaction capture."""
        snapshot, owner_binding = self._capture_transaction_snapshot()
        return snapshot.ps_state, snapshot.live_ps_state, owner_binding

    def capture(self, *, checkpoint_id: str, sequence: int) -> dict[str, Any]:
        a = self._adapters
        owner_binding = self._capture_owner_binding()
        checkpoint = self._build_checkpoint(
            checkpoint_id=checkpoint_id,
            sequence=sequence,
            ps_state=a.capture_ps(),
        )
        if owner_binding is not None:
            self._require_owner_binding(owner_binding)
            _register_process_owner_binding(checkpoint, owner_binding)
        return checkpoint

    def capture_legacy_transaction(
        self,
        *,
        checkpoint_id: str,
        sequence: int,
    ) -> WorldBridgeLiveTransactionCheckpoint:
        """Capture checkpoint-only state when no completed tick exists yet."""

        callback = self._adapters.capture_legacy_transaction_snapshot
        if callback is None:
            raise RuntimeError("legacy transaction capture owner is unavailable")
        owner_binding_before = self._capture_owner_binding()
        result = callback()
        if not self._snapshot_is_detached(result):
            raise WorldBridgeTransactionCaptureError(
                "transaction_capture_snapshot_invalid"
            )
        snapshot = result
        if owner_binding_before is not None:
            self._require_owner_binding(owner_binding_before)
        _live_state_digest(snapshot.live_ps_state)
        checkpoint = self._build_checkpoint(
            checkpoint_id=checkpoint_id,
            sequence=sequence,
            ps_state=snapshot.ps_state,
            transaction_snapshot=snapshot,
        )
        if owner_binding_before is not None:
            _register_process_owner_binding(checkpoint, owner_binding_before)
        return WorldBridgeLiveTransactionCheckpoint(
            checkpoint=checkpoint,
            live_ps_state=snapshot.live_ps_state,
            live_ps_state_digest=_live_state_digest(snapshot.live_ps_state),
            tick_binding=copy.deepcopy(snapshot.tick_binding),
            tick_scope=copy.deepcopy(snapshot.tick_scope),
            tick_authority_state=copy.deepcopy(snapshot.tick_authority_state),
        )

    def capture_transaction(
        self,
        *,
        checkpoint_id: str,
        sequence: int,
        handoff_scope: bool = False,
    ) -> WorldBridgeLiveTransactionCheckpoint:
        """Capture every checkpoint owner behind one transaction boundary.

        Handoff callers may request active-tick scope evidence. Ordinary
        checkpoint callers keep the strict completed-receipt requirement.
        """
        snapshot, owner_binding = self._capture_transaction_snapshot(
            handoff_scope=handoff_scope
        )
        checkpoint = self._build_checkpoint(
            checkpoint_id=checkpoint_id,
            sequence=sequence,
            ps_state=snapshot.ps_state,
            transaction_snapshot=snapshot,
        )
        if owner_binding is not None:
            self._require_owner_binding(owner_binding)
            _register_process_owner_binding(checkpoint, owner_binding)
        live_ps_state_digest = _live_state_digest(snapshot.live_ps_state)
        return WorldBridgeLiveTransactionCheckpoint(
            checkpoint=checkpoint,
            live_ps_state=snapshot.live_ps_state,
            live_ps_state_digest=live_ps_state_digest,
            tick_binding=copy.deepcopy(snapshot.tick_binding),
            tick_scope=copy.deepcopy(snapshot.tick_scope),
            tick_authority_state=copy.deepcopy(snapshot.tick_authority_state),
        )

    def restore(
        self,
        checkpoint: Mapping[str, Any],
        *,
        live_ps_state: Any = None,
        transactional_ps: bool = False,
        tick_binding: Mapping[str, Any] | None = None,
        tick_scope: Mapping[str, Any] | None = None,
        tick_authority_state: Mapping[str, Any] | None = None,
        allow_active_tick: bool = False,
    ) -> dict[str, Any]:
        validation = validate_worldbridge_live_checkpoint(checkpoint)
        if not isinstance(allow_active_tick, bool):
            raise TypeError("allow_active_tick must be bool")
        expected_tick_binding = (
            None if tick_binding is None else copy.deepcopy(dict(tick_binding))
        )
        expected_tick_scope = (
            None if tick_scope is None else copy.deepcopy(dict(tick_scope))
        )
        tick_errors = _validate_tick_binding_value(expected_tick_binding)
        tick_errors.extend(_validate_tick_scope_value(expected_tick_scope))
        if expected_tick_binding is not None and expected_tick_scope is not None:
            tick_errors.append("tick_binding_and_scope_both_present")
        if expected_tick_scope is not None and not allow_active_tick:
            tick_errors.append("active_tick_restore_requires_opt_in")
        if expected_tick_scope is None and allow_active_tick:
            tick_errors.append("active_tick_opt_in_without_scope")
        if tick_errors:
            raise WorldBridgeTickBindingDrift(
                list(dict.fromkeys(tick_errors)),
                expected=expected_tick_binding or expected_tick_scope,
                actual=None,
            )
        if not validation["valid"]:
            raise ValueError("invalid live checkpoint: " + ", ".join(validation["errors"]))
        candidate = copy.deepcopy(dict(checkpoint))
        _validate_cross_lane_binding(candidate)
        # Reject owner replacement since checkpoint capture before capturing
        # compensation state or invoking a restore adapter.
        owner_binding_required = self._adapters.capture_owner_binding is not None
        checkpoint_owner_binding = _resolve_process_owner_binding(candidate)
        if owner_binding_required and not isinstance(checkpoint_owner_binding, Mapping):
            raise WorldBridgeOwnerBindingDrift(
                ["checkpoint_process_owner_binding_unavailable_or_mismatched"]
            )
        if owner_binding_required:
            # Runtime epoch/scene validity belongs to the lifecycle owner,
            # which emits the established project-binding diagnostic before
            # changing state. Root-object drift remains a coordinator gate.
            self._require_owner_binding(
                checkpoint_owner_binding,
                ignored_errors=("runtime_epoch_changed",),
            )
        if transactional_ps and (
            self._adapters.capture_live_ps is None
            or self._adapters.restore_live_ps is None
        ):
            raise RuntimeError(
                "transactional live PS capture/restore owners are unavailable"
            )
        if transactional_ps:
            _live_state_digest(live_ps_state)
        if tick_authority_state is not None and not isinstance(
            tick_authority_state, Mapping
        ):
            raise TypeError("tick_authority_state must be a mapping or None")
        expected_tick_authority = (
            None
            if tick_authority_state is None
            else copy.deepcopy(dict(tick_authority_state))
        )
        authority_requested = expected_tick_authority is not None
        if authority_requested and (
            self._adapters.restore_tick_authority is None
            or self._adapters.validate_tick_authority is None
        ):
            raise RuntimeError("tick authority restore adapters are unavailable")
        tick_authority_validated = False
        tick_authority_stable = False
        tick_authority_errors: list[str] = []
        actual_tick_authority: Mapping[str, Any] | None = None

        def validate_authority(snapshot: Mapping[str, Any]) -> None:
            nonlocal tick_authority_validated
            nonlocal tick_authority_errors
            nonlocal actual_tick_authority
            try:
                result = self._adapters.validate_tick_authority(snapshot)
            except Exception as exc:
                tick_authority_validated = True
                tick_authority_errors = [
                    f"tick_authority_validation_failed:{type(exc).__name__}"
                ]
                actual_tick_authority = None
                raise
            if not isinstance(result, Mapping):
                tick_authority_validated = True
                tick_authority_errors = ["tick_authority_validator_result_invalid"]
                actual_tick_authority = None
                raise RuntimeError("tick authority validator returned invalid result")
            errors = result.get("errors")
            tick_authority_validated = True
            if result.get("valid") is True and errors == []:
                tick_authority_errors = []
            elif isinstance(errors, (list, tuple)) and all(
                isinstance(item, str) and item for item in errors
            ):
                tick_authority_errors = list(dict.fromkeys(errors))
            else:
                tick_authority_errors = ["tick_authority_validator_errors_invalid"]
            actual_tick_authority = copy.deepcopy(snapshot)
            if tick_authority_errors:
                raise ValueError(
                    "invalid tick authority snapshot: "
                    + ",".join(tick_authority_errors)
                )

        if expected_tick_authority is not None:
            validate_authority(expected_tick_authority)
        tick_binding_validated = False
        tick_binding_stable = False
        tick_binding_errors: list[str] = []
        actual_tick_binding: Mapping[str, Any] | None = None
        actual_tick_scope: Mapping[str, Any] | None = None

        def refresh_tick_evidence() -> None:
            nonlocal tick_binding_validated
            nonlocal tick_binding_errors
            nonlocal actual_tick_binding
            nonlocal actual_tick_scope
            try:
                actual_binding, actual_scope = self._require_tick_evidence(
                    expected_tick_binding,
                    expected_tick_scope,
                )
            except WorldBridgeTickBindingDrift as exc:
                tick_binding_validated = True
                tick_binding_errors = list(dict.fromkeys(exc.errors))
                actual_tick_binding = copy.deepcopy(exc.actual_binding)
                actual_tick_scope = copy.deepcopy(exc.actual_scope)
                raise
            tick_binding_validated = True
            tick_binding_errors = []
            actual_tick_binding = copy.deepcopy(actual_binding)
            actual_tick_scope = copy.deepcopy(actual_scope)

        # A checkpoint-only restore has no prior evidence, but it still must
        # reject a live active tick instead of mutating an in-flight authority.
        # Completed bindings appearing in that mode are also drift: the
        # checkpoint was not captured with tick evidence to rewind.
        refresh_tick_evidence()
        rollback_tick_binding = expected_tick_binding
        rollback_tick_scope = expected_tick_scope
        rollback_tick_authority: Mapping[str, Any] | None = None
        if authority_requested and self._adapters.capture_tick_authority is not None:
            captured_authority = self._adapters.capture_tick_authority()
            if not isinstance(captured_authority, Mapping):
                raise RuntimeError(
                    "tick authority capture returned no snapshot during restore"
                )
            rollback_tick_authority = copy.deepcopy(dict(captured_authority))
            validate_authority(rollback_tick_authority)
        if transactional_ps:
            rollback_snapshot, rollback_owner_binding = (
                self._capture_transaction_snapshot(
                    handoff_scope=expected_tick_scope is not None
                )
            )
            rollback = self._build_checkpoint(
                checkpoint_id=f"rollback:{candidate['checkpoint_id']}",
                sequence=candidate["sequence"],
                ps_state=rollback_snapshot.ps_state,
                transaction_snapshot=rollback_snapshot,
            )
            if rollback_owner_binding is not None:
                self._require_owner_binding(rollback_owner_binding)
                _register_process_owner_binding(rollback, rollback_owner_binding)
            _live_state_digest(rollback_snapshot.live_ps_state)
            rollback_live_ps_state = rollback_snapshot.live_ps_state
        else:
            rollback = self.capture(
                checkpoint_id=f"rollback:{candidate['checkpoint_id']}",
                sequence=candidate["sequence"],
            )
            rollback_live_ps_state = None
        topology_owner_state = candidate.get("topology_owner_state")
        topology_owner_present = isinstance(topology_owner_state, Mapping) and bool(
            topology_owner_state
        )
        if topology_owner_present and (
            self._adapters.restore_topology is None
            or self._adapters.capture_topology is None
        ):
            raise RuntimeError(
                "checkpoint topology owner is present but restore adapters are unavailable"
            )
        states: dict[str, Any] = {
            "lifecycle": candidate["lifecycle"],
            "input": candidate["input_state"],
            **({"tick_authority": expected_tick_authority} if authority_requested else {}),
            "randomness": candidate["randomness_state"],
            "ps": live_ps_state if transactional_ps else candidate["ps_state"],
            "sr": candidate["sr_state"],
            **({"topology": topology_owner_state} if topology_owner_present else {}),
            "bridge": candidate["bridge_identity_links"],
        }
        rollback_states: dict[str, Any] = {
            "lifecycle": rollback["lifecycle"],
            "input": rollback["input_state"],
            **({"tick_authority": rollback_tick_authority} if authority_requested else {}),
            "randomness": rollback["randomness_state"],
            "ps": (
                rollback_live_ps_state
                if transactional_ps
                else rollback["ps_state"]
            ),
            "sr": rollback["sr_state"],
            **(
                {"topology": rollback["topology_owner_state"]}
                if topology_owner_present
                else {}
            ),
            "bridge": rollback["bridge_identity_links"],
        }
        apply = {
            "lifecycle": self._adapters.restore_lifecycle,
            "input": self._adapters.restore_input,
            **(
                {"tick_authority": self._adapters.restore_tick_authority}
                if authority_requested
                else {}
            ),
            "randomness": self._adapters.restore_randomness,
            "ps": (
                self._adapters.restore_live_ps
                if transactional_ps
                else self._adapters.restore_ps
            ),
            "sr": self._adapters.restore_sr,
            **(
                {"topology": self._adapters.restore_topology}
                if topology_owner_present
                else {}
            ),
            "bridge": self._adapters.restore_bridge,
        }
        compensate = {
            "lifecycle": self._adapters.compensate_lifecycle or self._adapters.restore_lifecycle,
            "input": self._adapters.compensate_input or self._adapters.restore_input,
            **(
                {
                    "tick_authority": self._adapters.compensate_tick_authority
                    or self._adapters.restore_tick_authority
                }
                if authority_requested
                else {}
            ),
            "randomness": self._adapters.compensate_randomness or self._adapters.restore_randomness,
            "ps": (
                self._adapters.restore_live_ps
                if transactional_ps
                else self._adapters.compensate_ps or self._adapters.restore_ps
            ),
            "sr": self._adapters.compensate_sr or self._adapters.restore_sr,
            **(
                {
                    "topology": self._adapters.compensate_topology
                    or self._adapters.restore_topology
                }
                if topology_owner_present
                else {}
            ),
            "bridge": self._adapters.compensate_bridge or self._adapters.restore_bridge,
        }
        restore_order = tuple(
            phase
            for phase in _RESTORE_ORDER
            if (phase != _TOPOLOGY_RESTORE_PHASE or topology_owner_present)
            and (phase != "tick_authority" or authority_requested)
        )
        applied: list[str] = []
        current_phase = restore_order[0]
        target_state_digest: str | None = None
        target_live_ps_state_digest: str | None = None
        try:
            for phase in restore_order:
                self._require_owner_binding(
                    checkpoint_owner_binding,
                    ignored_errors=("runtime_epoch_changed",),
                )
                refresh_tick_evidence()
                # An adapter may mutate its owner and then fail while
                # finalizing validation. Record the phase before invocation so
                # compensation also covers that partially-applied phase.
                current_phase = phase
                applied.append(phase)
                apply[phase](states[phase])
                if phase == "tick_authority":
                    validate_authority(states[phase])
                self._require_owner_binding(
                    checkpoint_owner_binding,
                    ignored_errors=("runtime_epoch_changed",),
                )
                refresh_tick_evidence()
            refresh_tick_evidence()
            if transactional_ps:
                fresh_snapshot, fresh_owner_binding = (
                    self._capture_transaction_snapshot(
                        handoff_scope=expected_tick_scope is not None
                    )
                )
                fresh = self._build_checkpoint(
                    checkpoint_id=f"transaction-verified:{candidate['checkpoint_id']}",
                    sequence=candidate["sequence"],
                    ps_state=fresh_snapshot.ps_state,
                    transaction_snapshot=fresh_snapshot,
                )
                if fresh_owner_binding is not None:
                    self._require_owner_binding(fresh_owner_binding)
                target_state_digest = _state_digest(fresh)
                target_live_ps_state_digest = _live_state_digest(
                    fresh_snapshot.live_ps_state
                )
                if target_state_digest != _state_digest(candidate):
                    raise RuntimeError("transaction restore target state digest mismatch")
                if target_live_ps_state_digest != _live_state_digest(live_ps_state):
                    raise RuntimeError("transaction restore target live PS digest mismatch")
                refresh_tick_evidence()
            tick_binding_stable = tick_binding_validated and not tick_binding_errors
            if authority_requested:
                final_authority = (
                    self._adapters.capture_tick_authority()
                    if self._adapters.capture_tick_authority is not None
                    else None
                )
                if not isinstance(final_authority, Mapping):
                    raise RuntimeError(
                        "tick authority capture returned no snapshot after restore"
                    )
                validate_authority(final_authority)
                actual_tick_authority = copy.deepcopy(final_authority)
                if _canonical(final_authority) != _canonical(expected_tick_authority):
                    tick_authority_errors = ["tick_authority_snapshot_mismatch"]
            tick_authority_stable = (
                not authority_requested
                or (
                    tick_authority_validated
                    and not tick_authority_errors
                    and actual_tick_authority == expected_tick_authority
                )
            )
            if authority_requested and not tick_authority_stable:
                raise RuntimeError(
                    "tick authority snapshot mismatch after restore: "
                    + ",".join(tick_authority_errors)
                )
        except Exception as exc:
            compensated: list[str] = []
            compensation_errors: dict[str, str] = {}
            owner_binding_errors = self._owner_binding_errors(
                checkpoint_owner_binding,
                ignored_errors=("runtime_epoch_changed",),
            )
            if owner_binding_errors:
                # Once a root owner changes, adapters may resolve through the
                # replacement object. Do not attempt compensation against an
                # owner set different from the one captured at operation start.
                compensation_errors["owner_binding"] = ", ".join(owner_binding_errors)
            else:
                for phase in reversed(applied):
                    drift_errors = self._owner_binding_errors(
                        checkpoint_owner_binding,
                        ignored_errors=("runtime_epoch_changed",),
                    )
                    if drift_errors:
                        owner_binding_errors = drift_errors
                        compensation_errors["owner_binding"] = ", ".join(drift_errors)
                        break
                    try:
                        refresh_tick_evidence()
                    except WorldBridgeTickBindingDrift:
                        compensation_errors["tick_binding"] = ", ".join(
                            tick_binding_errors
                        )
                    try:
                        compensate[phase](rollback_states[phase])
                        if phase == "tick_authority":
                            validate_authority(rollback_states[phase])
                        compensated.append(phase)
                    except Exception as rollback_exc:
                        compensation_errors[phase] = f"{type(rollback_exc).__name__}: {rollback_exc}"
                    try:
                        refresh_tick_evidence()
                    except WorldBridgeTickBindingDrift:
                        compensation_errors["tick_binding"] = ", ".join(
                            tick_binding_errors
                        )
                    drift_errors = self._owner_binding_errors(
                        checkpoint_owner_binding,
                        ignored_errors=("runtime_epoch_changed",),
                    )
                    if drift_errors:
                        owner_binding_errors = drift_errors
                        compensation_errors["owner_binding"] = ", ".join(drift_errors)
                        break
            rollback_verification_error: str | None = None
            rollback_state_digest: str | None = None
            rollback_live_state_digest: str | None = None
            try:
                # A compensator returning normally is not proof that its owner
                # actually returned to the pre-restore state. Re-capture every
                # owner and compare the detached state, excluding checkpoint
                # identity metadata which is intentionally regenerated.
                if transactional_ps:
                    rollback_verified_snapshot, rollback_owner_binding = (
                        self._capture_transaction_snapshot(
                            handoff_scope=rollback_tick_scope is not None
                        )
                    )
                    rollback_state = self._build_checkpoint(
                        checkpoint_id=(
                            f"rollback-verified:{candidate['checkpoint_id']}"
                        ),
                        sequence=candidate["sequence"],
                        ps_state=rollback_verified_snapshot.ps_state,
                        transaction_snapshot=rollback_verified_snapshot,
                    )
                    if rollback_owner_binding is not None:
                        self._require_owner_binding(rollback_owner_binding)
                    rollback_live_state_digest = _live_state_digest(
                        rollback_verified_snapshot.live_ps_state
                    )
                else:
                    rollback_state = self.capture(
                        checkpoint_id=(
                            f"rollback-verified:{candidate['checkpoint_id']}"
                        ),
                        sequence=candidate["sequence"],
                    )
                refresh_tick_evidence()
                if authority_requested:
                    final_authority = (
                        self._adapters.capture_tick_authority()
                        if self._adapters.capture_tick_authority is not None
                        else None
                    )
                    if not isinstance(final_authority, Mapping):
                        raise RuntimeError(
                            "tick authority capture returned no snapshot after rollback"
                        )
                    validate_authority(final_authority)
                    if _canonical(final_authority) != _canonical(rollback_tick_authority):
                        rollback_verification_error = (
                            "rollback tick authority snapshot mismatch"
                        )
                rollback_state_digest = _state_digest(rollback_state)
                if rollback_state_digest != _state_digest(rollback):
                    rollback_verification_error = "rollback state digest mismatch"
                if transactional_ps:
                    expected_live_digest = _live_state_digest(rollback_live_ps_state)
                    if rollback_live_state_digest != expected_live_digest:
                        rollback_verification_error = (
                            "rollback live PS state digest mismatch"
                        )
            except WorldBridgeTickBindingDrift:
                compensation_errors["tick_binding"] = ", ".join(
                    tick_binding_errors
                )
                rollback_verification_error = "tick binding drift after rollback"
            except Exception as verification_exc:
                rollback_verification_error = (
                    f"{type(verification_exc).__name__}: {verification_exc}"
                )
            if rollback_verification_error:
                compensation_errors["rollback_verification"] = rollback_verification_error
            if not tick_binding_errors:
                compensation_errors.pop("tick_binding", None)
            tick_binding_stable = tick_binding_validated and not tick_binding_errors
            tick_authority_stable = (
                not authority_requested
                or (
                    tick_authority_validated
                    and not tick_authority_errors
                    and rollback_tick_authority is not None
                    and actual_tick_authority == rollback_tick_authority
                )
            )
            report = {
                "schema_version": SCHEMA_VERSION,
                "status": STATUS,
                "phase": current_phase,
                "applied_phases": applied,
                "compensated_phases": compensated,
                "compensation_complete": (
                    not compensation_errors
                    and tick_binding_stable
                    and tick_authority_stable
                    and compensated == list(reversed(applied))
                    and rollback_state_digest == _state_digest(rollback)
                    and (
                        not transactional_ps
                        or rollback_live_state_digest
                        == _live_state_digest(rollback_live_ps_state)
                    )
                ),
                "compensation_errors": compensation_errors,
                "tick_authority_validated": tick_authority_validated,
                "tick_authority_stable": tick_authority_stable,
                "tick_authority_errors": tick_authority_errors,
                "owner_binding_validated": owner_binding_required,
                "owner_binding_errors": owner_binding_errors,
                "tick_binding_validated": tick_binding_validated,
                "tick_binding_stable": tick_binding_stable,
                "tick_binding_errors": tick_binding_errors,
                "expected_tick_binding": copy.deepcopy(expected_tick_binding),
                "actual_tick_binding": copy.deepcopy(actual_tick_binding),
                "expected_tick_scope": copy.deepcopy(expected_tick_scope),
                "actual_tick_scope": copy.deepcopy(actual_tick_scope),
                "rollback_state_digest": rollback_state_digest,
                "rollback_live_ps_state_digest": rollback_live_state_digest,
                "transactional_ps": transactional_ps,
                "target_state_digest": target_state_digest,
                "target_live_ps_state_digest": target_live_ps_state_digest,
                "rollback_performed": bool(applied),
                "atomic_checkpoint": False,
                "replay_admitted": False,
                "default_ready": False,
            }
            raise WorldBridgeLiveCheckpointError(report["phase"], exc, report) from exc
        result = {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS,
            "checkpoint_id": candidate["checkpoint_id"],
            "checkpoint_digest": candidate.get("digest"),
            "restored": True,
            "restore_order": list(restore_order),
            "rollback_performed": False,
            "owner_binding_validated": owner_binding_required,
            "owner_binding_errors": [],
            "tick_authority_validated": tick_authority_validated,
            "tick_authority_stable": tick_authority_stable,
            "tick_authority_errors": tick_authority_errors,
            "atomic_checkpoint": False,
            "replay_admitted": False,
            "default_ready": False,
            "transactional_ps": transactional_ps,
            "transaction_verified": bool(transactional_ps),
            "target_state_digest": target_state_digest,
            "rollback_state_digest": target_state_digest,
            "target_live_ps_state_digest": target_live_ps_state_digest,
            "rollback_live_ps_state_digest": target_live_ps_state_digest,
            "tick_binding_validated": tick_binding_validated,
            "tick_binding_stable": tick_binding_stable,
            "tick_binding_errors": tick_binding_errors,
            "expected_tick_binding": copy.deepcopy(expected_tick_binding),
            "actual_tick_binding": copy.deepcopy(actual_tick_binding),
            "expected_tick_scope": copy.deepcopy(expected_tick_scope),
            "actual_tick_scope": copy.deepcopy(actual_tick_scope),
        }
        return result


def _live_state_digest(value: Any) -> str:
    digest = getattr(value, "digest", None)
    if not isinstance(digest, str) or not digest:
        raise ValueError("transactional live PS state must expose a digest")
    return digest


def worldbridge_live_checkpoint_state_digest(
    checkpoint: Mapping[str, Any],
) -> str:
    """Return the stable digest of all checkpointed owners, excluding identity."""
    validation = validate_worldbridge_live_checkpoint(checkpoint)
    if not validation["valid"]:
        raise ValueError("invalid live checkpoint: " + ", ".join(validation["errors"]))
    return _state_digest(checkpoint)


__all__ = [
    "LiveCheckpointAdapters",
    "SCHEMA_VERSION",
    "STATUS",
    "WorldBridgeOwnerBindingDrift",
    "WorldBridgeTickBindingDrift",
    "WorldBridgeLiveCheckpointCoordinator",
    "WorldBridgeLiveCheckpointError",
    "WorldBridgeLiveTransactionCheckpoint",
    "WorldBridgeTransactionCapture",
    "WorldBridgeTransactionCaptureError",
    "build_worldbridge_live_checkpoint",
    "validate_worldbridge_live_checkpoint",
    "worldbridge_live_checkpoint_state_digest",
]
