"""Canonical project-local write interlock with same-thread reentrancy."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import threading
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from core.VitaLoom.project.asset_transaction_interlock import (
    AssetTransactionInterlockError,
    AssetTransactionInterlockLease,
    acquire_asset_transaction_interlock,
    inspect_asset_transaction_interlock,
)


SCHEMA_VERSION = 1
WITNESS_STATUS = "project_write_authority"
WITNESS_SCOPE = "supported_project_write_seams"
PROOF_FIELDS = (
    "checkpoint_import_blocked",
    "asset_transaction_blocked",
    "project_lock_refresh_blocked",
    "project_save_blocked",
    "post_release_import_succeeded",
    "interlock_released",
    "holder_importer_distinct",
)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATE = threading.local()


class ProjectWriteInterlockError(RuntimeError):
    """Structured failure for the canonical Project World write lock."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})


def _project(project_root: str | Path) -> Path:
    project = Path(project_root).expanduser().resolve()
    if not project.is_dir() or not (project / "project.json").is_file():
        raise ProjectWriteInterlockError(
            "project_write_project_not_found",
            "project_root must contain project.json",
            details={"project_path": str(project)},
        )
    return project


def _held() -> dict[str, dict[str, Any]]:
    current = getattr(_STATE, "held", None)
    if current is None:
        current = {}
        _STATE.held = current
    return current


def _pid_is_alive(pid: int) -> bool:
    if pid < 1:
        return False
    if sys.platform == "win32":
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        process_query_limited_information = 0x1000
        handle = kernel32.OpenProcess(
            process_query_limited_information,
            False,
            pid,
        )
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return ctypes.get_last_error() == 5  # ERROR_ACCESS_DENIED
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def inspect_project_write_interlock(project_root: str | Path) -> dict[str, Any]:
    """Inspect the shared lock record without changing it."""
    project = _project(project_root)
    inspection = inspect_asset_transaction_interlock(project)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "project_write_interlock",
        "project_path": str(project),
        "held": inspection.get("held") is True,
        "state": inspection.get("status"),
        "interlock_path": inspection.get("interlock_path"),
        "record": inspection.get("record"),
        "error_code": inspection.get("error_code"),
    }


@contextmanager
def project_write_interlock(
    project_root: str | Path,
    *,
    authority_action: str,
) -> Iterator[dict[str, Any]]:
    """Acquire one cross-process lock, reentrant in the owning thread."""
    project = _project(project_root)
    action = str(authority_action or "").strip()
    if not action:
        raise ProjectWriteInterlockError(
            "project_write_action_invalid",
            "authority_action is required",
        )
    key = str(project)
    held = _held()
    existing = held.get(key)
    if existing is not None:
        existing["depth"] = int(existing["depth"]) + 1
        existing["actions"].append(action)
        try:
            yield {
                "schema_version": SCHEMA_VERSION,
                "status": "held_reentrant",
                "owner_pid": os.getpid(),
                "owner_nonce": existing["lease"].inspection["record"][
                    "owner_nonce"
                ],
                "depth": existing["depth"],
                "authority_action": action,
                "interlock_path": existing["lease"].inspection[
                    "interlock_path"
                ],
            }
        finally:
            existing["actions"].pop()
            existing["depth"] = int(existing["depth"]) - 1
        return
    try:
        lease = acquire_asset_transaction_interlock(
            project,
            authority_action=action,
        )
    except AssetTransactionInterlockError as exc:
        raise ProjectWriteInterlockError(
            "project_write_interlock_held"
            if exc.code == "asset_transaction_interlock_held"
            else exc.code,
            str(exc),
            details=exc.details,
        ) from exc
    record = lease.inspection["record"]
    entry = {
        "lease": lease,
        "depth": 1,
        "actions": [action],
    }
    held[key] = entry
    try:
        yield {
            "schema_version": SCHEMA_VERSION,
            "status": "held",
            "owner_pid": os.getpid(),
            "owner_nonce": record["owner_nonce"],
            "depth": 1,
            "authority_action": action,
            "interlock_path": lease.inspection["interlock_path"],
        }
    finally:
        held.pop(key, None)
        try:
            lease.release()
        except AssetTransactionInterlockError as exc:
            raise ProjectWriteInterlockError(
                "project_write_interlock_release_failed",
                str(exc),
                details=exc.details,
            ) from exc


