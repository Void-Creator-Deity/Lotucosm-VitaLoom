"""Qt-free ownership for one shared Project World Host Adapter.

This module owns lifecycle only. It deliberately does not expose or forward
Project World business operations; callers use the E9-E11 capability seams.
"""

from __future__ import annotations

from threading import RLock
from typing import Callable, Generic, TypeVar


HostT = TypeVar("HostT")


class ProjectWorldHostLease(Generic[HostT]):
    """One idempotently releasable claim on a shared Host Adapter."""

    def __init__(
        self,
        ownership: "ProjectWorldHostOwnership[HostT]",
        token: object,
        owner: str,
        host: HostT,
    ) -> None:
        self._ownership = ownership
        self._token = token
        self._owner = owner
        self._host = host
        self._released = False

    @property
    def owner(self) -> str:
        return self._owner

    @property
    def host(self) -> HostT:
        return self._host

    @property
    def released(self) -> bool:
        return self._released

    def release(self) -> bool:
        """Release this claim; a repeated successful release is a no-op."""

        if self._released:
            return False
        released = self._ownership._release(self._token, self._host)
        if released:
            self._released = True
        return released


class ProjectWorldHostOwnership(Generic[HostT]):
    """Create, reuse and dispose one Host only at the final lease boundary."""

    def __init__(
        self,
        factory: Callable[[], HostT],
        disposer: Callable[[HostT], object],
    ) -> None:
        if not callable(factory):
            raise TypeError("Project World Host factory must be callable")
        if not callable(disposer):
            raise TypeError("Project World Host disposer must be callable")
        self._factory = factory
        self._disposer = disposer
        self._host: HostT | None = None
        self._leases: dict[object, str] = {}
        self._lock = RLock()

    @property
    def current_host(self) -> HostT | None:
        with self._lock:
            return self._host

    @property
    def active_lease_count(self) -> int:
        with self._lock:
            return len(self._leases)

    @property
    def owner_labels(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._leases.values())

    def acquire(self, owner: str) -> ProjectWorldHostLease[HostT]:
        owner_label = str(owner).strip()
        if not owner_label:
            raise ValueError("Project World Host lease owner must be non-empty")

        with self._lock:
            host = self._host
            if host is None:
                host = self._factory()
                if host is None:
                    raise RuntimeError("Project World Host factory returned None")
                self._host = host
            token = object()
            self._leases[token] = owner_label
            return ProjectWorldHostLease(self, token, owner_label, host)

    def dispose_if_idle(self) -> bool:
        """Dispose the retained Host when no leases exist."""

        with self._lock:
            if self._leases:
                return False
            host = self._host
            if host is None:
                return True
            self._dispose_retained_host(host)
            return True

    def _release(self, token: object, expected_host: HostT) -> bool:
        with self._lock:
            if token not in self._leases:
                return False
            if self._host is not expected_host:
                raise RuntimeError("Project World Host lease no longer matches retained Host")
            if len(self._leases) > 1:
                del self._leases[token]
                return True

            self._dispose_retained_host(expected_host)
            del self._leases[token]
            return True

    def _dispose_retained_host(self, host: HostT) -> None:
        result = self._disposer(host)
        if result is False:
            raise RuntimeError("Project World Host disposer refused the retained Host")
        self._host = None
