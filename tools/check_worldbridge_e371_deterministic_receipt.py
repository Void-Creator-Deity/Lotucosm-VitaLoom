from __future__ import annotations

import json
import os
import random
import subprocess
import sys
from pathlib import Path

try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:
    from tools._runtime_bootstrap import install_runtime_paths


ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

import numpy as np

from tools.check_worldbridge_e367_live_viewport_witness import build_e367_witness


def _child_receipt() -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_worldbridge_e367_live_viewport_witness.py"],
        cwd=ROOT,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads([line for line in proc.stdout.splitlines() if line.strip()][-1])


def _numpy_state_equal(left: tuple, right: tuple) -> bool:
    return (
        left[0] == right[0]
        and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


def verify_deterministic_receipt() -> dict[str, object]:
    first = _child_receipt()
    second = _child_receipt()
    cross_process_stable = (
        first["checkpoint_identity"]["digest"]
        == second["checkpoint_identity"]["digest"]
    )
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    local_first = build_e367_witness()
    python_after_first = random.getstate()
    numpy_after_first = np.random.get_state()
    local_second = build_e367_witness()
    python_after_second = random.getstate()
    numpy_after_second = np.random.get_state()
    local_stable = (
        local_first["checkpoint_identity"]["digest"]
        == local_second["checkpoint_identity"]["digest"]
        == first["checkpoint_identity"]["digest"]
    )
    global_state_restored = (
        python_before == python_after_first == python_after_second
        and _numpy_state_equal(numpy_before, numpy_after_first)
        and _numpy_state_equal(numpy_before, numpy_after_second)
    )
    result = {
        "status": "worldbridge_e371_deterministic_receipt",
        "contract_valid": cross_process_stable and local_stable and global_state_restored,
        "cross_process_stable": cross_process_stable,
        "local_receipt_stable": local_stable,
        "global_rng_state_restored": global_state_restored,
        "live_adapter_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    return result


if __name__ == "__main__":
    result = verify_deterministic_receipt()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] else 1)
