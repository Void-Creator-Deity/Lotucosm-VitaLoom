# -*- coding: utf-8 -*-
"""Bounded, read-only diagnostic projection for E227 inspection summaries."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_respawn_artifact_inspection import (
    ENCODING,
    MEDIA_TYPE as INSPECTION_MEDIA_TYPE,
    decode_worldbridge_respawn_artifact_inspection,
    validate_worldbridge_respawn_artifact_inspection,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_respawn_artifact_bounded_diagnostic_projection"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-respawn-diagnostic-projection+json"
MAX_PROJECTION_BYTES = 16 * 1024
DO_NOT_CLAIM = (
    "diagnostic_projection_replay_input",
    "diagnostic_projection_checkpoint_state",
    "diagnostic_projection_restore_authority",
    "diagnostic_projection_mutation_execution",
    "diagnostic_projection_live_runtime_state",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)
_STATIC_POLICIES = {
    "diagnostic_scope": "validated_inspection_projection_only",
    "read_only": True,
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
    "source_artifact_id",
    "source_artifact_digest",
    "source_inspection_digest",
    "context_id",
    "stream_roles",
    "outcome",
    "admitted",
    "ordered_steps",
    "mutation_stream_consumed",
    "snapshot_digests",
    "gene_counts",
    "diagnostic_scope",
    "read_only",
    "replay_input",
    "checkpoint_state",
    "restore_performed",
    "mutation_executed",
    "live_runtime_state",
    "replay_admitted",
    "default_ready",
    "do_not_claim",
    "projection_digest",
}


def project_worldbridge_respawn_artifact_inspection(
    inspection: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Project one validated E227 summary into compact non-executable diagnostics."""
    source = _validated_inspection(inspection)
    projection: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "source_inspection_media_type": INSPECTION_MEDIA_TYPE,
        "source_artifact_id": source["source_artifact_id"],
        "source_artifact_digest": source["source_artifact_digest"],
        "source_inspection_digest": source["inspection_digest"],
        "context_id": source["context_id"],
        "stream_roles": {
            "decision": source["decision_stream_name"],
            "mutation": source["mutation_stream_name"],
            "family": source["stream_family"],
        },
        "outcome": source["outcome"],
        "admitted": source["admitted"],
        "ordered_steps": copy.deepcopy(source["ordered_steps"]),
        "mutation_stream_consumed": source["mutation_stream_consumed"],
        "snapshot_digests": copy.deepcopy(source["snapshot_digests"]),
        "gene_counts": {
            "parent": source["parent_gene_count"],
            "child": source["child_gene_count"],
            "delta": source["delta_gene_count"],
        },
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    projection["projection_digest"] = _projection_digest(projection)
    validation = validate_worldbridge_respawn_artifact_diagnostic_projection(
        projection, inspection=source
    )
    if not validation["valid"]:
        raise RuntimeError(
            "constructed invalid respawn diagnostic projection: " + ",".join(validation["errors"])
        )
    return copy.deepcopy(projection)


