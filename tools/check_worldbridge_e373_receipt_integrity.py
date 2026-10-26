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
    MAX_ARTIFACT_BYTES,
    build_worldbridge_e372_receipt_artifact,
    encode_worldbridge_e372_receipt_artifact,
)
from core.Lotucosm.runtime.world_bridge_e373_receipt_integrity import (
    build_worldbridge_e373_receipt_integrity_artifact,
    consume_worldbridge_e373_receipt_artifact,
    decode_worldbridge_e373_receipt_integrity_artifact,
    encode_worldbridge_e373_receipt_integrity_artifact,
    validate_worldbridge_e373_receipt_integrity_artifact,
)


def _receipt() -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_worldbridge_e367_live_viewport_witness.py"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    return json.loads([line for line in proc.stdout.splitlines() if line.strip()][-1])


def verify_e373_integrity() -> dict[str, object]:
    receipt = _receipt()
    artifact = build_worldbridge_e372_receipt_artifact(
        receipt, artifact_id="e373-receipt", issued_at=1_000, ttl_seconds=100
    )
    integrity = build_worldbridge_e373_receipt_integrity_artifact(artifact)
    encoded = encode_worldbridge_e373_receipt_integrity_artifact(integrity)
    decoded = decode_worldbridge_e373_receipt_integrity_artifact(encoded)
    consumed: set[str] = set()
    consume_worldbridge_e373_receipt_artifact(encoded, consumed)
    rejected: dict[str, bool] = {}

    replay = False
    try:
        consume_worldbridge_e373_receipt_artifact(encoded, consumed)
    except ValueError:
        replay = True
    rejected["replay"] = replay

    identity = copy.deepcopy(integrity)
    identity["checkpoint_identity"]["digest"] = "tampered"
    rejected["identity_tamper"] = not validate_worldbridge_e373_receipt_integrity_artifact(identity)["valid"]

    reordered = json.dumps(dict(reversed(list(integrity.items()))), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    try:
        decode_worldbridge_e373_receipt_integrity_artifact(reordered)
    except ValueError:
        rejected["field_reorder"] = True
    else:
        rejected["field_reorder"] = False

    duplicate = encoded.replace(
        b'"status":"worldbridge_e373_receipt_integrity"',
        b'"status":"worldbridge_e373_receipt_integrity","status":"worldbridge_e373_receipt_integrity"',
        1,
    )
    try:
        decode_worldbridge_e373_receipt_integrity_artifact(duplicate)
    except ValueError:
        rejected["duplicate_key"] = True
    else:
        rejected["duplicate_key"] = False

    try:
        decode_worldbridge_e373_receipt_integrity_artifact(b"x" * (MAX_ARTIFACT_BYTES + 1))
    except ValueError:
        rejected["oversize"] = True
    else:
        rejected["oversize"] = False

    if decoded != integrity or not all(rejected.values()):
        raise AssertionError(f"E373 integrity audit failed: {rejected}")
    return {
        "status": "worldbridge_e373_receipt_integrity",
        "contract_valid": True,
        "canonical_roundtrip": True,
        "negative_cases": rejected,
        "all_rejected": True,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }


if __name__ == "__main__":
    result = verify_e373_integrity()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] and result["all_rejected"] else 1)
