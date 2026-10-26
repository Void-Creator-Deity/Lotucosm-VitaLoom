# -*- coding: utf-8 -*-
"""Mechanical E227 read-only respawn artifact consumer guard."""
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
INSPECTION = RUNTIME / "core/Lotucosm/runtime/world_bridge_respawn_artifact_inspection.py"
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
from core.Lotucosm.runtime.world_bridge_respawn_artifact_inspection import (
    _inspection_digest,
    build_worldbridge_respawn_artifact_inspection_contract,
    inspect_worldbridge_respawn_two_stream_artifact,
    validate_worldbridge_respawn_artifact_inspection,
)
from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import (
    build_worldbridge_respawn_two_stream_artifact,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _numpy_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def _artifact() -> dict[str, object]:
    context = create_worldbridge_deterministic_randomness_context("e227-guard", "e227-seed")
    register_worldbridge_deterministic_random_stream(context, "sr.war.respawn.decision", "python_random")
    register_worldbridge_deterministic_random_stream(context, "sr.war.respawn.mind", "python_random")
    handoff = run_worldbridge_named_stream_sr_respawn_handoff(
        context,
        "sr.war.respawn.decision",
        "sr.war.respawn.mind",
        {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3},
        0.25,
        1.0,
    )
    return build_worldbridge_respawn_two_stream_artifact(handoff, artifact_id="e227-guard-artifact")


def main() -> int:
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    summary = inspect_worldbridge_respawn_two_stream_artifact(_artifact())
    if random.getstate() != python_before or not _numpy_equal(numpy_before, np.random.get_state()):
        raise SystemExit("E227 inspection touched a module-global RNG")
    if summary["restore_performed"] is not False or summary["mutation_executed"] is not False:
        raise SystemExit("E227 inspection became an executable or restore boundary")
    if summary["outcome"] != "admitted_mutation" or summary["ordered_steps"] != ["decision", "mutation"]:
        raise SystemExit("E227 inspection lost bounded outcome evidence")

    tampered = copy.deepcopy(summary)
    tampered["checkpoint_state"] = True
    tampered["inspection_digest"] = _inspection_digest(tampered)
    validation = validate_worldbridge_respawn_artifact_inspection(tampered)
    if validation.get("valid") is not False or "checkpoint_state_mismatch" not in validation.get("errors", []):
        raise SystemExit("E227 semantic overclaim survived a recomputed summary digest")

    inspection_source = INSPECTION.read_text(encoding="utf-8")
    if "mind_dict_mutate" in inspection_source or "get_stream(" in inspection_source or "GameViewport" in inspection_source:
        raise SystemExit("E227 inspection crossed into runtime/mutation authority")
    tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and "world_bridge_respawn_artifact_inspection" in node.module:
            raise SystemExit("E227 inspection became a module-level GameViewport dependency")

    contract = build_worldbridge_respawn_artifact_inspection_contract()
    status = build_runtime_worldbridge_status()
    if status.get("opt_in_respawn_artifact_inspection_contract") != contract:
        raise SystemExit("E227 runtime status does not nest inspection contract")
    if status.get("runtime_mode") != "dual" or status.get("default_ready") is not False:
        raise SystemExit("E227 changed default WorldBridge mode/readiness")

    print(json.dumps({
        "status": "ok",
        "contract_valid": True,
        "outcome": summary["outcome"],
        "global_python_random_unchanged": True,
        "global_numpy_random_unchanged": True,
        "restores_streams": False,
        "executes_mutation": False,
        "replay_admitted": False,
        "default_ready": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
