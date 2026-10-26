# -*- coding: utf-8 -*-
"""Mechanical E221 cross-lane randomness authority and capture guard."""
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

from core.Lotucosm.runtime.world_bridge_randomness_authority import (
    AUTHORITY_IDS,
    CAPTURED_AUTHORITY_IDS,
    UNCAPTURED_AUTHORITY_IDS,
    _capture_digest,
    build_worldbridge_randomness_authority_contract,
    capture_worldbridge_global_random_states,
    validate_worldbridge_global_random_state_capture,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
VIEWPORT = RUNTIME / "core/VitaLoom/viewports/game_viewport.py"
BRIDGE = RUNTIME / "core/Lotucosm/runtime/world_bridge.py"
POND = RUNTIME / "core/Lotucosm/pond.py"
FLOATING = RUNTIME / "builtin/systems/floating_system.py"
TEMPLATE = RUNTIME / "builtin/templates/official_cell_behavior.py"


def _numpy_state_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return (
        left[0] == right[0]
        and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


def main() -> int:
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    contract = build_worldbridge_randomness_authority_contract()
    capture = capture_worldbridge_global_random_states(capture_id="e221-mechanical-guard")
    python_after = random.getstate()
    numpy_after = np.random.get_state()

    if contract.get("contract_valid") is not True:
        raise SystemExit("E221 static randomness authority contract is invalid")
    if contract.get("authority_ids") != list(AUTHORITY_IDS) or contract.get("authority_count") != 5:
        raise SystemExit("E221 authority inventory is incomplete or reordered")
    if set(contract.get("captured_authority_ids", [])) != set(CAPTURED_AUTHORITY_IDS):
        raise SystemExit("E221 supported global state capture set changed")
    if set(contract.get("uncaptured_authority_ids", [])) != set(UNCAPTURED_AUTHORITY_IDS):
        raise SystemExit("E221 uncaptured authority blocker set changed")
    if python_before != python_after or not _numpy_state_equal(numpy_before, numpy_after):
        raise SystemExit("E221 status/capture advanced a process-global RNG")
    if validate_worldbridge_global_random_state_capture(capture) != {
        "valid": True,
        "errors": [],
    }:
        raise SystemExit("E221 explicit state observation failed validation")

    for field in (
        "thread_atomic",
        "cross_authority_atomic",
        "global_states_advanced_by_capture",
        "global_states_reseeded",
        "restore_performed",
        "restore_api_exposed",
        "initial_seed_sufficient",
        "all_authorities_captured",
        "cross_lane_consumption_order_captured",
        "dynamic_entropy_boundary_closed",
        "native_entropy_boundary_closed",
        "replay_input",
        "checkpoint_state",
        "replay_admitted",
        "default_ready",
    ):
        if capture.get(field) is not False:
            raise SystemExit(f"E221 capture overclaimed {field}")

    overclaim = copy.deepcopy(capture)
    overclaim["replay_admitted"] = True
    overclaim["capture_digest"] = _capture_digest(overclaim)
    validation = validate_worldbridge_global_random_state_capture(overclaim)
    if validation.get("valid") is not False or "replay_admitted_mismatch" not in validation.get(
        "errors", []
    ):
        raise SystemExit("E221 replay overclaim survived validation")

    viewport_source = VIEWPORT.read_text(encoding="utf-8")
    bridge_source = BRIDGE.read_text(encoding="utf-8")
    pond_source = POND.read_text(encoding="utf-8")
    floating_source = FLOATING.read_text(encoding="utf-8")
    template_source = TEMPLATE.read_text(encoding="utf-8")
    required_source_tokens = (
        (viewport_source, "_run_unified_pond_bridge_tick"),
        (viewport_source, "_sr_runtime_rng"),
        (bridge_source, "sync_sr_entity_to_organism"),
        (bridge_source, "update()"),
        (bridge_source, "sync_organism_to_sr_display"),
        (pond_source, "self.generate_resources()"),
        (pond_source, "EvolutionRunner.apply_generation"),
        (floating_source, "self._normal(2)"),
        (floating_source, "self.randomness_rng"),
        (template_source, "self.random_uniform(-4.0, 4.0)"),
    )
    if any(token not in source for source, token in required_source_tokens):
        raise SystemExit("E221 source anchor disappeared from the actual bridge/randomness call graph")
    if "random.Random()" in viewport_source or "hash((lineage_id, death_count, now))" in viewport_source:
        raise SystemExit("E235 eliminated SR-local entropy/hash source reappeared")

    runtime_status = build_runtime_worldbridge_status()
    if runtime_status.get("cross_lane_randomness_authority_contract") != contract:
        raise SystemExit("runtime status does not nest deterministic E221 contract")
    if runtime_status.get("runtime_mode") != "dual":
        raise SystemExit("E221 changed the default dual runtime mode")
    if runtime_status.get("unified_pond_enabled") is not False:
        raise SystemExit("E221 enabled unified Pond by default")
    if runtime_status.get("default_ready") is not False:
        raise SystemExit("E221 overclaimed default readiness")

    print(
        json.dumps(
            {
                "status": "ok",
                "authority_count": len(AUTHORITY_IDS),
                "captured_authority_count": len(CAPTURED_AUTHORITY_IDS),
                "uncaptured_authority_count": len(UNCAPTURED_AUTHORITY_IDS),
                "python_global_state_unchanged": True,
                "numpy_global_state_unchanged": True,
                "thread_atomic": False,
                "cross_authority_atomic": False,
                "initial_seed_sufficient": False,
                "all_authorities_captured": False,
                "cross_lane_consumption_order_captured": False,
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
