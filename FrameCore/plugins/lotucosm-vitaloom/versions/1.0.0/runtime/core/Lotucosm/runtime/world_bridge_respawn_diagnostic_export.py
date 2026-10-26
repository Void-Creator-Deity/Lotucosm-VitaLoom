# -*- coding: utf-8 -*-
"""Presentation-only, in-memory E231 diagnostic export seam."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_presentation import (
    ENCODING,
    MEDIA_TYPE as PRESENTATION_MEDIA_TYPE,
    build_worldbridge_respawn_diagnostic_presentation_contract,
    decode_worldbridge_respawn_diagnostic_presentation,
    validate_worldbridge_respawn_diagnostic_presentation,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_respawn_diagnostic_presentation_export"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-respawn-diagnostic-export+json"
MAX_EXPORT_BYTES = 6 * 1024
DO_NOT_CLAIM = (
    "diagnostic_export_replay_input",
    "diagnostic_export_checkpoint_state",
    "diagnostic_export_restore_authority",
    "diagnostic_export_mutation_execution",
    "diagnostic_export_live_runtime_state",
    "diagnostic_export_ui_authority",
    "diagnostic_export_persistence",
    "diagnostic_export_file_or_network_output",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)
_STATIC_POLICIES = {
    "export_scope": "validated_diagnostic_presentation_only",
    "read_only": True,
    "presentation_integrity_valid": True,
    "export_persisted": False,
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
    "source_presentation_media_type",
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
    "export_scope",
    "read_only",
    "presentation_integrity_valid",
    "export_persisted",
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
    "export_digest",
}


def export_worldbridge_respawn_diagnostic_presentation(
    presentation: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Project one E230 presentation into a bounded in-memory export record."""
    source_presentation = _validated_presentation(presentation)
    export_record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "source_presentation_media_type": PRESENTATION_MEDIA_TYPE,
        "source_presentation_digest": source_presentation["presentation_digest"],
        "source_artifact_id": source_presentation["source_artifact_id"],
        "source_artifact_digest": source_presentation["source_artifact_digest"],
        "context_id": source_presentation["context_id"],
        "stream_roles": copy.deepcopy(source_presentation["stream_roles"]),
        "outcome": source_presentation["outcome"],
        "admitted": source_presentation["admitted"],
        "ordered_steps": copy.deepcopy(source_presentation["ordered_steps"]),
        "mutation_stream_consumed": source_presentation["mutation_stream_consumed"],
        "snapshot_digests": copy.deepcopy(source_presentation["snapshot_digests"]),
        "gene_counts": copy.deepcopy(source_presentation["gene_counts"]),
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    export_record["export_digest"] = _export_digest(export_record)
    validation = validate_worldbridge_respawn_diagnostic_export_record(
        export_record, presentation=source_presentation
    )
    if validation["valid"] is not True:
        raise RuntimeError("constructed invalid diagnostic export_record: " + ",".join(validation["errors"]))
    return copy.deepcopy(export_record)


