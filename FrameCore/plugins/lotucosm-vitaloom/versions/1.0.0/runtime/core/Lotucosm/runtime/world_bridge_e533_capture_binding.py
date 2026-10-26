"""Qt-free binding contract for one real GameViewport source/fresh pair.

E533 is deliberately an evidence gate, not a replay authority.  Each record
contains the topology event, the shared-state envelope produced by the same
tick, and the full checkpoint captured at that boundary.  The validator
recomputes every cross-link instead of trusting summary digests alone.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from .world_bridge_dynamic_topology_receipt import (
    validate_worldbridge_dynamic_topology_receipt,
)
from .world_bridge_live_checkpoint import validate_worldbridge_live_checkpoint
from .world_bridge_shared_state_transport import (
    validate_worldbridge_shared_state_envelope,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e533_capture_binding"
BLOCKERS = (
    "unified_runtime_replay_authority_not_proven",
    "cross_lane_lossless_mapping_not_proven",
    "live_topology_mutation_owner_not_admitted",
)
_PROJECT_KEYS = {
    "project_path",
    "project_lock_digest",
    "scene_path",
    "scene_digest",
}
_EVENT_KEYS = {
    "event_index",
    "tick",
    "kind",
    "runtime_epoch",
    "structure_fingerprint",
    "receipt_digest",
    "node_ids",
    "topology_receipt",
}
_BINDING_KEYS = {
    "simulation_tick",
    "envelope_sequence",
    "capture_epoch",
    "input_sequence",
    "input_event_digest",
    "rng_context_id",
    "rng_snapshot_digest",
    "checkpoint_digest",
    "scene_project_binding_digest",
}
_RECORD_KEYS = {"event", "checkpoint", "envelope", "binding", "record_digest"}
_CAPTURE_KEYS = {
    "pair_id",
    "role",
    "host_id",
    "runtime_epoch",
    "project_binding",
    "records",
    "capture_digest",
}
_ARTIFACT_KEYS = {
    "schema_version",
    "status",
    "read_only",
    "pair_id",
    "project_binding",
    "source_capture",
    "fresh_capture",
    "source_capture_digest",
    "fresh_capture_digest",
    "event_count",
    "host_capture_pair_binding_proven",
    "topology_tick_binding_proven",
    "checkpoint_scene_binding_proven",
    "blockers",
    "replay_admitted",
    "lossless",
    "default_ready",
    "artifact_digest",
}


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _digest_without(value: Mapping[str, Any], field: str) -> str:
    candidate = dict(value)
    candidate[field] = ""
    return _digest(candidate)


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _non_empty_string(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}_invalid")


def _non_negative_int(value: object, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field}_invalid")


def build_worldbridge_e533_project_binding(
    *,
    project_path: str,
    project_lock: Mapping[str, Any],
    scene_path: str,
    scene_digest: str,
) -> dict[str, str]:
    """Build the host-independent project/scene identity used by E533."""
    _non_empty_string(project_path, "project_path")
    _non_empty_string(scene_path, "scene_path")
    if not isinstance(project_lock, Mapping):
        raise TypeError("project_lock must be a mapping")
    if not _is_digest(scene_digest):
        raise ValueError("scene_digest_invalid")
    return {
        "project_path": project_path,
        "project_lock_digest": _digest(dict(project_lock)),
        "scene_path": scene_path,
        "scene_digest": scene_digest,
    }


def build_worldbridge_e533_pair_id(
    *,
    project_binding: Mapping[str, Any],
    source_runtime_epoch: str,
    fresh_runtime_epoch: str,
) -> str:
    """Derive a stable pair identity from the actual two host epochs."""
    project_errors = _validate_project_binding(project_binding)
    if project_errors:
        raise ValueError("invalid E533 project binding: " + ",".join(project_errors))
    _non_empty_string(source_runtime_epoch, "source_runtime_epoch")
    _non_empty_string(fresh_runtime_epoch, "fresh_runtime_epoch")
    if source_runtime_epoch == fresh_runtime_epoch:
        raise ValueError("E533 source/fresh runtime epoch must differ")
    return _digest(
        {
            "project_binding": dict(project_binding),
            "source_runtime_epoch": source_runtime_epoch,
            "fresh_runtime_epoch": fresh_runtime_epoch,
        }
    )


def _validate_project_binding(value: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return ["project_binding_not_mapping"]
    if set(value) != _PROJECT_KEYS:
        errors.append("project_binding_keys_mismatch")
    for field in ("project_path", "scene_path"):
        try:
            _non_empty_string(value.get(field), field)
        except ValueError:
            errors.append(f"{field}_invalid")
    for field in ("project_lock_digest", "scene_digest"):
        if not _is_digest(value.get(field)):
            errors.append(f"{field}_invalid")
    try:
        _canonical(dict(value))
    except (TypeError, ValueError, OverflowError):
        errors.append("project_binding_not_canonical")
    return errors


def _validate_event_record(
    record: Mapping[str, Any],
    *,
    index: int,
    runtime_epoch: str,
    project_binding: Mapping[str, Any],
    previous_sequence: int | None,
    previous_capture_epoch: int | None,
    previous_tick: int | None,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if set(record) != _RECORD_KEYS:
        return [f"record_{index}_keys_mismatch"], {}

    event = record.get("event")
    checkpoint = record.get("checkpoint")
    envelope = record.get("envelope")
    binding = record.get("binding")
    for name, nested in (
        ("event", event),
        ("checkpoint", checkpoint),
        ("envelope", envelope),
        ("binding", binding),
    ):
        if not isinstance(nested, Mapping):
            errors.append(f"record_{index}_{name}_not_mapping")
    if errors:
        return errors, {}

    if record.get("record_digest") != _digest_without(record, "record_digest"):
        errors.append(f"record_{index}_digest_mismatch")

    if set(event) != _EVENT_KEYS:
        errors.append(f"record_{index}_event_keys_mismatch")
    if event.get("event_index") != index:
        errors.append(f"record_{index}_event_index_invalid")
    if event.get("tick") != index + 1:
        errors.append(f"record_{index}_topology_tick_link_invalid")
    if event.get("kind") not in {"spawn", "despawn"}:
        errors.append(f"record_{index}_event_kind_invalid")
    if event.get("runtime_epoch") != runtime_epoch:
        errors.append(f"record_{index}_event_epoch_mismatch")
    for field in ("structure_fingerprint", "receipt_digest"):
        if not _is_digest(event.get(field)):
            errors.append(f"record_{index}_{field}_invalid")
    node_ids = event.get("node_ids")
    if (
        not isinstance(node_ids, list)
        or any(not isinstance(node, str) or not node.strip() for node in node_ids)
        or node_ids != sorted(set(node_ids))
    ):
        errors.append(f"record_{index}_node_ids_invalid")
    receipt = event.get("topology_receipt")
    receipt_validation = validate_worldbridge_dynamic_topology_receipt(
        receipt, runtime_epoch=runtime_epoch
    )
    if receipt_validation != {"valid": True, "errors": []}:
        errors.append(f"record_{index}_topology_receipt_invalid")
    elif (
        receipt.get("receipt_digest") != event.get("receipt_digest")
        or receipt.get("structure_fingerprint") != event.get("structure_fingerprint")
    ):
        errors.append(f"record_{index}_topology_event_receipt_binding_mismatch")

    checkpoint_validation = validate_worldbridge_live_checkpoint(checkpoint)
    if checkpoint_validation != {"valid": True, "errors": []}:
        errors.append(f"record_{index}_checkpoint_invalid")
    else:
        lifecycle = checkpoint.get("lifecycle")
        checkpoint_sr = checkpoint.get("sr_state")
        checkpoint_input = checkpoint.get("input_state")
        checkpoint_randomness = checkpoint.get("randomness_state")
        if not isinstance(lifecycle, Mapping):
            errors.append(f"record_{index}_checkpoint_lifecycle_invalid")
        else:
            if lifecycle.get("runtime_epoch") != runtime_epoch:
                errors.append(f"record_{index}_checkpoint_epoch_mismatch")
            if lifecycle.get("scene_path") != project_binding.get("scene_path"):
                errors.append(f"record_{index}_checkpoint_scene_mismatch")
            runtime_binding = lifecycle.get("project_runtime_binding")
            if not isinstance(runtime_binding, Mapping):
                errors.append(f"record_{index}_checkpoint_project_binding_missing")
            else:
                for field in ("project_path", "project_lock_digest", "scene_path"):
                    if runtime_binding.get(field) != project_binding.get(field):
                        errors.append(f"record_{index}_checkpoint_{field}_mismatch")
                if runtime_binding.get("runtime_epoch") != runtime_epoch:
                    errors.append(f"record_{index}_checkpoint_runtime_binding_epoch_mismatch")
        if not isinstance(checkpoint_sr, Mapping):
            errors.append(f"record_{index}_checkpoint_sr_invalid")
        else:
            structure = checkpoint_sr.get("structure_fingerprint")
            checkpoint_receipt = checkpoint_sr.get("topology_receipt")
            if not isinstance(structure, Mapping) or structure.get("fingerprint") != event.get("structure_fingerprint"):
                errors.append(f"record_{index}_checkpoint_structure_mismatch")
            if not isinstance(checkpoint_receipt, Mapping):
                errors.append(f"record_{index}_checkpoint_topology_receipt_missing")
            elif (
                checkpoint_receipt.get("receipt_digest") != event.get("receipt_digest")
                or checkpoint_receipt.get("structure_fingerprint") != event.get("structure_fingerprint")
            ):
                errors.append(f"record_{index}_checkpoint_topology_receipt_mismatch")
        if not isinstance(checkpoint_input, Mapping):
            errors.append(f"record_{index}_checkpoint_input_invalid")
        if not isinstance(checkpoint_randomness, Mapping):
            errors.append(f"record_{index}_checkpoint_randomness_invalid")

    envelope_validation = validate_worldbridge_shared_state_envelope(envelope)
    if envelope_validation != {"valid": True, "errors": []}:
        errors.append(f"record_{index}_envelope_invalid")
    input_sequence: int | None = None
    input_event_digest: str | None = None
    canonical_input_event: dict[str, Any] | None = None
    rng_context_id: str | None = None
    rng_snapshot_digest: str | None = None
    if envelope_validation == {"valid": True, "errors": []}:
        sequence = envelope.get("sequence")
        capture_epoch = envelope.get("capture_epoch")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
            errors.append(f"record_{index}_envelope_sequence_invalid")
        elif previous_sequence is not None and sequence != previous_sequence + 1:
            errors.append(f"record_{index}_envelope_sequence_gap")
        if isinstance(capture_epoch, bool) or not isinstance(capture_epoch, int) or capture_epoch < 0:
            errors.append(f"record_{index}_capture_epoch_invalid")
        elif previous_capture_epoch is not None and capture_epoch != previous_capture_epoch + 1:
            errors.append(f"record_{index}_capture_epoch_gap")
        input_events = envelope.get("input_events")
        if not isinstance(input_events, list) or len(input_events) != 1:
            errors.append(f"record_{index}_canonical_input_event_count_invalid")
        else:
            input_payload = input_events[0].get("payload")
            if not isinstance(input_payload, Mapping):
                errors.append(f"record_{index}_canonical_input_payload_invalid")
            else:
                input_sequence = input_payload.get("canonical_sequence")
                if isinstance(input_sequence, bool) or not isinstance(input_sequence, int) or input_sequence < 1:
                    errors.append(f"record_{index}_canonical_input_sequence_invalid")
                input_event_digest = input_payload.get("event_digest")
                if not _is_digest(input_event_digest):
                    errors.append(f"record_{index}_canonical_input_digest_invalid")
                else:
                    from .world_bridge_input_sequence import (
                        validate_worldbridge_input_events,
                    )

                    canonical_event = {
                        "schema_version": 1,
                        "status": "worldbridge_input_sequence",
                        "event_id": input_events[0].get("event_id"),
                        "sequence": input_sequence,
                        "pause_reset_epoch": input_payload.get("pause_reset_epoch"),
                        "kind": input_events[0].get("kind"),
                        "payload": copy.deepcopy(input_payload.get("data")),
                        "event_digest": input_event_digest,
                    }
                    canonical_input_event = canonical_event
                    input_validation = validate_worldbridge_input_events(
                        [canonical_event],
                        last_sequence=input_sequence - 1
                        if isinstance(input_sequence, int)
                        and not isinstance(input_sequence, bool)
                        else 0,
                        pause_reset_epoch=input_payload.get("pause_reset_epoch")
                        if isinstance(input_payload.get("pause_reset_epoch"), int)
                        and not isinstance(input_payload.get("pause_reset_epoch"), bool)
                        else 0,
                    )
                    if input_validation != {"valid": True, "errors": []}:
                        errors.append(f"record_{index}_canonical_input_event_invalid")
                if input_payload.get("pause_reset_epoch") != envelope.get("lifecycle", {}).get("pause_reset_epoch"):
                    errors.append(f"record_{index}_canonical_input_epoch_mismatch")
                data = input_payload.get("data")
                if not isinstance(data, Mapping):
                    errors.append(f"record_{index}_canonical_input_data_invalid")
        rng = envelope.get("rng_context_snapshot")
        if not isinstance(rng, Mapping):
            errors.append(f"record_{index}_rng_snapshot_missing")
        else:
            rng_context_id = rng.get("context_id")
            rng_snapshot_digest = rng.get("snapshot_digest")
            if not isinstance(rng_context_id, str) or not rng_context_id.strip():
                errors.append(f"record_{index}_rng_context_id_invalid")
            if not _is_digest(rng_snapshot_digest):
                errors.append(f"record_{index}_rng_snapshot_digest_invalid")
        clocks = envelope.get("clock_provenance")
        sr_clock = clocks.get("sr") if isinstance(clocks, Mapping) else None
        simulation_tick = sr_clock.get("tick") if isinstance(sr_clock, Mapping) else None
        try:
            _non_negative_int(simulation_tick, f"record_{index}_simulation_tick")
        except ValueError:
            errors.append(f"record_{index}_simulation_tick_invalid")
        else:
            if previous_tick is not None and simulation_tick <= previous_tick:
                errors.append(f"record_{index}_simulation_tick_not_increasing")
    else:
        sequence = None
        capture_epoch = None
        simulation_tick = None

    if isinstance(checkpoint, Mapping):
        checkpoint_input = checkpoint.get("input_state")
        canonical = checkpoint_input.get("canonical_sequence") if isinstance(checkpoint_input, Mapping) else None
        if not isinstance(canonical, Mapping):
            errors.append(f"record_{index}_checkpoint_canonical_input_missing")
        elif input_sequence is not None and canonical.get("next_sequence") != input_sequence + 1:
            errors.append(f"record_{index}_checkpoint_input_cursor_mismatch")
        elif input_sequence is not None:
            event_id = envelope["input_events"][0].get("event_id")
            if not isinstance(canonical.get("seen_event_ids"), list) or event_id not in canonical["seen_event_ids"]:
                errors.append(f"record_{index}_checkpoint_input_identity_mismatch")
        if canonical_input_event is not None:
            handoff_events = checkpoint_input.get("ps_handoff_input_events")
            if (
                not isinstance(handoff_events, list)
                or len(handoff_events) != 1
                or handoff_events[0] != canonical_input_event
            ):
                errors.append(f"record_{index}_checkpoint_ps_input_binding_mismatch")
        transport = checkpoint_input.get("shared_transport") if isinstance(checkpoint_input, Mapping) else None
        if not isinstance(transport, Mapping) or transport.get("runtime_epoch") != runtime_epoch:
            errors.append(f"record_{index}_checkpoint_transport_epoch_mismatch")
        randomness = checkpoint.get("randomness_state")
        deterministic_context = randomness.get("deterministic_context") if isinstance(randomness, Mapping) else None
        envelope_rng = envelope.get("rng_context_snapshot") if isinstance(envelope, Mapping) else None
        if not isinstance(deterministic_context, Mapping) or deterministic_context != envelope_rng:
            errors.append(f"record_{index}_checkpoint_rng_binding_mismatch")

    expected_binding = {
        "simulation_tick": simulation_tick,
        "envelope_sequence": sequence,
        "capture_epoch": capture_epoch,
        "input_sequence": input_sequence,
        "input_event_digest": input_event_digest,
        "rng_context_id": rng_context_id,
        "rng_snapshot_digest": rng_snapshot_digest,
        "checkpoint_digest": checkpoint.get("digest") if isinstance(checkpoint, Mapping) else None,
        "scene_project_binding_digest": _digest(dict(project_binding)),
    }
    if set(binding) != _BINDING_KEYS:
        errors.append(f"record_{index}_binding_keys_mismatch")
    elif dict(binding) != expected_binding:
        errors.append(f"record_{index}_binding_mismatch")
    return errors, {
        "sequence": sequence,
        "capture_epoch": capture_epoch,
        "simulation_tick": simulation_tick,
        "input_sequence": input_sequence,
        "input_event_digest": input_event_digest,
        "rng_context_id": rng_context_id,
        "rng_snapshot_digest": rng_snapshot_digest,
    }


def _validate_capture(
    value: object,
    *,
    pair_id: str,
    role: str,
    project_binding: Mapping[str, Any],
) -> tuple[list[str], list[dict[str, Any]]]:
    if not isinstance(value, Mapping):
        return [f"{role}_capture_not_mapping"], []
    errors: list[str] = []
    if set(value) != _CAPTURE_KEYS:
        errors.append(f"{role}_capture_keys_mismatch")
    if value.get("role") != role:
        errors.append(f"{role}_capture_role_mismatch")
    if value.get("pair_id") != pair_id:
        errors.append(f"{role}_capture_pair_id_mismatch")
    runtime_epoch = value.get("runtime_epoch")
    try:
        _non_empty_string(runtime_epoch, f"{role}_runtime_epoch")
    except ValueError:
        errors.append(f"{role}_runtime_epoch_invalid")
        runtime_epoch = ""
    expected_host_id = f"game_viewport:{role}:{runtime_epoch}"
    if value.get("host_id") != expected_host_id:
        errors.append(f"{role}_host_id_mismatch")
    if value.get("project_binding") != dict(project_binding):
        errors.append(f"{role}_project_binding_mismatch")
    records = value.get("records")
    if not isinstance(records, list) or not records:
        errors.append(f"{role}_records_invalid")
        records = []
    details: list[dict[str, Any]] = []
    previous_sequence = None
    previous_capture_epoch = None
    previous_tick = None
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"{role}_record_{index}_not_mapping")
            continue
        record_errors, detail = _validate_event_record(
            record,
            index=index,
            runtime_epoch=str(runtime_epoch),
            project_binding=project_binding,
            previous_sequence=previous_sequence,
            previous_capture_epoch=previous_capture_epoch,
            previous_tick=previous_tick,
        )
        errors.extend(record_errors)
        details.append(detail)
        previous_sequence = detail.get("sequence", previous_sequence)
        previous_capture_epoch = detail.get("capture_epoch", previous_capture_epoch)
        previous_tick = detail.get("simulation_tick", previous_tick)
    if value.get("capture_digest") != _digest_without(value, "capture_digest"):
        errors.append(f"{role}_capture_digest_mismatch")
    return errors, details


def build_worldbridge_e533_capture_binding(
    *,
    pair_id: str,
    project_binding: Mapping[str, Any],
    source_capture: Mapping[str, Any],
    fresh_capture: Mapping[str, Any],
) -> dict[str, Any]:
    _non_empty_string(pair_id, "pair_id")
    project_errors = _validate_project_binding(project_binding)
    if project_errors:
        raise ValueError("invalid E533 project binding: " + ",".join(project_errors))
    source_errors, source_details = _validate_capture(
        source_capture, pair_id=pair_id, role="source", project_binding=project_binding
    )
    fresh_errors, fresh_details = _validate_capture(
        fresh_capture, pair_id=pair_id, role="fresh", project_binding=project_binding
    )
    if source_errors or fresh_errors:
        raise ValueError("invalid E533 capture: " + ",".join(source_errors + fresh_errors))
    source_records = source_capture["records"]
    fresh_records = fresh_capture["records"]
    if len(source_records) != len(fresh_records):
        raise ValueError("E533 source/fresh event count mismatch")
    if source_capture["runtime_epoch"] == fresh_capture["runtime_epoch"]:
        raise ValueError("E533 source/fresh runtime epoch must differ")
    if source_capture["host_id"] == fresh_capture["host_id"]:
        raise ValueError("E533 source/fresh host identity must differ")
    expected_pair_id = build_worldbridge_e533_pair_id(
        project_binding=project_binding,
        source_runtime_epoch=source_capture["runtime_epoch"],
        fresh_runtime_epoch=fresh_capture["runtime_epoch"],
    )
    if pair_id != expected_pair_id:
        raise ValueError("E533 pair identity does not match project and host epochs")
    for index, (source, fresh, source_detail, fresh_detail) in enumerate(
        zip(source_records, fresh_records, source_details, fresh_details, strict=True)
    ):
        source_event = source["event"]
        fresh_event = fresh["event"]
        if source_event["kind"] != fresh_event["kind"]:
            raise ValueError(f"E533 event_{index} kind parity mismatch")
        for field in ("structure_fingerprint", "node_ids"):
            if source_event[field] != fresh_event[field]:
                raise ValueError(f"E533 event_{index} {field} parity mismatch")
        if source_event["receipt_digest"] == fresh_event["receipt_digest"]:
            raise ValueError(f"E533 event_{index} topology receipt was reused")
        if source["checkpoint"]["digest"] == fresh["checkpoint"]["digest"]:
            raise ValueError(f"E533 event_{index} checkpoint identity was reused")
        for field in ("input_sequence", "input_event_digest"):
            if source_detail.get(field) != fresh_detail.get(field):
                raise ValueError(
                    f"E533 event_{index} {field} parity mismatch: "
                    f"source={source_detail.get(field)!r}, fresh={fresh_detail.get(field)!r}"
                )
        source_tick_offset = source_detail.get("simulation_tick") - source_details[0].get("simulation_tick")
        fresh_tick_offset = fresh_detail.get("simulation_tick") - fresh_details[0].get("simulation_tick")
        if source_tick_offset != index or fresh_tick_offset != index:
            raise ValueError(f"E533 event_{index} logical tick offset mismatch")
        if source_detail.get("rng_context_id") != fresh_detail.get("rng_context_id"):
            raise ValueError(f"E533 event_{index} RNG context parity mismatch")
        if source_detail.get("rng_snapshot_digest") != fresh_detail.get("rng_snapshot_digest"):
            raise ValueError(f"E533 event_{index} RNG snapshot parity mismatch")
        if source["binding"]["scene_project_binding_digest"] != fresh["binding"]["scene_project_binding_digest"]:
            raise ValueError(f"E533 event_{index} project/scene binding mismatch")
    artifact: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "pair_id": pair_id,
        "project_binding": copy.deepcopy(dict(project_binding)),
        "source_capture": copy.deepcopy(dict(source_capture)),
        "fresh_capture": copy.deepcopy(dict(fresh_capture)),
        "source_capture_digest": source_capture["capture_digest"],
        "fresh_capture_digest": fresh_capture["capture_digest"],
        "event_count": len(source_records),
        "host_capture_pair_binding_proven": True,
        "topology_tick_binding_proven": True,
        "checkpoint_scene_binding_proven": True,
        "blockers": list(BLOCKERS),
        "replay_admitted": False,
        "lossless": False,
        "default_ready": False,
        "artifact_digest": "",
    }
    artifact["artifact_digest"] = _digest_without(artifact, "artifact_digest")
    return copy.deepcopy(artifact)


def build_worldbridge_e533_capture_record(
    *,
    event: Mapping[str, Any],
    checkpoint: Mapping[str, Any],
    envelope: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> dict[str, Any]:
    """Seal one event/tick/checkpoint tuple before host capture assembly."""
    record: dict[str, Any] = {
        "event": copy.deepcopy(dict(event)),
        "checkpoint": copy.deepcopy(dict(checkpoint)),
        "envelope": copy.deepcopy(dict(envelope)),
        "binding": copy.deepcopy(dict(binding)),
        "record_digest": "",
    }
    record["record_digest"] = _digest_without(record, "record_digest")
    return record


def build_worldbridge_e533_record_from_live_capture(
    *,
    event: Mapping[str, Any],
    checkpoint: Mapping[str, Any],
    envelope: Mapping[str, Any],
    project_binding: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive the record's cross-links from detached GameViewport evidence."""
    input_events = envelope.get("input_events")
    if not isinstance(input_events, list) or len(input_events) != 1:
        raise ValueError("E533 requires exactly one canonical input event per topology tick")
    input_event = input_events[0]
    input_payload = input_event.get("payload") if isinstance(input_event, Mapping) else None
    if not isinstance(input_payload, Mapping):
        raise ValueError("E533 canonical input payload is missing")
    clocks = envelope.get("clock_provenance")
    sr_clock = clocks.get("sr") if isinstance(clocks, Mapping) else None
    if not isinstance(sr_clock, Mapping):
        raise ValueError("E533 SR clock provenance is missing")
    rng = envelope.get("rng_context_snapshot")
    if not isinstance(rng, Mapping):
        raise ValueError("E533 RNG snapshot is missing")
    binding = {
        "simulation_tick": sr_clock.get("tick"),
        "envelope_sequence": envelope.get("sequence"),
        "capture_epoch": envelope.get("capture_epoch"),
        "input_sequence": input_payload.get("canonical_sequence"),
        "input_event_digest": input_payload.get("event_digest"),
        "rng_context_id": rng.get("context_id"),
        "rng_snapshot_digest": rng.get("snapshot_digest"),
        "checkpoint_digest": checkpoint.get("digest"),
        "scene_project_binding_digest": _digest(dict(project_binding)),
    }
    return build_worldbridge_e533_capture_record(
        event=event,
        checkpoint=checkpoint,
        envelope=envelope,
        binding=binding,
    )


