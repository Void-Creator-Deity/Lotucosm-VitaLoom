"""Composition authority for the current legacy PyQt Project World Host."""

from __future__ import annotations

from .project_world_host_ownership import (
    ProjectWorldHostLease,
    ProjectWorldHostOwnership,
)


def _create_legacy_project_world_host() -> object:
    from .project_manager import get_project_manager

    return get_project_manager()


def _dispose_legacy_project_world_host(host: object) -> bool:
    from .project_manager import release_project_manager_instance

    return release_project_manager_instance(expected=host)


_OWNERSHIP = ProjectWorldHostOwnership(
    _create_legacy_project_world_host,
    _dispose_legacy_project_world_host,
)


def acquire_project_world_host(owner: str) -> ProjectWorldHostLease[object]:
    """Acquire one owned lease for the current concrete Host Adapter."""

    return _OWNERSHIP.acquire(owner)


def dispose_project_world_host_if_idle() -> bool:
    """Clear idle composition state and any legacy unleased singleton."""

    if not _OWNERSHIP.dispose_if_idle():
        return False
    from .project_manager import release_project_manager_instance

    release_project_manager_instance()
    return True


def project_world_host_ownership_snapshot() -> dict[str, object]:
    """Return lifecycle diagnostics without exposing business methods."""

    return {
        "active_lease_count": _OWNERSHIP.active_lease_count,
        "owner_labels": _OWNERSHIP.owner_labels,
        "has_host": _OWNERSHIP.current_host is not None,
    }
