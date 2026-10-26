# -*- coding: utf-8 -*-
"""Mechanical E229 paired diagnostic-consumer receipt guard."""
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
CONSUMER = RUNTIME / "core/Lotucosm/runtime/world_bridge_respawn_diagnostic_consumer.py"
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import create_worldbridge_deterministic_randomness_context, register_worldbridge_deterministic_random_stream
from core.Lotucosm.runtime.world_bridge_named_stream_adapter import run_worldbridge_named_stream_sr_respawn_handoff
from core.Lotucosm.runtime.world_bridge_respawn_artifact_diagnostics import _projection_digest, project_worldbridge_respawn_artifact_inspection
from core.Lotucosm.runtime.world_bridge_respawn_artifact_inspection import inspect_worldbridge_respawn_two_stream_artifact
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_consumer import _receipt_digest, build_worldbridge_respawn_diagnostic_consumer_contract, consume_worldbridge_respawn_diagnostic_pair, validate_worldbridge_respawn_diagnostic_consumer_receipt
from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import build_worldbridge_respawn_two_stream_artifact
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _numpy_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def _pair() -> tuple[dict[str, object], dict[str, object]]:
    context = create_worldbridge_deterministic_randomness_context("e229-guard", "e229-seed")
    register_worldbridge_deterministic_random_stream(context, "sr.war.respawn.decision", "python_random")
    register_worldbridge_deterministic_random_stream(context, "sr.war.respawn.mind", "python_random")
    handoff = run_worldbridge_named_stream_sr_respawn_handoff(context, "sr.war.respawn.decision", "sr.war.respawn.mind", {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3}, 0.25, 1.0)
    artifact = build_worldbridge_respawn_two_stream_artifact(handoff, artifact_id="e229-guard-artifact")
    inspection = inspect_worldbridge_respawn_two_stream_artifact(artifact)
    return inspection, project_worldbridge_respawn_artifact_inspection(inspection)


def main() -> int:
    inspection, projection = _pair()
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    receipt = consume_worldbridge_respawn_diagnostic_pair(inspection, projection)
    if random.getstate() == python_before and _numpy_equal(numpy_before, np.random.get_state()):
        pass
    else:
        raise SystemExit("E229 diagnostic consumer touched a module-global RNG")
    validation = validate_worldbridge_respawn_diagnostic_consumer_receipt(receipt, inspection=inspection, projection=projection)
    if validation == {"valid": True, "errors": []}:
        pass
    else:
        raise SystemExit("E229 receipt did not preserve validated source/projection parity")
    if receipt["restore_performed"] is not False or receipt["mutation_executed"] is not False:
        raise SystemExit("E229 consumer became an executable or restore boundary")

    tampered_projection = copy.deepcopy(projection)
    tampered_projection["gene_counts"]["parent"] += 1
    tampered_projection["projection_digest"] = _projection_digest(tampered_projection)
    try:
        consume_worldbridge_respawn_diagnostic_pair(inspection, tampered_projection)
    except ValueError:
        pass
    else:
        raise SystemExit("E229 consumer admitted a recomputed but mismatched projection")

    tampered_receipt = copy.deepcopy(receipt)
    tampered_receipt["gene_counts"]["parent"] += 1
    tampered_receipt["receipt_digest"] = _receipt_digest(tampered_receipt)
    tampered_validation = validate_worldbridge_respawn_diagnostic_consumer_receipt(tampered_receipt, inspection=inspection, projection=projection)
    if tampered_validation.get("valid") is False and "pair_parity_gene_counts_mismatch" in tampered_validation.get("errors", []):
        pass
    else:
        raise SystemExit("E229 paired receipt mismatch survived a recomputed receipt digest")

    source = CONSUMER.read_text(encoding="utf-8")
    forbidden = ("mind_dict_mutate", "get_stream(", "GameViewport", "world_bridge_respawn_two_stream_artifact")
    if any(token in source for token in forbidden):
        raise SystemExit("E229 consumer crossed into raw-artifact/runtime/mutation authority")
    tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and "world_bridge_respawn_diagnostic_consumer" in node.module:
            raise SystemExit("E229 consumer became a module-level GameViewport dependency")

    contract = build_worldbridge_respawn_diagnostic_consumer_contract()
    status = build_runtime_worldbridge_status()
    if status.get("opt_in_respawn_diagnostic_consumer_contract") == contract:
        pass
    else:
        raise SystemExit("E229 runtime status does not nest diagnostic consumer contract")
    if status.get("runtime_mode") != "dual" or status.get("default_ready") is not False:
        raise SystemExit("E229 changed default WorldBridge mode/readiness")

    print(json.dumps({"status": "ok", "contract_valid": True, "pair_parity_valid": True, "global_python_random_unchanged": True, "global_numpy_random_unchanged": True, "accepts_raw_artifact": False, "restores_streams": False, "executes_mutation": False, "replay_admitted": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
