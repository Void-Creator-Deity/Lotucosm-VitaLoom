"""Caller-owned deterministic identity source for replay-relevant lifetimes."""
from __future__ import annotations

import copy
import hashlib
import re
from typing import Any, Mapping


SCHEMA_VERSION = 1
_DOMAIN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")


class DeterministicIdentitySource:
    """Generate stable domain identities without process/global entropy."""

    __slots__ = ("_seed", "_seed_digest", "_counters")

    def __init__(self, seed: str | bytes | int) -> None:
        if isinstance(seed, bytes):
            seed_bytes = bytes(seed)
        elif isinstance(seed, int):
            seed_bytes = str(seed).encode("ascii")
        elif isinstance(seed, str) and seed:
            seed_bytes = seed.encode("utf-8")
        else:
            raise TypeError("identity seed must be non-empty str, bytes, or int")
        self._seed = seed_bytes
        self._seed_digest = hashlib.sha256(seed_bytes).hexdigest()
        self._counters: dict[str, int] = {}

    def next(self, domain: str) -> str:
        domain = _domain(domain)
        index = self._counters.get(domain, 0)
        self._counters[domain] = index + 1
        digest = hashlib.sha256(
            self._seed + b"\0" + domain.encode("ascii") + b"\0" + str(index).encode("ascii")
        ).hexdigest()
        return f"{domain}_{digest[:32]}"

    def snapshot(self) -> dict[str, Any]:
        value = {
            "schema_version": SCHEMA_VERSION,
            "kind": "deterministic_identity_source",
            "seed_digest": self._seed_digest,
            "seed_material_revealed": False,
            "counters": dict(sorted(self._counters.items())),
        }
        return copy.deepcopy(value)

    def restore(self, snapshot: Mapping[str, Any]) -> None:
        if not isinstance(snapshot, Mapping):
            raise TypeError("identity snapshot must be a mapping")
        if snapshot.get("schema_version") != SCHEMA_VERSION or snapshot.get("kind") != "deterministic_identity_source":
            raise ValueError("unsupported identity snapshot")
        if snapshot.get("seed_digest") != self._seed_digest or snapshot.get("seed_material_revealed") is not False:
            raise ValueError("identity source seed mismatch")
        counters = snapshot.get("counters")
        if not isinstance(counters, Mapping):
            raise ValueError("identity counters must be a mapping")
        prepared: dict[str, int] = {}
        for raw_domain, raw_count in counters.items():
            domain = _domain(raw_domain)
            if isinstance(raw_count, bool) or not isinstance(raw_count, int) or raw_count < 0:
                raise ValueError("identity counter must be a non-negative integer")
            prepared[domain] = raw_count
        self._counters = prepared


def _domain(value: object) -> str:
    clean = str(value or "")
    if not _DOMAIN_RE.fullmatch(clean):
        raise ValueError("identity domain is invalid")
    return clean


__all__ = ["DeterministicIdentitySource", "SCHEMA_VERSION"]
