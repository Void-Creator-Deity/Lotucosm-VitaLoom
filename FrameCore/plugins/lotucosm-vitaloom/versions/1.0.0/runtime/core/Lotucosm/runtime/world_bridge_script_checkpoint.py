# -*- coding: utf-8 -*-
"""Project-source-bound SR scene-script checkpoint overlay."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Callable


SCHEMA_VERSION = 1
STATUS = "worldbridge_sr_script_checkpoint"
POLICY = "project_source_bound_scene_script_descriptor_v1"
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_INTERNAL_STATE_KEYS = frozenset(
    {
        "_scene_script_path",
        "_scene_script_properties",
        "_script_entropy_audit",
    }
)
_OVERLAY_KEYS = {
    "schema_version",
    "status",
    "policy",
    "runtime_epoch",
    "entities",
    "graph_digest",
}
_ENTITY_KEYS = {"entity_id", "scripts"}
_SCRIPT_KEYS = {
    "script_type",
    "source_path",
    "source_sha256",
    "properties",
    "runtime_state",
    "rebound_state_fields",
}


class ScriptCheckpointUnavailable(RuntimeError):
    """Raised when a live script cannot be represented by this overlay."""


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


def _graph_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["graph_digest"] = ""
    return _digest(payload)


def _json_value(value: object) -> Any | None:
    try:
        return json.loads(_canonical(value).decode("utf-8"))
    except (TypeError, ValueError, OverflowError):
        return None


def _script_type_name(script: object) -> str:
    script_type = type(script)
    module = script_type.__module__
    qualname = script_type.__qualname__
    if module.startswith("vitaloom_user_script_"):
        return qualname
    return f"{module}.{qualname}"


def _script_type_matches(script: object, declared: object) -> bool:
    if not isinstance(declared, str) or not declared:
        return False
    script_type = type(script)
    module = script_type.__module__
    qualname = script_type.__qualname__
    if declared in {qualname, f"{module}.{qualname}"}:
        return True
    if module.startswith("vitaloom_user_script_"):
        return declared.rsplit(".", 1)[-1] == qualname
    return False


def _relative_source_path(path: object, project_path: Path) -> str:
    if not isinstance(path, str) or not path.strip():
        raise ScriptCheckpointUnavailable("script_source_path_missing")
    source = Path(path).resolve()
    try:
        return source.relative_to(project_path).as_posix()
    except ValueError as exc:
        raise ScriptCheckpointUnavailable(
            "script_source_path_outside_project"
        ) from exc


def _describe_script(script: object, project_path: Path) -> dict[str, Any]:
    relative_path = _relative_source_path(
        getattr(script, "_scene_script_path", None),
        project_path,
    )
    source_path = project_path / relative_path
    if not source_path.is_file():
        raise ScriptCheckpointUnavailable("script_source_file_missing")
    properties = _json_value(getattr(script, "_scene_script_properties", {}))
    if not isinstance(properties, dict):
        raise ScriptCheckpointUnavailable("script_properties_not_portable")

    runtime_state: dict[str, Any] = {}
    rebound_state_fields: list[str] = []
    for name, value in vars(script).items():
        if name in _INTERNAL_STATE_KEYS:
            continue
        detached = _json_value(value)
        if detached is None and value is not None:
            rebound_state_fields.append(str(name))
            continue
        runtime_state[str(name)] = detached

    return {
        "script_type": _script_type_name(script),
        "source_path": relative_path,
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "properties": properties,
        "runtime_state": runtime_state,
        "rebound_state_fields": sorted(rebound_state_fields),
    }


def capture_sr_script_checkpoint(
    *,
    runtime_epoch: str,
    project_path: str | Path,
    entities: Iterable[object],
) -> dict[str, Any]:
    """Capture file-backed SR scripts as portable, source-bound descriptors."""
    if not isinstance(runtime_epoch, str) or not runtime_epoch.strip():
        raise ValueError("runtime_epoch must be non-empty")
    project = Path(project_path).resolve()
    if not project.is_dir():
        raise ScriptCheckpointUnavailable("project_path_unavailable")

    entity_rows: list[dict[str, Any]] = []
    seen_entities: set[str] = set()
    for entity in entities:
        entity_id = str(getattr(entity, "id", "") or "")
        if not entity_id:
            raise ScriptCheckpointUnavailable("entity_id_missing")
        if entity_id in seen_entities:
            raise ScriptCheckpointUnavailable("duplicate_entity_id")
        seen_entities.add(entity_id)
        scripts = getattr(entity, "scripts", None)
        if scripts is None:
            scripts = []
        if not isinstance(scripts, list):
            raise ScriptCheckpointUnavailable("entity_scripts_invalid")
        entity_rows.append(
            {
                "entity_id": entity_id,
                "scripts": [
                    _describe_script(script, project) for script in scripts
                ],
            }
        )
    overlay: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "policy": POLICY,
        "runtime_epoch": runtime_epoch,
        "entities": entity_rows,
        "graph_digest": "",
    }
    overlay["graph_digest"] = _graph_digest(overlay)
    return overlay


def validate_sr_script_checkpoint(
    value: object,
    *,
    runtime_epoch: str,
) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["graph_not_mapping"]}
    if set(value) != _OVERLAY_KEYS:
        errors.append("graph_keys_invalid")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("policy") != POLICY:
        errors.append("policy_mismatch")
    if value.get("runtime_epoch") != runtime_epoch:
        errors.append("runtime_epoch_mismatch")
    entities = value.get("entities")
    if not isinstance(entities, list):
        return {"valid": False, "errors": errors + ["entities_invalid"]}

    seen_entities: set[str] = set()
    for entity_index, entity in enumerate(entities):
        if not isinstance(entity, Mapping) or set(entity) != _ENTITY_KEYS:
            errors.append(f"entity_{entity_index}_invalid")
            continue
        entity_id = entity.get("entity_id")
        if not isinstance(entity_id, str) or not entity_id:
            errors.append(f"entity_{entity_index}_id_invalid")
        elif entity_id in seen_entities:
            errors.append(f"entity_{entity_index}_duplicate")
        else:
            seen_entities.add(entity_id)
        scripts = entity.get("scripts")
        if not isinstance(scripts, list):
            errors.append(f"entity_{entity_index}_scripts_invalid")
            continue
        for script_index, script in enumerate(scripts):
            prefix = f"entity_{entity_index}_script_{script_index}"
            if not isinstance(script, Mapping) or set(script) != _SCRIPT_KEYS:
                errors.append(f"{prefix}_keys_invalid")
                continue
            if (
                not isinstance(script.get("script_type"), str)
                or not script["script_type"]
            ):
                errors.append(f"{prefix}_type_invalid")
            source_path = script.get("source_path")
            if (
                not isinstance(source_path, str)
                or not source_path
                or Path(source_path).is_absolute()
                or ".." in Path(source_path).parts
            ):
                errors.append(f"{prefix}_source_path_invalid")
            source_digest = script.get("source_sha256")
            if (
                not isinstance(source_digest, str)
                or _DIGEST_RE.fullmatch(source_digest) is None
            ):
                errors.append(f"{prefix}_source_digest_invalid")
            if not isinstance(script.get("properties"), Mapping):
                errors.append(f"{prefix}_properties_invalid")
            if not isinstance(script.get("runtime_state"), Mapping):
                errors.append(f"{prefix}_runtime_state_invalid")
            rebound = script.get("rebound_state_fields")
            if (
                not isinstance(rebound, list)
                or any(not isinstance(item, str) or not item for item in rebound)
                or len(set(rebound)) != len(rebound)
            ):
                errors.append(f"{prefix}_rebound_fields_invalid")
    try:
        if value.get("graph_digest") != _graph_digest(value):
            errors.append("graph_digest_mismatch")
    except (TypeError, ValueError, OverflowError):
        errors.append("graph_not_canonical_json")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}


def retarget_sr_script_checkpoint(
    value: object,
    *,
    target_runtime_epoch: str,
) -> dict[str, Any]:
    """Validate a source-session graph and reseal it for a fresh session.

    Cross-session restore must not mutate the source checkpoint. The returned
    graph keeps every script descriptor unchanged while binding the graph
    digest to the target runtime epoch.
    """
    if not isinstance(target_runtime_epoch, str) or not target_runtime_epoch:
        raise ValueError("target_runtime_epoch must be non-empty")
    if not isinstance(value, Mapping):
        raise ValueError("SR script checkpoint must be a mapping")
    source_runtime_epoch = value.get("runtime_epoch")
    if not isinstance(source_runtime_epoch, str) or not source_runtime_epoch:
        raise ValueError("SR script checkpoint runtime_epoch is invalid")
    validation = validate_sr_script_checkpoint(
        value,
        runtime_epoch=source_runtime_epoch,
    )
    if validation["valid"] is not True:
        raise ValueError(
            "SR script checkpoint invalid: " + ",".join(validation["errors"])
        )
    retargeted = copy.deepcopy(dict(value))
    retargeted["runtime_epoch"] = target_runtime_epoch
    retargeted["graph_digest"] = _graph_digest(retargeted)
    target_validation = validate_sr_script_checkpoint(
        retargeted,
        runtime_epoch=target_runtime_epoch,
    )
    if target_validation["valid"] is not True:
        raise ValueError(
            "retargeted SR script checkpoint invalid: "
            + ",".join(target_validation["errors"])
        )
    return retargeted


def restore_sr_script_checkpoint(
    value: object,
    *,
    runtime_epoch: str,
    project_path: str | Path,
    entities: Iterable[object],
    instantiate_script: Callable[[dict[str, Any]], object | None],
) -> dict[str, Any]:
    """Rehydrate and atomically replace each entity's file-backed script list."""
    validation = validate_sr_script_checkpoint(
        value,
        runtime_epoch=runtime_epoch,
    )
    if validation["valid"] is not True:
        raise ValueError(
            "SR script checkpoint invalid: " + ",".join(validation["errors"])
        )
    overlay = copy.deepcopy(dict(value))
    project = Path(project_path).resolve()
    entity_by_id = {
        str(getattr(entity, "id", "") or ""): entity for entity in entities
    }
    declared_ids = {
        str(entity["entity_id"]) for entity in overlay["entities"]
    }
    if set(entity_by_id) != declared_ids:
        raise ValueError("SR script checkpoint entity set mismatch")

    prepared: dict[str, list[object]] = {}
    for entity in overlay["entities"]:
        entity_id = str(entity["entity_id"])
        scripts: list[object] = []
        for descriptor in entity["scripts"]:
            source_path = project / descriptor["source_path"]
            if not source_path.is_file():
                raise ValueError("SR script checkpoint source file missing")
            current_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
            if current_digest != descriptor["source_sha256"]:
                raise ValueError("SR script checkpoint source digest mismatch")
            script = instantiate_script(
                {
                    "path": str(source_path),
                    "type": descriptor["script_type"].rsplit(".", 1)[-1],
                    "properties": copy.deepcopy(descriptor["properties"]),
                }
            )
            if script is None:
                raise ValueError("SR script checkpoint instantiation failed")
            if not _script_type_matches(script, descriptor["script_type"]):
                raise ValueError("SR script checkpoint type mismatch")
            scripts.append(script)
        prepared[entity_id] = scripts

    originals = {
        entity_id: list(getattr(entity, "scripts", ()))
        for entity_id, entity in entity_by_id.items()
    }
    replaced: list[str] = []
    try:
        for entity_row in overlay["entities"]:
            entity_id = str(entity_row["entity_id"])
            entity = entity_by_id[entity_id]
            replace = getattr(entity, "replace_scripts", None)
            if not callable(replace):
                raise ValueError("SR script checkpoint owner API unavailable")
            replace(prepared[entity_id])
            replaced.append(entity_id)
            for script, descriptor in zip(
                prepared[entity_id],
                entity_row["scripts"],
            ):
                for name, state in descriptor["runtime_state"].items():
                    setattr(script, name, copy.deepcopy(state))
                for name in descriptor["rebound_state_fields"]:
                    if not hasattr(script, name):
                        raise ValueError(
                            "SR script checkpoint rebound state missing: " + name
                        )
    except Exception:
        for entity_id in reversed(replaced):
            entity_by_id[entity_id].replace_scripts(originals[entity_id])
        raise

    return {
        "schema_version": 1,
        "status": "worldbridge_sr_script_checkpoint_restore",
        "read_only": False,
        "runtime_epoch": runtime_epoch,
        "restored_entities": len(replaced),
        "restored_scripts": sum(len(rows) for rows in prepared.values()),
        "graph_digest": overlay["graph_digest"],
    }


__all__ = [
    "POLICY",
    "SCHEMA_VERSION",
    "STATUS",
    "ScriptCheckpointUnavailable",
    "capture_sr_script_checkpoint",
    "retarget_sr_script_checkpoint",
    "restore_sr_script_checkpoint",
    "validate_sr_script_checkpoint",
]
