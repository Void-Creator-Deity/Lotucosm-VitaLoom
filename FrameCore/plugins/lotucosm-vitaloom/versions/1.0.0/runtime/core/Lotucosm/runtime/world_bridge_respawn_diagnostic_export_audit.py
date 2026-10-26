# -*- coding: utf-8 -*-
"""Final in-memory, read-only audit sink for the E231 diagnostic export record."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_export import (
    ENCODING,
    MEDIA_TYPE as EXPORT_MEDIA_TYPE,
    build_worldbridge_respawn_diagnostic_export_contract,
    decode_worldbridge_respawn_diagnostic_export_record,
    validate_worldbridge_respawn_diagnostic_export_record,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_respawn_diagnostic_export_audit"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-respawn-diagnostic-export-audit+json"
MAX_AUDIT_BYTES = 4 * 1024
DO_NOT_CLAIM = (
    "diagnostic_audit_persistence",
    "diagnostic_audit_file_or_network_output",
    "diagnostic_audit_replay_input",
    "diagnostic_audit_checkpoint_state",
    "diagnostic_audit_restore_authority",
    "diagnostic_audit_mutation_execution",
    "diagnostic_audit_live_runtime_state",
    "diagnostic_audit_ui_authority",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)
_STATIC_POLICIES = {
    "audit_scope": "validated_diagnostic_export_only",
    "read_only": True,
    "export_integrity_valid": True,
    "audit_persisted": False,
    "file_written": False,
    "network_transmitted": False,
    "replay_input": False,
    "checkpoint_state": False,
    "restore_performed": False,
    "mutation_executed": False,
    "live_runtime_state": False,
    "ui_authority": False,
    "replay_admitted": False,
    "default_ready": False,
}
_REQUIRED_KEYS = {
    "schema_version",
    "status",
    "media_type",
    "encoding",
    "canonical_json",
    "source_export_media_type",
    "source_export_digest",
    "source_presentation_digest",
    "source_artifact_id",
    "source_artifact_digest",
    "context_id",
    "stream_roles",
    "outcome",
    "admitted",
    "ordered_steps",
    "mutation_stream_consumed",
    "snapshot_digests",
    "gene_counts",
    "audit_scope",
    "read_only",
    "export_integrity_valid",
    "audit_persisted",
    "file_written",
    "network_transmitted",
    "replay_input",
    "checkpoint_state",
    "restore_performed",
    "mutation_executed",
    "live_runtime_state",
    "ui_authority",
    "replay_admitted",
    "default_ready",
    "do_not_claim",
    "audit_digest",
}


def audit_worldbridge_respawn_diagnostic_export(
    export_record: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Audit one E231 export record without persistence, I/O, or runtime access."""
    source_export = _validated_export(export_record)
    audit: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "source_export_media_type": EXPORT_MEDIA_TYPE,
        "source_export_digest": source_export["export_digest"],
        "source_presentation_digest": source_export["source_presentation_digest"],
        "source_artifact_id": source_export["source_artifact_id"],
        "source_artifact_digest": source_export["source_artifact_digest"],
        "context_id": source_export["context_id"],
        "stream_roles": copy.deepcopy(source_export["stream_roles"]),
        "outcome": source_export["outcome"],
        "admitted": source_export["admitted"],
        "ordered_steps": copy.deepcopy(source_export["ordered_steps"]),
        "mutation_stream_consumed": source_export["mutation_stream_consumed"],
        "snapshot_digests": copy.deepcopy(source_export["snapshot_digests"]),
        "gene_counts": copy.deepcopy(source_export["gene_counts"]),
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    audit["audit_digest"] = _audit_digest(audit)
    validation = validate_worldbridge_respawn_diagnostic_export_audit(audit, export_record=source_export)
    if validation["valid"] is not True:
        raise RuntimeError("constructed invalid diagnostic export audit: " + ",".join(validation["errors"]))
    return copy.deepcopy(audit)


