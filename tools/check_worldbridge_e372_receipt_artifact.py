from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:
    from tools._runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e372_receipt_artifact import (
    build_worldbridge_e372_receipt_artifact,
    decode_worldbridge_e372_receipt_artifact,
    encode_worldbridge_e372_receipt_artifact,
    validate_worldbridge_e372_receipt_artifact,
)


def _receipt() -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_worldbridge_e367_live_viewport_witness.py"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    return json.loads([line for line in proc.stdout.splitlines() if line.strip()][-1])


def verify_e372_artifact() -> dict[str, object]:
    receipt = _receipt()
    artifact = build_worldbridge_e372_receipt_artifact(
        receipt, artifact_id="e372-receipt", issued_at=1_000, ttl_seconds=100
    )
    encoded = encode_worldbridge_e372_receipt_artifact(artifact)
    decoded = decode_worldbridge_e372_receipt_artifact(encoded, now_epoch=1_050)
    rejected: dict[str, bool] = {}
    old = copy.deepcopy(artifact); old["schema_version"] = 0
    rejected["old_schema"] = not validate_worldbridge_e372_receipt_artifact(old)["valid"]
    missing = copy.deepcopy(artifact); missing.pop("retention")
    rejected["missing_retention"] = not validate_worldbridge_e372_receipt_artifact(missing)["valid"]
    expired = validate_worldbridge_e372_receipt_artifact(artifact, now_epoch=1_100)
    rejected["expired"] = not expired["valid"] and "artifact_expired" in expired["errors"]
    unknown = copy.deepcopy(artifact); unknown["receipt_schema_version"] = 99
    rejected["unknown_receipt_schema"] = not validate_worldbridge_e372_receipt_artifact(unknown)["valid"]
    if decoded != artifact or not all(rejected.values()):
        raise AssertionError(f"E372 artifact audit failed: {rejected}")
    return {
        "status": "worldbridge_e372_receipt_artifact",
        "contract_valid": True,
        "canonical_roundtrip": True,
        "negative_cases": rejected,
        "all_rejected": True,
        "migration_admitted": False,
        "live_adapter_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }


if __name__ == "__main__":
    result = verify_e372_artifact()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] and result["all_rejected"] else 1)