def build_worldbridge_e533_host_capture(
    *,
    pair_id: str,
    role: str,
    runtime_epoch: str,
    project_binding: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Seal and validate one source or fresh GameViewport capture."""
    if role not in {"source", "fresh"}:
        raise ValueError("E533 host capture role is invalid")
    _non_empty_string(pair_id, "pair_id")
    _non_empty_string(runtime_epoch, "runtime_epoch")
    capture: dict[str, Any] = {
        "pair_id": pair_id,
        "role": role,
        "host_id": f"game_viewport:{role}:{runtime_epoch}",
        "runtime_epoch": runtime_epoch,
        "project_binding": copy.deepcopy(dict(project_binding)),
        "records": [copy.deepcopy(dict(record)) for record in records],
        "capture_digest": "",
    }
    capture["capture_digest"] = _digest_without(capture, "capture_digest")
    errors, _details = _validate_capture(
        capture, pair_id=pair_id, role=role, project_binding=project_binding
    )
    if errors:
        raise ValueError("invalid E533 host capture: " + ",".join(errors))
    return capture


def validate_worldbridge_e533_capture_binding(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["artifact_not_mapping"]}
    errors: list[str] = []
    if set(value) != _ARTIFACT_KEYS:
        errors.append("artifact_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("artifact_identity_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_mismatch")
    try:
        _non_empty_string(value.get("pair_id"), "pair_id")
    except ValueError:
        errors.append("pair_id_invalid")
    project_binding = value.get("project_binding")
    project_errors = _validate_project_binding(project_binding)
    errors.extend(project_errors)
    if not isinstance(project_binding, Mapping):
        project_binding = {}
    source_errors, source_details = _validate_capture(
        value.get("source_capture"), pair_id=value.get("pair_id"), role="source", project_binding=project_binding
    )
    fresh_errors, fresh_details = _validate_capture(
        value.get("fresh_capture"), pair_id=value.get("pair_id"), role="fresh", project_binding=project_binding
    )
    errors.extend(source_errors)
    errors.extend(fresh_errors)
    source = value.get("source_capture")
    fresh = value.get("fresh_capture")
    if isinstance(source, Mapping) and isinstance(fresh, Mapping) and not source_errors and not fresh_errors:
        if source.get("runtime_epoch") == fresh.get("runtime_epoch"):
            errors.append("runtime_epoch_reuse")
        if source.get("host_id") == fresh.get("host_id"):
            errors.append("host_identity_reuse")
        try:
            expected_pair_id = build_worldbridge_e533_pair_id(
                project_binding=project_binding,
                source_runtime_epoch=source.get("runtime_epoch"),
                fresh_runtime_epoch=fresh.get("runtime_epoch"),
            )
        except (TypeError, ValueError):
            expected_pair_id = None
        if value.get("pair_id") != expected_pair_id:
            errors.append("pair_id_binding_mismatch")
        source_records = source.get("records", [])
        fresh_records = fresh.get("records", [])
        if value.get("event_count") != len(source_records) or len(source_records) != len(fresh_records):
            errors.append("event_count_mismatch")
        for index, (source_record, fresh_record, source_detail, fresh_detail) in enumerate(
            zip(source_records, fresh_records, source_details, fresh_details)
        ):
            source_event = source_record["event"]
            fresh_event = fresh_record["event"]
            if source_event.get("kind") != fresh_event.get("kind"):
                errors.append(f"event_{index}_kind_parity_mismatch")
            for field in ("structure_fingerprint", "node_ids"):
                if source_event.get(field) != fresh_event.get(field):
                    errors.append(f"event_{index}_{field}_parity_mismatch")
            if source_event.get("receipt_digest") == fresh_event.get("receipt_digest"):
                errors.append(f"event_{index}_receipt_reused")
            if source_record["checkpoint"].get("digest") == fresh_record["checkpoint"].get("digest"):
                errors.append(f"event_{index}_checkpoint_reused")
            for field in ("input_sequence", "input_event_digest", "rng_context_id", "rng_snapshot_digest"):
                if source_detail.get(field) != fresh_detail.get(field):
                    errors.append(f"event_{index}_{field}_parity_mismatch")
            source_tick_offset = source_detail.get("simulation_tick") - source_details[0].get("simulation_tick")
            fresh_tick_offset = fresh_detail.get("simulation_tick") - fresh_details[0].get("simulation_tick")
            if source_tick_offset != index or fresh_tick_offset != index:
                errors.append(f"event_{index}_logical_tick_offset_mismatch")
    if value.get("source_capture_digest") != (source.get("capture_digest") if isinstance(source, Mapping) else None):
        errors.append("source_capture_binding_mismatch")
    if value.get("fresh_capture_digest") != (fresh.get("capture_digest") if isinstance(fresh, Mapping) else None):
        errors.append("fresh_capture_binding_mismatch")
    for field in (
        "host_capture_pair_binding_proven",
        "topology_tick_binding_proven",
        "checkpoint_scene_binding_proven",
    ):
        if value.get(field) is not True:
            errors.append(f"{field}_not_proven")
    if value.get("blockers") != list(BLOCKERS):
        errors.append("blockers_mismatch")
    for field in ("replay_admitted", "lossless", "default_ready"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    if value.get("artifact_digest") != _digest_without(value, "artifact_digest"):
        errors.append("artifact_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_e533_capture_binding(value: Mapping[str, Any]) -> bytes:
    validation = validate_worldbridge_e533_capture_binding(value)
    if validation != {"valid": True, "errors": []}:
        raise ValueError("invalid E533 capture binding: " + ",".join(validation["errors"]))
    return _canonical(value)


def decode_worldbridge_e533_capture_binding(
    encoded: bytes | bytearray | memoryview,
) -> dict[str, Any]:
    if not isinstance(encoded, (bytes, bytearray, memoryview)):
        raise TypeError("encoded E533 artifact must be bytes-like")
    raw = bytes(encoded)
    try:
        parsed = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("encoded E533 artifact is not strict JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("encoded E533 artifact root must be an object")
    validation = validate_worldbridge_e533_capture_binding(parsed)
    if validation != {"valid": True, "errors": []}:
        raise ValueError("invalid E533 capture binding: " + ",".join(validation["errors"]))
    if _canonical(parsed) != raw:
        raise ValueError("encoded E533 artifact is not canonical JSON")
    return copy.deepcopy(parsed)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


__all__ = [
    "BLOCKERS",
    "build_worldbridge_e533_capture_binding",
    "build_worldbridge_e533_capture_record",
    "build_worldbridge_e533_host_capture",
    "build_worldbridge_e533_project_binding",
    "build_worldbridge_e533_pair_id",
    "build_worldbridge_e533_record_from_live_capture",
    "decode_worldbridge_e533_capture_binding",
    "encode_worldbridge_e533_capture_binding",
    "validate_worldbridge_e533_capture_binding",
]