def validate_worldbridge_respawn_diagnostic_export_audit(
    audit: object,
    *,
    export_record: Mapping[str, Any] | bytes | bytearray | memoryview | None = None,
) -> dict[str, Any]:
    """Validate audit self-integrity and optional exact E231 field parity."""
    if not isinstance(audit, Mapping):
        return {"valid": False, "errors": ["audit_not_mapping"]}
    try:
        value = dict(audit)
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["audit_mapping_copy_failed"]}
    errors: list[str] = []
    if set(value) != _REQUIRED_KEYS:
        errors.append("audit_keys_mismatch")
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
    if value.get("source_export_media_type") != EXPORT_MEDIA_TYPE:
        errors.append("source_export_media_type_mismatch")
    for field in ("source_artifact_id", "context_id"):
        if not _clean_nonempty_string(value.get(field)):
            errors.append(f"{field}_invalid")
    for field in ("source_export_digest", "source_presentation_digest", "source_artifact_digest"):
        if not _is_sha256(value.get(field)):
            errors.append(f"{field}_invalid")
    _validate_facts(value, errors)
    for field, expected in _STATIC_POLICIES.items():
        if value.get(field) != expected or type(value.get(field)) is not type(expected):
            errors.append(f"{field}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    if value.get("audit_digest") != _audit_digest(value):
        errors.append("audit_digest_mismatch")
    try:
        if len(_canonical_json_bytes(value)) > MAX_AUDIT_BYTES:
            errors.append("audit_oversized")
    except (TypeError, ValueError):
        errors.append("audit_not_canonical_json")

    if export_record is not None:
        try:
            source_export = _validated_export(export_record)
        except (TypeError, ValueError) as exc:
            errors.append("source_export_invalid")
            return {"valid": False, "errors": errors + [str(exc)]}
        errors.extend(_export_parity_errors(value, source_export))
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_respawn_diagnostic_export_audit(audit: Mapping[str, Any]) -> bytes:
    """Encode one validated audit as exact bounded canonical bytes."""
    validation = validate_worldbridge_respawn_diagnostic_export_audit(audit)
    if validation["valid"] is not True:
        raise ValueError("invalid worldbridge respawn diagnostic export audit: " + ",".join(validation["errors"]))
    encoded = _canonical_json_bytes(dict(audit))
    if len(encoded) > MAX_AUDIT_BYTES:
        raise ValueError("worldbridge respawn diagnostic export audit exceeds byte bound")
    return encoded


def decode_worldbridge_respawn_diagnostic_export_audit(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    """Decode only exact canonical, bounded audit bytes."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("audit bytes required")
    raw = bytes(data)
    if len(raw) > MAX_AUDIT_BYTES:
        raise ValueError("worldbridge respawn diagnostic export audit exceeds byte bound")
    try:
        decoded = json.loads(
            raw.decode(ENCODING),
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid worldbridge respawn diagnostic export audit bytes") from exc
    if not isinstance(decoded, dict):
        raise ValueError("worldbridge respawn diagnostic export audit must decode to object")
    validation = validate_worldbridge_respawn_diagnostic_export_audit(decoded)
    if validation["valid"] is not True:
        raise ValueError("invalid worldbridge respawn diagnostic export audit: " + ",".join(validation["errors"]))
    if _canonical_json_bytes(decoded) != raw:
        raise ValueError("worldbridge respawn diagnostic export audit bytes are not canonical")
    return copy.deepcopy(decoded)


def build_worldbridge_respawn_diagnostic_export_audit_contract() -> dict[str, Any]:
    """Build static E232 evidence without touching live runtime state."""
    export_record = build_worldbridge_respawn_diagnostic_export_contract()["export_record"]
    audit = audit_worldbridge_respawn_diagnostic_export(export_record)
    encoded = encode_worldbridge_respawn_diagnostic_export_audit(audit)
    decoded = decode_worldbridge_respawn_diagnostic_export_audit(encoded)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_respawn_diagnostic_export_audit_contract",
        "contract_valid": validate_worldbridge_respawn_diagnostic_export_audit(audit, export_record=export_record)["valid"],
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "max_audit_bytes": MAX_AUDIT_BYTES,
        "round_trip_equal": decoded == audit,
        "audit": copy.deepcopy(audit),
        "export_consumer_only": True,
        "accepts_raw_receipt": False,
        "accepts_raw_artifact": False,
        "accepts_inspection": False,
        "accepts_projection": False,
        "accepts_presentation": False,
        "audit_persisted": False,
        "file_written": False,
        "network_transmitted": False,
        "ui_authority": False,
        "restores_streams": False,
        "executes_mutation": False,
        "replay_admitted": False,
        "default_ready": False,
        "do_not_claim": list(DO_NOT_CLAIM),
    }


def _validated_export(
    export_record: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    if isinstance(export_record, (bytes, bytearray, memoryview)):
        return decode_worldbridge_respawn_diagnostic_export_record(export_record)
    validation = validate_worldbridge_respawn_diagnostic_export_record(export_record)
    if validation["valid"] is not True:
        raise ValueError("invalid worldbridge respawn diagnostic export record: " + ",".join(validation["errors"]))
    return copy.deepcopy(dict(export_record))


def _validate_facts(value: Mapping[str, Any], errors: list[str]) -> None:
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


def _export_parity_errors(audit: Mapping[str, Any], export_record: Mapping[str, Any]) -> list[str]:
    expected = {
        "source_export_media_type": EXPORT_MEDIA_TYPE,
        "source_export_digest": export_record["export_digest"],
        "source_presentation_digest": export_record["source_presentation_digest"],
        "source_artifact_id": export_record["source_artifact_id"],
        "source_artifact_digest": export_record["source_artifact_digest"],
        "context_id": export_record["context_id"],
        "stream_roles": export_record["stream_roles"],
        "outcome": export_record["outcome"],
        "admitted": export_record["admitted"],
        "ordered_steps": export_record["ordered_steps"],
        "mutation_stream_consumed": export_record["mutation_stream_consumed"],
        "snapshot_digests": export_record["snapshot_digests"],
        "gene_counts": export_record["gene_counts"],
    }
    return [f"export_parity_{field}_mismatch" for field, expected_value in expected.items() if audit.get(field) != expected_value]


def _audit_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical.pop("audit_digest", None)
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
    "MAX_AUDIT_BYTES",
    "MEDIA_TYPE",
    "audit_worldbridge_respawn_diagnostic_export",
    "build_worldbridge_respawn_diagnostic_export_audit_contract",
    "decode_worldbridge_respawn_diagnostic_export_audit",
    "encode_worldbridge_respawn_diagnostic_export_audit",
    "validate_worldbridge_respawn_diagnostic_export_audit",
]
