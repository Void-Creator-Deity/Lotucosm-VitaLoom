"""Qt-free, non-admitting replay-trace candidate over a real E533 pair.

E539 is a read-only evidence projection. It never restores a host, advances a
clock, merges SR/PS time, or turns a successful trace into replay authority.
Source and fresh hosts have different absolute clock origins, so continuity is
checked against each host's first observed tick and the fixed offset is recorded
explicitly.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from .world_bridge_e507_next_tick_replay_witness import (
    validate_worldbridge_e507_next_tick_replay_witness,
)
from .world_bridge_e508_fresh_replay_corpus import (
    project_worldbridge_e508_portable_state,
)
from .world_bridge_e533_capture_binding import (
    validate_worldbridge_e533_capture_binding,
)
from .world_bridge_e538_shared_contracts import (
    validate_worldbridge_e538_shared_contract,
)
from .world_bridge_input_sequence import validate_worldbridge_input_events
from .world_bridge_live_checkpoint import validate_worldbridge_live_checkpoint
from .world_bridge_shared_state_transport import (
    validate_worldbridge_shared_state_envelope,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_e539_replay_trace_candidate"
AUTHORITY_SCOPE = "candidate_non_admitting_replay_trace"
BLOCKERS = (
    "shared_runtime_clock_not_admitted",
    "scheduler_owned_input_not_admitted",
    "cross_lane_rng_draw_order_not_admitted",
    "shared_pause_reset_authority_not_admitted",
    "atomic_sr_ps_checkpoint_not_admitted",
    "full_unified_replay_not_admitted",
)
_FALSE_ADMISSIONS = (
    "replay_admitted",
    "tick_merge_admitted",
    "full_unified_replay_admitted",
    "cross_lane_behavior_admitted",
    "lossless",
    "default_ready",
)
_TRACE_KEYS = {
    "schema_version",
    "status",
    "read_only",
    "authority_scope",
    "source_host",
    "fresh_host",
    "project_binding",
    "source_tick_offset",
    "fresh_tick_offset",
    "trace_count",
    "tick_records",
    "all_portable_state_parity",
    "source_fresh_parity_proven",
    "e533_artifact_digest",
    "e538_contract_digest",
    "e507_witness_bindings",
    "e507_witness_bound",
    "blockers",
    "trace_valid",
    "replay_admitted",
    "tick_merge_admitted",
    "full_unified_replay_admitted",
    "cross_lane_behavior_admitted",
    "lossless",
    "default_ready",
    "compensation",
    "trace_digest",
}
_RECORD_KEYS = {
    "trace_tick",
    "source_host_id",
    "fresh_host_id",
    "source_runtime_epoch",
    "fresh_runtime_epoch",
    "project_binding_digest",
    "scene_digest",
    "source_tick",
    "fresh_tick",
    "source_relative_tick",
    "fresh_relative_tick",
    "source_clock",
    "fresh_clock",
    "source_checkpoint_digest",
    "fresh_checkpoint_digest",
    "source_input",
    "fresh_input",
    "source_rng",
    "fresh_rng",
    "source_pause_reset_epoch",
    "fresh_pause_reset_epoch",
    "source_topology_receipt_digest",
    "fresh_topology_receipt_digest",
    "source_structure_fingerprint",
    "fresh_structure_fingerprint",
    "source_lane_state_digests",
    "fresh_lane_state_digests",
    "portable_state_parity",
    "source_fresh_portable_state_parity",
    "e507_witness_digest",
    "record_digest",
}
_FIELD_PARITY_KEYS = (
    "topology_owner_state",
    "sr_state",
    "ps_state",
    "bridge_identity_links",
    "input_state",
    "randomness_state",
    "lifecycle",
)


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


def _clock_projection(envelope: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    clocks = envelope.get("clock_provenance")
    if not isinstance(clocks, Mapping):
        raise ValueError("E539 clock provenance missing")
    result: dict[str, dict[str, Any]] = {}
    for lane in ("sr", "ps"):
        clock = clocks.get(lane)
        if not isinstance(clock, Mapping):
            raise ValueError(f"E539 {lane} clock missing")
        result[lane] = copy.deepcopy(dict(clock))
    return result


def _input_projection(
    envelope: Mapping[str, Any], checkpoint: Mapping[str, Any]
) -> dict[str, Any]:
    input_state = checkpoint.get("input_state")
    if not isinstance(input_state, Mapping):
        raise ValueError("E539 input state missing")
    cursor = input_state.get("canonical_sequence")
    if not isinstance(cursor, Mapping):
        raise ValueError("E539 canonical input cursor missing")
    events = envelope.get("input_events")
    if not isinstance(events, list):
        raise ValueError("E539 input events missing")
    canonical_events: list[dict[str, Any]] = []
    for raw in events:
        if not isinstance(raw, Mapping):
            raise ValueError("E539 input event is not mapping")
        payload = raw.get("payload")
        if not isinstance(payload, Mapping):
            raise ValueError("E539 input payload missing")
        canonical_events.append(
            {
                "event_id": raw.get("event_id"),
                "kind": raw.get("kind"),
                "sequence": payload.get("canonical_sequence"),
                "pause_reset_epoch": payload.get("pause_reset_epoch"),
                "event_digest": payload.get("event_digest"),
                "data_digest": _digest(payload.get("data")),
            }
        )
    return {
        "events": canonical_events,
        "next_sequence": cursor.get("next_sequence"),
        "seen_event_ids": copy.deepcopy(cursor.get("seen_event_ids")),
        "pause_reset_epoch": cursor.get("pause_reset_epoch"),
        "ps_handoff_event_digest": _digest(
            input_state.get("ps_handoff_input_events")
        ),
        "shared_transport_digest": _digest(input_state.get("shared_transport")),
    }


def _rng_projection(checkpoint: Mapping[str, Any]) -> dict[str, Any]:
    randomness = checkpoint.get("randomness_state")
    if not isinstance(randomness, Mapping):
        raise ValueError("E539 randomness state missing")
    context = randomness.get("deterministic_context")
    if not isinstance(context, Mapping):
        raise ValueError("E539 deterministic RNG context missing")
    return {
        "context_id": context.get("context_id"),
        "snapshot_digest": context.get("snapshot_digest"),
        "checkpoint_digest": randomness.get("checkpoint_digest"),
        "runtime_epoch": randomness.get("runtime_epoch"),
    }


def _lane_state_digests(checkpoint: Mapping[str, Any]) -> dict[str, str]:
    return {
        field: _digest(checkpoint.get(field))
        for field in (
            "topology_owner_state",
            "sr_state",
            "ps_state",
            "bridge_identity_links",
            "input_state",
            "randomness_state",
            "lifecycle",
        )
    }


def _field_parity(
    source_checkpoint: Mapping[str, Any], fresh_checkpoint: Mapping[str, Any]
) -> dict[str, bool]:
    source = project_worldbridge_e508_portable_state(source_checkpoint)
    fresh = project_worldbridge_e508_portable_state(fresh_checkpoint)
    return {
        field: source.get(field) == fresh.get(field)
        for field in _FIELD_PARITY_KEYS
    }


def _record_digest(record: Mapping[str, Any]) -> str:
    return _digest_without(record, "record_digest")


def _host_projection(capture: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "host_id": capture.get("host_id"),
        "runtime_epoch": capture.get("runtime_epoch"),
        "capture_digest": capture.get("capture_digest"),
    }


def _witness_bindings(
    records: Sequence[Mapping[str, Any]],
    witnesses: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(witnesses, Sequence) or isinstance(
        witnesses, (str, bytes, bytearray)
    ):
        raise TypeError("E539 E507 witnesses must be a sequence")
    checkpoint_map = {
        record["checkpoint"]["digest"]: (index, record)
        for index, record in enumerate(records)
    }
    bindings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for witness_index, raw in enumerate(witnesses):
        if not isinstance(raw, Mapping):
            raise TypeError(f"E539 E507 witness_{witness_index} must be a mapping")
        validation = validate_worldbridge_e507_next_tick_replay_witness(raw)
        if validation != {"valid": True, "errors": []}:
            raise ValueError(
                f"invalid E539 E507 witness_{witness_index}: "
                + ",".join(validation["errors"])
            )
        checkpoint_digest = raw.get("checkpoint_digest")
        if checkpoint_digest in seen:
            raise ValueError("E539 E507 witness checkpoint binding is duplicated")
        if checkpoint_digest not in checkpoint_map:
            raise ValueError("E539 E507 witness checkpoint is outside the E533 pair")
        seen.add(checkpoint_digest)
        trace_tick, _record = checkpoint_map[checkpoint_digest]
        bindings.append(
            {
                "trace_tick": trace_tick,
                "checkpoint_digest": checkpoint_digest,
                "witness_digest": raw.get("witness_digest"),
            }
        )
    return sorted(bindings, key=lambda item: item["trace_tick"])


def _build_trace_records(
    artifact: Mapping[str, Any],
    *,
    witness_by_checkpoint: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    source_capture = artifact["source_capture"]
    fresh_capture = artifact["fresh_capture"]
    source_records = source_capture["records"]
    fresh_records = fresh_capture["records"]
    source_origin = source_records[0]["binding"]["simulation_tick"]
    fresh_origin = fresh_records[0]["binding"]["simulation_tick"]
    records: list[dict[str, Any]] = []
    for index, (source_record, fresh_record) in enumerate(
        zip(source_records, fresh_records, strict=True)
    ):
        source_envelope = source_record["envelope"]
        fresh_envelope = fresh_record["envelope"]
        source_checkpoint = source_record["checkpoint"]
        fresh_checkpoint = fresh_record["checkpoint"]
        source_clock = _clock_projection(source_envelope)
        fresh_clock = _clock_projection(fresh_envelope)
        source_input = _input_projection(source_envelope, source_checkpoint)
        fresh_input = _input_projection(fresh_envelope, fresh_checkpoint)
        source_rng = _rng_projection(source_checkpoint)
        fresh_rng = _rng_projection(fresh_checkpoint)
        parity = _field_parity(source_checkpoint, fresh_checkpoint)
        all_fields_parity = all(parity.values())
        source_tick = source_clock["sr"].get("tick")
        fresh_tick = fresh_clock["sr"].get("tick")
        checkpoint_digest = source_checkpoint.get("digest")
        record: dict[str, Any] = {
            "trace_tick": index,
            "source_host_id": source_capture.get("host_id"),
            "fresh_host_id": fresh_capture.get("host_id"),
            "source_runtime_epoch": source_capture.get("runtime_epoch"),
            "fresh_runtime_epoch": fresh_capture.get("runtime_epoch"),
            "project_binding_digest": _digest(artifact.get("project_binding")),
            "scene_digest": artifact.get("project_binding", {}).get("scene_digest"),
            "source_tick": source_tick,
            "fresh_tick": fresh_tick,
            "source_relative_tick": source_tick - source_origin,
            "fresh_relative_tick": fresh_tick - fresh_origin,
            "source_clock": source_clock,
            "fresh_clock": fresh_clock,
            "source_checkpoint_digest": checkpoint_digest,
            "fresh_checkpoint_digest": fresh_checkpoint.get("digest"),
            "source_input": source_input,
            "fresh_input": fresh_input,
            "source_rng": source_rng,
            "fresh_rng": fresh_rng,
            "source_pause_reset_epoch": source_input.get("pause_reset_epoch"),
            "fresh_pause_reset_epoch": fresh_input.get("pause_reset_epoch"),
            "source_topology_receipt_digest": source_record["event"].get("receipt_digest"),
            "fresh_topology_receipt_digest": fresh_record["event"].get("receipt_digest"),
            "source_structure_fingerprint": source_record["event"].get("structure_fingerprint"),
            "fresh_structure_fingerprint": fresh_record["event"].get("structure_fingerprint"),
            "source_lane_state_digests": _lane_state_digests(source_checkpoint),
            "fresh_lane_state_digests": _lane_state_digests(fresh_checkpoint),
            "portable_state_parity": parity,
            "source_fresh_portable_state_parity": all_fields_parity,
            "e507_witness_digest": (
                witness_by_checkpoint.get(checkpoint_digest)
                if witness_by_checkpoint is not None
                else None
            ),
            "record_digest": "",
        }
        record["record_digest"] = _record_digest(record)
        records.append(record)
    return records


def build_worldbridge_e539_replay_trace_candidate(
    *,
    e533_artifact: Mapping[str, Any],
    e538_contract: Mapping[str, Any],
    e507_witnesses: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Build a read-only replay trace without granting replay authority."""
    artifact_validation = validate_worldbridge_e533_capture_binding(e533_artifact)
    if artifact_validation != {"valid": True, "errors": []}:
        raise ValueError(
            "invalid E533 artifact: " + ",".join(artifact_validation["errors"])
        )
    contract_validation = validate_worldbridge_e538_shared_contract(e538_contract)
    if contract_validation != {"valid": True, "errors": []}:
        raise ValueError(
            "invalid E538 contract: " + ",".join(contract_validation["errors"])
        )
    source_records = e533_artifact["source_capture"]["records"]
    fresh_records = e533_artifact["fresh_capture"]["records"]
    if not source_records or not fresh_records:
        raise ValueError("E539 requires at least one captured tick")
    witness_bindings = _witness_bindings(source_records, e507_witnesses)
    witness_by_checkpoint = {
        item["checkpoint_digest"]: item["witness_digest"]
        for item in witness_bindings
    }
    records = _build_trace_records(
        e533_artifact, witness_by_checkpoint=witness_by_checkpoint
    )
    all_parity = bool(records) and all(
        record["source_fresh_portable_state_parity"] is True for record in records
    )
    trace: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "authority_scope": AUTHORITY_SCOPE,
        "source_host": _host_projection(e533_artifact["source_capture"]),
        "fresh_host": _host_projection(e533_artifact["fresh_capture"]),
        "project_binding": copy.deepcopy(dict(e533_artifact["project_binding"])),
        "source_tick_offset": source_records[0]["binding"]["simulation_tick"],
        "fresh_tick_offset": fresh_records[0]["binding"]["simulation_tick"],
        "trace_count": len(records),
        "tick_records": records,
        "all_portable_state_parity": all_parity,
        "source_fresh_parity_proven": all_parity,
        "e533_artifact_digest": e533_artifact.get("artifact_digest"),
        "e538_contract_digest": _digest(e538_contract),
        "e507_witness_bindings": witness_bindings,
        "e507_witness_bound": bool(witness_bindings),
        "blockers": list(BLOCKERS),
        "trace_valid": True,
        "replay_admitted": False,
        "tick_merge_admitted": False,
        "full_unified_replay_admitted": False,
        "cross_lane_behavior_admitted": False,
        "lossless": False,
        "default_ready": False,
        "compensation": {
            "required": False,
            "applied": False,
            "reason": "read_only_projection_no_live_mutation",
        },
        "trace_digest": "",
    }
    trace["trace_digest"] = _digest_without(trace, "trace_digest")
    validation = validate_worldbridge_e539_replay_trace_candidate(
        trace,
        e533_artifact=e533_artifact,
        e538_contract=e538_contract,
        e507_witnesses=e507_witnesses,
    )
    if validation != {"valid": True, "errors": []}:
        raise ValueError(
            "E539 produced invalid trace: " + ",".join(validation["errors"])
        )
    return copy.deepcopy(trace)


