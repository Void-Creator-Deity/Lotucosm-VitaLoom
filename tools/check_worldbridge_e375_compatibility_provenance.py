from __future__ import annotations

import copy
import base64
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

from core.Lotucosm.runtime.world_bridge_e375_compatibility_provenance import (
    build_worldbridge_e375_compatibility_provenance,
    decode_worldbridge_e375_compatibility_provenance,
    encode_worldbridge_e375_compatibility_provenance,
    validate_worldbridge_e375_compatibility_provenance,
)

EXPECTED_CORPUS_DIGEST = "9a088db56500948161698690acb8184792f8b963d6b8cd3fc8ba1f3a812f74a9"


def _e374_result() -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_worldbridge_e374_compatibility_corpus.py"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    return json.loads([line for line in proc.stdout.splitlines() if line.strip()][-1])


def verify_provenance() -> dict[str, object]:
    result = _e374_result()
    provenance = build_worldbridge_e375_compatibility_provenance(result)
    expected_python = provenance["python_version"]
    valid = validate_worldbridge_e375_compatibility_provenance(
        provenance,
        expected_corpus_digest=EXPECTED_CORPUS_DIGEST,
        expected_python=expected_python,
    )
    encoded = encode_worldbridge_e375_compatibility_provenance(
        provenance,
        expected_corpus_digest=EXPECTED_CORPUS_DIGEST,
        expected_python=expected_python,
    )
    decoded = decode_worldbridge_e375_compatibility_provenance(
        encoded,
        expected_corpus_digest=EXPECTED_CORPUS_DIGEST,
        expected_python=expected_python,
    )
    if decoded != provenance:
        raise AssertionError("E375 canonical roundtrip drifted")
    child_code = """
import base64, json, sys
from core.Lotucosm.runtime.world_bridge_e375_compatibility_provenance import decode_worldbridge_e375_compatibility_provenance
value = decode_worldbridge_e375_compatibility_provenance(
    base64.b64decode(sys.argv[1]),
    expected_corpus_digest=sys.argv[2],
    expected_python=json.loads(sys.argv[3]),
)
print(json.dumps(value, ensure_ascii=False, sort_keys=True))
"""
    child_env = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"),
    }
    child = subprocess.run(
        [sys.executable, "-B", "-c", child_code, base64.b64encode(encoded).decode("ascii"),
         EXPECTED_CORPUS_DIGEST, json.dumps(expected_python)],
        cwd=ROOT, env=child_env, capture_output=True, text=True, check=True,
    )
    child_value = json.loads(child.stdout.strip())
    cross_process_stable = child_value == provenance
    rejected: dict[str, bool] = {}
    digest_tamper = copy.deepcopy(provenance)
    digest_tamper["artifact_digest"] = "tampered"
    rejected["artifact_digest_tamper"] = not validate_worldbridge_e375_compatibility_provenance(
        digest_tamper, expected_corpus_digest=EXPECTED_CORPUS_DIGEST, expected_python=expected_python
    )["valid"]
    version_mismatch = copy.deepcopy(provenance)
    version_mismatch["python_version"] = [3, 12, 0]
    rejected["python_version_mismatch"] = not validate_worldbridge_e375_compatibility_provenance(
        version_mismatch, expected_corpus_digest=EXPECTED_CORPUS_DIGEST, expected_python=expected_python
    )["valid"]
    corpus_mismatch = copy.deepcopy(provenance)
    corpus_mismatch["corpus_digest"] = "wrong-corpus"
    rejected["corpus_digest_mismatch"] = not validate_worldbridge_e375_compatibility_provenance(
        corpus_mismatch, expected_corpus_digest=EXPECTED_CORPUS_DIGEST, expected_python=expected_python
    )["valid"]
    missing_runtime = copy.deepcopy(provenance)
    missing_runtime["runtime_artifact_verified"] = False
    rejected["runtime_artifact_missing"] = not validate_worldbridge_e375_compatibility_provenance(
        missing_runtime, expected_corpus_digest=EXPECTED_CORPUS_DIGEST, expected_python=expected_python
    )["valid"]
    if valid["valid"] is not True or not all(rejected.values()) or not cross_process_stable:
        raise AssertionError(f"E375 provenance audit failed: {valid}, {rejected}")
    return {
        "status": "worldbridge_e375_compatibility_provenance",
        "contract_valid": True,
        "canonical_roundtrip": decoded == provenance,
        "cross_process_stable": cross_process_stable,
        "runtime_artifact_verified": provenance["runtime_artifact_verified"],
        "negative_cases": rejected,
        "all_rejected": True,
        "migration_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }


if __name__ == "__main__":
    result = verify_provenance()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] and result["all_rejected"] else 1)
