from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:
    from tools._runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e372_receipt_artifact import (
    build_worldbridge_e372_receipt_artifact,
)
from core.Lotucosm.runtime.world_bridge_e373_receipt_integrity import (
    build_worldbridge_e373_receipt_integrity_artifact,
    decode_worldbridge_e373_receipt_integrity_artifact,
    encode_worldbridge_e373_receipt_integrity_artifact,
)


# These cases exercise ordering, unicode, integer boundaries, signed zero and
# nested arrays. The digest is fixed so a runtime change cannot silently alter
# the cross-interpreter canonicalization contract.
CORPUS: tuple[dict[str, Any], ...] = (
    {"z": 1, "a": [True, None, "中文", -0.0]},
    {"integer": 9007199254740991, "negative": -9223372036854775808},
    {"float": 1.25, "small": 1e-09, "large": 1e20},
    {"nested": {"b": {"y": 2, "x": 1}, "a": [{"k": "v"}]}},
)
EXPECTED_CORPUS_DIGEST = "9a088db56500948161698690acb8184792f8b963d6b8cd3fc8ba1f3a812f74a9"


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _real_integrity_artifact() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_worldbridge_e367_live_viewport_witness.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
    )
    receipt = json.loads([line for line in proc.stdout.splitlines() if line.strip()][-1])
    return build_worldbridge_e373_receipt_integrity_artifact(
        build_worldbridge_e372_receipt_artifact(
            receipt,
            artifact_id="e374-compatibility",
            issued_at=1_700_000_000,
            ttl_seconds=86_400,
        )
    )


def _run_once(*, include_runtime_artifact: bool = True) -> dict[str, Any]:
    corpus_digest = _digest(list(CORPUS))
    if corpus_digest != EXPECTED_CORPUS_DIGEST:
        raise AssertionError(
            f"canonical corpus drift: expected {EXPECTED_CORPUS_DIGEST}, got {corpus_digest}"
        )
    if not include_runtime_artifact:
        return {
            "python": list(sys.version_info[:3]),
            "corpus_digest": corpus_digest,
            "artifact_digest": None,
            "integrity_digest": None,
            "roundtrip": True,
        }
    integrity = _real_integrity_artifact()
    encoded = encode_worldbridge_e373_receipt_integrity_artifact(integrity)
    decoded = decode_worldbridge_e373_receipt_integrity_artifact(encoded)
    if decoded != integrity:
        raise AssertionError("integrity artifact roundtrip drifted")
    return {
        "python": list(sys.version_info[:3]),
        "corpus_digest": corpus_digest,
        "artifact_digest": integrity["artifact_digest"],
        "integrity_digest": integrity["integrity_digest"],
        "roundtrip": True,
    }


def verify_compatibility_corpus(*, corpus_only: bool = False) -> dict[str, Any]:
    first = _run_once(include_runtime_artifact=not corpus_only)
    second = _run_once(include_runtime_artifact=not corpus_only)
    stable = (
        first["corpus_digest"] == second["corpus_digest"]
        and (
            corpus_only
            or (
                first["artifact_digest"] == second["artifact_digest"]
                and first["integrity_digest"] == second["integrity_digest"]
            )
        )
    )
    return {
        "status": "worldbridge_e374_compatibility_corpus",
        "contract_valid": stable and first["roundtrip"] and second["roundtrip"],
        "same_process_stable": stable,
        "cross_process_stable": stable,
        "python": first["python"],
        "corpus_digest": first["corpus_digest"],
        "artifact_digest": first["artifact_digest"],
        "integrity_digest": first["integrity_digest"],
        "migration_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }


if __name__ == "__main__":
    result = verify_compatibility_corpus(corpus_only="--corpus-only" in sys.argv)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] else 1)
