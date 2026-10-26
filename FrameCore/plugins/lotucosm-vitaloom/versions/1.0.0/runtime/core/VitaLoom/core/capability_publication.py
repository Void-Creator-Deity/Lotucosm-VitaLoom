# -*- coding: utf-8 -*-
"""Qt-free capability publication lifecycle for versioned runtime Adapters.

The registry keeps the existing last-writer-wins lookup semantics. This Module
adds owner-labelled publication evidence, transactional multi-key registration,
and exact-object unpublication without turning the registry into a global owner
stack.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


_MISSING = object()


@dataclass(frozen=True)
class CapabilityPublicationRecord:
    """Evidence captured for one successfully published capability key."""

    owner: str
    key: str
    capability: object
    replaced_existing: bool


@dataclass(frozen=True)
class CapabilityPublicationRelease:
    """Deterministic evidence from one lease release attempt."""

    owner: str
    removed_keys: tuple[str, ...]
    retained_replacement_keys: tuple[str, ...]
    already_absent_keys: tuple[str, ...]
    already_released: bool


class CapabilityPublicationError(RuntimeError):
    """Publication failed and the registry could not be restored completely."""


class CapabilityUnpublicationError(RuntimeError):
    """Exact unpublication failed for one or more still-owned keys."""


def _require_registry(registry: object) -> None:
    if registry is None:
        raise TypeError("registry must provide register/get/unregister")
    missing = tuple(
        name
        for name in ("register", "get", "unregister")
        if not callable(getattr(registry, name, None))
    )
    if missing:
        raise TypeError(
            "registry must provide callable register/get/unregister; missing "
            + ", ".join(missing)
        )


def _normalize_publication(
    owner: str,
    capabilities: Mapping[str, object],
) -> tuple[str, tuple[tuple[str, object], ...]]:
    normalized_owner = str(owner or "").strip()
    if not normalized_owner:
        raise ValueError("publication owner must not be empty")
    if not isinstance(capabilities, Mapping):
        raise TypeError("capabilities must be a mapping")
    if not capabilities:
        raise ValueError("capabilities must not be empty")

    entries: list[tuple[str, object]] = []
    seen: set[str] = set()
    for raw_key, capability in capabilities.items():
        if not isinstance(raw_key, str):
            raise TypeError("capability keys must be strings")
        key = raw_key.strip()
        if not key:
            raise ValueError("capability key must not be empty")
        if key in seen:
            raise ValueError(f"duplicate normalized capability key: {key}")
        if capability is None:
            raise ValueError(f"capability must not be None: {key}")
        seen.add(key)
        entries.append((key, capability))
    return normalized_owner, tuple(entries)


class CapabilityPublicationLease:
    """Owns exact-object unpublication for one successful publication batch."""

    def __init__(
        self,
        registry: object,
        *,
        owner: str,
        records: tuple[CapabilityPublicationRecord, ...],
    ) -> None:
        self._registry = registry
        self._owner = owner
        self._records = records
        self._released = False

    @property
    def owner(self) -> str:
        return self._owner

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(record.key for record in self._records)

    @property
    def records(self) -> tuple[CapabilityPublicationRecord, ...]:
        return self._records

    @property
    def active(self) -> bool:
        return not self._released

    def release(self) -> CapabilityPublicationRelease:
        if self._released:
            return CapabilityPublicationRelease(
                owner=self._owner,
                removed_keys=(),
                retained_replacement_keys=(),
                already_absent_keys=(),
                already_released=True,
            )

        removed: list[str] = []
        retained: list[str] = []
        absent: list[str] = []
        failures: list[tuple[str, BaseException]] = []
        registry = self._registry

        for record in self._records:
            current = registry.get(record.key, _MISSING)
            if current is _MISSING:
                absent.append(record.key)
                continue
            if current is not record.capability:
                retained.append(record.key)
                continue
            try:
                registry.unregister(record.key)
            except BaseException as exc:
                failures.append((record.key, exc))
            else:
                removed.append(record.key)

        if failures:
            details = ", ".join(
                f"{key}: {type(exc).__name__}: {exc}" for key, exc in failures
            )
            raise CapabilityUnpublicationError(
                f"capability unpublication failed for owner {self._owner!r}: {details}"
            ) from failures[0][1]

        self._released = True
        return CapabilityPublicationRelease(
            owner=self._owner,
            removed_keys=tuple(removed),
            retained_replacement_keys=tuple(retained),
            already_absent_keys=tuple(absent),
            already_released=False,
        )


def publish_capabilities(
    registry: object,
    *,
    owner: str,
    capabilities: Mapping[str, object],
) -> CapabilityPublicationLease:
    """Publish a validated batch and return its exact-unpublication lease.

    All previous registry values are captured before the first write. If any
    registration raises, every attempted key is restored to its pre-publication
    state, including a failing registration that mutated before raising.
    """

    _require_registry(registry)
    normalized_owner, entries = _normalize_publication(owner, capabilities)
    previous: dict[str, Any] = {
        key: registry.get(key, _MISSING) for key, _capability in entries
    }
    attempted: list[str] = []

    try:
        for key, capability in entries:
            attempted.append(key)
            registry.register(key, capability)
    except BaseException as registration_error:
        rollback_failures: list[tuple[str, BaseException]] = []
        for key in reversed(attempted):
            prior = previous[key]
            try:
                if prior is _MISSING:
                    registry.unregister(key)
                else:
                    registry.register(key, prior)
            except BaseException as rollback_error:
                rollback_failures.append((key, rollback_error))
        if rollback_failures:
            details = ", ".join(
                f"{key}: {type(exc).__name__}: {exc}"
                for key, exc in rollback_failures
            )
            raise CapabilityPublicationError(
                "capability registration failed and rollback was incomplete for "
                f"owner {normalized_owner!r}: {details}"
            ) from registration_error
        raise

    records = tuple(
        CapabilityPublicationRecord(
            owner=normalized_owner,
            key=key,
            capability=capability,
            replaced_existing=previous[key] is not _MISSING,
        )
        for key, capability in entries
    )
    return CapabilityPublicationLease(
        registry,
        owner=normalized_owner,
        records=records,
    )


__all__ = [
    "CapabilityPublicationError",
    "CapabilityPublicationLease",
    "CapabilityPublicationRecord",
    "CapabilityPublicationRelease",
    "CapabilityUnpublicationError",
    "publish_capabilities",
]