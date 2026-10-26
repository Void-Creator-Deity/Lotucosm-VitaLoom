# -*- coding: utf-8 -*-
"""Qt-free Authority for run-scoped PS organism runtime snapshots.

The Module owns only opaque run identity and copy-isolated JSON values. Live
Pond/Organism objects, Qt objects, worker threads, scripts, components, and
mutable registries remain behind runner/service Adapters.
"""
from __future__ import annotations

import json
import math
from collections.abc import Mapping
from threading import RLock
from typing import Any
from itertools import count
from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource


SCHEMA_VERSION = 1
AUTHORITY_NAME = "ps_runtime_snapshot_authority"
SCOPE = "ps_runtime_organism"
DISCOVERY_SCOPE = "ps_runtime_population"
TRACK = "ps_batch"
IDENTITY_RELATION = "run_scoped_not_cross_track"
SNAPSHOT_SOURCE = "read_only_json_snapshot"
_EDITOR_COMPAT_RUN_COUNTER = count(1)


class PsRuntimeSnapshotAuthority:
    """Own one active PS run and its complete organism snapshot replacement."""

    def __init__(self, *, identity_source: DeterministicIdentitySource | None = None) -> None:
        self._lock = RLock()
        self._active_run_id: str | None = None
        self._revision = 0
        self._snapshots: dict[str, dict[str, Any]] = {}
        self._identity_source = identity_source

    def begin(self) -> str:
        """Begin a new run lifetime, superseding any previous run."""
        run_id = (
            self._identity_source.next("ps")
            if self._identity_source is not None
            else f"ps_editor_{next(_EDITOR_COMPAT_RUN_COUNTER)}"
        )
        with self._lock:
            self._active_run_id = run_id
            self._revision = 0
            self._snapshots = {}
        return run_id

    def current_run_id(self) -> str | None:
        """Return the active opaque run ID without exposing snapshot storage."""
        with self._lock:
            return self._active_run_id

    def discover(self) -> dict[str, Any]:
        """Atomically acquire the active run and its current organism identities."""
        with self._lock:
            run_id = self._active_run_id
            if run_id is None:
                status = "not_running"
                revision = 0
                identities: list[dict[str, str]] = []
            else:
                status = "ok"
                revision = self._revision
                identities = [
                    {
                        "track": TRACK,
                        "run_id": run_id,
                        "organism_id": organism_id,
                    }
                    for organism_id in sorted(self._snapshots)
                ]
            return {
                "schema_version": SCHEMA_VERSION,
                "status": status,
                "scope": DISCOVERY_SCOPE,
                "authority": AUTHORITY_NAME,
                "track": TRACK,
                "read_only": True,
                "identity_relation": IDENTITY_RELATION,
                "run_id": run_id,
                "revision": revision,
                "organism_count": len(identities),
                "identities": identities,
            }

    def publish(self, run_id: str, organism_snapshots: list[dict[str, Any]]) -> int:
        """Completely replace the active population and return its revision."""
        normalized_run_id = _required_string(run_id, "run_id")
        if not isinstance(organism_snapshots, list):
            raise TypeError("organism_snapshots must be a list")

        published: dict[str, dict[str, Any]] = {}
        for index, raw_snapshot in enumerate(organism_snapshots):
            if not isinstance(raw_snapshot, dict):
                raise TypeError(f"organism_snapshots[{index}] must be an object")
            _validate_json_value(raw_snapshot, f"organism_snapshots[{index}]")
            copied = _json_copy(raw_snapshot)
            organism_id = _required_string(copied.get("organism_id"), "organism_id")
            if organism_id in published:
                raise ValueError(f"duplicate organism_id: {organism_id}")
            if "source" in copied:
                raise ValueError("source is authority-owned")
            published[organism_id] = {
                "source": SNAPSHOT_SOURCE,
                **copied,
                "organism_id": organism_id,
            }

        with self._lock:
            if self._active_run_id is None:
                raise RuntimeError("not_running")
            if normalized_run_id != self._active_run_id:
                raise RuntimeError("stale")
            self._snapshots = published
            self._revision += 1
            return self._revision

    def query(self, identity: Mapping[str, Any] | object) -> dict[str, Any]:
        """Query one organism, resolving stale run before organism lookup."""
        parsed, status = self._parse_identity(identity)
        if status is not None:
            return self._query_envelope(status=status, identity=parsed)

        assert parsed is not None
        with self._lock:
            if self._active_run_id is None:
                return self._query_envelope(status="not_running", identity=parsed)
            if parsed["run_id"] != self._active_run_id:
                return self._query_envelope(status="stale", identity=parsed)

            organism_id = parsed["organism_id"]
            if organism_id not in self._snapshots:
                return self._query_envelope(
                    status="missing",
                    identity=parsed,
                    revision=self._revision,
                )
            return self._query_envelope(
                status="ok",
                identity=parsed,
                revision=self._revision,
                snapshot=_json_copy(self._snapshots[organism_id]),
            )

    def end(self, run_id: str) -> dict[str, Any]:
        """End only the matching active run lifetime."""
        try:
            normalized_run_id = _required_string(run_id, "run_id")
        except (TypeError, ValueError):
            return self._lifecycle_envelope("invalid_identity", None)

        with self._lock:
            if self._active_run_id is None:
                return self._lifecycle_envelope("not_running", normalized_run_id)
            if normalized_run_id != self._active_run_id:
                return self._lifecycle_envelope("stale", normalized_run_id)
            self._active_run_id = None
            self._revision = 0
            self._snapshots = {}
            return self._lifecycle_envelope("ended", normalized_run_id)

    def _parse_identity(
        self,
        identity: Mapping[str, Any] | object,
    ) -> tuple[dict[str, str] | None, str | None]:
        if not isinstance(identity, Mapping):
            return None, "invalid_identity"
        track = identity.get("track")
        if not isinstance(track, str) or not track.strip():
            return None, "invalid_identity"
        if track.strip() != TRACK:
            return _safe_identity(identity), "unsupported_track"

        required: dict[str, str] = {"track": TRACK}
        for field in ("run_id", "organism_id"):
            value = identity.get(field)
            if not isinstance(value, str) or not value.strip():
                return _safe_identity(identity), "invalid_identity"
            required[field] = value.strip()
        return required, None

    def _query_envelope(
        self,
        *,
        status: str,
        identity: dict[str, str] | None,
        revision: int | None = None,
        snapshot: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "scope": SCOPE,
            "authority": AUTHORITY_NAME,
            "track": TRACK,
            "read_only": True,
            "identity_relation": IDENTITY_RELATION,
            "identity": identity,
        }
        if revision is not None:
            result["revision"] = int(revision)
        if snapshot is not None:
            result["snapshot"] = snapshot
        return result

    def _lifecycle_envelope(self, status: str, run_id: str | None) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "authority": AUTHORITY_NAME,
            "track": TRACK,
            "run_id": run_id,
        }


def _required_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _safe_identity(identity: Mapping[str, Any]) -> dict[str, str] | None:
    result: dict[str, str] = {}
    for field in ("track", "run_id", "organism_id"):
        value = identity.get(field)
        if isinstance(value, str):
            result[field] = value.strip()
    return result or None


def _validate_json_value(value: object, path: str) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} must not contain NaN or Infinity")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} keys must be strings")
            _validate_json_value(item, f"{path}.{key}")
        return
    raise TypeError(f"{path} contains non-JSON value: {type(value).__name__}")


def _json_copy(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
