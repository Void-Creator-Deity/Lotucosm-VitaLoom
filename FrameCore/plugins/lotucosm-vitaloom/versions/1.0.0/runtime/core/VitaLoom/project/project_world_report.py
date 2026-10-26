# -*- coding: utf-8 -*-
"""Qt-free canonical report support for Project World transitions."""

from __future__ import annotations

import hashlib
import json
import math
import os
from enum import Enum
from typing import Any, Mapping


def _json_safe(value: Any, *, _seen: set[int] | None = None) -> Any:
    """Project arbitrary Adapter evidence into deterministic JSON values."""

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, Enum):
        return _json_safe(value.value, _seen=_seen)
    if isinstance(value, os.PathLike):
        return os.fspath(value)
    if isinstance(value, bytes):
        return {"encoding": "hex", "value": value.hex()}

    seen = _seen if _seen is not None else set()
    identity = id(value)
    if identity in seen:
        return {"unsupported": "circular_reference", "type": type(value).__qualname__}

    if isinstance(value, Mapping):
        seen.add(identity)
        try:
            return {
                str(key): _json_safe(item, _seen=seen)
                for key, item in value.items()
            }
        finally:
            seen.remove(identity)
    if isinstance(value, (list, tuple)):
        seen.add(identity)
        try:
            return [_json_safe(item, _seen=seen) for item in value]
        finally:
            seen.remove(identity)
    if isinstance(value, (set, frozenset)):
        seen.add(identity)
        try:
            items = [_json_safe(item, _seen=seen) for item in value]
        finally:
            seen.remove(identity)
        return sorted(
            items,
            key=lambda item: json.dumps(
                item,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ),
        )
    return {
        "unsupported": "python_object",
        "type": f"{type(value).__module__}.{type(value).__qualname__}",
        "text": str(value),
    }


def _canonical_report_id(report: Mapping[str, Any]) -> str:
    payload = json.dumps(
        dict(report),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def finalize_project_world_report(report: Mapping[str, Any]) -> dict[str, Any]:
    """Return a strict JSON-safe report with a canonical SHA-256 identity."""

    safe = _json_safe(report)
    if not isinstance(safe, dict):
        raise TypeError("Project World report must be a mapping")
    safe.pop("report_id", None)
    safe["report_id"] = _canonical_report_id(safe)
    return safe
