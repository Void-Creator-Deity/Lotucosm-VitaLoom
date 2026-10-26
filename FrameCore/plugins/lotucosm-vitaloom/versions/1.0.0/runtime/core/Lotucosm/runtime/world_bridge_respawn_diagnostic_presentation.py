# -*- coding: utf-8 -*-
"""Receipt-only, read-only E230 diagnostic presentation seam."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_consumer import (
    ENCODING,
    MEDIA_TYPE as RECEIPT_MEDIA_TYPE,
    build_worldbridge_respawn_diagnostic_consumer_contract,
    decode_worldbridge_respawn_diagnostic_consumer_receipt,
    validate_worldbridge_respawn_diagnostic_consumer_receipt,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_respawn_diagnostic_receipt_presentation"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-respawn-diagnostic-presentation+json"
MAX_PRESENTATION_BYTES = 6 * 1024
DO_NOT_CLAIM = (
    "diagnostic_presentation_replay_input",
    "diagnostic_presentation_checkpoint_state",
    "diagnostic_presentation_restore_authority",
    "diagnostic_presentation_mutation_execution",
    "diagnostic_presentation_live_runtime_state",
    "diagnostic_presentation_ui_authority",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)
_STATIC_POLICIES = {
    "presentation_scope": "validated_diagnostic_receipt_only",
    "read_only": True,
    "receipt_integrity_valid": True,
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
    "source_receipt_media_type",
    "source_receipt_digest",
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
    "presentation_scope",
    "read_only",
    "receipt_integrity_valid",
    "replay_input",
    "checkpoint_state",
    "restore_performed",
    "mutation_executed",
    "live_runtime_state",
    "ui_authority",
    "replay_admitted",
    "default_ready",
    "do_not_claim",
    "presentation_digest",
}


def present_worldbridge_respawn_diagnostic_receipt(
    receipt: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Project one E229 receipt into a bounded, non-UI presentation model."""
    source_receipt = _validated_receipt(receipt)
    presentation: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "source_receipt_media_type": RECEIPT_MEDIA_TYPE,
        "source_receipt_digest": source_receipt["receipt_digest"],
        "source_artifact_id": source_receipt["source_artifact_id"],
        "source_artifact_digest": source_receipt["source_artifact_digest"],
        "context_id": source_receipt["context_id"],
        "stream_roles": copy.deepcopy(source_receipt["stream_roles"]),
        "outcome": source_receipt["outcome"],
        "admitted": source_receipt["admitted"],
        "ordered_steps": copy.deepcopy(source_receipt["ordered_steps"]),
        "mutation_stream_consumed": source_receipt["mutation_stream_consumed"],
        "snapshot_digests": copy.deepcopy(source_receipt["snapshot_digests"]),
        "gene_counts": copy.deepcopy(source_receipt["gene_counts"]),
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    presentation["presentation_digest"] = _presentation_digest(presentation)
    validation = validate_worldbridge_respawn_diagnostic_presentation(
        presentation, receipt=source_receipt
    )
    if validation["valid"] is not True:
        raise RuntimeError("constructed invalid diagnostic presentation: " + ",".join(validation["errors"]))
    return copy.deepcopy(presentation)


