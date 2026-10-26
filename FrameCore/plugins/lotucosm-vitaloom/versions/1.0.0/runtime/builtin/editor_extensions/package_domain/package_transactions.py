"""Durable, Qt-free receipts for package storage/project-command transactions."""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

SCHEMA_VERSION = 1
TRANSACTION_DIRECTORY = ".vitaloom/package_transactions"
RECOVERABLE_STATES = frozenset({"prepared", "local_applied", "project_applied", "failed_recoverable"})
TERMINAL_STATES = frozenset({"completed", "failed"})
_VALID_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_VALID_ACTIONS = frozenset({"install", "uninstall"})


class PackageTransactionError(RuntimeError):
    """Raised when receipt persistence or validation cannot be trusted."""

    def __init__(self, code: str, message: str, *, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}

class ProjectPackageArtifactPort:
    """Qt-free project-root artifact adapter used by operator recovery commands.

    Receipts store absolute package-artifact paths.  Recovery may only inspect or
    remove a real directory rooted inside ``<project>/packages``; it never reads
    the live editor project manager or mutates project package state.
    """

    def __init__(self, project_root: str | Path) -> None:
        self._project = _as_project_path(project_root)
        self._packages_root = self._project / "packages"

    def _snapshot(self, package_id: str, artifact_path: str, *, recorded: bool) -> Dict[str, Any]:
        normalized_id = str(package_id or "").strip()
        raw_path = str(artifact_path or "").strip()
        if not normalized_id:
            return {"ok": False, "error": "unsafe_artifact_path", "package_id": normalized_id}
        if not raw_path:
            return {
                "ok": True,
                "package_id": normalized_id,
                "path": "",
                "recorded": bool(recorded),
                "exists": False,
                "artifact_present": False,
            }
        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            return {"ok": False, "error": "unsafe_artifact_path", "package_id": normalized_id, "path": raw_path}
        try:
            packages_root = self._packages_root.resolve(strict=False)
            if self._packages_root.exists() and self._packages_root.is_symlink():
                return {"ok": False, "error": "unsafe_artifact_path", "package_id": normalized_id, "path": raw_path}
            resolved = candidate.resolve(strict=False)
            resolved.relative_to(packages_root)
            if candidate.exists() or candidate.is_symlink():
                info = candidate.lstat()
                if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                    return {"ok": False, "error": "unsafe_artifact_path", "package_id": normalized_id, "path": raw_path}
        except (OSError, ValueError):
            return {"ok": False, "error": "unsafe_artifact_path", "package_id": normalized_id, "path": raw_path}
        return {
            "ok": True,
            "package_id": normalized_id,
            "path": str(resolved),
            "recorded": bool(recorded),
            "exists": candidate.is_dir(),
            "artifact_present": candidate.is_dir(),
        }

    def inspect_local_artifact_path(self, package_id: str, artifact_path: str) -> Dict[str, Any]:
        return self._snapshot(package_id, artifact_path, recorded=True)

    def remove_local_artifact(self, snapshot: Mapping[str, Any]) -> Dict[str, Any]:
        package_id = str(snapshot.get("package_id", "") or "").strip()
        validated = self._snapshot(
            package_id,
            str(snapshot.get("path", "") or ""),
            recorded=bool(snapshot.get("recorded")),
        )
        if not validated.get("ok"):
            return {"ok": False, "error": str(validated.get("error", "unsafe_artifact_path")), "package_id": package_id}
        path_text = str(validated.get("path", ""))
        if not path_text or not validated.get("exists"):
            return {
                "ok": True,
                "package_id": package_id,
                "removed_path": path_text,
                "was_installed": bool(validated.get("recorded")),
                "already_absent": True,
            }
        try:
            shutil.rmtree(path_text)
        except OSError as exc:
            return {"ok": False, "error": str(exc), "package_id": package_id, "removed_path": path_text}
        return {
            "ok": True,
            "package_id": package_id,
            "removed_path": path_text,
            "was_installed": bool(validated.get("recorded")),
            "already_absent": False,
        }

def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_project_path(project_root: str | Path) -> Path:
    project = Path(project_root).expanduser()
    try:
        resolved = project.resolve(strict=True)
    except OSError as exc:
        raise PackageTransactionError(
            "package_transaction_project_unavailable",
            "Project root must exist before package transaction receipt creation",
            details={"project_root": str(project_root)},
        ) from exc
    if not resolved.is_dir():
        raise PackageTransactionError(
            "package_transaction_project_unavailable",
            "Project root must be a directory",
            details={"project_root": str(resolved)},
        )
    return resolved


def _safe_child_directory(parent: Path, name: str) -> Path:
    path = parent / name
    try:
        info = path.lstat()
    except FileNotFoundError:
        try:
            path.mkdir(mode=0o700)
        except FileExistsError:
            info = path.lstat()
        except OSError as exc:
            raise PackageTransactionError(
                "package_transaction_directory_create_failed",
                "Could not create package transaction directory",
                details={"path": str(path)},
            ) from exc
        else:
            return path
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise PackageTransactionError(
            "package_transaction_unsafe_directory",
            "Package transaction directory is not a real directory",
            details={"path": str(path)},
        )
    return path

