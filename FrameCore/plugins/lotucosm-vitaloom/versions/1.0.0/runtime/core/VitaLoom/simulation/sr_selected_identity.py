# -*- coding: utf-8 -*-
"""Qt-free correlation between editor scene identity and live SR identity.

The Module accepts JSON-only selection and runtime facts.  It owns validation,
scene correlation, status precedence, Authority querying, counterpart truth, and
copy isolation.  Qt objects and live runtime objects must be projected by an
Adapter before entering this Seam.
"""
from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from typing import Any


SCHEMA_VERSION = 1
SCOPE = "selected_sr_runtime_entity"
TRACK = "sr_play"
IDENTITY_RELATION = "scene_correlated_not_unified"
AUTHORITY_NAME = "sr_selected_identity_correlation"


class SrSelectedIdentityCorrelation:
    """Resolve one projected editor selection against an SR snapshot Authority."""

    def resolve(
        self,
        selection_snapshot: object,
        runtime_context: object,
        query_snapshot: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        *,
        explicit_identity: object | None = None,
    ) -> dict[str, Any]:
        selection, selection_result = self._parse_selection(selection_snapshot)
        if selection_result is not None:
            return selection_result
        assert selection is not None

        runtime, runtime_result = self._parse_runtime_context(runtime_context)
        if runtime_result is not None:
            return runtime_result
        assert runtime is not None

        if runtime["runtime_epoch"] is None:
            return self._envelope(status="not_running", identity=None)

        runtime_scene_path = runtime["scene_path"]
        if runtime_scene_path is None:
            return self._envelope(
                status="invalid_identity",
                reason="malformed_runtime_context",
                identity=None,
            )
        if _canonical_scene_path(selection["scene_path"]) != _canonical_scene_path(
            runtime_scene_path
        ):
            return self._envelope(
                status="invalid_identity",
                reason="scene_mismatch",
                identity=None,
            )

        identity: dict[str, str]
        if explicit_identity is None:
            identity = {
                "track": TRACK,
                "runtime_epoch": runtime["runtime_epoch"],
                "scene_path": runtime["scene_path"],
                "entity_id": selection["entity_id"],
            }
        else:
            parsed_identity, identity_result = self._parse_explicit_identity(
                explicit_identity,
                selection,
                runtime,
            )
            if identity_result is not None:
                return identity_result
            assert parsed_identity is not None
            identity = parsed_identity

        try:
            authority_result = query_snapshot(_json_copy(identity))
        except Exception as exc:
            return self._envelope(
                status="error",
                reason="authority_query_failed",
                identity=identity,
                error_type=type(exc).__name__,
            )

        if not isinstance(authority_result, Mapping):
            return self._envelope(
                status="error",
                reason="invalid_authority_response",
                identity=identity,
            )
        try:
            copied = _json_copy(dict(authority_result))
        except (TypeError, ValueError):
            return self._envelope(
                status="error",
                reason="non_json_authority_response",
                identity=identity,
            )

        status = copied.get("status")
        if not isinstance(status, str) or not status:
            return self._envelope(
                status="error",
                reason="invalid_authority_response",
                identity=identity,
            )
        if status != "ok":
            return self._envelope_from_authority(copied, identity)

        snapshot = copied.get("snapshot")
        if not isinstance(snapshot, dict):
            return self._envelope(
                status="error",
                reason="invalid_authority_snapshot",
                identity=identity,
            )
        if snapshot.get("serialized_scene_counterpart") is not True:
            return self._envelope(
                status="invalid_identity",
                reason="not_serialized_scene_counterpart",
                identity=identity,
            )

        result = self._envelope(status="ok", identity=identity)
        revision = copied.get("revision")
        if isinstance(revision, int) and not isinstance(revision, bool):
            result["revision"] = revision
        result["snapshot"] = _json_copy(snapshot)
        return result

    def _parse_selection(
        self,
        value: object,
    ) -> tuple[dict[str, str] | None, dict[str, Any] | None]:
        if not isinstance(value, Mapping):
            return None, self._envelope(
                status="invalid_identity",
                reason="malformed_selection_projection",
                identity=None,
            )
        count = value.get("selection_count")
        items = value.get("items")
        if (
            not isinstance(count, int)
            or isinstance(count, bool)
            or count < 0
            or not isinstance(items, list)
            or count != len(items)
        ):
            return None, self._envelope(
                status="invalid_identity",
                reason="malformed_selection_projection",
                identity=None,
            )
        if count == 0:
            return None, self._envelope(
                status="unavailable",
                reason="no_selection",
                identity=None,
            )
        if count != 1:
            return None, self._envelope(
                status="unavailable",
                reason="multiple_selection",
                identity=None,
            )

        item = items[0]
        if not isinstance(item, Mapping):
            return None, self._envelope(
                status="invalid_identity",
                reason="malformed_selection_projection",
                identity=None,
            )
        kind = item.get("kind")
        if kind == "invalid_scene_entity":
            return None, self._envelope(
                status="invalid_identity",
                reason=str(item.get("reason") or "invalid_scene_entity"),
                identity=None,
            )
        if kind != "scene_entity":
            return None, self._envelope(
                status="unavailable",
                reason="non_entity_selection",
                identity=None,
            )
        scene_path = _nonempty_string(item.get("scene_path"))
        entity_id = _nonempty_string(item.get("entity_id"))
        if scene_path is None or entity_id is None:
            return None, self._envelope(
                status="invalid_identity",
                reason="malformed_scene_entity_identity",
                identity=None,
            )
        return {"scene_path": scene_path, "entity_id": entity_id}, None

    def _parse_runtime_context(
        self,
        value: object,
    ) -> tuple[dict[str, str | None] | None, dict[str, Any] | None]:
        if not isinstance(value, Mapping):
            return None, self._envelope(
                status="invalid_identity",
                reason="malformed_runtime_context",
                identity=None,
            )
        track = _nonempty_string(value.get("track"))
        if track is None:
            return None, self._envelope(
                status="invalid_identity",
                reason="malformed_runtime_context",
                identity=None,
            )
        if track != TRACK:
            return None, self._envelope(
                status="unsupported_track",
                reason="unsupported_track",
                identity=None,
            )
        scene_path = _nonempty_string(value.get("scene_path"))
        raw_epoch = value.get("runtime_epoch")
        runtime_epoch = None if raw_epoch is None else _nonempty_string(raw_epoch)
        if raw_epoch is not None and (runtime_epoch is None or scene_path is None):
            return None, self._envelope(
                status="invalid_identity",
                reason="malformed_runtime_context",
                identity=None,
            )
        return {
            "track": TRACK,
            "runtime_epoch": runtime_epoch,
            "scene_path": scene_path,
        }, None

    def _parse_explicit_identity(
        self,
        value: object,
        selection: Mapping[str, str],
        runtime: Mapping[str, str | None],
    ) -> tuple[dict[str, str] | None, dict[str, Any] | None]:
        if not isinstance(value, Mapping):
            return None, self._envelope(
                status="invalid_identity",
                reason="malformed_explicit_identity",
                identity=None,
            )
        track = _nonempty_string(value.get("track"))
        if track is None:
            return None, self._envelope(
                status="invalid_identity",
                reason="malformed_explicit_identity",
                identity=None,
            )
        if track != TRACK:
            safe = _safe_identity(value)
            return None, self._envelope(
                status="unsupported_track",
                reason="unsupported_track",
                identity=safe,
            )
        fields: dict[str, str] = {"track": TRACK}
        for field in ("runtime_epoch", "scene_path", "entity_id"):
            parsed = _nonempty_string(value.get(field))
            if parsed is None:
                return None, self._envelope(
                    status="invalid_identity",
                    reason="malformed_explicit_identity",
                    identity=_safe_identity(value),
                )
            fields[field] = parsed

        if _canonical_scene_path(fields["scene_path"]) != _canonical_scene_path(
            selection["scene_path"]
        ):
            return None, self._envelope(
                status="invalid_identity",
                reason="scene_mismatch",
                identity=fields,
            )
        if fields["entity_id"] != selection["entity_id"]:
            return None, self._envelope(
                status="invalid_identity",
                reason="selection_entity_mismatch",
                identity=fields,
            )
        # The explicit epoch may be old by design. The Authority owns stale order.
        return fields, None

    def _envelope_from_authority(
        self,
        authority_result: Mapping[str, Any],
        identity: Mapping[str, str],
    ) -> dict[str, Any]:
        status = str(authority_result.get("status"))
        allowed = {
            "not_running",
            "stale",
            "missing",
            "invalid_identity",
            "unsupported_track",
            "error",
        }
        if status not in allowed:
            return self._envelope(
                status="error",
                reason="unsupported_authority_status",
                identity=identity,
            )
        result = self._envelope(status=status, identity=identity)
        revision = authority_result.get("revision")
        if isinstance(revision, int) and not isinstance(revision, bool):
            result["revision"] = revision
        return result

    def _envelope(
        self,
        *,
        status: str,
        identity: Mapping[str, str] | None,
        reason: str | None = None,
        error_type: str | None = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "scope": SCOPE,
            "authority": AUTHORITY_NAME,
            "track": TRACK,
            "read_only": True,
            "selection_relation": IDENTITY_RELATION,
            "identity": _json_copy(dict(identity)) if identity is not None else None,
        }
        if reason is not None:
            result["reason"] = str(reason)
        if error_type is not None:
            result["error_type"] = str(error_type)
        return result


def _nonempty_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _canonical_scene_path(value: str) -> str:
    return os.path.normcase(os.path.abspath(os.path.normpath(value)))


def _safe_identity(value: Mapping[str, Any]) -> dict[str, str] | None:
    result: dict[str, str] = {}
    for field in ("track", "runtime_epoch", "scene_path", "entity_id"):
        parsed = _nonempty_string(value.get(field))
        if parsed is not None:
            result[field] = parsed
    return result or None


def _json_copy(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))

