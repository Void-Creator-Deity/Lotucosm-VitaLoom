"""Durable, fail-closed one-shot ledger for E382 diagnostic receipts."""
from __future__ import annotations

import json
import hashlib
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .world_bridge_e382_restore_receipt import (
    COMPONENT_FIELDS,
    decode_e382_receipt,
    digest,
    validate_e382_receipt,
    validate_e382_receipt_against_child,
)

SCHEMA_VERSION = 1
LEDGER_DIRECTORY = ".vitaloom"
LEDGER_FILENAME = "worldbridge_e382_receipt_ledger.json"
LOCK_FILENAME = "worldbridge_e382_receipt_ledger.lock"


class E384LedgerError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _project(project_root: str | Path) -> Path:
    root = Path(project_root).expanduser().resolve()
    if not root.is_dir():
        raise E384LedgerError("project_not_found", "project root is not a directory")
    return root


def _paths(root: Path) -> tuple[Path, Path]:
    metadata = root / LEDGER_DIRECTORY
    return metadata / LEDGER_FILENAME, metadata / LOCK_FILENAME


def _identity_digest(project_identity: object) -> str:
    return digest({"project_identity": project_identity})


def _identity_snapshot(project_identity: object) -> dict[str, Any] | None:
    if not isinstance(project_identity, Mapping):
        return None
    return dict(project_identity)


def build_project_world_identity(project_root: str | Path, scene_path: str | Path) -> dict[str, Any]:
    """Derive identity from the real project manifest and contained scene bytes."""
    root = _project(project_root)
    manifest = root / "project.json"
    scene = (root / scene_path).resolve() if not Path(scene_path).is_absolute() else Path(scene_path).resolve()
    try:
        scene.relative_to(root)
    except ValueError as exc:
        raise E384LedgerError("project_scene_escape", "scene path escapes project root") from exc
    if not manifest.is_file() or not scene.is_file():
        raise E384LedgerError("project_world_missing", "project manifest or scene is missing")
    def file_digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "project_manifest_digest": file_digest(manifest),
        "scene_digest": file_digest(scene),
        "scene_relative_path": scene.relative_to(root).as_posix(),
    }


def _empty(identity_digest: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "project_identity_digest": identity_digest,
        "consumed": [],
        "component_provenance": {},
    }


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    sealed = dict(value)
    sealed["ledger_digest"] = digest({key: item for key, item in sealed.items() if key != "ledger_digest"})
    return sealed


def _valid_digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _read(path: Path, expected_identity_digest: str) -> dict[str, Any]:
    if not path.exists():
        return _empty(expected_identity_digest)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise E384LedgerError("ledger_malformed", "receipt ledger is unreadable") from exc
    if not isinstance(value, Mapping) or value.get("schema_version") != SCHEMA_VERSION:
        raise E384LedgerError("ledger_schema_invalid", "receipt ledger schema is invalid")
    if set(value) != {"schema_version", "project_identity_digest", "consumed", "component_provenance", "ledger_digest"}:
        raise E384LedgerError("ledger_schema_invalid", "receipt ledger contains unknown or missing fields")
    if value.get("project_identity_digest") != expected_identity_digest:
        raise E384LedgerError("ledger_project_identity_mismatch", "receipt ledger belongs to another project identity")
    consumed = value.get("consumed")
    if not isinstance(consumed, list) or any(not isinstance(item, str) or not item for item in consumed):
        raise E384LedgerError("ledger_entries_invalid", "receipt ledger entries are invalid")
    if len(set(consumed)) != len(consumed):
        raise E384LedgerError("ledger_entries_duplicate", "receipt ledger contains duplicate consumption")
    provenance = value.get("component_provenance")
    if not isinstance(provenance, Mapping):
        raise E384LedgerError("ledger_provenance_missing", "receipt ledger component provenance is missing")
    if set(provenance) != set(consumed):
        raise E384LedgerError("ledger_provenance_entries_mismatch", "receipt ledger provenance entries do not match consumption")
    normalized_provenance: dict[str, dict[str, Any]] = {}
    for receipt_digest in consumed:
        record = provenance.get(receipt_digest)
        if not isinstance(record, Mapping):
            raise E384LedgerError("ledger_provenance_invalid", "receipt ledger component provenance is invalid")
        if set(record) != {"receipt_digest", "child_result_digest", "component_digests", "project_identity_digest", "project_identity"}:
            raise E384LedgerError("ledger_provenance_invalid", "receipt ledger provenance contains unknown or missing fields")
        components = record.get("component_digests")
        identity_snapshot = record.get("project_identity") if "project_identity" in record else ...
        if (
            record.get("receipt_digest") != receipt_digest
            or record.get("project_identity_digest") != expected_identity_digest
            or not _valid_digest(record.get("child_result_digest"))
            or not isinstance(components, Mapping)
            or set(components) != set(COMPONENT_FIELDS)
            or any(not _valid_digest(components.get(field)) for field in COMPONENT_FIELDS)
            or identity_snapshot is ...
            or (
                identity_snapshot is not None
                and digest({"project_identity": identity_snapshot}) != expected_identity_digest
            )
        ):
            raise E384LedgerError("ledger_provenance_invalid", "receipt ledger component provenance is invalid")
        normalized_provenance[receipt_digest] = {
            "receipt_digest": receipt_digest,
            "child_result_digest": record["child_result_digest"],
            "component_digests": {field: components[field] for field in COMPONENT_FIELDS},
            "project_identity_digest": expected_identity_digest,
            "project_identity": identity_snapshot,
        }
    ledger_digest = value.get("ledger_digest")
    unsigned = {
        "schema_version": SCHEMA_VERSION,
        "project_identity_digest": expected_identity_digest,
        "consumed": list(consumed),
        "component_provenance": normalized_provenance,
    }
    if not _valid_digest(ledger_digest) or ledger_digest != digest(unsigned):
        raise E384LedgerError("ledger_digest_mismatch", "receipt ledger digest does not match its contents")
    return _seal(unsigned)


