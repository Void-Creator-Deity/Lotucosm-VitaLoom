"""Canonical, bounded artifact envelope for one E367 witness receipt."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .world_bridge_e367_live_viewport_witness import (
    validate_worldbridge_e367_live_viewport_witness_contract,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e372_receipt_artifact"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-e367-receipt+json"
ENCODING = "utf-8"
MAX_ARTIFACT_BYTES = 16 * 1024 * 1024
RETENTION_CLASS = "diagnostic_ephemeral"
DEFAULT_TTL_SECONDS = 24 * 60 * 60
_REQUIRED_KEYS = {
    "schema_version", "status", "media_type", "encoding", "canonical_json",
    "artifact_id", "receipt_schema_version", "receipt", "receipt_digest",
    "retention", "migration_admitted", "artifact_digest",
}


def build_worldbridge_e372_receipt_artifact(
    receipt: Mapping[str, Any],
    *,
    artifact_id: str,
    issued_at: int,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        raise TypeError("receipt must be a mapping")
    _validate_receipt(receipt)
    if not isinstance(issued_at, int) or isinstance(issued_at, bool) or issued_at < 0:
        raise ValueError("issued_at must be a non-negative integer")
    if not isinstance(ttl_seconds, int) or isinstance(ttl_seconds, bool) or ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be a positive integer")
    receipt_copy = copy.deepcopy(dict(receipt))
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "artifact_id": _clean_id(artifact_id),
        "receipt_schema_version": 1,
        "receipt": receipt_copy,
        "receipt_digest": _digest(receipt_copy),
        "retention": {
            "class": RETENTION_CLASS,
            "issued_at": issued_at,
            "expires_at": issued_at + ttl_seconds,
            "max_age_seconds": ttl_seconds,
            "persistent_authority": False,
        },
        "migration_admitted": False,
        "artifact_digest": "",
    }
    artifact["artifact_digest"] = _artifact_digest(artifact)
    if len(_canonical(artifact)) > MAX_ARTIFACT_BYTES:
        raise OverflowError("receipt artifact exceeds maximum size")
    return copy.deepcopy(artifact)


def encode_worldbridge_e372_receipt_artifact(
    artifact: Mapping[str, Any], *, max_bytes: int = MAX_ARTIFACT_BYTES
) -> bytes:
    validation = validate_worldbridge_e372_receipt_artifact(artifact)
    if not validation["valid"]:
        raise ValueError("invalid E372 receipt artifact: " + ",".join(validation["errors"]))
    encoded = _canonical(dict(artifact))
    if len(encoded) > max_bytes:
        raise OverflowError("receipt artifact exceeds maximum size")
    return encoded


def decode_worldbridge_e372_receipt_artifact(
    encoded: bytes | bytearray | memoryview, *, now_epoch: int | None = None
) -> dict[str, Any]:
    if not isinstance(encoded, (bytes, bytearray, memoryview)):
        raise TypeError("encoded artifact must be bytes-like")
    raw = bytes(encoded)
    if not raw or len(raw) > MAX_ARTIFACT_BYTES:
        raise ValueError("encoded artifact size is invalid")
    try:
        value = json.loads(raw.decode(ENCODING))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("encoded artifact is not strict JSON") from exc
    if not isinstance(value, dict) or _canonical(value) != raw:
        raise ValueError("encoded artifact is not canonical JSON")
    validation = validate_worldbridge_e372_receipt_artifact(value, now_epoch=now_epoch)
    if not validation["valid"]:
        raise ValueError("invalid E372 receipt artifact: " + ",".join(validation["errors"]))
    return copy.deepcopy(value)


def validate_worldbridge_e372_receipt_artifact(
    value: object, *, now_epoch: int | None = None
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["artifact_must_be_mapping"]}
    errors: list[str] = []
    if set(value) != _REQUIRED_KEYS:
        errors.append("artifact_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("media_type") != MEDIA_TYPE or value.get("encoding") != ENCODING:
        errors.append("encoding_mismatch")
    if value.get("canonical_json") is not True:
        errors.append("canonical_json_mismatch")
    try:
        _clean_id(value.get("artifact_id"))
    except ValueError:
        errors.append("artifact_id_invalid")
    if value.get("receipt_schema_version") != 1:
        errors.append("receipt_schema_version_mismatch")
    receipt = value.get("receipt")
    if not isinstance(receipt, Mapping):
        errors.append("receipt_missing")
    else:
        try:
            _validate_receipt(receipt)
        except (TypeError, ValueError):
            errors.append("receipt_invalid")
        if value.get("receipt_digest") != _digest(dict(receipt)):
            errors.append("receipt_digest_mismatch")
    retention = value.get("retention")
    required_retention = {"class", "issued_at", "expires_at", "max_age_seconds", "persistent_authority"}
    if not isinstance(retention, Mapping) or set(retention) != required_retention:
        errors.append("retention_shape_invalid")
    else:
        if retention.get("class") != RETENTION_CLASS or retention.get("persistent_authority") is not False:
            errors.append("retention_policy_mismatch")
        issued = retention.get("issued_at")
        expires = retention.get("expires_at")
        max_age = retention.get("max_age_seconds")
        if any(not isinstance(item, int) or isinstance(item, bool) or item < 0 for item in (issued, expires, max_age)):
            errors.append("retention_time_invalid")
        elif expires != issued + max_age or max_age <= 0:
            errors.append("retention_window_invalid")
        elif now_epoch is not None and (not isinstance(now_epoch, int) or isinstance(now_epoch, bool)):
            errors.append("now_epoch_invalid")
        elif now_epoch is not None and now_epoch >= expires:
            errors.append("artifact_expired")
    if value.get("migration_admitted") is not False:
        errors.append("migration_overclaim")
    if not isinstance(value.get("artifact_digest"), str) or value.get("artifact_digest") != _artifact_digest(value):
        errors.append("artifact_digest_mismatch")
    try:
        if len(_canonical(dict(value))) > MAX_ARTIFACT_BYTES:
            errors.append("artifact_size_exceeded")
    except (TypeError, ValueError):
        errors.append("artifact_not_canonicalizable")
    return {"valid": not errors, "errors": errors}


def _validate_receipt(receipt: Mapping[str, Any]) -> None:
    if validate_worldbridge_e367_live_viewport_witness_contract(receipt.get("runtime_witness"))["valid"] is not True:
        raise ValueError("runtime witness is invalid")
    if receipt.get("contract_valid") is not True or receipt.get("cleanup", {}).get("viewport_deleted") is not True:
        raise ValueError("receipt is incomplete")


def _clean_id(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 128 or any(ch.isspace() for ch in value):
        raise ValueError("artifact_id must be a non-empty bounded token")
    return value


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode(ENCODING)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _artifact_digest(value: Mapping[str, Any]) -> str:
    unsigned = dict(value)
    unsigned.pop("artifact_digest", None)
    return _digest(unsigned)


__all__ = [
    "DEFAULT_TTL_SECONDS", "MAX_ARTIFACT_BYTES", "SCHEMA_VERSION", "STATUS",
    "build_worldbridge_e372_receipt_artifact", "encode_worldbridge_e372_receipt_artifact",
    "decode_worldbridge_e372_receipt_artifact", "validate_worldbridge_e372_receipt_artifact",
]
