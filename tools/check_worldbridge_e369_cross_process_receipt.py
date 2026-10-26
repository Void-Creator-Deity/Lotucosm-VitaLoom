from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:  # Imported as tools.* by the focused test suite.
    from tools._runtime_bootstrap import install_runtime_paths


ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e366_live_checkpoint_admission import (
    validate_worldbridge_e366_live_checkpoint_admission_contract,
)
from core.Lotucosm.runtime.world_bridge_e367_live_viewport_witness import (
    build_worldbridge_e367_live_viewport_witness_contract,
    validate_worldbridge_e367_live_viewport_witness_contract,
)


def _parse_receipt(stdout: str) -> dict[str, object]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise AssertionError("e367 subprocess emitted no receipt")
    try:
        receipt = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        raise AssertionError("e367 receipt is not the final JSON line") from exc
    if not isinstance(receipt, dict):
        raise AssertionError("e367 receipt must be an object")
    return receipt


def verify_cross_process_receipt() -> dict[str, object]:
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_worldbridge_e367_live_viewport_witness.py"],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    receipt = _parse_receipt(proc.stdout)
    witness = receipt.get("witness")
    cleanup = receipt.get("cleanup")
    e366 = receipt.get("aggregate")
    if receipt.get("checkpoint_identity") != witness.get("checkpoint_identity"):
        raise AssertionError("checkpoint identity binding drifted")
    if validate_worldbridge_e366_live_checkpoint_admission_contract(e366)["valid"] is not True:
        raise AssertionError("cross-process E366 aggregate is invalid")
    if validate_worldbridge_e367_live_viewport_witness_contract(
        receipt.get("runtime_witness")
    )["valid"] is not True:
        raise AssertionError("cross-process E367 projection is invalid")
    expected = build_worldbridge_e367_live_viewport_witness_contract(witness, cleanup)
    if receipt.get("runtime_witness") != expected:
        raise AssertionError("cross-process E367 projection drifted")
    if receipt.get("runtime_status_e367") != expected:
        raise AssertionError("runtime status projection drifted")
    if receipt.get("failure_report") != {
        "phase": "ps",
        "compensation_complete": True,
        "target_preserved": True,
    }:
        raise AssertionError("rollback receipt drifted")
    if expected["opt_in_live_adapter_admitted"] is not True:
        raise AssertionError("complete witness was not admitted opt-in")
    for field in ("live_adapter_admitted", "replay_admitted", "default_ready", "lossless"):
        if expected[field] is not False:
            raise AssertionError(f"{field} overclaimed")
    return {
        "status": "worldbridge_e369_cross_process_receipt",
        "contract_valid": True,
        "child_returncode": proc.returncode,
        "receipt_schema_valid": True,
        "projection_recomputed": True,
        "rollback_receipt_valid": True,
        "opt_in_live_adapter_admitted": True,
        "live_adapter_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }


if __name__ == "__main__":
    result = verify_cross_process_receipt()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] else 1)