def validate_worldbridge_respawn_artifact_diagnostic_projection(
    projection: object,
    *,
    inspection: Mapping[str, Any] | bytes | bytearray | memoryview | None = None,
) -> dict[str, Any]:
    """Validate exact projection structure, integrity, bounds, and optional source parity."""
    errors: list[str] = []
    if not isinstance(projection, Mapping):
        return {"valid": False, "errors": ["projection_not_mapping"]}
    try:
        value = dict(projection)
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["projection_mapping_copy_failed"]}

    if set(value) != _REQUIRED_KEYS:
        errors.append("projection_keys_mismatch")
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
    for field in ("source_artifact_id", "context_id"):
        if not _clean_nonempty_string(value.get(field)):
            errors.append(f"{field}_invalid")
    for field in ("source_artifact_digest", "source_inspection_digest"):
        if not _is_sha256(value.get(field)):
            errors.append(f"{field}_invalid")

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

    for field, expected in _STATIC_POLICIES.items():
        if value.get(field) != expected or type(value.get(field)) is not type(expected):
            errors.append(f"{field}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    if not _is_sha256(value.get("projection_digest")):
        errors.append("projection_digest_invalid")
    else:
        try:
            if value["projection_digest"] != _projection_digest(value):
                errors.append("projection_digest_mismatch")
        except (TypeError, ValueError, OverflowError):
            errors.append("projection_digest_uncomputable")
    try:
        canonical = _canonical_json_bytes(value)
        if len(canonical) > MAX_PROJECTION_BYTES:
            errors.append("projection_exceeds_bound")
    except (TypeError, ValueError, OverflowError):
        errors.append("projection_not_canonicalizable")

    if inspection is not None:
        try:
            source = _validated_inspection(inspection)
        except (TypeError, ValueError) as exc:
            errors.append("source_inspection_invalid")
        else:
            errors.extend(_parity_errors(value, source))
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_respawn_artifact_diagnostic_projection(
    projection: Mapping[str, Any],
) -> bytes:
    """Encode a validated bounded projection; this is not persistence or replay input."""
    validation = validate_worldbridge_respawn_artifact_diagnostic_projection(projection)
    if not validation["valid"]:
        raise ValueError("invalid respawn diagnostic projection: " + ",".join(validation["errors"]))
    encoded = _canonical_json_bytes(dict(projection))
    if len(encoded) > MAX_PROJECTION_BYTES:
        raise OverflowError("respawn diagnostic projection exceeds bound")
    return encoded


def decode_worldbridge_respawn_artifact_diagnostic_projection(
    encoded: bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Decode only canonical bounded diagnostic-projection bytes."""
    if not isinstance(encoded, (bytes, bytearray, memoryview)):
        raise TypeError("encoded respawn diagnostic projection must be bytes-like")
    raw = bytes(encoded)
    if not raw or len(raw) > MAX_PROJECTION_BYTES:
        raise ValueError("encoded respawn diagnostic projection is empty or exceeds bound")
    try:
        parsed = json.loads(
            raw.decode(ENCODING, errors="strict"),
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("encoded respawn diagnostic projection is not strict UTF-8 JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("encoded respawn diagnostic projection root must be an object")
    validation = validate_worldbridge_respawn_artifact_diagnostic_projection(parsed)
    if not validation["valid"]:
        raise ValueError("invalid respawn diagnostic projection: " + ",".join(validation["errors"]))
    if _canonical_json_bytes(parsed) != raw:
        raise ValueError("encoded respawn diagnostic projection is not canonical JSON")
    return copy.deepcopy(parsed)


def build_worldbridge_respawn_artifact_diagnostic_projection_contract() -> dict[str, Any]:
    """Build deterministic status evidence through E227 then this projection seam."""
    from core.Lotucosm.runtime.world_bridge_respawn_artifact_inspection import (
        build_worldbridge_respawn_artifact_inspection_contract,
    )

    inspection = build_worldbridge_respawn_artifact_inspection_contract()["summary"]
    projection = project_worldbridge_respawn_artifact_inspection(inspection)
    encoded = encode_worldbridge_respawn_artifact_diagnostic_projection(projection)
    decoded = decode_worldbridge_respawn_artifact_diagnostic_projection(encoded)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_respawn_artifact_diagnostic_projection_contract",
        "contract_valid": validate_worldbridge_respawn_artifact_diagnostic_projection(
            projection, inspection=inspection
        )["valid"],
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "max_projection_bytes": MAX_PROJECTION_BYTES,
        "round_trip_equal": decoded == projection,
        "projection": copy.deepcopy(projection),
        "inspection_consumer_only": True,
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


def _parity_errors(projection: Mapping[str, Any], inspection: Mapping[str, Any]) -> list[str]:
    expected = {
        "source_inspection_media_type": INSPECTION_MEDIA_TYPE,
        "source_artifact_id": inspection["source_artifact_id"],
        "source_artifact_digest": inspection["source_artifact_digest"],
        "source_inspection_digest": inspection["inspection_digest"],
        "context_id": inspection["context_id"],
        "stream_roles": {
            "decision": inspection["decision_stream_name"],
            "mutation": inspection["mutation_stream_name"],
            "family": inspection["stream_family"],
        },
        "outcome": inspection["outcome"],
        "admitted": inspection["admitted"],
        "ordered_steps": inspection["ordered_steps"],
        "mutation_stream_consumed": inspection["mutation_stream_consumed"],
        "snapshot_digests": inspection["snapshot_digests"],
        "gene_counts": {
            "parent": inspection["parent_gene_count"],
            "child": inspection["child_gene_count"],
            "delta": inspection["delta_gene_count"],
        },
    }
    return [f"parity_{field}_mismatch" for field, expected_value in expected.items() if projection.get(field) != expected_value]


def _projection_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical.pop("projection_digest", None)
    return hashlib.sha256(_canonical_json_bytes(canonical)).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode(ENCODING)


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
    "MAX_PROJECTION_BYTES",
    "MEDIA_TYPE",
    "build_worldbridge_respawn_artifact_diagnostic_projection_contract",
    "decode_worldbridge_respawn_artifact_diagnostic_projection",
    "encode_worldbridge_respawn_artifact_diagnostic_projection",
    "project_worldbridge_respawn_artifact_inspection",
    "validate_worldbridge_respawn_artifact_diagnostic_projection",
]