def validate_worldbridge_respawn_diagnostic_presentation(
    presentation: object,
    *,
    receipt: Mapping[str, Any] | bytes | bytearray | memoryview | None = None,
) -> dict[str, Any]:
    """Validate presentation integrity and optional exact receipt-field parity."""
    if not isinstance(presentation, Mapping):
        return {"valid": False, "errors": ["presentation_not_mapping"]}
    try:
        value = dict(presentation)
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["presentation_mapping_copy_failed"]}
    errors: list[str] = []
    if set(value) != _REQUIRED_KEYS:
        errors.append("presentation_keys_mismatch")
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
    if value.get("source_receipt_media_type") != RECEIPT_MEDIA_TYPE:
        errors.append("source_receipt_media_type_mismatch")
    for field in ("source_artifact_id", "context_id"):
        if not _clean_nonempty_string(value.get(field)):
            errors.append(f"{field}_invalid")
    for field in ("source_receipt_digest", "source_artifact_digest"):
        if not _is_sha256(value.get(field)):
            errors.append(f"{field}_invalid")
    _validate_presentation_facts(value, errors)
    for field, expected in _STATIC_POLICIES.items():
        if value.get(field) != expected or type(value.get(field)) is not type(expected):
            errors.append(f"{field}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    if value.get("presentation_digest") != _presentation_digest(value):
        errors.append("presentation_digest_mismatch")
    try:
        if len(_canonical_json_bytes(value)) > MAX_PRESENTATION_BYTES:
            errors.append("presentation_oversized")
    except (TypeError, ValueError):
        errors.append("presentation_not_canonical_json")

    if receipt is not None:
        try:
            source_receipt = _validated_receipt(receipt)
        except (TypeError, ValueError) as exc:
            errors.append("source_receipt_invalid")
            return {"valid": False, "errors": errors + [str(exc)]}
        errors.extend(_receipt_parity_errors(value, source_receipt))
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_respawn_diagnostic_presentation(presentation: Mapping[str, Any]) -> bytes:
    """Return exact canonical UTF-8 presentation bytes after validation."""
    validation = validate_worldbridge_respawn_diagnostic_presentation(presentation)
    if validation["valid"] is not True:
        raise ValueError("invalid worldbridge respawn diagnostic presentation: " + ",".join(validation["errors"]))
    encoded = _canonical_json_bytes(dict(presentation))
    if len(encoded) > MAX_PRESENTATION_BYTES:
        raise ValueError("worldbridge respawn diagnostic presentation exceeds byte bound")
    return encoded


def decode_worldbridge_respawn_diagnostic_presentation(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    """Decode only exact canonical, bounded presentation bytes."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("presentation bytes required")
    raw = bytes(data)
    if len(raw) > MAX_PRESENTATION_BYTES:
        raise ValueError("worldbridge respawn diagnostic presentation exceeds byte bound")
    try:
        decoded = json.loads(
            raw.decode(ENCODING),
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid worldbridge respawn diagnostic presentation bytes") from exc
    if not isinstance(decoded, dict):
        raise ValueError("worldbridge respawn diagnostic presentation must decode to object")
    validation = validate_worldbridge_respawn_diagnostic_presentation(decoded)
    if validation["valid"] is not True:
        raise ValueError("invalid worldbridge respawn diagnostic presentation: " + ",".join(validation["errors"]))
    if _canonical_json_bytes(decoded) != raw:
        raise ValueError("worldbridge respawn diagnostic presentation bytes are not canonical")
    return copy.deepcopy(decoded)


def build_worldbridge_respawn_diagnostic_presentation_contract() -> dict[str, Any]:
    """Build static E230 evidence without touching a live runtime."""
    receipt = build_worldbridge_respawn_diagnostic_consumer_contract()["receipt"]
    presentation = present_worldbridge_respawn_diagnostic_receipt(receipt)
    encoded = encode_worldbridge_respawn_diagnostic_presentation(presentation)
    decoded = decode_worldbridge_respawn_diagnostic_presentation(encoded)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_respawn_diagnostic_presentation_contract",
        "contract_valid": validate_worldbridge_respawn_diagnostic_presentation(
            presentation, receipt=receipt
        )["valid"],
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "max_presentation_bytes": MAX_PRESENTATION_BYTES,
        "round_trip_equal": decoded == presentation,
        "presentation": copy.deepcopy(presentation),
        "receipt_consumer_only": True,
        "accepts_raw_artifact": False,
        "accepts_inspection": False,
        "accepts_projection": False,
        "ui_authority": False,
        "restores_streams": False,
        "executes_mutation": False,
        "replay_admitted": False,
        "default_ready": False,
        "do_not_claim": list(DO_NOT_CLAIM),
    }


def _validated_receipt(
    receipt: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    if isinstance(receipt, (bytes, bytearray, memoryview)):
        return decode_worldbridge_respawn_diagnostic_consumer_receipt(receipt)
    validation = validate_worldbridge_respawn_diagnostic_consumer_receipt(receipt)
    if validation["valid"] is not True:
        raise ValueError("invalid worldbridge respawn diagnostic receipt: " + ",".join(validation["errors"]))
    return copy.deepcopy(dict(receipt))


def _validate_presentation_facts(value: Mapping[str, Any], errors: list[str]) -> None:
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


def _receipt_parity_errors(presentation: Mapping[str, Any], receipt: Mapping[str, Any]) -> list[str]:
    expected = {
        "source_receipt_media_type": RECEIPT_MEDIA_TYPE,
        "source_receipt_digest": receipt["receipt_digest"],
        "source_artifact_id": receipt["source_artifact_id"],
        "source_artifact_digest": receipt["source_artifact_digest"],
        "context_id": receipt["context_id"],
        "stream_roles": receipt["stream_roles"],
        "outcome": receipt["outcome"],
        "admitted": receipt["admitted"],
        "ordered_steps": receipt["ordered_steps"],
        "mutation_stream_consumed": receipt["mutation_stream_consumed"],
        "snapshot_digests": receipt["snapshot_digests"],
        "gene_counts": receipt["gene_counts"],
    }
    return [f"receipt_parity_{field}_mismatch" for field, expected_value in expected.items() if presentation.get(field) != expected_value]


def _presentation_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical.pop("presentation_digest", None)
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
    "MAX_PRESENTATION_BYTES",
    "MEDIA_TYPE",
    "build_worldbridge_respawn_diagnostic_presentation_contract",
    "decode_worldbridge_respawn_diagnostic_presentation",
    "encode_worldbridge_respawn_diagnostic_presentation",
    "present_worldbridge_respawn_diagnostic_receipt",
    "validate_worldbridge_respawn_diagnostic_presentation",
]
