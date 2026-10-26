# -*- coding: utf-8 -*-
"""Qt-free, fail-closed cross-process interlock for package transaction mutations.

This Module deliberately protects only the durable package-transaction write
sequences.  It is not a project session lock, a lease, or a stale-lock repair
mechanism.  Any existing, malformed, foreign, or interrupted lock fails closed
until an explicit future operator recovery Authority is introduced.
"""
from __future__ import annotations

import json
import os
import secrets
import stat
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
INTERLOCK_DIRECTORY = ".vitaloom"
INTERLOCK_FILENAME = "package_transaction_interlock.json"


class PackageTransactionInterlockError(RuntimeError):
    """Structured failure for a project-local package mutation interlock."""

    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = str(code)
        self.details = dict(details or {})


def _project_path(project_root: str | Path) -> Path:
    project = Path(project_root).expanduser().resolve()
    if not project.is_dir():
        raise PackageTransactionInterlockError(
            "package_transaction_interlock_project_not_found",
            "project_root must be an existing directory",
            details={"project_path": str(project)},
        )
    return project


def _metadata_root(project: Path) -> Path:
    return project / INTERLOCK_DIRECTORY


def _interlock_path(project: Path) -> Path:
    return _metadata_root(project) / INTERLOCK_FILENAME


def _safe_metadata_root(project: Path, *, create: bool) -> Path:
    """Return the metadata directory only when it is a contained real directory."""

    root = _metadata_root(project)
    if not root.exists() and not root.is_symlink():
        if not create:
            return root
        try:
            root.mkdir(mode=0o700, parents=False, exist_ok=False)
        except FileExistsError:
            pass
        except OSError as exc:
            raise PackageTransactionInterlockError(
                "package_transaction_interlock_io_failed",
                "Cannot create the project transaction interlock directory",
                details={"interlock_path": str(_interlock_path(project)), "error": type(exc).__name__},
            ) from exc
    try:
        root_stat = root.lstat()
    except OSError as exc:
        raise PackageTransactionInterlockError(
            "package_transaction_interlock_io_failed",
            "Cannot inspect the project transaction interlock directory",
            details={"interlock_path": str(_interlock_path(project)), "error": type(exc).__name__},
        ) from exc
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise PackageTransactionInterlockError(
            "package_transaction_interlock_path_unsafe",
            "Project transaction interlock directory is not a real directory",
            details={"interlock_path": str(_interlock_path(project))},
        )
    try:
        root.resolve().relative_to(project)
    except ValueError as exc:
        raise PackageTransactionInterlockError(
            "package_transaction_interlock_path_unsafe",
            "Project transaction interlock directory escapes the project",
            details={"interlock_path": str(_interlock_path(project))},
        ) from exc
    return root


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _valid_record(value: Any, *, project: Path) -> tuple[bool, str]:
    if not isinstance(value, Mapping):
        return False, "record_not_object"
    if value.get("schema_version") != SCHEMA_VERSION:
        return False, "unsupported_schema"
    if value.get("project_path") != str(project):
        return False, "foreign_project"
    nonce = value.get("owner_nonce")
    if not isinstance(nonce, str) or len(nonce) != 64 or any(char not in "0123456789abcdef" for char in nonce):
        return False, "invalid_owner_nonce"
    if not isinstance(value.get("pid"), int) or int(value["pid"]) < 1:
        return False, "invalid_pid"
    if not isinstance(value.get("created_at_utc"), str) or not str(value["created_at_utc"]).endswith("Z"):
        return False, "invalid_created_at_utc"
    if not isinstance(value.get("authority_action"), str) or not str(value["authority_action"]).strip():
        return False, "invalid_authority_action"
    return True, "valid"


def _record_snapshot(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    return {
        "schema_version": value.get("schema_version"),
        "project_path": value.get("project_path"),
        "owner_nonce": value.get("owner_nonce"),
        "pid": value.get("pid"),
        "created_at_utc": value.get("created_at_utc"),
        "authority_action": value.get("authority_action"),
    }


def inspect_package_transaction_interlock(project_root: str | Path) -> dict[str, Any]:
    """Inspect interlock evidence without creating, changing, or recovering it."""

    project = _project_path(project_root)
    path = _interlock_path(project)
    root = _metadata_root(project)
    if not root.exists() and not root.is_symlink():
        return {
            "schema_version": SCHEMA_VERSION,
            "project_path": str(project),
            "interlock_path": str(path),
            "held": False,
            "status": "absent",
            "record": None,
        }
    try:
        _safe_metadata_root(project, create=False)
    except PackageTransactionInterlockError as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "project_path": str(project),
            "interlock_path": str(path),
            "held": True,
            "status": "unsafe_metadata_directory",
            "record": None,
            "error_code": exc.code,
        }
    try:
        path_stat = path.lstat()
    except FileNotFoundError:
        return {
            "schema_version": SCHEMA_VERSION,
            "project_path": str(project),
            "interlock_path": str(path),
            "held": False,
            "status": "absent",
            "record": None,
        }
    except OSError as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "project_path": str(project),
            "interlock_path": str(path),
            "held": True,
            "status": "unreadable",
            "record": None,
            "error_code": type(exc).__name__,
        }
    if stat.S_ISLNK(path_stat.st_mode) or not stat.S_ISREG(path_stat.st_mode):
        return {
            "schema_version": SCHEMA_VERSION,
            "project_path": str(project),
            "interlock_path": str(path),
            "held": True,
            "status": "unsafe_lock_path",
            "record": None,
        }
    try:
        raw = path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {
            "schema_version": SCHEMA_VERSION,
            "project_path": str(project),
            "interlock_path": str(path),
            "held": True,
            "status": "malformed",
            "record": None,
        }
    valid, classification = _valid_record(data, project=project)
    return {
        "schema_version": SCHEMA_VERSION,
        "project_path": str(project),
        "interlock_path": str(path),
        "held": True,
        "status": "valid" if valid else classification,
        "record": _record_snapshot(data),
    }


