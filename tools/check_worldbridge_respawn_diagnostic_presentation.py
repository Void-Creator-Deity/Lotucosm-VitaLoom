# -*- coding: utf-8 -*-
"""Mechanical E230 receipt-only presentation guard."""
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
PRESENTATION = RUNTIME / "core/Lotucosm/runtime/world_bridge_respawn_diagnostic_presentation.py"
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import create_worldbridge_deterministic_randomness_context, register_worldbridge_deterministic_random_stream
from core.Lotucosm.runtime.world_bridge_named_stream_adapter import run_worldbridge_named_stream_sr_respawn_handoff
from core.Lotucosm.runtime.world_bridge_respawn_artifact_diagnostics import project_worldbridge_respawn_artifact_inspection
from core.Lotucosm.runtime.world_bridge_respawn_artifact_inspection import inspect_worldbridge_respawn_two_stream_artifact
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_consumer import consume_worldbridge_respawn_diagnostic_pair
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_presentation import _presentation_digest, build_worldbridge_respawn_diagnostic_presentation_contract, present_worldbridge_respawn_diagnostic_receipt, validate_worldbridge_respawn_diagnostic_presentation
from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import build_worldbridge_respawn_two_stream_artifact
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _numpy_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def _receipt() -> dict[str, object]:
    context = create_worldbridge_deterministic_randomness_context("e230-guard", "e230-seed")
    register_worldbridge_deterministic_random_stream(context, "sr.war.respawn.decision", "python_random")
    register_worldbridge_deterministic_random_stream(context, "sr.war.respawn.mind", "python_random")
    handoff = run_worldbridge_named_stream_sr_respawn_handoff(context, "sr.war.respawn.decision", "sr.war.respawn.mind", {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3}, 0.25, 1.0)
    artifact = build_worldbridge_respawn_two_stream_artifact(handoff, artifact_id="e230-guard-artifact")
    inspection = inspect_worldbridge_respawn_two_stream_artifact(artifact)
    projection = project_worldbridge_respawn_artifact_inspection(inspection)
    return consume_worldbridge_respawn_diagnostic_pair(inspection, projection)


def main() -> int:
    receipt = _receipt()
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    presentation = present_worldbridge_respawn_diagnostic_receipt(receipt)
    if random.getstate() == python_before and _numpy_equal(numpy_before, np.random.get_state()):
        pass
    else:
        raise SystemExit("E230 presentation touched a module-global RNG")
    validation = validate_worldbridge_respawn_diagnostic_presentation(presentation, receipt=receipt)
    if validation == {"valid": True, "errors": []}:
        pass
    else:
        raise SystemExit("E230 presentation did not preserve receipt parity")
    if presentation["ui_authority"] is not False or presentation["restore_performed"] is not False or presentation["mutation_executed"] is not False:
        raise SystemExit("E230 presentation became UI, executable, or restore authority")

    tampered = copy.deepcopy(presentation)
    tampered["gene_counts"]["parent"] += 1
    tampered["presentation_digest"] = _presentation_digest(tampered)
    tampered_validation = validate_worldbridge_respawn_diagnostic_presentation(tampered, receipt=receipt)
    if tampered_validation.get("valid") is False and "receipt_parity_gene_counts_mismatch" in tampered_validation.get("errors", []):
        pass
    else:
        raise SystemExit("E230 receipt parity mismatch survived a recomputed presentation digest")

    source = PRESENTATION.read_text(encoding="utf-8")
    forbidden = ("mind_dict_mutate", "get_stream(", "GameViewport", "QWidget", "QPainter", "world_bridge_respawn_two_stream_artifact", "world_bridge_respawn_artifact_inspection", "world_bridge_respawn_artifact_diagnostics")
    if any(token in source for token in forbidden):
        raise SystemExit("E230 presentation crossed into raw-source, runtime, mutation, or UI authority")
    tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and "world_bridge_respawn_diagnostic_presentation" in node.module:
            raise SystemExit("E230 presentation became a module-level GameViewport dependency")

    contract = build_worldbridge_respawn_diagnostic_presentation_contract()
    status = build_runtime_worldbridge_status()
    if status.get("opt_in_respawn_diagnostic_presentation_contract") == contract:
        pass
    else:
        raise SystemExit("E230 runtime status does not nest presentation contract")
    if status.get("runtime_mode") != "dual" or status.get("default_ready") is not False:
        raise SystemExit("E230 changed default WorldBridge mode/readiness")

    print(json.dumps({"status": "ok", "contract_valid": True, "receipt_parity_valid": True, "global_python_random_unchanged": True, "global_numpy_random_unchanged": True, "accepts_raw_artifact": False, "ui_authority": False, "restores_streams": False, "executes_mutation": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
