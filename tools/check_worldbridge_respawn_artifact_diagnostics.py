# -*- coding: utf-8 -*-
"""Mechanical E228 bounded respawn diagnostic-projection guard."""
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
DIAGNOSTICS = RUNTIME / "core/Lotucosm/runtime/world_bridge_respawn_artifact_diagnostics.py"
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
from core.Lotucosm.runtime.world_bridge_respawn_artifact_diagnostics import (
    _projection_digest,
    build_worldbridge_respawn_artifact_diagnostic_projection_contract,
    project_worldbridge_respawn_artifact_inspection,
    validate_worldbridge_respawn_artifact_diagnostic_projection,
)
from core.Lotucosm.runtime.world_bridge_respawn_artifact_inspection import (
    inspect_worldbridge_respawn_two_stream_artifact,
)
from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import (
    build_worldbridge_respawn_two_stream_artifact,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _numpy_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def _inspection() -> dict[str, object]:
    context = create_worldbridge_deterministic_randomness_context("e228-guard", "e228-seed")
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
    artifact = build_worldbridge_respawn_two_stream_artifact(handoff, artifact_id="e228-guard-artifact")
    return inspect_worldbridge_respawn_two_stream_artifact(artifact)


def main() -> int:
    summary = _inspection()
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    projection = project_worldbridge_respawn_artifact_inspection(summary)
    if random.getstate() != python_before or not _numpy_equal(numpy_before, np.random.get_state()):
        raise SystemExit("E228 diagnostic projection touched a module-global RNG")
    parity = validate_worldbridge_respawn_artifact_diagnostic_projection(projection, inspection=summary)
    if parity != {"valid": True, "errors": []}:
        raise SystemExit("E228 projection did not preserve validated inspection parity")
    if projection["restore_performed"] is not False or projection["mutation_executed"] is not False:
        raise SystemExit("E228 projection became an executable or restore boundary")
    if projection["outcome"] != "admitted_mutation" or projection["ordered_steps"] != ["decision", "mutation"]:
        raise SystemExit("E228 projection lost bounded outcome evidence")

    tampered = copy.deepcopy(projection)
    tampered["gene_counts"]["parent"] += 1
    tampered["projection_digest"] = _projection_digest(tampered)
    tampered_validation = validate_worldbridge_respawn_artifact_diagnostic_projection(tampered, inspection=summary)
    if tampered_validation.get("valid") is not False or "parity_gene_counts_mismatch" not in tampered_validation.get("errors", []):
        raise SystemExit("E228 parity mismatch survived a recomputed projection digest")

    source = DIAGNOSTICS.read_text(encoding="utf-8")
    forbidden = ("mind_dict_mutate", "get_stream(", "GameViewport", "world_bridge_respawn_two_stream_artifact")
    if any(token in source for token in forbidden):
        raise SystemExit("E228 diagnostics crossed into raw-artifact/runtime/mutation authority")
    tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and "world_bridge_respawn_artifact_diagnostics" in node.module:
            raise SystemExit("E228 diagnostics became a module-level GameViewport dependency")

    contract = build_worldbridge_respawn_artifact_diagnostic_projection_contract()
    status = build_runtime_worldbridge_status()
    if status.get("opt_in_respawn_artifact_diagnostic_projection_contract") != contract:
        raise SystemExit("E228 runtime status does not nest diagnostic projection contract")
    if status.get("runtime_mode") != "dual" or status.get("default_ready") is not False:
        raise SystemExit("E228 changed default WorldBridge mode/readiness")

    print(json.dumps({
        "status": "ok",
        "contract_valid": True,
        "parity_valid": True,
        "global_python_random_unchanged": True,
        "global_numpy_random_unchanged": True,
        "accepts_raw_artifact": False,
        "restores_streams": False,
        "executes_mutation": False,
        "replay_admitted": False,
        "default_ready": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
