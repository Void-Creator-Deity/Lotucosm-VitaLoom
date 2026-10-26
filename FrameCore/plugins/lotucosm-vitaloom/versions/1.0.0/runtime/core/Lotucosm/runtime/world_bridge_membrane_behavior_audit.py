"""Read-only evidence for WorldBridge membrane behavior mapping boundaries.

The world bridge may project the PS membrane's ``radius``/``ingest_threshold``/
``efficiency`` as read-only fields, but ``auto_ingest``/``is_inside`` stay
lane-local PS behaviors. This module binds that boundary to the real producer
(``builtin.components.membrane.Membrane``), proves the behavior is live inside
the PS lane, and proves the cross-lane projection surfaces never call it.
It never grants cross-lane behavior authority.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path
from typing import Any


_RUNTIME_ROOT = Path(__file__).resolve().parents[3]
_MEMBRANE_OWNER_MODULE = "builtin.components.membrane"
_SAFE_PROJECTION_FIELDS = ("radius", "ingest_threshold", "efficiency")
_FORBIDDEN_BEHAVIOR = ("auto_ingest", "is_inside")
_PS_LANE_ROOT = _RUNTIME_ROOT / "builtin"
_CROSS_LANE_ROOTS = (
    _RUNTIME_ROOT / "core" / "Lotucosm" / "runtime",
    _RUNTIME_ROOT / "core" / "VitaLoom" / "simulation",
    _RUNTIME_ROOT / "core" / "VitaLoom" / "viewports",
)


def build_worldbridge_membrane_behavior_audit() -> dict[str, Any]:
    """Classify PS membrane behavior without granting cross-lane authority."""
    decision = _component_decision()
    membrane_kind = decision.get("component_kinds", {}).get("Membrane", {})
    declared_safe = [str(name) for name in membrane_kind.get("safe_projection_fields", [])]
    declared_forbidden = [str(name) for name in membrane_kind.get("forbidden_behavior", [])]

    producer = _produce_membrane_surface()
    registered = producer["registered_projection_fields"]
    behavior_methods = producer["behavior_methods"]

    missing_projection_fields = sorted(set(declared_safe) - set(registered))
    missing_forbidden_behavior = sorted(set(declared_forbidden) - set(behavior_methods))

    ps_lane = _scan_behavior_calls((_PS_LANE_ROOT,), lane="ps_lane")
    cross_lane = _scan_behavior_calls(_CROSS_LANE_ROOTS, lane="cross_lane")

    # Non-vacuous positive proof: the PS lane really consumes the behavior.
    behavior_is_lane_local = bool(ps_lane["calls"]) and not cross_lane["calls"]
    # Fail closed: an empty scan surface must never read as "no cross-lane calls".
    producer_projection_bound = bool(
        producer["membrane_class_importable"]
        and producer["safe_projection_fields_match"]
        and not missing_forbidden_behavior
        and declared_safe == list(_SAFE_PROJECTION_FIELDS)
        and declared_forbidden == list(_FORBIDDEN_BEHAVIOR)
    )
    cross_lane_behavior_isolated = bool(
        producer_projection_bound
        and cross_lane["scanned_files"] > 0
        and ps_lane["scanned_files"] > 0
        and behavior_is_lane_local
    )

    return {
        "schema_version": 1,
        "status": "worldbridge_membrane_behavior_audit",
        "read_only": True,
        "audit_only": True,
        "mapping_state": "decision_only",
        "producer": producer,
        "declared_safe_projection_fields": declared_safe,
        "declared_forbidden_behavior": declared_forbidden,
        "missing_projection_fields": missing_projection_fields,
        "missing_forbidden_behavior": missing_forbidden_behavior,
        "ps_lane_usage": ps_lane,
        "cross_lane_scan": cross_lane,
        "behavior_is_lane_local": behavior_is_lane_local,
        "producer_projection_bound": producer_projection_bound,
        "cross_lane_behavior_isolated": cross_lane_behavior_isolated,
        "cross_lane_behavior_admitted": False,
        "lossless": False,
        "replay_admitted": False,
        "default_ready": False,
        "blockers": [
            "cross_lane_behavior_authority",
            "live_membrane_behavior_transaction",
            "replay_trace",
        ],
        "do_not_claim": [
            "worldbridge_live_membrane_mapping",
            "membrane_behavior_cross_lane_authority",
            "lossless_worldbridge_mapping",
            "unified_runtime_replay",
        ],
    }


def scan_membrane_behavior_calls(roots: tuple[Path, ...] | list[Path]) -> dict[str, Any]:
    """Scan ``roots`` for ``auto_ingest``/``is_inside`` attribute calls.

    Exposed so tests can plant a call and prove the detector is not vacuous.
    """
    return _scan_behavior_calls(tuple(roots), lane="adhoc")


def _component_decision() -> dict[str, Any]:
    module = importlib.import_module("core.Lotucosm.runtime.world_bridge_component_decision")
    decision = module.build_worldbridge_component_decision()
    if not isinstance(decision, dict):
        raise TypeError("worldbridge_component_decision_invalid")
    return decision


def _produce_membrane_surface() -> dict[str, Any]:
    """Introspect the real PS ``Membrane`` type; fail closed when unavailable."""
    surface: dict[str, Any] = {
        "module": _MEMBRANE_OWNER_MODULE,
        "membrane_class_importable": False,
        "registered_projection_fields": [],
        "behavior_methods": [],
        "safe_projection_fields_match": False,
        "error": None,
    }
    try:
        module = importlib.import_module(_MEMBRANE_OWNER_MODULE)
    except Exception as exc:  # pragma: no cover - environment dependent
        surface["error"] = type(exc).__name__
        return surface

    membrane_type = getattr(module, "Membrane", None)
    if not isinstance(membrane_type, type):
        surface["error"] = "membrane_type_missing"
        return surface
    surface["membrane_class_importable"] = True

    try:
        instance = membrane_type(component_id="worldbridge_membrane_behavior_audit_probe")
    except Exception as exc:  # pragma: no cover - producer contract change
        surface["error"] = type(exc).__name__
        return surface
    try:
        props = instance.get_inspectable_properties()
        if isinstance(props, dict):
            surface["registered_projection_fields"] = sorted(str(name) for name in props)
            surface["safe_projection_fields_match"] = set(_SAFE_PROJECTION_FIELDS) <= set(props)
    except Exception as exc:  # pragma: no cover - producer contract change
        surface["error"] = type(exc).__name__
        return surface
    finally:
        del instance

    surface["behavior_methods"] = sorted(
        name
        for name in dir(membrane_type)
        if not name.startswith("_") and callable(getattr(membrane_type, name, None))
    )
    return surface


def _scan_behavior_calls(roots: tuple[Path, ...], *, lane: str) -> dict[str, Any]:
    """Find forbidden membrane behavior calls under ``roots``."""
    calls: list[dict[str, str]] = []
    scanned = 0
    scanned_roots: list[str] = []
    for root in roots:
        if not root.is_dir():
            continue
        scanned_roots.append(_relative(root))
        for path in sorted(root.rglob("*.py")):
            if _is_membrane_owner(path):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            except (OSError, SyntaxError):
                continue
            scanned += 1
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in _FORBIDDEN_BEHAVIOR:
                    calls.append(
                        {
                            "file": _relative(path),
                            "line": str(getattr(node, "lineno", 0)),
                            "call": func.attr,
                        }
                    )
    return {
        "lane": lane,
        "scan_roots": scanned_roots,
        "scanned_files": scanned,
        "calls": calls,
    }


def _is_membrane_owner(path: Path) -> bool:
    normalized = str(path).replace("\\", "/")
    return normalized.endswith("builtin/components/membrane.py")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(_RUNTIME_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


__all__ = [
    "build_worldbridge_membrane_behavior_audit",
    "scan_membrane_behavior_calls",
]