# -*- coding: utf-8 -*-
"""Qt-free Project World Host capability catalog.

The versioned VitaLoom runtime owns these narrow Interfaces.  Concrete UI Hosts
register Adapters at the composition root; L2/L3 consumers never receive the
legacy ProjectManager itself.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from core.VitaLoom.core.runtime_capability_registry import (
    resolve_runtime_capability_registry,
)
from core.VitaLoom.core.service_keys import (
    PROJECT_WORLD_CONFIGURATION_HOST,
    PROJECT_WORLD_CREATION_HOST,
    PROJECT_WORLD_MANIFEST_VALIDATION_HOST,
    PROJECT_WORLD_READ_MODEL,
    PROJECT_WORLD_RECENT_REGISTRY,
)


@runtime_checkable
class IProjectWorldReadModel(Protocol):
    """Read-only snapshot Interface for the currently applied Project World."""

    def current_project_world_path(self) -> str: ...

    def current_project_world_config(self) -> dict[str, Any]: ...


@runtime_checkable
class IProjectWorldConfigurationHost(Protocol):
    """Narrow mutation Interface for top-level project.json fields."""

    def update_current_project_world_config_fields(
        self, fields: Mapping[str, Any]
    ) -> bool: ...


@runtime_checkable
class IRecentProjectWorldRegistry(Protocol):
    """Read-only registry Interface intended for Hub Adapters."""

    def recent_project_world_paths(self) -> tuple[str, ...]: ...


@runtime_checkable
class IProjectWorldCreationHost(Protocol):
    """Host application Interface around the Qt-free creation authority."""

    def default_project_world_parent(self) -> str: ...

    def available_project_world_templates(self) -> tuple[str, ...]: ...

    def create_project_world(
        self,
        project_name: str,
        project_path: str | None = None,
        template: str | None = None,
        description: str = "",
    ) -> str | None: ...


@runtime_checkable
class IProjectWorldManifestValidationHost(Protocol):
    """Explicit refresh Interface for current Project World manifest evidence."""

    def refresh_current_project_manifest_validation(self) -> dict[str, Any]: ...


def _copy_json_mapping(value: object, *, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    try:
        copied = json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{label} must be strict JSON-compatible") from exc
    if not isinstance(copied, dict):
        raise TypeError(f"{label} must serialize to an object")
    return copied


def _normalized_path(value: object) -> str:
    raw = str(value or "").strip()
    return str(Path(raw).expanduser().resolve()) if raw else ""


class _LegacyProjectWorldReadModelAdapter:
    def __init__(self, host: object) -> None:
        self._host = host

    def current_project_world_path(self) -> str:
        return _normalized_path(self._host.get_current_project_path())

    def current_project_world_config(self) -> dict[str, Any]:
        return _copy_json_mapping(
            self._host.get_current_project_config(),
            label="Project World configuration",
        )


class _LegacyProjectWorldConfigurationHostAdapter:
    def __init__(self, host: object) -> None:
        self._host = host

    def update_current_project_world_config_fields(
        self, fields: Mapping[str, Any]
    ) -> bool:
        copied = _copy_json_mapping(fields, label="Project World configuration fields")
        return bool(self._host.update_project_config_fields(copied))


class _LegacyRecentProjectWorldRegistryAdapter:
    def __init__(self, host: object) -> None:
        self._host = host

    def recent_project_world_paths(self) -> tuple[str, ...]:
        seen: set[str] = set()
        paths: list[str] = []
        for value in self._host.get_recent_projects() or ():
            normalized = _normalized_path(value)
            key = normalized.casefold()
            if normalized and key not in seen:
                seen.add(key)
                paths.append(normalized)
        return tuple(paths)


class _LegacyProjectWorldCreationHostAdapter:
    def __init__(self, host: object) -> None:
        self._host = host

    def default_project_world_parent(self) -> str:
        return _normalized_path(getattr(self._host, "projects_dir", ""))

    def available_project_world_templates(self) -> tuple[str, ...]:
        return tuple(str(item) for item in (self._host.get_available_templates() or ()))

    def create_project_world(
        self,
        project_name: str,
        project_path: str | None = None,
        template: str | None = None,
        description: str = "",
    ) -> str | None:
        created = self._host.create_project(
            str(project_name),
            project_path,
            template,
            str(description or ""),
        )
        return _normalized_path(created) or None


class _LegacyProjectWorldManifestValidationHostAdapter:
    def __init__(self, host: object) -> None:
        self._host = host

    def refresh_current_project_manifest_validation(self) -> dict[str, Any]:
        report = self._host.refresh_current_project_manifest_validation()
        return _copy_json_mapping(report, label="Project World manifest validation report")


class _UnavailableProjectWorldReadModel:
    def current_project_world_path(self) -> str:
        return ""

    def current_project_world_config(self) -> dict[str, Any]:
        return {}


class _UnavailableProjectWorldConfigurationHost:
    def update_current_project_world_config_fields(
        self, fields: Mapping[str, Any]
    ) -> bool:
        return False


class _UnavailableRecentProjectWorldRegistry:
    def recent_project_world_paths(self) -> tuple[str, ...]:
        return ()


class _UnavailableProjectWorldCreationHost:
    def default_project_world_parent(self) -> str:
        return ""

    def available_project_world_templates(self) -> tuple[str, ...]:
        return ()

    def create_project_world(
        self,
        project_name: str,
        project_path: str | None = None,
        template: str | None = None,
        description: str = "",
    ) -> str | None:
        return None


class _UnavailableProjectWorldManifestValidationHost:
    def refresh_current_project_manifest_validation(self) -> dict[str, Any]:
        return {
            "status": "unavailable",
            "code": "project_world_manifest_validation_host_unavailable",
            "project_path": "",
            "missing_packages": [],
        }


_UNAVAILABLE_READ_MODEL = _UnavailableProjectWorldReadModel()
_UNAVAILABLE_CONFIGURATION_HOST = _UnavailableProjectWorldConfigurationHost()
_UNAVAILABLE_RECENT_REGISTRY = _UnavailableRecentProjectWorldRegistry()
_UNAVAILABLE_CREATION_HOST = _UnavailableProjectWorldCreationHost()
_UNAVAILABLE_MANIFEST_HOST = _UnavailableProjectWorldManifestValidationHost()


def _register_legacy_capability_adapter(
    capabilities: dict[str, object],
    host: object,
    *,
    key: str,
    method_names: tuple[str, ...],
    adapter_type: type,
) -> None:
    available = {
        name: callable(getattr(host, name, None)) for name in method_names
    }
    if not any(available.values()):
        return
    missing = sorted(name for name, present in available.items() if not present)
    if missing:
        raise TypeError(
            f"Project World Host exposes an incomplete {key} capability; "
            + "missing methods: "
            + ", ".join(missing)
        )
    capabilities[key] = adapter_type(host)


def adapt_project_world_host_capabilities(host: object) -> dict[str, object]:
    """Project one legacy Host into every complete narrow capability it exposes."""

    capabilities: dict[str, object] = {}
    _register_legacy_capability_adapter(
        capabilities,
        host,
        key=PROJECT_WORLD_READ_MODEL,
        method_names=("get_current_project_path", "get_current_project_config"),
        adapter_type=_LegacyProjectWorldReadModelAdapter,
    )
    _register_legacy_capability_adapter(
        capabilities,
        host,
        key=PROJECT_WORLD_CONFIGURATION_HOST,
        method_names=("update_project_config_fields",),
        adapter_type=_LegacyProjectWorldConfigurationHostAdapter,
    )
    _register_legacy_capability_adapter(
        capabilities,
        host,
        key=PROJECT_WORLD_RECENT_REGISTRY,
        method_names=("get_recent_projects",),
        adapter_type=_LegacyRecentProjectWorldRegistryAdapter,
    )
    _register_legacy_capability_adapter(
        capabilities,
        host,
        key=PROJECT_WORLD_CREATION_HOST,
        method_names=("get_available_templates", "create_project"),
        adapter_type=_LegacyProjectWorldCreationHostAdapter,
    )
    _register_legacy_capability_adapter(
        capabilities,
        host,
        key=PROJECT_WORLD_MANIFEST_VALIDATION_HOST,
        method_names=("refresh_current_project_manifest_validation",),
        adapter_type=_LegacyProjectWorldManifestValidationHostAdapter,
    )
    if not capabilities:
        raise TypeError(
            "Project World Host does not expose any supported capability group"
        )
    return capabilities

def register_project_world_host_capabilities(
    services: object, host: object
) -> dict[str, object]:
    """Publish distinct narrow Adapters for one concrete Project World Host."""

    register = getattr(services, "register", None)
    if not callable(register):
        raise TypeError("Project World capability catalog requires services.register")
    capabilities = adapt_project_world_host_capabilities(host)
    for key, capability in capabilities.items():
        register(key, capability)
    return capabilities


def unregister_project_world_host_capabilities(
    services: object, capabilities: dict[str, object]
) -> tuple[str, ...]:
    """Unpublish only capability Adapters still owned by this registration."""

    get = getattr(services, "get", None)
    unregister = getattr(services, "unregister", None)
    if not callable(get) or not callable(unregister):
        raise TypeError(
            "Project World capability catalog requires services.get/unregister"
        )
    removed: list[str] = []
    for key, capability in capabilities.items():
        if get(key) is capability:
            unregister(key)
            removed.append(key)
    return tuple(removed)


def _existing_editor_context() -> object | None:
    try:
        from core.VitaLoom.core.editor_context import get_existing_editor_context

        return get_existing_editor_context()
    except Exception:
        return None


def _resolve(source: object | None, key: str, interface: type, fallback: object):
    registry = resolve_runtime_capability_registry(source)
    if registry is None and source is None:
        registry = resolve_runtime_capability_registry(_existing_editor_context())
    capability = registry.get(key) if registry is not None else None
    return capability if isinstance(capability, interface) else fallback


def get_project_world_read_model(
    editor_context: object | None = None,
) -> IProjectWorldReadModel:
    return _resolve(
        editor_context,
        PROJECT_WORLD_READ_MODEL,
        IProjectWorldReadModel,
        _UNAVAILABLE_READ_MODEL,
    )


def get_project_world_configuration_host(
    editor_context: object | None = None,
) -> IProjectWorldConfigurationHost:
    return _resolve(
        editor_context,
        PROJECT_WORLD_CONFIGURATION_HOST,
        IProjectWorldConfigurationHost,
        _UNAVAILABLE_CONFIGURATION_HOST,
    )


def get_recent_project_world_registry(
    editor_context: object | None = None,
) -> IRecentProjectWorldRegistry:
    return _resolve(
        editor_context,
        PROJECT_WORLD_RECENT_REGISTRY,
        IRecentProjectWorldRegistry,
        _UNAVAILABLE_RECENT_REGISTRY,
    )


def get_project_world_creation_host(
    editor_context: object | None = None,
) -> IProjectWorldCreationHost:
    return _resolve(
        editor_context,
        PROJECT_WORLD_CREATION_HOST,
        IProjectWorldCreationHost,
        _UNAVAILABLE_CREATION_HOST,
    )


def get_project_world_manifest_validation_host(
    editor_context: object | None = None,
) -> IProjectWorldManifestValidationHost:
    return _resolve(
        editor_context,
        PROJECT_WORLD_MANIFEST_VALIDATION_HOST,
        IProjectWorldManifestValidationHost,
        _UNAVAILABLE_MANIFEST_HOST,
    )
