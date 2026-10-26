# -*- coding: utf-8 -*-
"""Mechanical E232 guard for the final in-memory diagnostic audit sink."""
from __future__ import annotations

import ast
import copy
import json
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
AUDIT = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_respawn_diagnostic_export_audit.py"
VIEWPORT = RUNTIME / "core" / "VitaLoom" / "viewports" / "game_viewport.py"
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
)
from core.Lotucosm.runtime.world_bridge_named_stream_adapter import run_worldbridge_named_stream_sr_respawn_handoff
from core.Lotucosm.runtime.world_bridge_respawn_artifact_diagnostics import project_worldbridge_respawn_artifact_inspection
from core.Lotucosm.runtime.world_bridge_respawn_artifact_inspection import inspect_worldbridge_respawn_two_stream_artifact
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_consumer import consume_worldbridge_respawn_diagnostic_pair
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_export import export_worldbridge_respawn_diagnostic_presentation
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_export_audit import (
    _audit_digest,
    audit_worldbridge_respawn_diagnostic_export,
    build_worldbridge_respawn_diagnostic_export_audit_contract,
    validate_worldbridge_respawn_diagnostic_export_audit,
)
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_presentation import present_worldbridge_respawn_diagnostic_receipt
from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import build_worldbridge_respawn_two_stream_artifact
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _numpy_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def _export_record() -> dict[str, object]:
    context = create_worldbridge_deterministic_randomness_context("e232-guard", "e232-seed")
    register_worldbridge_deterministic_random_stream(context, "sr.war.respawn.decision", "python_random")
    register_worldbridge_deterministic_random_stream(context, "sr.war.respawn.mind", "python_random")
    handoff = run_worldbridge_named_stream_sr_respawn_handoff(context, "sr.war.respawn.decision", "sr.war.respawn.mind", {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3}, 0.25, 1.0)
    artifact = build_worldbridge_respawn_two_stream_artifact(handoff, artifact_id="e232-guard-artifact")
    inspection = inspect_worldbridge_respawn_two_stream_artifact(artifact)
    projection = project_worldbridge_respawn_artifact_inspection(inspection)
    receipt = consume_worldbridge_respawn_diagnostic_pair(inspection, projection)
    presentation = present_worldbridge_respawn_diagnostic_receipt(receipt)
    return export_worldbridge_respawn_diagnostic_presentation(presentation)


def main() -> int:
    export_record = _export_record()
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    audit = audit_worldbridge_respawn_diagnostic_export(export_record)
    if random.getstate() != python_before or not _numpy_equal(numpy_before, np.random.get_state()):
        raise SystemExit("E232 audit touched a module-global RNG")
    if validate_worldbridge_respawn_diagnostic_export_audit(audit, export_record=export_record) != {"valid": True, "errors": []}:
        raise SystemExit("E232 audit did not preserve export parity")
    if any(audit[field] is not False for field in ("audit_persisted", "file_written", "network_transmitted", "ui_authority", "restore_performed", "mutation_executed")):
        raise SystemExit("E232 audit became persistence, I/O, UI, executable, or restore authority")

    tampered = copy.deepcopy(audit)
    tampered["gene_counts"]["parent"] += 1
    tampered["audit_digest"] = _audit_digest(tampered)
    tampered_validation = validate_worldbridge_respawn_diagnostic_export_audit(tampered, export_record=export_record)
    if tampered_validation.get("valid") is not False or "export_parity_gene_counts_mismatch" not in tampered_validation.get("errors", []):
        raise SystemExit("E232 export parity mismatch survived a recomputed audit digest")

    source = AUDIT.read_text(encoding="utf-8")
    forbidden = ("mind_dict_mutate", "get_stream(", "GameViewport", "QWidget", "QPainter", "world_bridge_respawn_two_stream_artifact", "world_bridge_respawn_artifact_inspection", "world_bridge_respawn_artifact_diagnostics", "world_bridge_respawn_diagnostic_consumer", "world_bridge_respawn_diagnostic_presentation", "open(", "Path(", "requests", "urllib", "socket")
    if any(token in source for token in forbidden):
        raise SystemExit("E232 audit crossed into raw-source, runtime, UI, or I/O authority")
    tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and "world_bridge_respawn_diagnostic_export_audit" in node.module:
            raise SystemExit("E232 audit became a module-level GameViewport dependency")

    contract = build_worldbridge_respawn_diagnostic_export_audit_contract()
    status = build_runtime_worldbridge_status()
    if status.get("opt_in_respawn_diagnostic_export_audit_contract") != contract:
        raise SystemExit("E232 runtime status does not nest audit contract")
    if status.get("runtime_mode") != "dual" or status.get("default_ready") is not False:
        raise SystemExit("E232 changed default WorldBridge mode/readiness")

    print(json.dumps({"status": "ok", "contract_valid": True, "export_parity_valid": True, "global_python_random_unchanged": True, "global_numpy_random_unchanged": True, "accepts_raw_export": False, "writes_files": False, "transmits_network": False, "ui_authority": False, "restores_streams": False, "executes_mutation": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())