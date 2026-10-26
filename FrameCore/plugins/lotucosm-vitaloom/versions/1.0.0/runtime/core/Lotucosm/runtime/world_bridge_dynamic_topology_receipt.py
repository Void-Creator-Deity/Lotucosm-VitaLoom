"""Digest-bound topology receipt for dynamic SR spawn/checkpoint evidence."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_dynamic_topology_receipt"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def build_worldbridge_dynamic_topology_receipt(
    *,
    runtime_epoch: str,
    generation: int,
    structure_fingerprint: Mapping[str, Any],
    component_identity_artifact: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(runtime_epoch, str) or not runtime_epoch.strip():
        raise ValueError("runtime_epoch must be non-empty")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ValueError("generation must be non-negative")
    structure = copy.deepcopy(dict(structure_fingerprint))
    fingerprint = structure.get("fingerprint")
    if not _is_digest(fingerprint):
        raise ValueError("structure fingerprint is invalid")
    artifact = None if component_identity_artifact is None else copy.deepcopy(dict(component_identity_artifact))
    if artifact is not None:
        from .world_bridge_component_identity_artifact import (
            validate_worldbridge_component_identity_artifact,
        )

        validation = validate_worldbridge_component_identity_artifact(artifact)
        if not validation["valid"]:
            raise ValueError(
                "component identity artifact is invalid: "
                + ",".join(validation["errors"])
            )
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "runtime_epoch": runtime_epoch,
        "generation": generation,
        "structure_fingerprint": fingerprint,
        "component_identity_artifact_digest": None if artifact is None else _digest(artifact),
        "component_identity_artifact": artifact,
        "live_topology_mutation": False,
        "replay_admitted": False,
        "receipt_digest": "",
    }
    receipt["receipt_digest"] = _digest(receipt)
    return copy.deepcopy(receipt)


def validate_worldbridge_dynamic_topology_receipt(value: object, *, runtime_epoch: str | None = None) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["receipt_must_be_mapping"]}
    required = {
        "schema_version", "status", "runtime_epoch", "generation", "structure_fingerprint",
        "component_identity_artifact_digest", "component_identity_artifact",
        "live_topology_mutation", "replay_admitted", "receipt_digest",
    }
    if set(value) != required:
        errors.append("receipt_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("receipt_version_mismatch")
    epoch = value.get("runtime_epoch")
    if not isinstance(epoch, str) or not epoch.strip():
        errors.append("receipt_runtime_epoch_invalid")
    if runtime_epoch is not None and value.get("runtime_epoch") != runtime_epoch:
        errors.append("receipt_runtime_epoch_mismatch")
    if isinstance(value.get("generation"), bool) or not isinstance(value.get("generation"), int) or value.get("generation", -1) < 0:
        errors.append("receipt_generation_invalid")
    if not _is_digest(value.get("structure_fingerprint")):
        errors.append("receipt_structure_fingerprint_invalid")
    artifact = value.get("component_identity_artifact")
    if artifact is not None:
        if not isinstance(artifact, Mapping):
            errors.append("receipt_component_artifact_invalid")
        else:
            from .world_bridge_component_identity_artifact import (
                validate_worldbridge_component_identity_artifact,
            )

            artifact_validation = validate_worldbridge_component_identity_artifact(artifact)
            if not artifact_validation["valid"]:
                errors.append("receipt_component_artifact_invalid")
    try:
        expected_artifact_digest = None if artifact is None else _digest(artifact)
    except (TypeError, ValueError, OverflowError):
        expected_artifact_digest = None
        errors.append("receipt_component_artifact_not_canonical")
    if value.get("component_identity_artifact_digest") != expected_artifact_digest:
        errors.append("receipt_component_artifact_digest_mismatch")
    if value.get("live_topology_mutation") is not False or value.get("replay_admitted") is not False:
        errors.append("receipt_admission_overclaim")
    candidate = dict(value)
    candidate["receipt_digest"] = ""
    try:
        expected_receipt_digest = _digest(candidate)
    except (TypeError, ValueError, OverflowError):
        expected_receipt_digest = None
        errors.append("receipt_not_canonical")
    if value.get("receipt_digest") != expected_receipt_digest:
        errors.append("receipt_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def _is_digest(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


__all__ = [
    "build_worldbridge_dynamic_topology_receipt",
    "validate_worldbridge_dynamic_topology_receipt",
]
