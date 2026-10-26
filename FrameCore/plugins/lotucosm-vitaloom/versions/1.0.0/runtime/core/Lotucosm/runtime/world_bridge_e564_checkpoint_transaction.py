# -*- coding: utf-8 -*-
"""Locked checkpoint artifact export/import/restore transaction boundary."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .world_bridge_e384_receipt_ledger import build_project_world_identity
from .world_bridge_e563_cross_session_script_rehydration import (
    restore_cross_session_script_checkpoint,
    validate_cross_session_source_bundle,
)
from .world_bridge_script_checkpoint import validate_sr_script_checkpoint


SCHEMA_VERSION = 1
STATUS = "worldbridge_e564_checkpoint_artifact"
POLICY = "locked_checkpoint_source_bundle_transaction_v1"
TRANSACTION_DIRECTORY = ".vitaloom"
INTERLOCK_FILENAME = "worldbridge_e564_checkpoint_transaction.lock"
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ARTIFACT_KEYS = {
    "schema_version",
    "status",
    "policy",
    "runtime_contract_version",
    "checkpoint_graph",
    "source_bundle",
    "project_lock_digest",
    "project_world_identity",
    "artifact_digest",
}


class CheckpointTransactionError(RuntimeError):
    """Explicit E564 transaction failure with a stable diagnostic code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


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


def _artifact_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["artifact_digest"] = ""
    return _digest(payload)


def _project(project_path: str | Path) -> Path:
    project = Path(project_path).expanduser().resolve()
    if not project.is_dir():
        raise CheckpointTransactionError(
            "project_not_found",
            "checkpoint transaction project is not a directory",
        )
    return project


def _interlock_path(project: Path) -> Path:
    return project / TRANSACTION_DIRECTORY / INTERLOCK_FILENAME


def _read_project_lock(project: Path) -> tuple[dict[str, Any], str]:
    from core.VitaLoom.suite.project_lock import (
        load_project_lock,
        project_lock_schema_error,
    )

    lock = load_project_lock(project)
    if lock is None:
        raise CheckpointTransactionError(
            "project_lock_missing",
            "checkpoint transaction requires project.lock.json",
        )
    schema_error = project_lock_schema_error(lock)
    if schema_error:
        raise CheckpointTransactionError("project_lock_invalid", schema_error)
    return lock, _digest(lock)


def _validate_project_lock_digest(
    project: Path,
    expected_digest: object,
) -> str:
    _lock, actual_digest = _read_project_lock(project)
    if actual_digest != expected_digest:
        raise CheckpointTransactionError(
            "project_lock_drift",
            "checkpoint artifact project lock binding is stale",
        )
    return actual_digest


def _validate_work_graph(
    *,
    checkpoint_graph: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    project: Path,
    runtime_contract_version: str,
) -> None:
    graph_epoch = checkpoint_graph.get("runtime_epoch")
    if not isinstance(graph_epoch, str) or not graph_epoch:
        raise CheckpointTransactionError(
            "checkpoint_runtime_epoch_invalid",
            "checkpoint graph runtime epoch is invalid",
        )
    graph_validation = validate_sr_script_checkpoint(
        checkpoint_graph,
        runtime_epoch=graph_epoch,
    )
    if graph_validation["valid"] is not True:
        raise CheckpointTransactionError(
            "checkpoint_graph_invalid",
            ",".join(graph_validation["errors"]),
        )
    bundle_validation = validate_cross_session_source_bundle(
        source_bundle,
        checkpoint_graph=checkpoint_graph,
        project_path=project,
        expected_runtime_contract_version=runtime_contract_version,
    )
    if bundle_validation["valid"] is not True:
        raise CheckpointTransactionError(
            "checkpoint_source_bundle_invalid",
            ",".join(bundle_validation["errors"]),
        )


def checkpoint_interlock(
    project_path: str | Path,
) -> Any:
    """Hold the shared Project World write interlock for E564."""

    @contextmanager
    def _hold() -> Iterator[dict[str, Any]]:
        from core.VitaLoom.project.project_write_authority import (
            ProjectWriteInterlockError,
            project_write_interlock,
        )

        try:
            with project_write_interlock(
                project_path,
                authority_action="worldbridge_checkpoint_transaction",
            ) as ticket:
                yield ticket
        except ProjectWriteInterlockError as exc:
            if exc.code == "project_write_interlock_held":
                raise CheckpointTransactionError(
                    "checkpoint_interlock_held",
                    str(exc),
                ) from exc
            raise CheckpointTransactionError(
                "checkpoint_interlock_failed",
                str(exc),
            ) from exc

    return _hold()


def checkpoint_interlock_status(project_path: str | Path) -> dict[str, Any]:
    """Inspect the E564 interlock without acquiring or breaking it."""
    from core.VitaLoom.project.project_write_authority import (
        inspect_project_write_interlock,
    )

    inspection = inspect_project_write_interlock(project_path)
    record = inspection.get("record")
    return {
        "held": inspection["held"],
        "owner_pid": (
            record.get("pid") if isinstance(record, Mapping) else None
        ),
        "interlock_path": inspection["interlock_path"],
        "state": inspection["state"],
        "owner_nonce": (
            record.get("owner_nonce")
            if isinstance(record, Mapping)
            else None
        ),
    }


