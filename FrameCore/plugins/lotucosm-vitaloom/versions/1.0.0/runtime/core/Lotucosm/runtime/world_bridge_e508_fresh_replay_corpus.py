"""Canonical multi-tick fresh-host replay evidence for WorldBridge."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

SCHEMA_VERSION = 1
STATUS = "worldbridge_e508_fresh_replay_corpus"
REPLAY_ADMITTED = False
_FIELD_PARITY_KEYS = frozenset({
    "topology_owner_state",
    "sr_state",
    "ps_state",
    "bridge_identity_links",
    "input_state",
    "randomness_state",
    "lifecycle",
})


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _digest_without(value: Mapping[str, Any], field: str) -> str:
    payload = dict(value)
    payload[field] = ""
    return _digest(payload)


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _record_digest(record: Mapping[str, Any]) -> str:
    return _digest_without(record, "record_digest")


def project_worldbridge_e508_portable_state(
    checkpoint: Mapping[str, Any],
) -> dict[str, Any]:
    """Project a checkpoint onto E508's cross-host comparable state.

    Host-local epochs, receipt digests and process owner binding tokens remain
    validated by their owner contracts, but are not portable state.  The SR
    topology/membrane owner is an independent portable slice, so it is compared
    directly instead of being hidden inside the SR entity envelope.
    """
    if not isinstance(checkpoint, Mapping):
        raise TypeError("checkpoint must be a mapping")
    sr_state = copy.deepcopy(checkpoint.get("sr_state"))
    if isinstance(sr_state, dict):
        runtime_envelope = sr_state.get("runtime_restore_envelope")
        if isinstance(runtime_envelope, dict):
            for field in ("digest", "revision", "runtime_epoch"):
                runtime_envelope.pop(field, None)
        topology_receipt = sr_state.get("topology_receipt")
        if isinstance(topology_receipt, dict):
            for field in ("receipt_digest", "runtime_epoch"):
                topology_receipt.pop(field, None)

    randomness = copy.deepcopy(checkpoint.get("randomness_state"))
    if isinstance(randomness, dict):
        for field in ("checkpoint_digest", "runtime_epoch"):
            randomness.pop(field, None)
        process_global = randomness.get("process_global")
        if isinstance(process_global, dict):
            for field in ("capture_digest", "capture_id"):
                process_global.pop(field, None)
    lifecycle = copy.deepcopy(checkpoint.get("lifecycle"))
    if isinstance(lifecycle, dict):
        lifecycle.pop("runtime_epoch", None)
        # Gate hold/acquisition counters are process-local capture evidence,
        # not portable simulation state across a fresh host.
        lifecycle.pop("owner_gate_snapshot", None)
        binding = lifecycle.get("project_runtime_binding")
        if isinstance(binding, dict):
            binding.pop("runtime_epoch", None)
        script_evidence = lifecycle.get("script_evidence")
        if isinstance(script_evidence, dict):
            script_evidence.pop("runtime_epoch", None)
        lifecycle.pop("process_owner_binding", None)

    input_state = copy.deepcopy(checkpoint.get("input_state"))
    if isinstance(input_state, dict):
        # Transport receiver history is host-local; canonical input and cursor
        # remain the portable replay input.
        input_state.pop("shared_transport", None)
    return {
        "topology_owner_state": copy.deepcopy(
            checkpoint.get("topology_owner_state", {})
        ),
        "sr_state": sr_state,
        "ps_state": copy.deepcopy(checkpoint.get("ps_state")),
        "bridge_identity_links": copy.deepcopy(checkpoint.get("bridge_identity_links")),
        "input_state": input_state,
        "randomness_state": randomness,
        "lifecycle": lifecycle,
    }


def build_worldbridge_e508_fresh_replay_corpus(
    *,
    checkpoint_digest: str,
    source_epoch: str,
    fresh_epoch: str,
    tick_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if not _is_digest(checkpoint_digest):
        raise ValueError("checkpoint_digest_invalid")
    if not isinstance(source_epoch, str) or not source_epoch or source_epoch == "None":
        raise ValueError("source_epoch_invalid")
    if not isinstance(fresh_epoch, str) or not fresh_epoch or fresh_epoch == "None":
        raise ValueError("fresh_epoch_invalid")
    records: list[dict[str, Any]] = []
    for expected_tick, item in enumerate(tick_records, start=1):
        if not isinstance(item, Mapping):
            raise TypeError("tick_record_must_be_mapping")
        record = copy.deepcopy(dict(item))
        if record.get("tick") != expected_tick:
            raise ValueError("tick_sequence_invalid")
        evidence_errors = _field_evidence_errors(record)
        if evidence_errors:
            raise ValueError("tick_field_evidence_invalid: " + ",".join(evidence_errors))
        record["record_digest"] = ""
        record["record_digest"] = _record_digest(record)
        records.append(record)
    corpus: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "checkpoint_digest": checkpoint_digest,
        "source_epoch": source_epoch,
        "fresh_epoch": fresh_epoch,
        "distinct_runtime_epochs": source_epoch != fresh_epoch,
        "tick_count": len(records),
        "tick_records": records,
        "all_tick_parity": bool(records) and all(item.get("parity") is True for item in records),
        "cross_session_replay_parity": source_epoch != fresh_epoch and bool(records) and all(item.get("parity") is True for item in records),
        "replay_admitted": REPLAY_ADMITTED,
        "default_ready": False,
        "lossless": False,
        "corpus_digest": "",
    }
    corpus["corpus_digest"] = _digest_without(corpus, "corpus_digest")
    return copy.deepcopy(corpus)


def validate_worldbridge_e508_fresh_replay_corpus(value: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["corpus_not_mapping"]}
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("identity_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_mismatch")
    if not _is_digest(value.get("checkpoint_digest")):
        errors.append("checkpoint_digest_invalid")
    source_epoch = value.get("source_epoch")
    fresh_epoch = value.get("fresh_epoch")
    if not isinstance(source_epoch, str) or not source_epoch or source_epoch == "None":
        errors.append("source_epoch_invalid")
    if not isinstance(fresh_epoch, str) or not fresh_epoch or fresh_epoch == "None":
        errors.append("fresh_epoch_invalid")
    if source_epoch == fresh_epoch:
        errors.append("runtime_epoch_reused")
    records = value.get("tick_records")
    if not isinstance(records, list) or not records:
        errors.append("tick_records_invalid")
        records = []
    for expected_tick, record in enumerate(records, start=1):
        if not isinstance(record, Mapping):
            errors.append(f"tick_{expected_tick}_not_mapping")
            continue
        if record.get("tick") != expected_tick:
            errors.append("tick_sequence_invalid")
        if record.get("parity") is not True:
            errors.append(f"tick_{expected_tick}_parity_false")
        errors.extend(
            f"tick_{expected_tick}_{error}"
            for error in _field_evidence_errors(record)
        )
        for field in ("sr_state_digest", "ps_state_digest", "input_state_digest", "randomness_state_digest", "bridge_identity_digest", "baseline_digest", "restored_digest"):
            if not _is_digest(record.get(field)):
                errors.append(f"tick_{expected_tick}_{field}_invalid")
        if record.get("baseline_digest") != record.get("restored_digest"):
            errors.append(f"tick_{expected_tick}_state_digest_mismatch")
        if record.get("record_digest") != _record_digest(record):
            errors.append(f"tick_{expected_tick}_record_digest_mismatch")
    if value.get("tick_count") != len(records):
        errors.append("tick_count_mismatch")
    expected_all = bool(records) and all(item.get("parity") is True for item in records if isinstance(item, Mapping))
    if value.get("all_tick_parity") is not expected_all:
        errors.append("all_tick_parity_mismatch")
    expected_cross = source_epoch != fresh_epoch and expected_all
    if value.get("cross_session_replay_parity") is not expected_cross:
        errors.append("cross_session_parity_mismatch")
    for field in ("replay_admitted", "default_ready", "lossless"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    if value.get("corpus_digest") != _digest_without(value, "corpus_digest"):
        errors.append("corpus_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def _field_evidence_errors(record: Mapping[str, Any]) -> list[str]:
    """Reject contradictory detail when a producer includes per-field evidence.

    Older corpus producers did not include ``field_parity`` or
    ``field_diff_paths``. Those records remain readable, while current records
    cannot claim aggregate parity when their detailed evidence reports drift.
    """
    errors: list[str] = []
    field_parity = record.get("field_parity")
    if field_parity is not None:
        if not isinstance(field_parity, Mapping):
            errors.append("field_parity_not_mapping")
        elif set(field_parity) != _FIELD_PARITY_KEYS:
            errors.append("field_parity_keys_mismatch")
        elif any(type(value) is not bool for value in field_parity.values()):
            errors.append("field_parity_value_invalid")
        elif record.get("parity") is not all(field_parity.values()):
            errors.append("field_parity_aggregate_mismatch")

    field_diff_paths = record.get("field_diff_paths")
    if field_diff_paths is not None:
        if not isinstance(field_diff_paths, Mapping):
            errors.append("field_diff_paths_not_mapping")
        elif any(key not in _FIELD_PARITY_KEYS for key in field_diff_paths):
            errors.append("field_diff_paths_keys_invalid")
        elif any(
            not isinstance(paths, list)
            or any(not isinstance(path, str) or not path for path in paths)
            for paths in field_diff_paths.values()
        ):
            errors.append("field_diff_paths_value_invalid")
        elif record.get("parity") is True and any(field_diff_paths.values()):
            errors.append("field_diff_paths_aggregate_mismatch")
    return errors


def encode_worldbridge_e508_fresh_replay_corpus(value: Mapping[str, Any]) -> bytes:
    validation = validate_worldbridge_e508_fresh_replay_corpus(value)
    if validation["valid"] is not True:
        raise ValueError("invalid E508 corpus: " + ",".join(validation["errors"]))
    return _canonical(value)


def decode_worldbridge_e508_fresh_replay_corpus(encoded: bytes | bytearray | memoryview) -> dict[str, Any]:
    if not isinstance(encoded, (bytes, bytearray, memoryview)):
        raise TypeError("encoded corpus must be bytes-like")
    raw = bytes(encoded)
    try:
        parsed = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_constant)
    except (UnicodeDecodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("encoded E508 corpus is not strict JSON") from exc
    if not isinstance(parsed, dict) or validate_worldbridge_e508_fresh_replay_corpus(parsed)["valid"] is not True:
        raise ValueError("invalid E508 corpus")
    if _canonical(parsed) != raw:
        raise ValueError("encoded E508 corpus is not canonical JSON")
    return copy.deepcopy(parsed)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = item
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant rejected: {value}")


__all__ = [
    "build_worldbridge_e508_fresh_replay_corpus",
    "decode_worldbridge_e508_fresh_replay_corpus",
    "encode_worldbridge_e508_fresh_replay_corpus",
    "project_worldbridge_e508_portable_state",
    "validate_worldbridge_e508_fresh_replay_corpus",
]
