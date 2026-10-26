# -*- coding: utf-8 -*-
"""Scoped authority for same-host SR scene-script checkpoint round-trips."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from .world_bridge_script_checkpoint import (
    validate_sr_script_checkpoint,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e562_script_checkpoint_authority"
SCOPE = "project_source_bound_same_host_scene_script_roundtrip"
POLICY = "rehydrate_scene_scripts_from_trusted_project_source_v1"
ADMISSION_EFFECT = "none"
PROOF_FIELDS = (
    "source_graph_valid",
    "restore_succeeded",
    "recaptured_graph_valid",
    "runtime_epoch_equal",
    "graph_digest_equal",
    "entity_count_equal",
    "script_count_equal",
    "source_paths_project_relative",
    "descriptors_equal",
)
CLOSED_ADMISSION_FIELDS = (
    "script_checkpoint_admitted",
    "lossless",
    "default_ready",
)
WITNESS_KEYS = (
    "schema_version",
    "status",
    "read_only",
    "scope",
    "policy",
    "runtime_epoch",
    "source_script_graph",
    "restore_result",
    "recaptured_script_graph",
    "source_graph_digest",
    "recaptured_graph_digest",
    *PROOF_FIELDS,
    "remaining_script_blockers",
    "grants_admission",
    "admission_effect",
    *CLOSED_ADMISSION_FIELDS,
    "witness_digest",
)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _json_copy(value: object, field: str) -> Any:
    try:
        return json.loads(_canonical(value).decode("utf-8"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be finite canonical JSON") from exc


def _mapping_copy(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a mapping")
    copied = _json_copy(dict(value), field)
    if not isinstance(copied, dict):
        raise TypeError(f"{field} must remain a mapping")
    return copied


def _witness_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["witness_digest"] = ""
    return _digest(payload)


def _script_count(graph: Mapping[str, Any]) -> int:
    entities = graph.get("entities")
    if not isinstance(entities, list):
        return 0
    return sum(
        len(entity.get("scripts", []))
        for entity in entities
        if isinstance(entity, Mapping)
        and isinstance(entity.get("scripts"), list)
    )


def _evaluate(
    *,
    runtime_epoch: str,
    source_graph: Mapping[str, Any],
    restore_result: Mapping[str, Any],
    recaptured_graph: Mapping[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    source_validation = validate_sr_script_checkpoint(
        source_graph,
        runtime_epoch=runtime_epoch,
    )
    recaptured_validation = validate_sr_script_checkpoint(
        recaptured_graph,
        runtime_epoch=runtime_epoch,
    )
    source_graph_valid = source_validation == {"valid": True, "errors": []}
    recaptured_graph_valid = recaptured_validation == {
        "valid": True,
        "errors": [],
    }
    if not source_graph_valid:
        errors.extend(f"source_{item}" for item in source_validation["errors"])
    if not recaptured_graph_valid:
        errors.extend(
            f"recaptured_{item}" for item in recaptured_validation["errors"]
        )

    restore_succeeded = (
        restore_result.get("status")
        == "worldbridge_sr_script_checkpoint_restore"
        and restore_result.get("runtime_epoch") == runtime_epoch
        and restore_result.get("restored_entities")
        == len(source_graph.get("entities", ()))
        and restore_result.get("restored_scripts") == _script_count(source_graph)
    )
    if not restore_succeeded:
        errors.append("script_restore_result_invalid")

    source_epochs = {
        source_graph.get("runtime_epoch"),
        recaptured_graph.get("runtime_epoch"),
    }
    runtime_epoch_equal = source_epochs == {runtime_epoch}
    if not runtime_epoch_equal:
        errors.append("script_runtime_epoch_mismatch")

    graph_digest_equal = (
        source_graph.get("graph_digest")
        == recaptured_graph.get("graph_digest")
    )
    if not graph_digest_equal:
        errors.append("script_graph_digest_mismatch")

    source_entities = source_graph.get("entities")
    recaptured_entities = recaptured_graph.get("entities")
    entity_count_equal = (
        isinstance(source_entities, list)
        and isinstance(recaptured_entities, list)
        and len(source_entities) == len(recaptured_entities)
    )
    if not entity_count_equal:
        errors.append("script_entity_count_mismatch")

    script_count_equal = _script_count(source_graph) == _script_count(
        recaptured_graph
    )
    if not script_count_equal:
        errors.append("script_count_mismatch")

    source_paths_project_relative = all(
        isinstance(script.get("source_path"), str)
        and not script["source_path"].startswith(("/", "\\"))
        and ".." not in script["source_path"].replace("\\", "/").split("/")
        for entity in source_entities or ()
        if isinstance(entity, Mapping)
        for script in entity.get("scripts", ())
        if isinstance(script, Mapping)
    )
    if not source_paths_project_relative:
        errors.append("script_source_path_not_project_relative")

    descriptors_equal = source_entities == recaptured_entities
    if not descriptors_equal:
        errors.append("script_descriptors_mismatch")

    proof = {
        "source_graph_valid": source_graph_valid,
        "restore_succeeded": restore_succeeded,
        "recaptured_graph_valid": recaptured_graph_valid,
        "runtime_epoch_equal": runtime_epoch_equal,
        "graph_digest_equal": graph_digest_equal,
        "entity_count_equal": entity_count_equal,
        "script_count_equal": script_count_equal,
        "source_paths_project_relative": source_paths_project_relative,
        "descriptors_equal": descriptors_equal,
    }
    for field in PROOF_FIELDS:
        if proof[field] is not True:
            errors.append(f"{field}_not_proven")
    return list(dict.fromkeys(errors)), {
        **proof,
        "runtime_epoch": runtime_epoch,
        "source_graph_digest": source_graph.get("graph_digest"),
        "recaptured_graph_digest": recaptured_graph.get("graph_digest"),
    }


def build_worldbridge_e562_script_checkpoint_authority(
    *,
    runtime_epoch: str,
    source_script_graph: Mapping[str, Any],
    restore_result: Mapping[str, Any],
    recaptured_script_graph: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(runtime_epoch, str) or not runtime_epoch:
        raise ValueError("runtime_epoch must be non-empty")
    source = _mapping_copy(source_script_graph, "source_script_graph")
    restore = _mapping_copy(restore_result, "restore_result")
    recaptured = _mapping_copy(
        recaptured_script_graph,
        "recaptured_script_graph",
    )
    errors, projection = _evaluate(
        runtime_epoch=runtime_epoch,
        source_graph=source,
        restore_result=restore,
        recaptured_graph=recaptured,
    )
    if errors:
        raise ValueError(
            "E562 script checkpoint witness rejected: " + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "policy": POLICY,
        "source_script_graph": source,
        "restore_result": restore,
        "recaptured_script_graph": recaptured,
        **projection,
        "remaining_script_blockers": [
            "cross_session_script_rehydration_not_proven",
            "arbitrary_external_script_state_not_admitted",
        ],
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e562_script_checkpoint_authority(
    value: object,
) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    if set(value) != set(WITNESS_KEYS):
        errors.append("witness_keys_invalid")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_required")
    if value.get("scope") != SCOPE:
        errors.append("scope_mismatch")
    if value.get("policy") != POLICY:
        errors.append("policy_mismatch")
    source = value.get("source_script_graph")
    restore = value.get("restore_result")
    recaptured = value.get("recaptured_script_graph")
    runtime_epoch = value.get("runtime_epoch")
    if (
        not isinstance(source, Mapping)
        or not isinstance(restore, Mapping)
        or not isinstance(recaptured, Mapping)
        or not isinstance(runtime_epoch, str)
    ):
        return {"valid": False, "errors": errors + ["witness_payload_invalid"]}
    revalidation, projection = _evaluate(
        runtime_epoch=runtime_epoch,
        source_graph=source,
        restore_result=restore,
        recaptured_graph=recaptured,
    )
    errors.extend(revalidation)
    for field, expected in projection.items():
        if value.get(field) != expected:
            errors.append(f"{field}_mismatch")
        if field in PROOF_FIELDS and value.get(field) is not True:
            errors.append(f"{field}_not_true")
    if value.get("remaining_script_blockers") != [
        "cross_session_script_rehydration_not_proven",
        "arbitrary_external_script_state_not_admitted",
    ]:
        errors.append("remaining_script_blockers_mismatch")
    if value.get("grants_admission") is not False:
        errors.append("grants_admission_overclaim")
    if value.get("admission_effect") != ADMISSION_EFFECT:
        errors.append("admission_effect_mismatch")
    for field in CLOSED_ADMISSION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    digest = value.get("witness_digest")
    if (
        not isinstance(digest, str)
        or _DIGEST_RE.fullmatch(digest) is None
        or digest != _witness_digest(value)
    ):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}


__all__ = [
    "ADMISSION_EFFECT",
    "CLOSED_ADMISSION_FIELDS",
    "POLICY",
    "PROOF_FIELDS",
    "SCHEMA_VERSION",
    "SCOPE",
    "STATUS",
    "WITNESS_KEYS",
    "build_worldbridge_e562_script_checkpoint_authority",
    "validate_worldbridge_e562_script_checkpoint_authority",
]