def _write_atomic(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    except Exception as exc:
        try:
            os.unlink(name)
        except OSError:
            pass
        raise E384LedgerError("ledger_write_failed", "receipt ledger atomic write failed") from exc


def _acquire_lock(lock: Path) -> None:
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(lock), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise E384LedgerError("ledger_interlock_held", "receipt ledger interlock is held") from exc
    try:
        with os.fdopen(fd, "w", encoding="ascii") as stream:
            stream.write(str(os.getpid()))
            stream.flush()
            os.fsync(stream.fileno())
    except Exception as exc:
        raise E384LedgerError("ledger_interlock_write_failed", "receipt ledger interlock write failed") from exc


def _release_lock(lock: Path) -> None:
    try:
        lock.unlink()
    except OSError as exc:
        raise E384LedgerError("ledger_interlock_release_failed", "receipt ledger interlock release failed") from exc


def consume_e382_receipt_durable(
    project_root: str | Path,
    encoded: bytes,
    *,
    project_identity: object,
    expected_child_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate and consume one receipt with durable cross-process exclusion."""
    receipt = decode_e382_receipt(encoded)
    validation = validate_e382_receipt(receipt)
    if validation["valid"] is not True:
        raise E384LedgerError("receipt_component_validation_failed", ";".join(validation["errors"]))
    if expected_child_result is not None:
        child_validation = validate_e382_receipt_against_child(receipt, expected_child_result)
        if child_validation["valid"] is not True:
            raise E384LedgerError("receipt_child_binding_mismatch", ";".join(child_validation["errors"]))
    identity_digest = _identity_digest(project_identity)
    if receipt.get("project_identity_digest") != identity_digest:
        raise E384LedgerError("receipt_project_identity_mismatch", "receipt belongs to another project identity")
    root = _project(project_root)
    ledger, lock = _paths(root)
    _acquire_lock(lock)
    try:
        state = _read(ledger, identity_digest)
        receipt_digest = receipt["receipt_digest"]
        if receipt_digest in state["consumed"]:
            raise E384LedgerError("receipt_replay_rejected", "receipt was already consumed")
        state["consumed"].append(receipt_digest)
        state["consumed"].sort()
        state["component_provenance"][receipt_digest] = {
            "receipt_digest": receipt_digest,
            "child_result_digest": receipt["child_result_digest"],
            "component_digests": {field: receipt["component_digests"][field] for field in COMPONENT_FIELDS},
            "project_identity_digest": identity_digest,
            "project_identity": _identity_snapshot(project_identity),
        }
        sealed = _seal(state)
        _write_atomic(ledger, sealed)
        return {
            "status": "consumed",
            "receipt_digest": receipt_digest,
            "ledger_digest": sealed["ledger_digest"],
            "ledger_path": str(ledger.relative_to(root)),
        }
    finally:
        _release_lock(lock)


def inspect_e384_receipt_ledger(project_root: str | Path, *, project_identity: object | None = None) -> dict[str, Any]:
    root = _project(project_root)
    ledger, lock = _paths(root)
    identity_digest = _identity_digest(project_identity)
    state = _read(ledger, identity_digest)
    return {
        "schema_version": SCHEMA_VERSION,
        "project_identity_digest": identity_digest,
        "status": "held" if lock.exists() else "available",
        "ledger_exists": ledger.is_file(),
        "consumed_count": len(state["consumed"]),
        "consumed": list(state["consumed"]),
        "component_provenance": state["component_provenance"],
        "ledger_digest": state.get("ledger_digest"),
    }


__all__ = ["E384LedgerError", "build_project_world_identity", "consume_e382_receipt_durable", "inspect_e384_receipt_ledger"]
