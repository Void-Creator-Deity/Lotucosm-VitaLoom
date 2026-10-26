# -*- coding: utf-8 -*-
"""Qt-free control/observation Interface for the recursive VitaLoom plugin Host."""
from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from typing import Any, Protocol, runtime_checkable

from core.VitaLoom.core.runtime_capability_registry import (
    resolve_runtime_capability_registry,
)
from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION


@runtime_checkable
class PluginHostControlObservation(Protocol):
    def observe_plugins(self) -> dict[str, Any]: ...
    def reload_plugin(self, plugin_id: str) -> dict[str, Any]: ...
    def unload_plugin(self, plugin_id: str) -> dict[str, Any]: ...
    def scan_project_addons(self, project_path: object) -> dict[str, Any]: ...
    def sync_plugins_for_project(
        self, project_data: dict[str, Any], *, repo_root: object | None = None
    ) -> dict[str, Any]: ...


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [_json_safe(item) for item in sorted(value, key=lambda item: str(item))]
    return str(value)


def build_plugin_host_observation(host: object) -> dict[str, Any]:
    """Build fresh deterministic JSON-safe facts without leaking registry objects."""

    catalog_entries = list(host.catalog_entries())
    active_ids = sorted(str(item) for item in host.loaded_plugins)
    active = set(active_ids)
    reloadable_ids = sorted(str(item) for item in host.list_reloadable_plugins())
    reloadable = set(reloadable_ids)
    rows: list[dict[str, Any]] = []
    for entry in sorted(catalog_entries, key=lambda item: item.plugin_id):
        row = _json_safe(entry.to_dict())
        row["active"] = entry.plugin_id in active
        row["reloadable"] = entry.plugin_id in reloadable
        rows.append(row)

    failed = {
        str(plugin_id): _json_safe(error)
        for plugin_id, error in sorted(
            host.failed_plugins.items(), key=lambda item: str(item[0])
        )
    }
    discovery = {
        str(source): _json_safe(error)
        for source, error in sorted(
            host.discovery_errors.items(), key=lambda item: str(item[0])
        )
    }
    result = {
        "status": "degraded" if failed or discovery else "ready",
        "catalog": rows,
        "plugin_ids": [row["plugin_id"] for row in rows],
        "active_plugin_ids": active_ids,
        "reloadable_plugin_ids": reloadable_ids,
        "failed_plugin_ids": sorted(failed),
        "failed_plugins": failed,
        "discovery_errors": discovery,
        "lifecycle": _json_safe(getattr(host, "last_lifecycle_report", {})),
        "reload": _json_safe(getattr(host, "last_reload_report", {})),
        "counts": {
            "catalog": len(rows),
            "active": len(active_ids),
            "reloadable": len(reloadable_ids),
            "failed": len(failed),
            "discovery_errors": len(discovery),
        },
    }
    return _json_safe(result)


class _UnavailablePluginHost:
    def observe_plugins(self) -> dict[str, Any]:
        return {
            "status": "unavailable", "catalog": [], "plugin_ids": [],
            "active_plugin_ids": [], "reloadable_plugin_ids": [],
            "failed_plugin_ids": [], "failed_plugins": {},
            "discovery_errors": {}, "lifecycle": {}, "reload": {},
            "counts": {"catalog": 0, "active": 0, "reloadable": 0,
                       "failed": 0, "discovery_errors": 0},
        }

    @staticmethod
    def _blocked(action: str, plugin_id: str = "") -> dict[str, Any]:
        return {"status": "blocked", "code": "plugin_host_unavailable",
                "action": action, "plugin_id": str(plugin_id)}

    def reload_plugin(self, plugin_id: str) -> dict[str, Any]:
        return self._blocked("reload", plugin_id)

    def unload_plugin(self, plugin_id: str) -> dict[str, Any]:
        return self._blocked("unload", plugin_id)

    def scan_project_addons(self, project_path: object) -> dict[str, Any]:
        return self._blocked("scan_project_addons")

    def sync_plugins_for_project(
        self, project_data: dict[str, Any], *, repo_root: object | None = None
    ) -> dict[str, Any]:
        return self._blocked("sync_plugins_for_project")


_UNAVAILABLE = _UnavailablePluginHost()


def resolve_plugin_host(source: object | None) -> PluginHostControlObservation:
    registry = resolve_runtime_capability_registry(source)
    if registry is None:
        return _UNAVAILABLE
    capability = registry.get(PLUGIN_HOST_CONTROL_OBSERVATION)
    if capability is None:
        return _UNAVAILABLE
    if not isinstance(capability, PluginHostControlObservation):
        raise TypeError("plugin Host capability exposes an incomplete Interface")
    return capability


__all__ = [
    "PLUGIN_HOST_CONTROL_OBSERVATION", "PluginHostControlObservation",
    "build_plugin_host_observation", "resolve_plugin_host",
]