def _validate_record_sequence(
    records: object,
    *,
    trace: Mapping[str, Any],
    artifact: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if not isinstance(records, list):
        return ["tick_records_not_list"]
    if trace.get("trace_count") != len(records):
        errors.append("trace_count_mismatch")
    if not records:
        return errors + ["tick_records_empty"]
    source_capture = artifact["source_capture"]
    fresh_capture = artifact["fresh_capture"]
    source_records = source_capture["records"]
    fresh_records = fresh_capture["records"]
    if len(records) != len(source_records) or len(records) != len(fresh_records):
        errors.append("tick_record_count_mismatch")
        return errors
    source_origin = source_records[0]["binding"]["simulation_tick"]
    fresh_origin = fresh_records[0]["binding"]["simulation_tick"]
    if trace.get("source_tick_offset") != source_origin:
        errors.append("source_tick_offset_mismatch")
    if trace.get("fresh_tick_offset") != fresh_origin:
        errors.append("fresh_tick_offset_mismatch")
    project_digest = _digest(artifact.get("project_binding"))
    expected_scene_digest = artifact.get("project_binding", {}).get("scene_digest")
    previous_source_input: int | None = None
    previous_fresh_input: int | None = None
    previous_source_epoch: int | None = None
    previous_fresh_epoch: int | None = None
    expected_rng_context: str | None = None
    expected_rng_snapshot: str | None = None
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"record_{index}_not_mapping")
            continue
        if set(record) != _RECORD_KEYS:
            errors.append(f"record_{index}_keys_mismatch")
        if record.get("trace_tick") != index:
            errors.append(f"record_{index}_trace_tick_mismatch")
        if record.get("source_host_id") != source_capture.get("host_id"):
            errors.append(f"record_{index}_source_host_mismatch")
        if record.get("fresh_host_id") != fresh_capture.get("host_id"):
            errors.append(f"record_{index}_fresh_host_mismatch")
        if record.get("source_runtime_epoch") != source_capture.get("runtime_epoch"):
            errors.append(f"record_{index}_source_runtime_epoch_mismatch")
        if record.get("fresh_runtime_epoch") != fresh_capture.get("runtime_epoch"):
            errors.append(f"record_{index}_fresh_runtime_epoch_mismatch")
        if record.get("project_binding_digest") != project_digest:
            errors.append(f"record_{index}_project_binding_digest_mismatch")
        if record.get("scene_digest") != expected_scene_digest:
            errors.append(f"record_{index}_scene_digest_mismatch")
        source_tick = record.get("source_tick")
        fresh_tick = record.get("fresh_tick")
        if isinstance(source_tick, bool) or not isinstance(source_tick, int):
            errors.append(f"record_{index}_source_tick_invalid")
            source_tick = None
        if isinstance(fresh_tick, bool) or not isinstance(fresh_tick, int):
            errors.append(f"record_{index}_fresh_tick_invalid")
            fresh_tick = None
        if source_tick is not None:
            if source_tick != source_origin + index:
                errors.append(f"record_{index}_source_tick_origin_mismatch")
            if record.get("source_relative_tick") != index:
                errors.append(f"record_{index}_source_relative_tick_mismatch")
        if fresh_tick is not None:
            if fresh_tick != fresh_origin + index:
                errors.append(f"record_{index}_fresh_tick_origin_mismatch")
            if record.get("fresh_relative_tick") != index:
                errors.append(f"record_{index}_fresh_relative_tick_mismatch")
        expected_source = source_records[index]
        expected_fresh = fresh_records[index]
        expected_source_clock = _clock_projection(expected_source["envelope"])
        expected_fresh_clock = _clock_projection(expected_fresh["envelope"])
        if record.get("source_clock") != expected_source_clock:
            errors.append(f"record_{index}_source_clock_mismatch")
        if record.get("fresh_clock") != expected_fresh_clock:
            errors.append(f"record_{index}_fresh_clock_mismatch")
        expected_source_input = _input_projection(
            expected_source["envelope"], expected_source["checkpoint"]
        )
        expected_fresh_input = _input_projection(
            expected_fresh["envelope"], expected_fresh["checkpoint"]
        )
        if record.get("source_input") != expected_source_input:
            errors.append(f"record_{index}_source_input_mismatch")
        if record.get("fresh_input") != expected_fresh_input:
            errors.append(f"record_{index}_fresh_input_mismatch")
        expected_source_rng = _rng_projection(expected_source["checkpoint"])
        expected_fresh_rng = _rng_projection(expected_fresh["checkpoint"])
        if record.get("source_rng") != expected_source_rng:
            errors.append(f"record_{index}_source_rng_mismatch")
        if record.get("fresh_rng") != expected_fresh_rng:
            errors.append(f"record_{index}_fresh_rng_mismatch")
        if record.get("source_checkpoint_digest") != expected_source["checkpoint"].get("digest"):
            errors.append(f"record_{index}_source_checkpoint_mismatch")
        if record.get("fresh_checkpoint_digest") != expected_fresh["checkpoint"].get("digest"):
            errors.append(f"record_{index}_fresh_checkpoint_mismatch")
        if record.get("source_topology_receipt_digest") != expected_source["event"].get("receipt_digest"):
            errors.append(f"record_{index}_source_topology_receipt_mismatch")
        if record.get("fresh_topology_receipt_digest") != expected_fresh["event"].get("receipt_digest"):
            errors.append(f"record_{index}_fresh_topology_receipt_mismatch")
        if record.get("source_structure_fingerprint") != expected_source["event"].get("structure_fingerprint"):
            errors.append(f"record_{index}_source_structure_mismatch")
        if record.get("fresh_structure_fingerprint") != expected_fresh["event"].get("structure_fingerprint"):
            errors.append(f"record_{index}_fresh_structure_mismatch")
        expected_lane_source = _lane_state_digests(expected_source["checkpoint"])
        expected_lane_fresh = _lane_state_digests(expected_fresh["checkpoint"])
        if record.get("source_lane_state_digests") != expected_lane_source:
            errors.append(f"record_{index}_source_lane_digests_mismatch")
        if record.get("fresh_lane_state_digests") != expected_lane_fresh:
            errors.append(f"record_{index}_fresh_lane_digests_mismatch")
        expected_parity = _field_parity(
            expected_source["checkpoint"], expected_fresh["checkpoint"]
        )
        if record.get("portable_state_parity") != expected_parity:
            errors.append(f"record_{index}_portable_state_parity_mismatch")
        if record.get("source_fresh_portable_state_parity") is not all(expected_parity.values()):
            errors.append(f"record_{index}_source_fresh_portable_state_parity_mismatch")
        source_input = record.get("source_input")
        fresh_input = record.get("fresh_input")
        if not isinstance(source_input, Mapping):
            errors.append(f"record_{index}_source_input_invalid")
            source_input = {}
        if not isinstance(fresh_input, Mapping):
            errors.append(f"record_{index}_fresh_input_invalid")
            fresh_input = {}
        for lane, projected, prior in (
            ("source", source_input, previous_source_input),
            ("fresh", fresh_input, previous_fresh_input),
        ):
            events = projected.get("events")
            if not isinstance(events, list):
                errors.append(f"record_{index}_{lane}_input_events_invalid")
                events = []
            next_sequence = projected.get("next_sequence")
            if isinstance(next_sequence, bool) or not isinstance(next_sequence, int):
                errors.append(f"record_{index}_{lane}_input_cursor_invalid")
            last_sequence = prior
            for event_index, event in enumerate(events):
                if not isinstance(event, Mapping):
                    errors.append(f"record_{index}_{lane}_event_{event_index}_invalid")
                    continue
                sequence = event.get("sequence")
                if isinstance(sequence, bool) or not isinstance(sequence, int):
                    errors.append(f"record_{index}_{lane}_event_{event_index}_sequence_invalid")
                    continue
                if last_sequence is not None and sequence != last_sequence + 1:
                    errors.append(f"record_{index}_{lane}_event_{event_index}_sequence_gap")
                if last_sequence is not None and sequence <= last_sequence:
                    errors.append(f"record_{index}_{lane}_event_{event_index}_sequence_regression")
                last_sequence = sequence
                if not _is_digest(event.get("event_digest")):
                    errors.append(f"record_{index}_{lane}_event_{event_index}_digest_invalid")
                if not _is_digest(event.get("data_digest")):
                    errors.append(f"record_{index}_{lane}_event_{event_index}_data_digest_invalid")
            if isinstance(next_sequence, int) and events and last_sequence is not None:
                if next_sequence <= last_sequence:
                    errors.append(f"record_{index}_{lane}_input_cursor_mismatch")
            if events:
                if lane == "source":
                    previous_source_input = last_sequence
                else:
                    previous_fresh_input = last_sequence
        source_epoch = record.get("source_pause_reset_epoch")
        fresh_epoch = record.get("fresh_pause_reset_epoch")
        for lane, epoch, prior_epoch in (
            ("source", source_epoch, previous_source_epoch),
            ("fresh", fresh_epoch, previous_fresh_epoch),
        ):
            if isinstance(epoch, bool) or not isinstance(epoch, int) or epoch < 0:
                errors.append(f"record_{index}_{lane}_pause_epoch_invalid")
            elif prior_epoch is not None and epoch < prior_epoch:
                errors.append(f"record_{index}_{lane}_pause_epoch_regression")
            if lane == "source":
                previous_source_epoch = epoch if isinstance(epoch, int) else previous_source_epoch
            else:
                previous_fresh_epoch = epoch if isinstance(epoch, int) else previous_fresh_epoch
        if source_epoch != fresh_epoch:
            errors.append(f"record_{index}_pause_epoch_parity_mismatch")
        lane_rng: dict[str, dict[str, Any]] = {}
        for lane, rng in (("source", record.get("source_rng")), ("fresh", record.get("fresh_rng"))):
            if not isinstance(rng, Mapping):
                errors.append(f"record_{index}_{lane}_rng_invalid")
                continue
            lane_rng[lane] = dict(rng)
            context_id = rng.get("context_id")
            snapshot_digest = rng.get("snapshot_digest")
            if not isinstance(context_id, str) or not context_id:
                errors.append(f"record_{index}_{lane}_rng_context_invalid")
            if not _is_digest(snapshot_digest):
                errors.append(f"record_{index}_{lane}_rng_snapshot_invalid")
            if not _is_digest(rng.get("checkpoint_digest")):
                errors.append(f"record_{index}_{lane}_rng_checkpoint_digest_invalid")
            if expected_rng_context is None:
                expected_rng_context = context_id if isinstance(context_id, str) else None
            elif context_id != expected_rng_context:
                errors.append(f"record_{index}_{lane}_rng_context_changed")
        if "source" in lane_rng and "fresh" in lane_rng:
            if lane_rng["source"].get("context_id") != lane_rng["fresh"].get("context_id"):
                errors.append(f"record_{index}_rng_context_parity_mismatch")
            if lane_rng["source"].get("snapshot_digest") != lane_rng["fresh"].get("snapshot_digest"):
                errors.append(f"record_{index}_rng_snapshot_parity_mismatch")
        if record.get("record_digest") != _record_digest(record):
            errors.append(f"record_{index}_record_digest_mismatch")
    return errors


