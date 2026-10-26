# -*- coding: utf-8 -*-
"""Qt-free authority for epoch-scoped SR runtime entity snapshots.

The Module owns only opaque lifetime identity and JSON copies.  Live SR entities,
Qt objects, scripts, component objects, and mutable viewport registries remain in
the GameViewport Implementation and must be projected by an Adapter before
publication.
"""
from __future__ import annotations

import json
import math
from itertools import count
from collections.abc import Mapping
from typing import Any
from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource


SCHEMA_VERSION = 1
AUTHORITY_NAME = "sr_runtime_snapshot_authority"
SCOPE = "selected_sr_runtime_entity"
TRACK = "sr_play"
IDENTITY_RELATION = "scene_correlated_not_unified"
SNAPSHOT_SOURCE = "read_only_json_snapshot"
_EDITOR_COMPAT_EPOCH_COUNTER = count(1)


class SrRuntimeSnapshotAuthority:
    """Own one active SR runtime lifetime and copy-isolated JSON snapshots."""

    def __init__(self, *, identity_source: DeterministicIdentitySource | None = None) -> None:
        self._active_epoch: str | None = None
        self._active_scene_path: str | None = None
        self._revision = 0
        self._snapshots: dict[str, dict[str, Any]] = {}
        self._identity_source = identity_source

    def begin(self, scene_path: str) -> str:
        """Begin a new lifetime, superseding any previous epoch."""
        normalized_scene_path = _required_string(scene_path, "scene_path")
        runtime_epoch = (
            self._identity_source.next("sr")
            if self._identity_source is not None
            else f"sr_editor_{next(_EDITOR_COMPAT_EPOCH_COUNTER)}"
        )
        self._active_epoch = runtime_epoch
        self._active_scene_path = normalized_scene_path
        self._revision = 0
        self._snapshots = {}
        return runtime_epoch

    def current_epoch(self) -> str | None:
        """Return the active opaque epoch without exposing snapshot storage."""
        return self._active_epoch

    def publish(self, runtime_epoch: str, entity_snapshots: list[dict[str, Any]]) -> int:
        """Replace the current snapshot set and return its monotonic revision."""
        epoch = _required_string(runtime_epoch, "runtime_epoch")
        if self._active_epoch is None:
            raise RuntimeError("not_running")
        if epoch != self._active_epoch:
            raise RuntimeError("stale")
        if not isinstance(entity_snapshots, list):
            raise TypeError("entity_snapshots must be a list")

        published: dict[str, dict[str, Any]] = {}
        for index, raw_snapshot in enumerate(entity_snapshots):
            if not isinstance(raw_snapshot, dict):
                raise TypeError(f"entity_snapshots[{index}] must be an object")
            _validate_json_value(raw_snapshot, f"entity_snapshots[{index}]")
            copied = _json_copy(raw_snapshot)
            entity_id = _required_string(copied.get("entity_id"), "entity_id")
            if entity_id in published:
                raise ValueError(f"duplicate entity_id: {entity_id}")
            if "source" in copied:
                raise ValueError("source is authority-owned")
            published[entity_id] = {
                "source": SNAPSHOT_SOURCE,
                **copied,
                "entity_id": entity_id,
            }

        self._snapshots = published
        self._revision += 1
        return self._revision

    def query(self, identity: Mapping[str, Any] | object) -> dict[str, Any]:
        """Query one entity, resolving stale lifetime before entity lookup."""
        parsed, status = self._parse_identity(identity)
        if status is not None:
            return self._query_envelope(status=status, identity=parsed)

        assert parsed is not None
        if self._active_epoch is None:
            return self._query_envelope(status="not_running", identity=parsed)
        if parsed["runtime_epoch"] != self._active_epoch:
            return self._query_envelope(status="stale", identity=parsed)
        if parsed["scene_path"] != self._active_scene_path:
            return self._query_envelope(status="invalid_identity", identity=parsed)

        entity_id = parsed["entity_id"]
        if entity_id not in self._snapshots:
            return self._query_envelope(
                status="missing",
                identity=parsed,
                revision=self._revision,
            )
        return self._query_envelope(
            status="ok",
            identity=parsed,
            revision=self._revision,
            snapshot=_json_copy(self._snapshots[entity_id]),
        )

    def end(self, runtime_epoch: str) -> dict[str, Any]:
        """End only the matching active lifetime."""
        try:
            epoch = _required_string(runtime_epoch, "runtime_epoch")
        except (TypeError, ValueError):
            return self._lifecycle_envelope("invalid_identity", None)
        if self._active_epoch is None:
            return self._lifecycle_envelope("not_running", epoch)
        if epoch != self._active_epoch:
            return self._lifecycle_envelope("stale", epoch)

        self._active_epoch = None
        self._active_scene_path = None
        self._revision = 0
        self._snapshots = {}
        return self._lifecycle_envelope("ended", epoch)

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
        for field in ("runtime_epoch", "scene_path", "entity_id"):
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

    def _lifecycle_envelope(self, status: str, runtime_epoch: str | None) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "authority": AUTHORITY_NAME,
            "track": TRACK,
            "runtime_epoch": runtime_epoch,
        }


def _required_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _safe_identity(identity: Mapping[str, Any]) -> dict[str, str] | None:
    result: dict[str, str] = {}
    for field in ("track", "runtime_epoch", "scene_path", "entity_id"):
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