def validate_worldbridge_respawn_diagnostic_export_record(
    export_record: object,
    *,
    presentation: Mapping[str, Any] | bytes | bytearray | memoryview | None = None,
) -> dict[str, Any]:
    """Validate export_record integrity and optional exact presentation-field parity."""
    if not isinstance(export_record, Mapping):
        return {"valid": False, "errors": ["export_record_not_mapping"]}
    try:
        value = dict(export_record)
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["export_record_mapping_copy_failed"]}
    errors: list[str] = []
    if set(value) != _REQUIRED_KEYS:
        errors.append("export_record_keys_mismatch")
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
    if value.get("source_presentation_media_type") != PRESENTATION_MEDIA_TYPE:
        errors.append("source_presentation_media_type_mismatch")
    for field in ("source_artifact_id", "context_id"):
        if not _clean_nonempty_string(value.get(field)):
            errors.append(f"{field}_invalid")
    for field in ("source_presentation_digest", "source_artifact_digest"):
        if not _is_sha256(value.get(field)):
            errors.append(f"{field}_invalid")
    _validate_export_record_facts(value, errors)
    for field, expected in _STATIC_POLICIES.items():
        if value.get(field) != expected or type(value.get(field)) is not type(expected):
            errors.append(f"{field}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    if value.get("export_digest") != _export_digest(value):
        errors.append("export_digest_mismatch")
    try:
        if len(_canonical_json_bytes(value)) > MAX_EXPORT_BYTES:
            errors.append("export_record_oversized")
    except (TypeError, ValueError):
        errors.append("export_record_not_canonical_json")

    if presentation is not None:
        try:
            source_presentation = _validated_presentation(presentation)
        except (TypeError, ValueError) as exc:
            errors.append("source_presentation_invalid")
            return {"valid": False, "errors": errors + [str(exc)]}
        errors.extend(_presentation_parity_errors(value, source_presentation))
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_respawn_diagnostic_export_record(export_record: Mapping[str, Any]) -> bytes:
    """Return exact canonical UTF-8 export_record bytes after validation."""
    validation = validate_worldbridge_respawn_diagnostic_export_record(export_record)
    if validation["valid"] is not True:
        raise ValueError("invalid worldbridge respawn diagnostic export_record: " + ",".join(validation["errors"]))
    encoded = _canonical_json_bytes(dict(export_record))
    if len(encoded) > MAX_EXPORT_BYTES:
        raise ValueError("worldbridge respawn diagnostic export_record exceeds byte bound")
    return encoded


def decode_worldbridge_respawn_diagnostic_export_record(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    """Decode only exact canonical, bounded export_record bytes."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("export_record bytes required")
    raw = bytes(data)
    if len(raw) > MAX_EXPORT_BYTES:
        raise ValueError("worldbridge respawn diagnostic export_record exceeds byte bound")
    try:
        decoded = json.loads(
            raw.decode(ENCODING),
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid worldbridge respawn diagnostic export_record bytes") from exc
    if not isinstance(decoded, dict):
        raise ValueError("worldbridge respawn diagnostic export_record must decode to object")
    validation = validate_worldbridge_respawn_diagnostic_export_record(decoded)
    if validation["valid"] is not True:
        raise ValueError("invalid worldbridge respawn diagnostic export_record: " + ",".join(validation["errors"]))
    if _canonical_json_bytes(decoded) != raw:
        raise ValueError("worldbridge respawn diagnostic export_record bytes are not canonical")
    return copy.deepcopy(decoded)


def build_worldbridge_respawn_diagnostic_export_contract() -> dict[str, Any]:
    """Build static E231 evidence without touching a live runtime."""
    presentation = build_worldbridge_respawn_diagnostic_presentation_contract()["presentation"]
    export_record = export_worldbridge_respawn_diagnostic_presentation(presentation)
    encoded = encode_worldbridge_respawn_diagnostic_export_record(export_record)
    decoded = decode_worldbridge_respawn_diagnostic_export_record(encoded)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_respawn_diagnostic_export_contract",
        "contract_valid": validate_worldbridge_respawn_diagnostic_export_record(
            export_record, presentation=presentation
        )["valid"],
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "max_export_bytes": MAX_EXPORT_BYTES,
        "round_trip_equal": decoded == export_record,
        "export_record": copy.deepcopy(export_record),
        "presentation_consumer_only": True,
        "accepts_raw_receipt": False,
        "accepts_raw_artifact": False,
        "accepts_inspection": False,
        "accepts_projection": False,
        "accepts_raw_presentation_receipt": False,
        "writes_files": False,
        "transmits_network": False,
        "ui_authority": False,
        "restores_streams": False,
        "executes_mutation": False,
        "replay_admitted": False,
        "default_ready": False,
        "do_not_claim": list(DO_NOT_CLAIM),
    }


def _validated_presentation(
    presentation: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    if isinstance(presentation, (bytes, bytearray, memoryview)):
        return decode_worldbridge_respawn_diagnostic_presentation(presentation)
    validation = validate_worldbridge_respawn_diagnostic_presentation(presentation)
    if validation["valid"] is not True:
        raise ValueError("invalid worldbridge respawn diagnostic presentation: " + ",".join(validation["errors"]))
    return copy.deepcopy(dict(presentation))


def _validate_export_record_facts(value: Mapping[str, Any], errors: list[str]) -> None:
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


def _presentation_parity_errors(export_record: Mapping[str, Any], presentation: Mapping[str, Any]) -> list[str]:
    expected = {
        "source_presentation_media_type": PRESENTATION_MEDIA_TYPE,
        "source_presentation_digest": presentation["presentation_digest"],
        "source_artifact_id": presentation["source_artifact_id"],
        "source_artifact_digest": presentation["source_artifact_digest"],
        "context_id": presentation["context_id"],
        "stream_roles": presentation["stream_roles"],
        "outcome": presentation["outcome"],
        "admitted": presentation["admitted"],
        "ordered_steps": presentation["ordered_steps"],
        "mutation_stream_consumed": presentation["mutation_stream_consumed"],
        "snapshot_digests": presentation["snapshot_digests"],
        "gene_counts": presentation["gene_counts"],
    }
    return [f"presentation_parity_{field}_mismatch" for field, expected_value in expected.items() if export_record.get(field) != expected_value]


def _export_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical.pop("export_digest", None)
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
    "MAX_EXPORT_BYTES",
    "MEDIA_TYPE",
    "build_worldbridge_respawn_diagnostic_export_contract",
    "decode_worldbridge_respawn_diagnostic_export_record",
    "encode_worldbridge_respawn_diagnostic_export_record",
    "export_worldbridge_respawn_diagnostic_presentation",
    "validate_worldbridge_respawn_diagnostic_export_record",
]
