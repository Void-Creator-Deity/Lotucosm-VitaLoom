"""Fresh-host provenance comparison for a quarantined topology corpus."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from .world_bridge_dynamic_topology_corpus import (
    validate_worldbridge_dynamic_topology_corpus,
)
from .world_bridge_dynamic_topology_receipt import (
    validate_worldbridge_dynamic_topology_receipt,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_dynamic_topology_fresh_provenance"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _is_digest(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def build_worldbridge_dynamic_topology_fresh_provenance(
    *,
    source_corpus: Mapping[str, Any],
    source_receipts: Sequence[Mapping[str, Any]],
    fresh_runtime_epoch: str,
    fresh_events: Sequence[Mapping[str, Any]],
    old_receipt_rejected: bool,
    old_receipt_restore_non_mutating: bool,
    old_receipt_restore_error: str,
) -> dict[str, Any]:
    source_validation = validate_worldbridge_dynamic_topology_corpus(source_corpus)
    if source_validation != {"valid": True, "errors": []}:
        raise ValueError("source topology corpus invalid: " + ",".join(source_validation["errors"]))
    source_epoch = source_corpus["runtime_epoch"]
    if not isinstance(fresh_runtime_epoch, str) or not fresh_runtime_epoch.strip():
        raise ValueError("fresh runtime epoch must be non-empty")
    if fresh_runtime_epoch == source_epoch:
        raise ValueError("fresh runtime epoch must differ from source")
    if old_receipt_rejected is not True:
        raise ValueError("source receipt rejection is required")
    if old_receipt_restore_non_mutating is not True:
        raise ValueError("old receipt restore must be non-mutating")
    if not isinstance(old_receipt_restore_error, str) or "dynamic topology receipt rejected" not in old_receipt_restore_error:
        raise ValueError("source receipt restore rejection diagnostic missing")
    source_events = source_corpus["events"]
    source_receipt_records = [copy.deepcopy(dict(receipt)) for receipt in source_receipts]
    if len(source_receipt_records) != len(source_events):
        raise ValueError("source topology receipt count mismatch")
    records = [copy.deepcopy(dict(event)) for event in fresh_events]
    if len(records) != len(source_events):
        raise ValueError("fresh topology event count mismatch")
    event_pairs: list[dict[str, Any]] = []
    for index, (source_event, source_receipt, fresh_event) in enumerate(zip(source_events, source_receipt_records, records)):
        source_receipt_validation = validate_worldbridge_dynamic_topology_receipt(
            source_receipt, runtime_epoch=source_epoch
        )
        if source_receipt_validation != {"valid": True, "errors": []}:
            raise ValueError("source topology receipt invalid: " + ",".join(source_receipt_validation["errors"]))
        if source_receipt.get("receipt_digest") != source_event.get("receipt_digest"):
            raise ValueError("source topology receipt digest mismatch")
        if source_receipt.get("structure_fingerprint") != source_event.get("structure_fingerprint"):
            raise ValueError("source topology receipt structure mismatch")
        stale_validation = validate_worldbridge_dynamic_topology_receipt(
            source_receipt, runtime_epoch=fresh_runtime_epoch
        )
        if stale_validation["valid"] is not False or "receipt_runtime_epoch_mismatch" not in stale_validation["errors"]:
            raise ValueError("source topology receipt was not epoch-rejected")
        if fresh_event.get("event_index") != index:
            raise ValueError("fresh topology event order mismatch")
        if fresh_event.get("runtime_epoch") != fresh_runtime_epoch:
            raise ValueError("fresh topology event epoch mismatch")
        if fresh_event.get("kind") != source_event.get("kind"):
            raise ValueError("fresh topology event kind mismatch")
        receipt = fresh_event.get("topology_receipt")
        receipt_validation = validate_worldbridge_dynamic_topology_receipt(
            receipt, runtime_epoch=fresh_runtime_epoch
        )
        if receipt_validation != {"valid": True, "errors": []}:
            raise ValueError("fresh topology receipt invalid: " + ",".join(receipt_validation["errors"]))
        if receipt.get("structure_fingerprint") != fresh_event.get("structure_fingerprint"):
            raise ValueError("fresh topology receipt structure mismatch")
        if receipt.get("receipt_digest") != fresh_event.get("receipt_digest"):
            raise ValueError("fresh topology receipt digest mismatch")
        if source_event.get("structure_fingerprint") != fresh_event.get("structure_fingerprint"):
            raise ValueError("fresh topology structure parity mismatch")
        if source_event.get("node_ids") != fresh_event.get("node_ids"):
            raise ValueError("fresh topology node set parity mismatch")
        if source_event.get("receipt_digest") == fresh_event.get("receipt_digest"):
            raise ValueError("source topology receipt was reused by fresh host")
        event_pairs.append({
            "event_index": index,
            "kind": fresh_event["kind"],
            "source_structure_fingerprint": source_event["structure_fingerprint"],
            "fresh_structure_fingerprint": fresh_event["structure_fingerprint"],
            "source_receipt_digest": source_event["receipt_digest"],
            "source_receipt": source_receipt,
            "source_receipt_fresh_epoch_rejection_errors": copy.deepcopy(stale_validation["errors"]),
            "fresh_receipt_digest": fresh_event["receipt_digest"],
            "node_ids": copy.deepcopy(fresh_event["node_ids"]),
            "fresh_receipt": copy.deepcopy(dict(receipt)),
        })
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "source_corpus": copy.deepcopy(dict(source_corpus)),
        "source_corpus_digest": source_corpus["corpus_digest"],
        "source_runtime_epoch": source_epoch,
        "fresh_runtime_epoch": fresh_runtime_epoch,
        "source_receipt_rejected": True,
        "source_receipt_restore_non_mutating": True,
        "source_receipt_restore_error": old_receipt_restore_error,
        "events": event_pairs,
        "structure_parity": True,
        "node_set_parity": True,
        "fresh_receipts_valid": True,
        "replay_admitted": False,
        "default_ready": False,
        "artifact_digest": "",
    }
    artifact["artifact_digest"] = _digest(artifact)
    return copy.deepcopy(artifact)


def validate_worldbridge_dynamic_topology_fresh_provenance(value: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["artifact_must_be_mapping"]}
    required = {
        "schema_version", "status", "source_corpus", "source_corpus_digest",
        "source_runtime_epoch", "fresh_runtime_epoch", "source_receipt_rejected",
        "source_receipt_restore_non_mutating", "source_receipt_restore_error",
        "events", "structure_parity", "node_set_parity", "fresh_receipts_valid",
        "replay_admitted", "default_ready", "artifact_digest",
    }
    if set(value) != required:
        errors.append("artifact_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("artifact_identity_mismatch")
    source = value.get("source_corpus")
    source_validation = validate_worldbridge_dynamic_topology_corpus(source)
    if source_validation != {"valid": True, "errors": []}:
        errors.append("source_corpus_invalid")
    elif value.get("source_corpus_digest") != source.get("corpus_digest"):
        errors.append("source_corpus_digest_mismatch")
    if value.get("source_runtime_epoch") != (source.get("runtime_epoch") if isinstance(source, Mapping) else None):
        errors.append("source_runtime_epoch_mismatch")
    source_epoch = value.get("source_runtime_epoch")
    fresh_epoch = value.get("fresh_runtime_epoch")
    if not isinstance(source_epoch, str) or not source_epoch.strip():
        errors.append("source_epoch_invalid")
    if not isinstance(fresh_epoch, str) or not fresh_epoch.strip():
        errors.append("fresh_epoch_invalid")
    if source_epoch == fresh_epoch:
        errors.append("runtime_epoch_not_distinct")
    if value.get("source_receipt_rejected") is not True:
        errors.append("source_receipt_rejection_required")
    if value.get("source_receipt_restore_non_mutating") is not True:
        errors.append("source_receipt_restore_mutation_overclaim")
    if not isinstance(value.get("source_receipt_restore_error"), str) or "dynamic topology receipt rejected" not in value.get("source_receipt_restore_error", ""):
        errors.append("source_receipt_restore_diagnostic_missing")
    source_events = source.get("events", []) if isinstance(source, Mapping) else []
    events = value.get("events")
    if not isinstance(events, list) or len(events) != len(source_events):
        errors.append("event_count_mismatch")
    else:
        for index, event in enumerate(events):
            source_event = source_events[index]
            if not isinstance(event, Mapping):
                errors.append(f"event_{index}_invalid")
                continue
            if event.get("event_index") != index or event.get("kind") != source_event.get("kind"):
                errors.append(f"event_{index}_identity_mismatch")
            if event.get("source_structure_fingerprint") != source_event.get("structure_fingerprint"):
                errors.append(f"event_{index}_source_structure_mismatch")
            if event.get("fresh_structure_fingerprint") != event.get("source_structure_fingerprint"):
                errors.append(f"event_{index}_structure_parity_mismatch")
            if event.get("source_receipt_digest") != source_event.get("receipt_digest"):
                errors.append(f"event_{index}_source_receipt_mismatch")
            source_receipt = event.get("source_receipt")
            source_receipt_validation = validate_worldbridge_dynamic_topology_receipt(
                source_receipt, runtime_epoch=source_epoch if isinstance(source_epoch, str) else None
            )
            if source_receipt_validation != {"valid": True, "errors": []}:
                errors.append(f"event_{index}_source_receipt_invalid")
            else:
                if source_receipt.get("receipt_digest") != event.get("source_receipt_digest"):
                    errors.append(f"event_{index}_source_receipt_digest_mismatch")
                stale_validation = validate_worldbridge_dynamic_topology_receipt(
                    source_receipt, runtime_epoch=fresh_epoch if isinstance(fresh_epoch, str) else None
                )
                if (
                    stale_validation["valid"] is not False
                    or "receipt_runtime_epoch_mismatch" not in stale_validation["errors"]
                    or event.get("source_receipt_fresh_epoch_rejection_errors") != stale_validation["errors"]
                ):
                    errors.append(f"event_{index}_source_receipt_epoch_rejection_missing")
            if event.get("fresh_receipt_digest") == event.get("source_receipt_digest"):
                errors.append(f"event_{index}_receipt_reused")
            if event.get("node_ids") != source_event.get("node_ids"):
                errors.append(f"event_{index}_node_set_mismatch")
            receipt = event.get("fresh_receipt")
            receipt_validation = validate_worldbridge_dynamic_topology_receipt(
                receipt, runtime_epoch=fresh_epoch if isinstance(fresh_epoch, str) else None
            )
            if receipt_validation != {"valid": True, "errors": []}:
                errors.append(f"event_{index}_fresh_receipt_invalid")
            elif (
                receipt.get("receipt_digest") != event.get("fresh_receipt_digest")
                or receipt.get("structure_fingerprint") != event.get("fresh_structure_fingerprint")
            ):
                errors.append(f"event_{index}_fresh_receipt_binding_mismatch")
    for field in ("structure_parity", "node_set_parity", "fresh_receipts_valid"):
        if value.get(field) is not True:
            errors.append(f"{field}_required")
    if value.get("replay_admitted") is not False or value.get("default_ready") is not False:
        errors.append("admission_overclaim")
    candidate = dict(value)
    candidate["artifact_digest"] = ""
    try:
        expected_digest = _digest(candidate)
    except (TypeError, ValueError, OverflowError):
        expected_digest = None
        errors.append("artifact_not_canonical")
    if value.get("artifact_digest") != expected_digest:
        errors.append("artifact_digest_mismatch")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "build_worldbridge_dynamic_topology_fresh_provenance",
    "validate_worldbridge_dynamic_topology_fresh_provenance",
]
