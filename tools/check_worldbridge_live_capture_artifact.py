# -*- coding: utf-8 -*-
"""Mechanical E220 sealed capture-session artifact and round-trip guard."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_live_capture_artifact import (
    _artifact_digest,
    build_worldbridge_live_capture_artifact_contract,
    decode_worldbridge_live_capture_artifact,
    encode_worldbridge_live_capture_artifact,
    validate_worldbridge_live_capture_artifact,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


def main() -> int:
    contract = build_worldbridge_live_capture_artifact_contract()
    if contract.get("contract_valid") is not True or contract.get("round_trip_equal") is not True:
        raise SystemExit("E220 artifact contract or round trip is invalid")
    artifact = contract["artifact"]
    if artifact.get("session", {}).get("lifecycle") != "sealed":
        raise SystemExit("E220 artifact did not retain a sealed E219 session")
    encoded = encode_worldbridge_live_capture_artifact(artifact)
    if decode_worldbridge_live_capture_artifact(encoded) != artifact:
        raise SystemExit("E220 canonical artifact round trip diverged")
    if any(
        artifact.get(field) is not False
        for field in (
            "replay_input",
            "checkpoint_state",
            "persistence_authority",
            "time_aligned",
            "causality_inferred",
            "atomic_checkpoint",
            "lossless",
            "replay_admitted",
            "default_ready",
        )
    ):
        raise SystemExit("E220 artifact overclaimed replay/checkpoint/default admission")

    tampered = copy.deepcopy(artifact)
    tampered["replay_input"] = True
    tampered["artifact_digest"] = _artifact_digest(tampered)
    validation = validate_worldbridge_live_capture_artifact(tampered)
    if validation.get("valid") is not False or "replay_input_mismatch" not in validation.get("errors", []):
        raise SystemExit("E220 semantic overclaim survived a recomputed artifact digest")

    try:
        decode_worldbridge_live_capture_artifact(
            json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        )
    except ValueError:
        pass
    else:
        raise SystemExit("E220 non-canonical JSON was accepted")

    runtime_status = build_runtime_worldbridge_status()
    if runtime_status.get("sealed_live_comparability_capture_artifact_contract") != contract:
        raise SystemExit("runtime status does not nest E220 contract")
    if runtime_status.get("runtime_mode") != "dual" or runtime_status.get("default_ready") is not False:
        raise SystemExit("runtime status overclaimed default readiness")

    print(
        json.dumps(
            {
                "status": "ok",
                "contract_valid": True,
                "round_trip_equal": True,
                "encoded_byte_length": len(encoded),
                "session_lifecycle": artifact["session"]["lifecycle"],
                "canonical_json": True,
                "replay_input": False,
                "checkpoint_state": False,
                "persistence_authority": False,
                "time_aligned": False,
                "causality_inferred": False,
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
