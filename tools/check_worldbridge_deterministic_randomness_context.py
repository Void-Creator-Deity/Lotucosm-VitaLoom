# -*- coding: utf-8 -*-
"""Mechanical E223 opt-in deterministic named-stream context guard."""
from __future__ import annotations

import copy
import ast
import json
import random
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    _snapshot_digest,
    build_worldbridge_deterministic_randomness_context_contract,
    validate_worldbridge_deterministic_randomness_snapshot,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
MODULE = RUNTIME / "core/Lotucosm/runtime/world_bridge_deterministic_randomness_context.py"
VIEWPORT = RUNTIME / "core/VitaLoom/viewports/game_viewport.py"


def _numpy_state_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return (
        left[0] == right[0]
        and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


def main() -> int:
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    contract = build_worldbridge_deterministic_randomness_context_contract()
    python_after = random.getstate()
    numpy_after = np.random.get_state()

    if contract.get("contract_valid") is not True:
        raise SystemExit("E223 deterministic context contract is invalid")
    if python_before != python_after or not _numpy_state_equal(numpy_before, numpy_after):
        raise SystemExit("E223 context/status touched a module-global RNG")
    snapshot = contract.get("snapshot")
    if validate_worldbridge_deterministic_randomness_snapshot(snapshot) != {
        "valid": True,
        "errors": [],
    }:
        raise SystemExit("E223 snapshot failed validation")
    if snapshot.get("stream_count") != 2:
        raise SystemExit("E223 example did not retain both named stream families")
    families = [row.get("family") for row in snapshot.get("streams", [])]
    if families != ["python_random", "numpy_pcg64_generator"]:
        raise SystemExit("E223 named stream family order changed")

    for field in (
        "global_python_random_touched",
        "global_numpy_random_touched",
        "restore_performed",
        "replay_input",
        "checkpoint_state",
        "replay_admitted",
        "default_ready",
    ):
        if snapshot.get(field) is not False:
            raise SystemExit(f"E223 snapshot overclaimed {field}")

    overclaim = copy.deepcopy(snapshot)
    overclaim["default_ready"] = True
    overclaim["snapshot_digest"] = _snapshot_digest(overclaim)
    validation = validate_worldbridge_deterministic_randomness_snapshot(overclaim)
    if validation.get("valid") is not False or "default_ready_mismatch" not in validation.get(
        "errors", []
    ):
        raise SystemExit("E223 default-readiness overclaim survived validation")

    source_tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    forbidden_calls: list[str] = []
    for node in ast.walk(source_tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "hash":
            forbidden_calls.append("hash")
        if not isinstance(node.func, ast.Attribute) or node.func.attr not in {
            "seed",
            "setstate",
            "set_state",
        }:
            continue
        owner = node.func.value
        if not isinstance(owner, ast.Name) or owner.id not in {"stream", "python_stream"}:
            forbidden_calls.append(node.func.attr)
    if forbidden_calls:
        raise SystemExit("E223 module contains forbidden hash/reseed/restore call syntax")
    viewport_tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    viewport_source = VIEWPORT.read_text(encoding="utf-8")
    if "set_worldbridge_opt_in_deterministic_randomness_context" not in viewport_source:
        raise SystemExit("E223 opt-in GameViewport binding API is missing")
    if "_worldbridge_opt_in_deterministic_randomness_context = context" in viewport_source:
        constructor = next(
            (
                node
                for node in ast.walk(viewport_tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "__init__"
            ),
            None,
        )
        constructor_source = ast.unparse(constructor) if constructor is not None else ""
        if "_worldbridge_opt_in_deterministic_randomness_context" in constructor_source:
            raise SystemExit("E223 default GameViewport context must remain unbound")
    opt_in_methods = [
        node
        for node in ast.walk(viewport_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "set_worldbridge_opt_in_deterministic_randomness_context"
    ]
    if len(opt_in_methods) != 1:
        raise SystemExit("E223 opt-in GameViewport binding must have one explicit method")
    if any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "create_worldbridge_deterministic_randomness_context"
        for node in ast.walk(opt_in_methods[0])
    ):
        raise SystemExit("E223 GameViewport must not create the caller-owned context")

    runtime_status = build_runtime_worldbridge_status()
    if runtime_status.get("opt_in_deterministic_randomness_context_contract") != contract:
        raise SystemExit("runtime status does not nest deterministic E223 contract")
    if runtime_status.get("runtime_mode") != "dual":
        raise SystemExit("E223 changed the default dual runtime mode")
    if runtime_status.get("unified_pond_enabled") is not False:
        raise SystemExit("E223 enabled unified Pond by default")
    if runtime_status.get("default_ready") is not False:
        raise SystemExit("E223 overclaimed default readiness")

    print(
        json.dumps(
            {
                "status": "ok",
                "stream_count": snapshot["stream_count"],
                "stream_families": families,
                "global_python_random_unchanged": True,
                "global_numpy_random_unchanged": True,
                "uses_python_hash": False,
                "uses_wall_time": False,
                "uses_os_entropy": False,
                "restore_api_exposed": False,
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