def _write_atomic(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(_canonical(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception as exc:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise CheckpointTransactionError(
            "checkpoint_artifact_write_failed",
            "checkpoint artifact atomic write failed",
        ) from exc


def export_checkpoint_artifact(
    *,
    project_path: str | Path,
    scene_path: str | Path,
    checkpoint_graph: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    runtime_contract_version: str,
    artifact_path: str | Path,
) -> dict[str, Any]:
    """Seal and atomically export a checkpoint under the project interlock."""
    if (
        not isinstance(runtime_contract_version, str)
        or not runtime_contract_version
    ):
        raise CheckpointTransactionError(
            "runtime_contract_version_invalid",
            "runtime contract version must be non-empty",
        )
    graph = copy.deepcopy(dict(checkpoint_graph))
    bundle = copy.deepcopy(dict(source_bundle))
    project = _project(project_path)
    output = Path(artifact_path).expanduser().resolve()
    with checkpoint_interlock(project) as interlock:
        _lock, lock_digest = _read_project_lock(project)
        _validate_work_graph(
            checkpoint_graph=graph,
            source_bundle=bundle,
            project=project,
            runtime_contract_version=runtime_contract_version,
        )
        try:
            world_identity = build_project_world_identity(project, scene_path)
        except Exception as exc:
            raise CheckpointTransactionError(
                "project_world_identity_invalid",
                "checkpoint transaction project/scene identity failed",
            ) from exc
        artifact: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS,
            "policy": POLICY,
            "runtime_contract_version": runtime_contract_version,
            "checkpoint_graph": graph,
            "source_bundle": bundle,
            "project_lock_digest": lock_digest,
            "project_world_identity": world_identity,
            "artifact_digest": "",
        }
        artifact["artifact_digest"] = _artifact_digest(artifact)
        _write_atomic(output, artifact)
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "worldbridge_e564_checkpoint_export",
            "read_only": False,
            "decision": "exported",
            "artifact_path": str(output),
            "artifact_digest": artifact["artifact_digest"],
            "project_lock_digest": lock_digest,
            "checkpoint_graph_digest": graph["graph_digest"],
            "source_bundle_digest": bundle["bundle_digest"],
            "interlock": interlock,
            "errors": [],
        }


def validate_checkpoint_artifact(
    value: object,
    *,
    project_path: str | Path,
    scene_path: str | Path,
    expected_runtime_contract_version: str,
) -> dict[str, Any]:
    """Validate artifact shape and its live project/lock/source binding."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["artifact_not_mapping"]}
    if set(value) != _ARTIFACT_KEYS:
        errors.append("artifact_keys_invalid")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("artifact_schema_mismatch")
    if value.get("status") != STATUS:
        errors.append("artifact_status_mismatch")
    if value.get("policy") != POLICY:
        errors.append("artifact_policy_mismatch")
    if (
        value.get("runtime_contract_version")
        != expected_runtime_contract_version
    ):
        errors.append("artifact_runtime_contract_mismatch")
    artifact_digest = value.get("artifact_digest")
    if (
        not isinstance(artifact_digest, str)
        or _DIGEST_RE.fullmatch(artifact_digest) is None
    ):
        errors.append("artifact_digest_invalid")
    else:
        try:
            if artifact_digest != _artifact_digest(value):
                errors.append("artifact_digest_mismatch")
        except (TypeError, ValueError, OverflowError):
            errors.append("artifact_not_canonical_json")

    graph = value.get("checkpoint_graph")
    bundle = value.get("source_bundle")
    project = _project(project_path)
    if not isinstance(graph, Mapping):
        errors.append("artifact_checkpoint_graph_invalid")
    if not isinstance(bundle, Mapping):
        errors.append("artifact_source_bundle_invalid")
    if isinstance(graph, Mapping) and isinstance(bundle, Mapping):
        graph_epoch = graph.get("runtime_epoch")
        if isinstance(graph_epoch, str) and graph_epoch:
            graph_validation = validate_sr_script_checkpoint(
                graph,
                runtime_epoch=graph_epoch,
            )
            errors.extend(
                f"artifact_checkpoint_{item}"
                for item in graph_validation["errors"]
            )
        else:
            errors.append("artifact_checkpoint_runtime_epoch_invalid")
        bundle_validation = validate_cross_session_source_bundle(
            bundle,
            checkpoint_graph=graph,
            project_path=project,
            expected_runtime_contract_version=expected_runtime_contract_version,
        )
        errors.extend(
            f"artifact_bundle_{item}"
            for item in bundle_validation["errors"]
        )
    try:
        _lock, lock_digest = _read_project_lock(project)
    except CheckpointTransactionError as exc:
        errors.append(f"artifact_{exc.code}")
        lock_digest = None
    if (
        lock_digest is not None
        and value.get("project_lock_digest") != lock_digest
    ):
        errors.append("artifact_project_lock_mismatch")
    try:
        identity = build_project_world_identity(project, scene_path)
    except Exception:
        errors.append("artifact_project_world_identity_unavailable")
    else:
        if value.get("project_world_identity") != identity:
            errors.append("artifact_project_world_identity_mismatch")
    return {
        "valid": not errors,
        "errors": list(dict.fromkeys(errors)),
        "artifact_digest": (
            artifact_digest if isinstance(artifact_digest, str) else None
        ),
    }


def _load_locked_artifact(
    *,
    artifact_path: str | Path,
    project: Path,
    scene_path: str | Path,
    runtime_contract_version: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = Path(artifact_path).expanduser().resolve()
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CheckpointTransactionError(
            "checkpoint_artifact_missing",
            "checkpoint artifact is missing or unreadable",
        ) from exc
    try:
        artifact = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CheckpointTransactionError(
            "checkpoint_artifact_malformed",
            "checkpoint artifact is not canonical JSON",
        ) from exc
    validation = validate_checkpoint_artifact(
        artifact,
        project_path=project,
        scene_path=scene_path,
        expected_runtime_contract_version=runtime_contract_version,
    )
    if validation["valid"] is not True:
        raise CheckpointTransactionError(
            "checkpoint_artifact_invalid",
            ",".join(validation["errors"]),
        )
    if _canonical(artifact) != raw:
        raise CheckpointTransactionError(
            "checkpoint_artifact_not_canonical",
            "checkpoint artifact bytes are not canonical",
        )
    return artifact, validation


def import_checkpoint_artifact(
    *,
    project_path: str | Path,
    scene_path: str | Path,
    artifact_path: str | Path,
    runtime_contract_version: str,
) -> dict[str, Any]:
    """Validate and decode an artifact while holding the project interlock."""
    project = _project(project_path)
    with checkpoint_interlock(project) as interlock:
        artifact, validation = _load_locked_artifact(
            artifact_path=artifact_path,
            project=project,
            scene_path=scene_path,
            runtime_contract_version=runtime_contract_version,
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "worldbridge_e564_checkpoint_import",
            "read_only": True,
            "decision": "imported",
            "artifact_digest": validation["artifact_digest"],
            "checkpoint_graph": copy.deepcopy(artifact["checkpoint_graph"]),
            "source_bundle": copy.deepcopy(artifact["source_bundle"]),
            "project_lock_digest": artifact["project_lock_digest"],
            "project_world_identity": copy.deepcopy(
                artifact["project_world_identity"]
            ),
            "interlock": interlock,
            "errors": [],
        }


def restore_checkpoint_artifact(
    *,
    project_path: str | Path,
    scene_path: str | Path,
    artifact_path: str | Path,
    runtime_contract_version: str,
    target_runtime_epoch: str,
    entities: Any,
    instantiate_script: Callable[[dict[str, Any]], object | None],
) -> dict[str, Any]:
    """Import and restore one artifact under a single project interlock."""
    project = _project(project_path)
    with checkpoint_interlock(project) as interlock:
        artifact, validation = _load_locked_artifact(
            artifact_path=artifact_path,
            project=project,
            scene_path=scene_path,
            runtime_contract_version=runtime_contract_version,
        )
        # Recheck both lock and world identity immediately before executable
        # script construction, so a changed project cannot consume the artifact.
        _validate_project_lock_digest(
            project,
            artifact["project_lock_digest"],
        )
        current_identity = build_project_world_identity(project, scene_path)
        if current_identity != artifact["project_world_identity"]:
            raise CheckpointTransactionError(
                "project_world_identity_drift",
                "checkpoint project identity changed before restore",
            )
        restore_result = restore_cross_session_script_checkpoint(
            checkpoint_graph=artifact["checkpoint_graph"],
            source_bundle=artifact["source_bundle"],
            runtime_contract_version=runtime_contract_version,
            target_runtime_epoch=target_runtime_epoch,
            project_path=project,
            entities=entities,
            instantiate_script=instantiate_script,
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "worldbridge_e564_checkpoint_restore",
            "read_only": False,
            "decision": restore_result["decision"],
            "artifact_digest": validation["artifact_digest"],
            "checkpoint_graph_digest": artifact["checkpoint_graph"][
                "graph_digest"
            ],
            "source_bundle_digest": artifact["source_bundle"][
                "bundle_digest"
            ],
            "project_lock_digest": artifact["project_lock_digest"],
            "project_world_identity": copy.deepcopy(
                artifact["project_world_identity"]
            ),
            "restore_result": restore_result,
            "interlock": interlock,
            "errors": [],
        }


__all__ = [
    "CheckpointTransactionError",
    "INTERLOCK_FILENAME",
    "POLICY",
    "SCHEMA_VERSION",
    "STATUS",
    "checkpoint_interlock",
    "checkpoint_interlock_status",
    "export_checkpoint_artifact",
    "import_checkpoint_artifact",
    "restore_checkpoint_artifact",
    "validate_checkpoint_artifact",
]
