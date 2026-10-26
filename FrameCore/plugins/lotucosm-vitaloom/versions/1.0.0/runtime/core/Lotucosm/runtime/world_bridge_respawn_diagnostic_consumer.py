# -*- coding: utf-8 -*-
"""Paired, read-only E227/E228 diagnostic consumer receipt seam."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_respawn_artifact_diagnostics import (
    MEDIA_TYPE as PROJECTION_MEDIA_TYPE,
    decode_worldbridge_respawn_artifact_diagnostic_projection,
    validate_worldbridge_respawn_artifact_diagnostic_projection,
)
from core.Lotucosm.runtime.world_bridge_respawn_artifact_inspection import (
    ENCODING,
    MEDIA_TYPE as INSPECTION_MEDIA_TYPE,
    decode_worldbridge_respawn_artifact_inspection,
    validate_worldbridge_respawn_artifact_inspection,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_respawn_paired_diagnostic_consumer_receipt"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-respawn-diagnostic-receipt+json"
MAX_RECEIPT_BYTES = 8 * 1024
DO_NOT_CLAIM = (
    "diagnostic_receipt_replay_input",
    "diagnostic_receipt_checkpoint_state",
    "diagnostic_receipt_restore_authority",
    "diagnostic_receipt_mutation_execution",
    "diagnostic_receipt_live_runtime_state",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)
_STATIC_POLICIES = {
    "consumer_scope": "validated_inspection_projection_pair_only",
    "read_only": True,
    "source_projection_parity_valid": True,
    "replay_input": False,
    "checkpoint_state": False,
    "restore_performed": False,
    "mutation_executed": False,
    "live_runtime_state": False,
    "replay_admitted": False,
    "default_ready": False,
}
_REQUIRED_KEYS = {
    "schema_version",
    "status",
    "media_type",
    "encoding",
    "canonical_json",
    "source_inspection_media_type",
    "source_projection_media_type",
    "source_artifact_id",
    "source_artifact_digest",
    "source_inspection_digest",
    "source_projection_digest",
    "context_id",
    "stream_roles",
    "outcome",
    "admitted",
    "ordered_steps",
    "mutation_stream_consumed",
    "snapshot_digests",
    "gene_counts",
    "consumer_scope",
    "read_only",
    "source_projection_parity_valid",
    "replay_input",
    "checkpoint_state",
    "restore_performed",
    "mutation_executed",
    "live_runtime_state",
    "replay_admitted",
    "default_ready",
    "do_not_claim",
    "receipt_digest",
}


def consume_worldbridge_respawn_diagnostic_pair(
    inspection: Mapping[str, Any] | bytes | bytearray | memoryview,
    projection: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Admit one matching E227/E228 pair and return a compact diagnostic-only receipt."""
    source_inspection = _validated_inspection(inspection)
    source_projection = _validated_projection(projection)
    parity = validate_worldbridge_respawn_artifact_diagnostic_projection(
        source_projection, inspection=source_inspection
    )
    if not parity["valid"]:
        raise ValueError("inspection/projection diagnostic pair rejected: " + ",".join(parity["errors"]))
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "source_inspection_media_type": INSPECTION_MEDIA_TYPE,
        "source_projection_media_type": PROJECTION_MEDIA_TYPE,
        "source_artifact_id": source_inspection["source_artifact_id"],
        "source_artifact_digest": source_inspection["source_artifact_digest"],
        "source_inspection_digest": source_inspection["inspection_digest"],
        "source_projection_digest": source_projection["projection_digest"],
        "context_id": source_inspection["context_id"],
        "stream_roles": copy.deepcopy(source_projection["stream_roles"]),
        "outcome": source_inspection["outcome"],
        "admitted": source_inspection["admitted"],
        "ordered_steps": copy.deepcopy(source_inspection["ordered_steps"]),
        "mutation_stream_consumed": source_inspection["mutation_stream_consumed"],
        "snapshot_digests": copy.deepcopy(source_inspection["snapshot_digests"]),
        "gene_counts": copy.deepcopy(source_projection["gene_counts"]),
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    receipt["receipt_digest"] = _receipt_digest(receipt)
    validation = validate_worldbridge_respawn_diagnostic_consumer_receipt(
        receipt, inspection=source_inspection, projection=source_projection
    )
    if not validation["valid"]:
        raise RuntimeError("constructed invalid diagnostic consumer receipt: " + ",".join(validation["errors"]))
    return copy.deepcopy(receipt)