class PackageTransactionInterlockLease:
    """One acquired interlock.  Only its exact owner nonce may release it."""

    def __init__(self, project: Path, path: Path, record: Mapping[str, Any]) -> None:
        self._project = project
        self._path = path
        self._record = dict(record)
        self._released = False

    @property
    def inspection(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "project_path": str(self._project),
            "interlock_path": str(self._path),
            "held": True,
            "status": "valid",
            "record": _record_snapshot(self._record),
        }

    def release(self) -> None:
        """Release only the same valid record created by this lease."""

        if self._released:
            return
        inspection = inspect_package_transaction_interlock(self._project)
        record = inspection.get("record")
        if (
            inspection.get("status") != "valid"
            or not isinstance(record, Mapping)
            or record.get("owner_nonce") != self._record["owner_nonce"]
            or record.get("project_path") != str(self._project)
        ):
            raise PackageTransactionInterlockError(
                "package_transaction_interlock_release_refused",
                "Transaction interlock changed or became malformed before owner release",
                details={"interlock_path": str(self._path), "inspection": inspection},
            )
        try:
            self._path.unlink()
        except FileNotFoundError as exc:
            raise PackageTransactionInterlockError(
                "package_transaction_interlock_release_refused",
                "Transaction interlock disappeared before owner release",
                details={"interlock_path": str(self._path)},
            ) from exc
        except OSError as exc:
            raise PackageTransactionInterlockError(
                "package_transaction_interlock_release_failed",
                "Cannot release the owned transaction interlock",
                details={"interlock_path": str(self._path), "error": type(exc).__name__},
            ) from exc
        self._released = True


def acquire_package_transaction_interlock(
    project_root: str | Path,
    *,
    authority_action: str,
) -> PackageTransactionInterlockLease:
    """Acquire one fail-closed, project-local lock for a mutation Authority call."""

    project = _project_path(project_root)
    action = str(authority_action or "").strip()
    if not action:
        raise PackageTransactionInterlockError(
            "package_transaction_interlock_action_invalid",
            "authority_action is required for an package transaction interlock",
        )
    _safe_metadata_root(project, create=True)
    path = _interlock_path(project)
    record = {
        "schema_version": SCHEMA_VERSION,
        "project_path": str(project),
        "owner_nonce": secrets.token_hex(32),
        "pid": os.getpid(),
        "created_at_utc": _timestamp(),
        "authority_action": action,
    }
    encoded = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    try:
        descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        inspection = inspect_package_transaction_interlock(project)
        raise PackageTransactionInterlockError(
            "package_transaction_interlock_held",
            "Another or interrupted package transaction mutation holds the project interlock",
            details={"interlock_path": str(path), "inspection": inspection},
        ) from exc
    except OSError as exc:
        raise PackageTransactionInterlockError(
            "package_transaction_interlock_io_failed",
            "Cannot acquire the project package transaction interlock",
            details={"interlock_path": str(path), "error": type(exc).__name__},
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception as exc:
        # A partially written lock is deliberately retained and therefore blocks
        # all future mutation; deleting an unverified artifact would violate the
        # same fail-closed contract that protects interrupted processes.
        raise PackageTransactionInterlockError(
            "package_transaction_interlock_io_failed",
            "Interlock creation was interrupted; the retained lock requires explicit recovery",
            details={"interlock_path": str(path), "error": type(exc).__name__},
        ) from exc
    return PackageTransactionInterlockLease(project, path, record)


@contextmanager
def package_transaction_mutation_interlock(
    project_root: str | Path,
    *,
    authority_action: str,
) -> Iterator[PackageTransactionInterlockLease]:
    """Context manager for exactly one public package-transaction mutation seam."""

    lease = acquire_package_transaction_interlock(project_root, authority_action=authority_action)
    try:
        yield lease
    finally:
        lease.release()