def validate_worldbridge_e539_replay_trace_candidate(
    value: object,
    *,
    e533_artifact: Mapping[str, Any] | None = None,
    e538_contract: Mapping[str, Any] | None = None,
    e507_witnesses: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Validate a non-admitting trace, rechecking source evidence when supplied."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["trace_not_mapping"]}
    if set(value) != _TRACE_KEYS:
        errors.append("trace_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_mismatch")
    if value.get("authority_scope") != AUTHORITY_SCOPE:
        errors.append("authority_scope_overclaim")
    for field in _FALSE_ADMISSIONS:
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    if value.get("compensation") != {
        "required": False,
        "applied": False,
        "reason": "read_only_projection_no_live_mutation",
    }:
        errors.append("compensation_overclaim")
    if value.get("blockers") != list(BLOCKERS):
        errors.append("blockers_mismatch")
    if not isinstance(value.get("all_portable_state_parity"), bool):
        errors.append("all_portable_state_parity_invalid")
    if not isinstance(value.get("source_fresh_parity_proven"), bool):
        errors.append("source_fresh_parity_proven_invalid")
    if value.get("source_fresh_parity_proven") is not value.get("all_portable_state_parity"):
        errors.append("source_fresh_parity_proven_mismatch")
    witness_bindings = value.get("e507_witness_bindings")
    if not isinstance(witness_bindings, list):
        errors.append("e507_witness_bindings_invalid")
        witness_bindings = []
    if value.get("e507_witness_bound") is not bool(witness_bindings):
        errors.append("e507_witness_bound_mismatch")
    if e533_artifact is None:
        errors.append("e533_artifact_required")
    if e538_contract is None:
        errors.append("e538_contract_required")
    if not isinstance(e507_witnesses, Sequence) or isinstance(
        e507_witnesses, (str, bytes, bytearray)
    ):
        errors.append("e507_witnesses_invalid")
        e507_witnesses = ()
    artifact = e533_artifact
    if artifact is not None:
        artifact_validation = validate_worldbridge_e533_capture_binding(artifact)
        if artifact_validation != {"valid": True, "errors": []}:
            errors.extend("e533_" + item for item in artifact_validation["errors"])
            artifact = None
        elif value.get("e533_artifact_digest") != artifact.get("artifact_digest"):
            errors.append("e533_artifact_digest_binding_mismatch")
    if e538_contract is not None:
        contract_validation = validate_worldbridge_e538_shared_contract(e538_contract)
        if contract_validation != {"valid": True, "errors": []}:
            errors.extend("e538_" + item for item in contract_validation["errors"])
        elif value.get("e538_contract_digest") != _digest(e538_contract):
            errors.append("e538_contract_digest_binding_mismatch")
    if artifact is not None:
        if value.get("project_binding") != artifact.get("project_binding"):
            errors.append("project_binding_mismatch")
        if value.get("source_host") != _host_projection(artifact["source_capture"]):
            errors.append("source_host_binding_mismatch")
        if value.get("fresh_host") != _host_projection(artifact["fresh_capture"]):
            errors.append("fresh_host_binding_mismatch")
        errors.extend(
            _validate_record_sequence(value.get("tick_records"), trace=value, artifact=artifact)
        )
        recomputed_parity = bool(value.get("tick_records")) and all(
            isinstance(record, Mapping)
            and record.get("source_fresh_portable_state_parity") is True
            for record in value.get("tick_records", [])
        )
        if value.get("all_portable_state_parity") is not recomputed_parity:
            errors.append("all_portable_state_parity_recompute_mismatch")
        try:
            expected_bindings = _witness_bindings(
                artifact["source_capture"]["records"], e507_witnesses
            )
        except (TypeError, ValueError) as exc:
            errors.append(f"e507_witness_invalid:{exc}")
            expected_bindings = []
        if witness_bindings != expected_bindings:
            errors.append("e507_witness_binding_mismatch")
        checkpoint_to_witness = {
            item["checkpoint_digest"]: item["witness_digest"]
            for item in expected_bindings
        }
        for index, record in enumerate(value.get("tick_records", [])):
            if isinstance(record, Mapping) and record.get("e507_witness_digest") != checkpoint_to_witness.get(record.get("source_checkpoint_digest")):
                errors.append(f"record_{index}_e507_witness_binding_mismatch")
    try:
        trace_digest_matches = value.get("trace_digest") == _digest_without(
            value, "trace_digest"
        )
    except (TypeError, ValueError) as exc:
        errors.append(f"trace_digest_invalid:{exc}")
    else:
        if not trace_digest_matches:
            errors.append("trace_digest_mismatch")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "AUTHORITY_SCOPE",
    "BLOCKERS",
    "SCHEMA_VERSION",
    "STATUS",
    "build_worldbridge_e539_replay_trace_candidate",
    "validate_worldbridge_e539_replay_trace_candidate",
]