def validate_worldbridge_respawn_diagnostic_consumer_receipt(
    receipt: object,
    *,
    inspection: Mapping[str, Any] | bytes | bytearray | memoryview | None = None,
    projection: Mapping[str, Any] | bytes | bytearray | memoryview | None = None,
) -> dict[str, Any]:
    """Validate bounded receipt structure and optional mandatory-pair source parity."""
    errors: list[str] = []
    if not isinstance(receipt, Mapping):
        return {"valid": False, "errors": ["receipt_not_mapping"]}
    try:
        value = dict(receipt)
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["receipt_mapping_copy_failed"]}
    if set(value) != _REQUIRED_KEYS:
        errors.append("receipt_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("media_type") != MEDIA_TYPE:
        errors.append("media_type_mismatch")
    if value.get("encoding") != ENCODING:
        errors.append("encoding_mismatch")
    if value.get("canonical_json") is not True:
        errors.append("canonical_json_mismatch")
    if value.get("source_inspection_media_type") != INSPECTION_MEDIA_TYPE:
        errors.append("source_inspection_media_type_mismatch")
    if value.get("source_projection_media_type") != PROJECTION_MEDIA_TYPE:
        errors.append("source_projection_media_type_mismatch")
    for field in ("source_artifact_id", "context_id"):
        if not _clean_nonempty_string(value.get(field)):
            errors.append(f"{field}_invalid")
    for field in ("source_artifact_digest", "source_inspection_digest", "source_projection_digest"):
        if not _is_sha256(value.get(field)):
            errors.append(f"{field}_invalid")
    _validate_projection_facts(value, errors)
    for field, expected in _STATIC_POLICIES.items():
        if value.get(field) != expected or type(value.get(field)) is not type(expected):
            errors.append(f"{field}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    if not _is_sha256(value.get("receipt_digest")):
        errors.append("receipt_digest_invalid")
    else:
        try:
            if value["receipt_digest"] != _receipt_digest(value):
                errors.append("receipt_digest_mismatch")
        except (TypeError, ValueError, OverflowError):
            errors.append("receipt_digest_uncomputable")
    try:
        if len(_canonical_json_bytes(value)) > MAX_RECEIPT_BYTES:
            errors.append("receipt_exceeds_bound")
    except (TypeError, ValueError, OverflowError):
        errors.append("receipt_not_canonicalizable")

    if (inspection is None) != (projection is None):
        errors.append("source_pair_incomplete")
    elif inspection is not None and projection is not None:
        try:
            source_inspection = _validated_inspection(inspection)
            source_projection = _validated_projection(projection)
        except (TypeError, ValueError):
            errors.append("source_pair_invalid")
        else:
            parity = validate_worldbridge_respawn_artifact_diagnostic_projection(
                source_projection, inspection=source_inspection
            )
            if not parity["valid"]:
                errors.append("source_projection_parity_invalid")
            errors.extend(_pair_parity_errors(value, source_inspection, source_projection))
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_respawn_diagnostic_consumer_receipt(
    receipt: Mapping[str, Any],
) -> bytes:
    """Encode a bounded validated receipt; this is never a replay/checkpoint format."""
    validation = validate_worldbridge_respawn_diagnostic_consumer_receipt(receipt)
    if not validation["valid"]:
        raise ValueError("invalid respawn diagnostic consumer receipt: " + ",".join(validation["errors"]))
    encoded = _canonical_json_bytes(dict(receipt))
    if len(encoded) > MAX_RECEIPT_BYTES:
        raise OverflowError("respawn diagnostic consumer receipt exceeds bound")
    return encoded


def decode_worldbridge_respawn_diagnostic_consumer_receipt(
    encoded: bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Decode only canonical bounded diagnostic-consumer receipt bytes."""
    if not isinstance(encoded, (bytes, bytearray, memoryview)):
        raise TypeError("encoded diagnostic consumer receipt must be bytes-like")
    raw = bytes(encoded)
    if not raw or len(raw) > MAX_RECEIPT_BYTES:
        raise ValueError("encoded diagnostic consumer receipt is empty or exceeds bound")
    try:
        parsed = json.loads(
            raw.decode(ENCODING, errors="strict"),
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("encoded diagnostic consumer receipt is not strict UTF-8 JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("encoded diagnostic consumer receipt root must be an object")
    validation = validate_worldbridge_respawn_diagnostic_consumer_receipt(parsed)
    if not validation["valid"]:
        raise ValueError("invalid diagnostic consumer receipt: " + ",".join(validation["errors"]))
    if _canonical_json_bytes(parsed) != raw:
        raise ValueError("encoded diagnostic consumer receipt is not canonical JSON")
    return copy.deepcopy(parsed)


def build_worldbridge_respawn_diagnostic_consumer_contract() -> dict[str, Any]:
    """Build deterministic status evidence through the mandatory-pair consumer seam."""
    from core.Lotucosm.runtime.world_bridge_respawn_artifact_diagnostics import (
        build_worldbridge_respawn_artifact_diagnostic_projection_contract,
    )
    from core.Lotucosm.runtime.world_bridge_respawn_artifact_inspection import (
        build_worldbridge_respawn_artifact_inspection_contract,
    )

    inspection = build_worldbridge_respawn_artifact_inspection_contract()["summary"]
    projection = build_worldbridge_respawn_artifact_diagnostic_projection_contract()["projection"]
    receipt = consume_worldbridge_respawn_diagnostic_pair(inspection, projection)
    encoded = encode_worldbridge_respawn_diagnostic_consumer_receipt(receipt)
    decoded = decode_worldbridge_respawn_diagnostic_consumer_receipt(encoded)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_respawn_diagnostic_consumer_contract",
        "contract_valid": validate_worldbridge_respawn_diagnostic_consumer_receipt(
            receipt, inspection=inspection, projection=projection
        )["valid"],
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "max_receipt_bytes": MAX_RECEIPT_BYTES,
        "round_trip_equal": decoded == receipt,
        "receipt": copy.deepcopy(receipt),
        "requires_inspection_projection_pair": True,
        "accepts_raw_artifact": False,
        "restores_streams": False,
        "executes_mutation": False,
        "replay_admitted": False,
        "default_ready": False,
        "do_not_claim": list(DO_NOT_CLAIM),
    }


def _validated_inspection(
    inspection: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    if isinstance(inspection, (bytes, bytearray, memoryview)):
        return decode_worldbridge_respawn_artifact_inspection(inspection)
    validation = validate_worldbridge_respawn_artifact_inspection(inspection)
    if not validation["valid"]:
        raise ValueError("invalid worldbridge respawn inspection summary: " + ",".join(validation["errors"]))
    return copy.deepcopy(dict(inspection))


def _validated_projection(
    projection: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    if isinstance(projection, (bytes, bytearray, memoryview)):
        return decode_worldbridge_respawn_artifact_diagnostic_projection(projection)
    validation = validate_worldbridge_respawn_artifact_diagnostic_projection(projection)
    if not validation["valid"]:
        raise ValueError("invalid worldbridge respawn diagnostic projection: " + ",".join(validation["errors"]))
    return copy.deepcopy(dict(projection))


def _validate_projection_facts(value: Mapping[str, Any], errors: list[str]) -> None:
    stream_roles = value.get("stream_roles")
    if not isinstance(stream_roles, Mapping) or set(stream_roles) != {"decision", "mutation", "family"}:
        errors.append("stream_roles_structure_invalid")
    else:
        if not _clean_nonempty_string(stream_roles.get("decision")):
            errors.append("decision_stream_invalid")
        if not _clean_nonempty_string(stream_roles.get("mutation")):
            errors.append("mutation_stream_invalid")
        if stream_roles.get("family") != "python_random":
            errors.append("stream_family_mismatch")
    admitted = value.get("admitted")
    if type(admitted) is not bool:
        errors.append("admitted_invalid")
    elif value.get("outcome") != ("admitted_mutation" if admitted else "rejected_no_mutation"):
        errors.append("outcome_mismatch")
    if value.get("ordered_steps") != (["decision", "mutation"] if admitted is True else ["decision"]):
        errors.append("ordered_steps_mismatch")
    if type(value.get("mutation_stream_consumed")) is not bool or value.get("mutation_stream_consumed") is not (admitted is True):
        errors.append("mutation_stream_consumed_mismatch")
    snapshot_digests = value.get("snapshot_digests")
    if not isinstance(snapshot_digests, Mapping) or set(snapshot_digests) != {"before", "after_decision", "after"}:
        errors.append("snapshot_digests_structure_invalid")
    else:
        for key, digest in snapshot_digests.items():
            if not _is_sha256(digest):
                errors.append(f"snapshot_digest_{key}_invalid")
    gene_counts = value.get("gene_counts")
    if not isinstance(gene_counts, Mapping) or set(gene_counts) != {"parent", "child", "delta"}:
        errors.append("gene_counts_structure_invalid")
    else:
        for key, count in gene_counts.items():
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                errors.append(f"gene_count_{key}_invalid")


def _pair_parity_errors(
    receipt: Mapping[str, Any], inspection: Mapping[str, Any], projection: Mapping[str, Any]
) -> list[str]:
    expected = {
        "source_inspection_media_type": INSPECTION_MEDIA_TYPE,
        "source_projection_media_type": PROJECTION_MEDIA_TYPE,
        "source_artifact_id": inspection["source_artifact_id"],
        "source_artifact_digest": inspection["source_artifact_digest"],
        "source_inspection_digest": inspection["inspection_digest"],
        "source_projection_digest": projection["projection_digest"],
        "context_id": inspection["context_id"],
        "stream_roles": projection["stream_roles"],
        "outcome": inspection["outcome"],
        "admitted": inspection["admitted"],
        "ordered_steps": inspection["ordered_steps"],
        "mutation_stream_consumed": inspection["mutation_stream_consumed"],
        "snapshot_digests": inspection["snapshot_digests"],
        "gene_counts": projection["gene_counts"],
    }
    return [f"pair_parity_{field}_mismatch" for field, expected_value in expected.items() if receipt.get(field) != expected_value]


def _receipt_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical.pop("receipt_digest", None)
    return hashlib.sha256(_canonical_json_bytes(canonical)).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode(ENCODING)


def _clean_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant rejected: {value}")


__all__ = [
    "MAX_RECEIPT_BYTES",
    "MEDIA_TYPE",
    "build_worldbridge_respawn_diagnostic_consumer_contract",
    "consume_worldbridge_respawn_diagnostic_pair",
    "decode_worldbridge_respawn_diagnostic_consumer_receipt",
    "encode_worldbridge_respawn_diagnostic_consumer_receipt",
    "validate_worldbridge_respawn_diagnostic_consumer_receipt",
]
