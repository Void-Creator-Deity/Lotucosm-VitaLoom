"""Integrity and one-shot consumption boundary for E372 receipt artifacts."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, MutableSet
from typing import Any

from .world_bridge_e372_receipt_artifact import (
    MAX_ARTIFACT_BYTES,
    decode_worldbridge_e372_receipt_artifact,
    encode_worldbridge_e372_receipt_artifact,
    validate_worldbridge_e372_receipt_artifact,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e373_receipt_integrity"
_REQUIRED_KEYS = {
    "schema_version", "status", "artifact", "artifact_digest",
    "checkpoint_identity", "witness_identity_digest", "integrity_digest",
    "replay_admitted", "default_ready", "lossless",
}


def build_worldbridge_e373_receipt_integrity_artifact(
    artifact: Mapping[str, Any],
) -> dict[str, Any]:
    if validate_worldbridge_e372_receipt_artifact(artifact)["valid"] is not True:
        raise ValueError("E372 artifact is invalid")
    receipt = artifact["receipt"]
    identity = receipt.get("checkpoint_identity")
    witness = receipt.get("witness")
    if not isinstance(identity, Mapping) or identity != witness.get("checkpoint_identity"):
        raise ValueError("checkpoint and witness identity are not bound")
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "artifact": copy.deepcopy(dict(artifact)),
        "artifact_digest": _digest(artifact),
        "checkpoint_identity": copy.deepcopy(dict(identity)),
        "witness_identity_digest": _digest(witness["checkpoint_identity"]),
        "integrity_digest": "",
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    result["integrity_digest"] = _integrity_digest(result)
    return result


def validate_worldbridge_e373_receipt_integrity_artifact(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["integrity_artifact_must_be_mapping"]}
    errors: list[str] = []
    if set(value) != _REQUIRED_KEYS:
        errors.append("integrity_artifact_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("integrity_schema_mismatch")
    nested = value.get("artifact")
    if validate_worldbridge_e372_receipt_artifact(nested)["valid"] is not True:
        errors.append("nested_artifact_invalid")
    if value.get("artifact_digest") != _digest(nested):
        errors.append("artifact_digest_binding_mismatch")
    identity = value.get("checkpoint_identity")
    receipt = nested.get("receipt") if isinstance(nested, Mapping) else None
    witness = receipt.get("witness") if isinstance(receipt, Mapping) else None
    witness_identity = witness.get("checkpoint_identity") if isinstance(witness, Mapping) else None
    if not isinstance(identity, Mapping) or identity != receipt.get("checkpoint_identity") or identity != witness_identity:
        errors.append("checkpoint_identity_binding_mismatch")
    if value.get("witness_identity_digest") != _digest(witness_identity):
        errors.append("witness_identity_digest_mismatch")
    if value.get("integrity_digest") != _integrity_digest(value):
        errors.append("integrity_digest_mismatch")
    for field in ("replay_admitted", "default_ready", "lossless"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_e373_receipt_integrity_artifact(value: Mapping[str, Any]) -> bytes:
    if validate_worldbridge_e373_receipt_integrity_artifact(value)["valid"] is not True:
        raise ValueError("invalid E373 integrity artifact")
    encoded = _canonical(value)
    if len(encoded) > MAX_ARTIFACT_BYTES:
        raise OverflowError("integrity artifact exceeds maximum size")
    return encoded


def decode_worldbridge_e373_receipt_integrity_artifact(encoded: bytes) -> dict[str, Any]:
    raw = bytes(encoded)
    if not raw or len(raw) > MAX_ARTIFACT_BYTES:
        raise ValueError("integrity artifact size is invalid")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("integrity artifact is not strict JSON") from exc
    if not isinstance(value, dict) or _canonical(value) != raw:
        raise ValueError("integrity artifact is not canonical JSON")
    if validate_worldbridge_e373_receipt_integrity_artifact(value)["valid"] is not True:
        raise ValueError("invalid E373 integrity artifact")
    return copy.deepcopy(value)


def consume_worldbridge_e373_receipt_artifact(
    encoded: bytes,
    consumed_integrity_digests: MutableSet[str],
) -> dict[str, Any]:
    value = decode_worldbridge_e373_receipt_integrity_artifact(encoded)
    digest = value["integrity_digest"]
    if digest in consumed_integrity_digests:
        raise ValueError("receipt artifact replay rejected")
    consumed_integrity_digests.add(digest)
    return value


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _integrity_digest(value: Mapping[str, Any]) -> str:
    unsigned = dict(value)
    unsigned.pop("integrity_digest", None)
    return _digest(unsigned)


__all__ = [
    "build_worldbridge_e373_receipt_integrity_artifact",
    "validate_worldbridge_e373_receipt_integrity_artifact",
    "encode_worldbridge_e373_receipt_integrity_artifact",
    "decode_worldbridge_e373_receipt_integrity_artifact",
    "consume_worldbridge_e373_receipt_artifact",
]
