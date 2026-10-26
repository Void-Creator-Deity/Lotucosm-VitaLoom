from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:
    from tools._runtime_bootstrap import install_runtime_paths


ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e366_live_checkpoint_admission import (
    validate_worldbridge_e366_live_checkpoint_admission_contract,
)
from core.Lotucosm.runtime.world_bridge_e367_live_viewport_witness import (
    build_worldbridge_e367_live_viewport_witness_contract,
)
from core.Lotucosm.runtime.world_bridge_live_checkpoint_admission import (
    validate_worldbridge_live_checkpoint_admission_witness,
)


def _receipt() -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_worldbridge_e367_live_viewport_witness.py"],
        cwd=ROOT,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads([line for line in proc.stdout.splitlines() if line.strip()][-1])


def verify_tamper_matrix() -> dict[str, object]:
    receipt = _receipt()
    rejected: dict[str, bool] = {}

    identity_tamper = copy.deepcopy(receipt)
    identity_tamper["witness"]["checkpoint_identity"]["digest"] = "tampered"
    rejected["checkpoint_identity_binding"] = (
        identity_tamper["checkpoint_identity"]
        != identity_tamper["witness"]["checkpoint_identity"]
        or validate_worldbridge_live_checkpoint_admission_witness(
            identity_tamper["witness"]
        )["valid"] is False
    )

    projection_tamper = copy.deepcopy(receipt)
    projection_tamper["runtime_status_e367"]["evidence"]["fresh_restore_parity"] = False
    expected_projection = build_worldbridge_e367_live_viewport_witness_contract(
        projection_tamper["witness"], projection_tamper["cleanup"]
    )
    rejected["runtime_projection_binding"] = (
        projection_tamper["runtime_status_e367"] != expected_projection
    )

    cleanup_tamper = copy.deepcopy(receipt)
    cleanup_tamper["cleanup"]["viewport_deleted"] = False
    cleanup_projection = build_worldbridge_e367_live_viewport_witness_contract(
        cleanup_tamper["witness"], cleanup_tamper["cleanup"]
    )
    rejected["cleanup_receipt"] = (
        cleanup_projection["cleanup_complete"] is False
        and cleanup_projection["opt_in_live_adapter_admitted"] is False
    )

    overclaim = copy.deepcopy(receipt["aggregate"])
    overclaim["default_ready"] = True
    rejected["default_ready_overclaim"] = (
        validate_worldbridge_e366_live_checkpoint_admission_contract(overclaim)["valid"]
        is False
    )
    if not all(rejected.values()):
        raise AssertionError(f"tamper matrix did not fail closed: {rejected}")
    return {
        "status": "worldbridge_e370_receipt_tamper_matrix",
        "contract_valid": True,
        "negative_cases": rejected,
        "all_rejected": True,
        "live_adapter_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }


if __name__ == "__main__":
    result = verify_tamper_matrix()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] and result["all_rejected"] else 1)
