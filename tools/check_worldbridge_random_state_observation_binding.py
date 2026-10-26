# -*- coding: utf-8 -*-
"""Mechanical E222 pre/post RNG observation and sealed-artifact binding guard."""
from __future__ import annotations

import copy
import json
import random
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_random_state_observation_binding import (
    _binding_digest,
    build_worldbridge_random_state_observation_binding_contract,
    validate_worldbridge_random_state_observation_binding,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
VIEWPORT = RUNTIME / "core/VitaLoom/viewports/game_viewport.py"
BRIDGE = RUNTIME / "core/Lotucosm/runtime/world_bridge.py"


def _numpy_state_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return (
        left[0] == right[0]
        and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


def main() -> int:
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    contract = build_worldbridge_random_state_observation_binding_contract()
    python_after = random.getstate()
    numpy_after = np.random.get_state()

    if contract.get("contract_valid") is not True:
        raise SystemExit("E222 deterministic binding contract is invalid")
    if python_before != python_after or not _numpy_state_equal(numpy_before, numpy_after):
        raise SystemExit("E222 status construction observed or advanced a global RNG")

    binding = contract["binding"]
    if validate_worldbridge_random_state_observation_binding(binding) != {
        "valid": True,
        "errors": [],
    }:
        raise SystemExit("E222 example binding failed validation")
    if binding.get("artifact", {}).get("session", {}).get("lifecycle") != "sealed":
        raise SystemExit("E222 binding did not retain a sealed E220 artifact")
    if binding.get("before_capture_id") == binding.get("after_capture_id"):
        raise SystemExit("E222 boundary capture identities are not distinct")
    if binding.get("changed_authority_ids") != ["python_process_global_random"]:
        raise SystemExit("E222 deterministic changed classification diverged")
    if binding.get("unchanged_authority_ids") != ["numpy_legacy_global_randomstate"]:
        raise SystemExit("E222 deterministic unchanged classification diverged")

    for field in (
        "draw_counts_inferred",
        "lane_attribution_inferred",
        "cross_lane_consumption_order_captured",
        "supported_globals_prove_entropy_closure",
        "clocks_compared",
        "time_aligned",
        "causality_inferred",
        "thread_atomic",
        "cross_authority_atomic",
        "atomic_checkpoint",
        "replay_input",
        "checkpoint_state",
        "lossless",
        "replay_admitted",
        "default_ready",
    ):
        if binding.get(field) is not False:
            raise SystemExit(f"E222 binding overclaimed {field}")

    overclaim = copy.deepcopy(binding)
    overclaim["lane_attribution_inferred"] = True
    overclaim["binding_digest"] = _binding_digest(overclaim)
    validation = validate_worldbridge_random_state_observation_binding(overclaim)
    if validation.get("valid") is not False or "lane_attribution_inferred_mismatch" not in validation.get(
        "errors", []
    ):
        raise SystemExit("E222 lane attribution overclaim survived validation")

    viewport_source = VIEWPORT.read_text(encoding="utf-8")
    bridge_source = BRIDGE.read_text(encoding="utf-8")
    if "world_bridge_random_state_observation_binding" in viewport_source:
        raise SystemExit("E222 binding leaked into default GameViewport ownership")
    for token in ("sync_sr_entity_to_organism", "update()", "sync_organism_to_sr_display"):
        if token not in bridge_source:
            raise SystemExit(f"actual bridge call-path anchor disappeared: {token}")

    runtime_status = build_runtime_worldbridge_status()
    if runtime_status.get("pre_post_random_state_observation_binding_contract") != contract:
        raise SystemExit("runtime status does not nest deterministic E222 contract")
    if runtime_status.get("runtime_mode") != "dual":
        raise SystemExit("E222 changed the default dual runtime mode")
    if runtime_status.get("unified_pond_enabled") is not False:
        raise SystemExit("E222 enabled unified Pond by default")
    if runtime_status.get("default_ready") is not False:
        raise SystemExit("E222 overclaimed default readiness")

    print(
        json.dumps(
            {
                "status": "ok",
                "artifact_lifecycle": "sealed",
                "boundary_capture_ids_distinct": True,
                "changed_authority_ids": binding["changed_authority_ids"],
                "unchanged_authority_ids": binding["unchanged_authority_ids"],
                "draw_counts_inferred": False,
                "lane_attribution_inferred": False,
                "cross_lane_consumption_order_captured": False,
                "supported_globals_prove_entropy_closure": False,
                "atomic_checkpoint": False,
                "replay_admitted": False,
                "default_ready": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
