# -*- coding: utf-8 -*-
"""Mechanical E224 opt-in named-stream SR mind hand-off guard."""
from __future__ import annotations

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
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
)
from core.Lotucosm.runtime.world_bridge_named_stream_adapter import (
    build_worldbridge_named_stream_adapter_contract,
    mutate_sr_mind_with_worldbridge_named_stream,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
VIEWPORT = RUNTIME / "core/VitaLoom/viewports/game_viewport.py"


def _numpy_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def main() -> int:
    context = create_worldbridge_deterministic_randomness_context("e224-guard", "e224-seed")
    register_worldbridge_deterministic_random_stream(
        context, "sr.war.respawn.mind", "python_random"
    )
    parent = {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3}
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    result = mutate_sr_mind_with_worldbridge_named_stream(
        context, "sr.war.respawn.mind", parent, 0.25
    )
    if random.getstate() != python_before or not _numpy_equal(numpy_before, np.random.get_state()):
        raise SystemExit("E224 adapter touched a module-global RNG")
    if result["stream_state_changed"] is not True:
        raise SystemExit("E224 adapter did not consume the named local stream")
    if result["default_tick_attached"] is not False or result["default_ready"] is not False:
        raise SystemExit("E224 adapter overclaimed default adoption")

    contract = build_worldbridge_named_stream_adapter_contract()
    if contract["supported_consumer"] != "sr_mind_gene.mind_dict_mutate":
        raise SystemExit("E224 consumer seam changed")
    source = VIEWPORT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and "world_bridge_named_stream_adapter" in node.module:
            raise SystemExit("E224 adapter became a module-level GameViewport dependency")
    if "create_worldbridge_deterministic_randomness_context" in source:
        raise SystemExit("E224 GameViewport creates a context")
    for token in ("set_worldbridge_opt_in_named_stream", "_apply_sr_respawn_mind_mutation"):
        if token not in source:
            raise SystemExit(f"E224 viewport seam missing: {token}")

    status = build_runtime_worldbridge_status()
    if status["runtime_mode"] != "dual" or status["unified_pond_enabled"] is not False:
        raise SystemExit("E224 changed default WorldBridge mode")
    if status["opt_in_named_stream_sr_mind_adapter_contract"]["default_ready"] is not False:
        raise SystemExit("E224 status overclaimed default readiness")

    print(
        json.dumps(
            {
                "status": "ok",
                "adapter_kind": result["adapter_kind"],
                "consumer": contract["supported_consumer"],
                "stream_name": result["stream_name"],
                "stream_state_changed": result["stream_state_changed"],
                "global_python_random_unchanged": True,
                "global_numpy_random_unchanged": True,
                "default_context_created": False,
                "default_tick_attached": False,
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