def recover_project_write_interlock(
    project_root: str | Path,
    *,
    expected_owner_nonce: str,
    reason: str,
    allow_live_owner: bool = False,
) -> dict[str, Any]:
    """Explicitly recover one stale lock after exact owner evidence is supplied."""
    project = _project(project_root)
    explanation = str(reason or "").strip()
    if not explanation:
        raise ProjectWriteInterlockError(
            "project_write_recovery_reason_required",
            "explicit recovery reason is required",
        )
    inspection = inspect_project_write_interlock(project)
    record = inspection.get("record")
    if inspection.get("state") != "valid" or not isinstance(record, Mapping):
        raise ProjectWriteInterlockError(
            "project_write_recovery_evidence_invalid",
            "lock record is not valid for recovery",
            details={"inspection": inspection},
        )
    if record.get("owner_nonce") != expected_owner_nonce:
        raise ProjectWriteInterlockError(
            "project_write_recovery_owner_mismatch",
            "lock owner nonce does not match recovery evidence",
        )
    pid = record.get("pid")
    owner_alive = _pid_is_alive(pid) if isinstance(pid, int) else False
    if owner_alive and not allow_live_owner:
        raise ProjectWriteInterlockError(
            "project_write_recovery_owner_alive",
            "live lock owner cannot be recovered without explicit override",
        )
    path = Path(str(inspection["interlock_path"]))
    try:
        path.unlink()
    except OSError as exc:
        raise ProjectWriteInterlockError(
            "project_write_recovery_failed",
            "stale project write lock could not be removed",
        ) from exc
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "project_write_interlock_recovered",
        "project_path": str(project),
        "recovered_owner_nonce": expected_owner_nonce,
        "recovered_pid": pid,
        "owner_was_alive": owner_alive,
        "allow_live_owner": bool(allow_live_owner),
        "reason": explanation,
        "interlock_path": str(path),
    }


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


def _witness_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["witness_digest"] = ""
    return _digest(payload)


def build_project_write_authority_witness(
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Seal real cross-process write-seam rejection evidence."""
    required = {
        "holder_pid",
        "importer_pid",
        "canonical_interlock_path",
        "checkpoint_import_blocked",
        "asset_transaction_blocked",
        "project_lock_refresh_blocked",
        "project_save_blocked",
        "post_release_import_succeeded",
        "interlock_released",
    }
    if not isinstance(evidence, Mapping) or set(evidence) != required:
        raise ValueError("project write evidence keys are invalid")
    holder = evidence.get("holder_pid")
    importer = evidence.get("importer_pid")
    if (
        isinstance(holder, bool)
        or not isinstance(holder, int)
        or holder < 1
        or isinstance(importer, bool)
        or not isinstance(importer, int)
        or importer < 1
        or holder == importer
    ):
        raise ValueError("project write evidence process identity is invalid")
    if (
        not isinstance(evidence.get("canonical_interlock_path"), str)
        or not evidence["canonical_interlock_path"].endswith(
            "asset_transaction_interlock.json"
        )
    ):
        raise ValueError("project write evidence shared lock path is invalid")
    for field in (
        "checkpoint_import_blocked",
        "asset_transaction_blocked",
        "project_lock_refresh_blocked",
        "project_save_blocked",
        "post_release_import_succeeded",
        "interlock_released",
    ):
        if evidence.get(field) is not True:
            raise ValueError(f"project write evidence {field} is not true")
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": WITNESS_STATUS,
        "scope": WITNESS_SCOPE,
        "read_only": True,
        **{field: True for field in PROOF_FIELDS},
        "holder_pid": holder,
        "importer_pid": importer,
        "canonical_interlock_filename": "asset_transaction_interlock.json",
        "global_cross_process_atomicity": True,
        "portable_sr_executable_script_checkpoint": False,
        "default_ready": False,
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_project_write_authority_witness(value: object) -> dict[str, Any]:
    """Reject forged booleans, process reuse or lock-name drift."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    required = {
        "schema_version",
        "status",
        "scope",
        "read_only",
        *PROOF_FIELDS,
        "holder_pid",
        "importer_pid",
        "canonical_interlock_filename",
        "global_cross_process_atomicity",
        "portable_sr_executable_script_checkpoint",
        "default_ready",
        "witness_digest",
    }
    if set(value) != required:
        errors.append("witness_keys_invalid")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != WITNESS_STATUS:
        errors.append("status_mismatch")
    if value.get("scope") != WITNESS_SCOPE:
        errors.append("scope_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_required")
    holder = value.get("holder_pid")
    importer = value.get("importer_pid")
    if (
        isinstance(holder, bool)
        or not isinstance(holder, int)
        or holder < 1
        or isinstance(importer, bool)
        or not isinstance(importer, int)
        or importer < 1
        or holder == importer
    ):
        errors.append("process_identity_invalid")
    if (
        value.get("canonical_interlock_filename")
        != "asset_transaction_interlock.json"
    ):
        errors.append("canonical_interlock_filename_mismatch")
    for field in PROOF_FIELDS:
        if value.get(field) is not True:
            errors.append(f"{field}_not_proven")
    if value.get("global_cross_process_atomicity") is not True:
        errors.append("global_cross_process_atomicity_not_proven")
    if value.get("portable_sr_executable_script_checkpoint") is not False:
        errors.append("portable_script_checkpoint_overclaim")
    if value.get("default_ready") is not False:
        errors.append("default_ready_overclaim")
    digest = value.get("witness_digest")
    if (
        not isinstance(digest, str)
        or _DIGEST_RE.fullmatch(digest) is None
        or digest != _witness_digest(value)
    ):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}


__all__ = [
    "PROOF_FIELDS",
    "ProjectWriteInterlockError",
    "WITNESS_SCOPE",
    "WITNESS_STATUS",
    "build_project_write_authority_witness",
    "inspect_project_write_interlock",
    "project_write_interlock",
    "recover_project_write_interlock",
    "validate_project_write_authority_witness",
]