def _safe_existing_child_directory(parent: Path, name: str) -> Optional[Path]:
    """Return a verified directory without creating metadata during read-only inspection."""

    path = parent / name
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise PackageTransactionError(
            "package_transaction_unreadable_directory",
            "Package transaction directory cannot be inspected",
            details={"path": str(path)},
        ) from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise PackageTransactionError(
            "package_transaction_unsafe_directory",
            "Package transaction directory is not a real directory",
            details={"path": str(path)},
        )
    return path

def _atomic_replace(path: Path, value: Mapping[str, Any]) -> None:
    encoded = json.dumps(dict(value), ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def _exclusive_create(path: Path, value: Mapping[str, Any]) -> None:
    encoded = json.dumps(dict(value), ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    try:
        descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise PackageTransactionError(
            "package_transaction_conflict",
            "Package transaction receipt already exists",
            details={"path": str(path)},
        ) from exc
    except OSError as exc:
        raise PackageTransactionError(
            "package_transaction_create_failed",
            "Could not create package transaction receipt",
            details={"path": str(path)},
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def _string_map(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _receipt_error(receipt: Mapping[str, Any], transaction_id: str) -> Optional[str]:
    if not isinstance(receipt, Mapping):
        return "receipt_not_mapping"
    if receipt.get("schema_version") != SCHEMA_VERSION:
        return "schema_version"
    if str(receipt.get("transaction_id", "")) != transaction_id:
        return "transaction_id"
    if str(receipt.get("action", "")) not in _VALID_ACTIONS:
        return "action"
    if not str(receipt.get("package_id", "")).strip():
        return "package_id"
    if not str(receipt.get("state", "")).strip():
        return "state"
    if not isinstance(receipt.get("events"), list):
        return "events"
    if not isinstance(receipt.get("payload"), Mapping):
        return "payload"
    if not isinstance(receipt.get("local_snapshot"), Mapping):
        return "local_snapshot"
    return None


def _allowed_transitions(action: str) -> Dict[str, set[str]]:
    if action == "install":
        return {
            "prepared": {"local_applied", "failed"},
            "local_applied": {"project_applied", "failed_recoverable"},
            "project_applied": {"completed"},
            "failed_recoverable": {"project_applied", "failed_recoverable"},
            "completed": set(),
            "failed": set(),
        }
    return {
        "prepared": {"project_applied", "failed"},
        "project_applied": {"local_applied", "failed_recoverable"},
        "local_applied": {"completed"},
        "failed_recoverable": {"local_applied", "failed_recoverable"},
        "completed": set(),
        "failed": set(),
    }


class PackageTransactionStore:
    """Project-local durable receipts; never a replacement for project package state."""

    def __init__(self, project_root: str | Path) -> None:
        self._project = _as_project_path(project_root)

    @property
    def project_path(self) -> str:
        return str(self._project)

    def _receipt_directory(self, *, create: bool) -> Optional[Path]:
        if create:
            metadata = _safe_child_directory(self._project, ".vitaloom")
            return _safe_child_directory(metadata, "package_transactions")
        metadata = _safe_existing_child_directory(self._project, ".vitaloom")
        if metadata is None:
            return None
        return _safe_existing_child_directory(metadata, "package_transactions")

    @property
    def receipt_directory(self) -> Path:
        directory = self._receipt_directory(create=True)
        assert directory is not None
        return directory

    def _receipt_path(self, transaction_id: str, *, create_directory: bool = False) -> Path:
        normalized = str(transaction_id or "").strip()
        if not _VALID_ID.fullmatch(normalized):
            raise PackageTransactionError(
                "package_transaction_invalid_id",
                "Invalid package transaction id",
                details={"transaction_id": normalized},
            )
        directory = self._receipt_directory(create=create_directory)
        if directory is None:
            directory = self._project / ".vitaloom" / "package_transactions"
        return directory / f"{normalized}.json"

    def begin(
        self,
        action: str,
        package_id: str,
        *,
        payload: Optional[Mapping[str, Any]] = None,
        local_snapshot: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        normalized_action = str(action).strip()
        normalized_package_id = str(package_id).strip()
        if normalized_action not in _VALID_ACTIONS:
            raise PackageTransactionError("package_transaction_invalid_action", "Unsupported package transaction action")
        if not normalized_package_id:
            raise PackageTransactionError("package_transaction_invalid_package", "Package id is required")
        transaction_id = uuid.uuid4().hex
        now = _utc_now()
        receipt: Dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "transaction_id": transaction_id,
            "action": normalized_action,
            "package_id": normalized_package_id,
            "state": "prepared",
            "created_at_utc": now,
            "updated_at_utc": now,
            "payload": _string_map(payload),
            "local_snapshot": _string_map(local_snapshot),
            "local_result": {},
            "project_command": {},
            "recovery": {},
            "events": [{"at_utc": now, "from": None, "to": "prepared", "details": {}}],
        }
        _exclusive_create(self._receipt_path(transaction_id, create_directory=True), receipt)
        return receipt

    def read(self, transaction_id: str) -> Dict[str, Any]:
        path = self._receipt_path(transaction_id)
        try:
            info = path.lstat()
        except FileNotFoundError as exc:
            raise PackageTransactionError(
                "package_transaction_not_found",
                "Package transaction receipt does not exist",
                details={"transaction_id": transaction_id},
            ) from exc
        except OSError as exc:
            raise PackageTransactionError(
                "package_transaction_unreadable",
                "Package transaction receipt cannot be inspected",
                details={"transaction_id": transaction_id},
            ) from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise PackageTransactionError(
                "package_transaction_unsafe_receipt",
                "Package transaction receipt is not a regular file",
                details={"transaction_id": transaction_id},
            )
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PackageTransactionError(
                "package_transaction_malformed",
                "Package transaction receipt is unreadable",
                details={"transaction_id": transaction_id},
            ) from exc
        issue = _receipt_error(receipt, str(transaction_id))
        if issue:
            raise PackageTransactionError(
                "package_transaction_malformed",
                "Package transaction receipt is structurally invalid",
                details={"transaction_id": transaction_id, "issue": issue},
            )
        return dict(receipt)

    def advance(
        self,
        transaction_id: str,
        state: str,
        *,
        details: Optional[Mapping[str, Any]] = None,
        payload: Optional[Mapping[str, Any]] = None,
        local_snapshot: Optional[Mapping[str, Any]] = None,
        local_result: Optional[Mapping[str, Any]] = None,
        project_command: Optional[Mapping[str, Any]] = None,
        recovery: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        receipt = self.read(transaction_id)
        previous = str(receipt["state"])
        target = str(state).strip()
        allowed = _allowed_transitions(str(receipt["action"])).get(previous, set())
        if target not in allowed:
            raise PackageTransactionError(
                "package_transaction_invalid_transition",
                "Package transaction state transition is not allowed",
                details={"transaction_id": transaction_id, "from": previous, "to": target},
            )
        now = _utc_now()
        receipt["state"] = target
        receipt["updated_at_utc"] = now
        if payload is not None:
            receipt["payload"] = _string_map(payload)
        if local_snapshot is not None:
            receipt["local_snapshot"] = _string_map(local_snapshot)
        if local_result is not None:
            receipt["local_result"] = _string_map(local_result)
        if project_command is not None:
            receipt["project_command"] = _string_map(project_command)
        if recovery is not None:
            receipt["recovery"] = _string_map(recovery)
        events = receipt.get("events")
        if not isinstance(events, list):
            events = []
        events.append({"at_utc": now, "from": previous, "to": target, "details": _string_map(details)})
        receipt["events"] = events[-100:]
        _atomic_replace(self._receipt_path(transaction_id), receipt)
        return receipt

    def inspect(self, transaction_id: str) -> Dict[str, Any]:
        receipt = self.read(transaction_id)
        return {
            "ok": True,
            "transaction_id": receipt["transaction_id"],
            "action": receipt["action"],
            "package_id": receipt["package_id"],
            "state": receipt["state"],
            "recoverable": receipt["state"] in RECOVERABLE_STATES,
            "receipt": receipt,
        }

    def list_recoverable(self) -> Dict[str, Any]:
        root = self._receipt_directory(create=False)
        if root is None:
            return {"ok": True, "records": [], "malformed": []}
        records = []
        malformed = []
        for path in sorted(root.glob("*.json")):
            transaction_id = path.stem
            try:
                receipt = self.read(transaction_id)
            except PackageTransactionError as exc:
                malformed.append({"path": str(path), "error": exc.code})
                continue
            if receipt.get("state") in RECOVERABLE_STATES:
                records.append(
                    {
                        "transaction_id": receipt["transaction_id"],
                        "action": receipt["action"],
                        "package_id": receipt["package_id"],
                        "state": receipt["state"],
                        "recovery": _string_map(receipt.get("recovery")),
                    }
                )
        return {"ok": not malformed, "records": records, "malformed": malformed}


def create_store_from_operation_service(operation_service: Any) -> Optional[PackageTransactionStore]:
    """Build a store from the narrow Project World read capability when available."""

    read_model = getattr(operation_service, "project_world_read_model", None)
    getter = getattr(read_model, "current_project_world_path", None)
    if not callable(getter):
        # Compatibility for transaction-focused test Adapters and older callers;
        # PackageOperationService itself no longer retains the concrete manager.
        manager = getattr(operation_service, "project_manager", None)
        getter = getattr(manager, "get_current_project_path", None)
    if not callable(getter):
        return None
    project_path = getter()
    if not project_path:
        return None
    return PackageTransactionStore(project_path)
