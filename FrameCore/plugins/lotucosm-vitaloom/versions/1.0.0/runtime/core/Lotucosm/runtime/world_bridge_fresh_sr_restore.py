"""Fresh SR runtime restore parity coordinator.

The coordinator is deliberately Qt-free.  A UI host supplies two already
constructed SR runtimes; this module verifies structure before applying the
dynamic slice.  It never treats a partial slice as a complete runtime restore.
"""
from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from typing import Any

from core.VitaLoom.simulation.sr_runtime_structure_parity import (
    build_sr_runtime_structure_fingerprint,
    compare_sr_runtime_structure_fingerprints,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_fresh_sr_restore_parity"


def verify_fresh_sr_restore_parity(source: Any, fresh: Any) -> dict[str, Any]:
    """Restore one source dynamic SR slice into a fresh runtime atomically.

    ``source`` and ``fresh`` must expose the existing GameViewport SR seams.
    The fresh runtime must already have completed scene loading and snapshot
    lifetime setup; this function does not create or destroy host objects.
    """
    source_fp = _structure_fingerprint(source)
    fresh_fp = _structure_fingerprint(fresh)
    structure = compare_sr_runtime_structure_fingerprints(source_fp, fresh_fp)
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "fresh_instance": source is not fresh,
        "structure": structure,
        "dynamic_slice_restored": False,
        "dynamic_state_equal": False,
        "cross_lane_parity": False,
        "default_ready": False,
        "replay_admitted": False,
        "lossless": False,
    }
    if structure.get("equal") is not True:
        result["errors"] = ["sr_structure_mismatch"]
        return result

    source_envelope = source.capture_sr_runtime_restore_envelope()
    if not isinstance(source_envelope, Mapping):
        result["errors"] = ["source_restore_envelope_invalid"]
        return result
    snapshots = source_envelope.get("snapshots")
    scene_time = source_envelope.get("scene_time")
    if not isinstance(snapshots, list):
        result["errors"] = ["source_restore_snapshots_invalid"]
        return result
    try:
        fresh.restore_sr_runtime_snapshot_slice(
            copy.deepcopy(snapshots), scene_time=scene_time
        )
    except Exception as exc:
        result["errors"] = ["fresh_sr_restore_failed", type(exc).__name__]
        return result
    result["dynamic_slice_restored"] = True
    restored = fresh.capture_sr_runtime_restore_envelope()
    result["dynamic_state_equal"] = _canonical_dynamic_state(restored) == _canonical_dynamic_state(source_envelope)
    result["cross_lane_parity"] = bool(result["dynamic_state_equal"])
    result["errors"] = [] if result["dynamic_state_equal"] else ["dynamic_state_mismatch"]
    return result


def build_worldbridge_fresh_sr_restore_contract() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": "fresh_loaded_sr_runtime_structure_and_dynamic_slice",
        "structure_fingerprint_required": True,
        "script_type_parity_required": True,
        "topology_parity_required": True,
        "dynamic_slice_restore": True,
        "fresh_scene_construction": False,
        "cross_lane_parity": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
        "contract_valid": True,
    }


def _structure_fingerprint(viewport: Any) -> dict[str, Any]:
    return build_sr_runtime_structure_fingerprint(
        entities=getattr(viewport, "scene_runtime_entities"),
        scene_path=getattr(viewport, "_sr_runtime_scene_path", None),
        structural_edges=getattr(viewport, "_sr_structural_edges", ()),
        signal_edges=getattr(viewport, "_sr_signal_edges", ()),
        membrane_attach=getattr(viewport, "_sr_membrane_attach", {}),
        membrane_template=getattr(viewport, "_sr_membrane_template", {}),
    )


def _canonical_dynamic_state(value: Mapping[str, Any]) -> bytes:
    snapshots = value.get("snapshots")
    if not isinstance(snapshots, list):
        raise ValueError("restore envelope snapshots must be a list")
    payload = {"scene_time": value.get("scene_time"), "snapshots": snapshots}
    return json.dumps(
        payload, ensure_ascii=False, allow_nan=False,
        sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


__all__ = [
    "build_worldbridge_fresh_sr_restore_contract",
    "verify_fresh_sr_restore_parity",
]
