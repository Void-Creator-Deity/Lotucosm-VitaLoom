# -*- coding: utf-8 -*-
"""Mechanical E226 canonical respawn two-stream artifact guard."""
from __future__ import annotations

import ast
import copy
import json
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
VIEWPORT = RUNTIME / "core/VitaLoom/viewports/game_viewport.py"
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
)
from core.Lotucosm.runtime.world_bridge_named_stream_adapter import (
    run_worldbridge_named_stream_sr_respawn_handoff,
)
from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import (
    _artifact_digest,
    build_worldbridge_respawn_two_stream_artifact,
    build_worldbridge_respawn_two_stream_artifact_contract,
    decode_worldbridge_respawn_two_stream_artifact,
    encode_worldbridge_respawn_two_stream_artifact,
    validate_worldbridge_respawn_two_stream_artifact,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _numpy_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def _handoff(probability: float) -> dict[str, object]:
    context = create_worldbridge_deterministic_randomness_context("e226-guard", "e226-seed")
    register_worldbridge_deterministic_random_stream(
        context, "sr.war.respawn.decision", "python_random"
    )
    register_worldbridge_deterministic_random_stream(
        context, "sr.war.respawn.mind", "python_random"
    )
    return run_worldbridge_named_stream_sr_respawn_handoff(
        context,
        "sr.war.respawn.decision",
        "sr.war.respawn.mind",
        {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3},
        0.25,
        probability,
    )


def main() -> int:
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    admitted = build_worldbridge_respawn_two_stream_artifact(
        _handoff(1.0), artifact_id="e226-guard-admitted"
    )
    rejected = build_worldbridge_respawn_two_stream_artifact(
        _handoff(0.0), artifact_id="e226-guard-rejected"
    )
    if random.getstate() != python_before or not _numpy_equal(numpy_before, np.random.get_state()):
        raise SystemExit("E226 artifact construction touched a module-global RNG")
    if validate_worldbridge_respawn_two_stream_artifact(admitted).get("valid") is not True:
        raise SystemExit("E226 admitted artifact is invalid")
    if admitted["ordered_steps"] != ["decision", "mutation"] or admitted["mutation_stream_consumed"] is not True:
        raise SystemExit("E226 admitted artifact lost ordered two-stream evidence")
    if rejected["ordered_steps"] != ["decision"] or rejected["mutation_stream_consumed"] is not False:
        raise SystemExit("E226 rejected artifact consumed mutation evidence")
    encoded = encode_worldbridge_respawn_two_stream_artifact(admitted)
    if decode_worldbridge_respawn_two_stream_artifact(encoded) != admitted:
        raise SystemExit("E226 canonical artifact round trip diverged")

    tampered = copy.deepcopy(admitted)
    tampered["replay_input"] = True
    tampered["artifact_digest"] = _artifact_digest(tampered)
    validation = validate_worldbridge_respawn_two_stream_artifact(tampered)
    if validation.get("valid") is not False or "replay_input_mismatch" not in validation.get("errors", []):
        raise SystemExit("E226 replay overclaim survived a recomputed digest")

    source = VIEWPORT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and "world_bridge_respawn_two_stream_artifact" in node.module:
            raise SystemExit("E226 artifact became a module-level GameViewport dependency")
    if "build_worldbridge_respawn_two_stream_artifact" in source:
        raise SystemExit("E226 artifact construction became default viewport behavior")

    contract = build_worldbridge_respawn_two_stream_artifact_contract()
    status = build_runtime_worldbridge_status()
    if status.get("opt_in_respawn_two_stream_artifact_contract") != contract:
        raise SystemExit("E226 runtime status does not nest artifact contract")
    if status.get("runtime_mode") != "dual" or status.get("default_ready") is not False:
        raise SystemExit("E226 changed default WorldBridge mode/readiness")

    print(
        json.dumps(
            {
                "status": "ok",
                "contract_valid": True,
                "round_trip_equal": True,
                "admitted_ordered_steps": admitted["ordered_steps"],
                "rejected_ordered_steps": rejected["ordered_steps"],
                "global_python_random_unchanged": True,
                "global_numpy_random_unchanged": True,
                "replay_input": False,
                "checkpoint_state": False,
                "atomic_handoff": False,
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



