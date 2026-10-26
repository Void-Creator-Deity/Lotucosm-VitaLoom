# -*- coding: utf-8 -*-
"""Qt-free Host Seam for PS runtime organism discovery and explicit queries."""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from core.Lotucosm.runtime.ps_runtime_snapshot_authority import (
    IDENTITY_RELATION,
    SCHEMA_VERSION,
    TRACK,
)
from core.VitaLoom.core.service_keys import PS_RUNTIME_SNAPSHOT_HOST


HOST_AUTHORITY = "ps_runtime_snapshot_host"
DISCOVERY_SCOPE = "ps_runtime_population"
QUERY_SCOPE = "ps_runtime_organism"
UNAVAILABLE_REASON = "ps_runtime_snapshot_host_unavailable"


@runtime_checkable
class IPsRuntimeSnapshotSource(Protocol):
    """Narrow source Interface implemented by the editor-owned PS Service."""

    def discover_runtime_organisms(self) -> dict[str, Any]: ...

    def query_runtime_organism_snapshot(self, identity: object) -> dict[str, Any]: ...


@runtime_checkable
class IPsRuntimeSnapshotHost(Protocol):
    """Command-facing Interface that never exposes a Service or live runtime object."""

    def discover_ps_runtime_organisms(self) -> dict[str, Any]: ...

    def query_ps_runtime_organism_snapshot(self, identity: object) -> dict[str, Any]: ...


class PsRuntimeSnapshotHostAdapter:
    """Adapt one narrow PS snapshot source to the Command-facing Host Interface."""

    def __init__(self, source: object) -> None:
        if not isinstance(source, IPsRuntimeSnapshotSource):
            raise TypeError("runtime snapshot source must implement discovery and query")
        self._source = source

    def discover_ps_runtime_organisms(self) -> dict[str, Any]:
        return _copy_json_object(self._source.discover_runtime_organisms())

    def query_ps_runtime_organism_snapshot(self, identity: object) -> dict[str, Any]:
        return _copy_json_object(
            self._source.query_runtime_organism_snapshot(identity)
        )


class _NullPsRuntimeSnapshotHost:
    def discover_ps_runtime_organisms(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "unavailable",
            "scope": DISCOVERY_SCOPE,
            "authority": HOST_AUTHORITY,
            "track": TRACK,
            "read_only": True,
            "identity_relation": IDENTITY_RELATION,
            "run_id": None,
            "revision": 0,
            "organism_count": 0,
            "identities": [],
            "reason": UNAVAILABLE_REASON,
        }

    def query_ps_runtime_organism_snapshot(self, identity: object) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "unavailable",
            "scope": QUERY_SCOPE,
            "authority": HOST_AUTHORITY,
            "track": TRACK,
            "read_only": True,
            "identity_relation": IDENTITY_RELATION,
            "identity": _safe_identity(identity),
            "reason": UNAVAILABLE_REASON,
        }


def get_ps_runtime_snapshot_host(source: Any = None) -> IPsRuntimeSnapshotHost:
    """Resolve the registered Host or return a deterministic Headless-safe Adapter."""
    from core.VitaLoom.core.runtime_capability_registry import (
        resolve_runtime_capability_registry,
    )

    registry = resolve_runtime_capability_registry(source)
    if registry is None and source is None:
        try:
            from core.VitaLoom.core.editor_context import get_existing_editor_context

            registry = resolve_runtime_capability_registry(get_existing_editor_context())
        except Exception:
            registry = None
    host = registry.get(PS_RUNTIME_SNAPSHOT_HOST) if registry is not None else None
    if isinstance(host, IPsRuntimeSnapshotHost):
        return host
    return _NullPsRuntimeSnapshotHost()


def _safe_identity(identity: object) -> dict[str, str] | None:
    if not isinstance(identity, Mapping):
        return None
    result: dict[str, str] = {}
    for field in ("track", "run_id", "organism_id"):
        value = identity.get(field)
        if isinstance(value, str):
            result[field] = value.strip()
    return result or None


def _copy_json_object(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("runtime snapshot Host result must be a JSON-compatible object")
    try:
        copied = json.loads(
            json.dumps(value, ensure_ascii=False, allow_nan=False)
        )
    except (TypeError, ValueError) as exc:
        raise TypeError(
            "runtime snapshot Host result must be a JSON-compatible object"
        ) from exc
    if not isinstance(copied, dict):
        raise TypeError("runtime snapshot Host result must be a JSON-compatible object")
    return copied
