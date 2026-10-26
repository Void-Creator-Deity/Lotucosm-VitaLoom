"""Process-local reentrant gate shared by WorldBridge tick and checkpoint owners."""
from __future__ import annotations

import threading
from collections.abc import Mapping
from contextlib import contextmanager
from typing import Any, Iterator


SCHEMA_VERSION = 1
STATUS = "worldbridge_process_owner_gate"


class WorldBridgeOwnerGate:
    """Serialize one process-local WorldBridge owner set without Qt."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._metadata_lock = threading.Lock()
        self._depth = 0
        self._owner_thread_id: int | None = None
        self._current_operation: str | None = None
        self._hold_count = 0
        self._top_level_acquisitions = 0
        self._blocked_attempts = 0
        self._max_depth = 0

    @contextmanager
    def hold(self, operation: str) -> Iterator[None]:
        """Block competing owners while one runtime operation is in progress."""
        if not isinstance(operation, str) or not operation.strip():
            raise ValueError("owner gate operation must be non-empty")
        acquired = self._lock.acquire(blocking=False)
        if not acquired:
            with self._metadata_lock:
                self._blocked_attempts += 1
            self._lock.acquire()
        with self._metadata_lock:
            self._depth += 1
            self._hold_count += 1
            if self._depth == 1:
                self._top_level_acquisitions += 1
                self._owner_thread_id = threading.get_ident()
            self._current_operation = operation
            self._max_depth = max(self._max_depth, self._depth)
        try:
            yield
        finally:
            with self._metadata_lock:
                self._depth -= 1
                if self._depth == 0:
                    self._owner_thread_id = None
                    self._current_operation = None
            self._lock.release()

    def snapshot(self) -> dict[str, Any]:
        """Return detached gate state without exposing the lock object."""
        with self._metadata_lock:
            return {
                "schema_version": SCHEMA_VERSION,
                "status": STATUS,
                "process_local": True,
                "locked": self._depth > 0,
                "owner_thread_id": self._owner_thread_id,
                "current_thread_id": threading.get_ident(),
                "current_operation": self._current_operation,
                "depth": self._depth,
                "hold_count": self._hold_count,
                "top_level_acquisitions": self._top_level_acquisitions,
                "blocked_attempts": self._blocked_attempts,
                "max_depth": self._max_depth,
            }


def validate_worldbridge_owner_gate_snapshot(value: object) -> dict[str, Any]:
    """Validate one gate snapshot without trusting or exposing the live lock."""
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["snapshot_not_mapping"]}
    required = {
        "schema_version",
        "status",
        "process_local",
        "locked",
        "owner_thread_id",
        "current_thread_id",
        "current_operation",
        "depth",
        "hold_count",
        "top_level_acquisitions",
        "blocked_attempts",
        "max_depth",
    }
    errors: list[str] = []
    if set(value) != required:
        errors.append("snapshot_keys_invalid")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("process_local") is not True:
        errors.append("process_local_required")
    for field in ("locked",):
        if not isinstance(value.get(field), bool):
            errors.append(f"{field}_invalid")
    for field in (
        "depth",
        "hold_count",
        "top_level_acquisitions",
        "blocked_attempts",
        "max_depth",
    ):
        item = value.get(field)
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            errors.append(f"{field}_invalid")
    for field in ("owner_thread_id", "current_thread_id"):
        item = value.get(field)
        if item is not None and (
            isinstance(item, bool) or not isinstance(item, int) or item < 0
        ):
            errors.append(f"{field}_invalid")
    operation = value.get("current_operation")
    if operation is not None and (
        not isinstance(operation, str) or not operation.strip()
    ):
        errors.append("current_operation_invalid")
    if value.get("locked") is True:
        if value.get("depth", 0) < 1 or operation is None:
            errors.append("locked_state_incomplete")
        if value.get("owner_thread_id") is None:
            errors.append("locked_owner_missing")
    elif value.get("locked") is False:
        if value.get("depth") != 0 or operation is not None:
            errors.append("unlocked_state_inconsistent")
    if value.get("depth", 0) > value.get("max_depth", -1):
        errors.append("depth_exceeds_max")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "SCHEMA_VERSION",
    "STATUS",
    "WorldBridgeOwnerGate",
    "validate_worldbridge_owner_gate_snapshot",
]
