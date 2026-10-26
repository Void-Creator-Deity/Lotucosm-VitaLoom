# -*- coding: utf-8 -*-
"""Mechanical E217 WorldBridge live field-comparability contract guard."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_live_trace_comparability import (
    build_worldbridge_live_trace_comparability_contract,
    evaluate_worldbridge_live_trace_fields,
    validate_worldbridge_live_trace_field_evaluation,
)
from core.Lotucosm.runtime.world_bridge_live_trace_producer import (
    build_worldbridge_live_dual_lane_trace,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


def _producer(*, energy: float) -> dict[str, object]:
    shared = {
        "position": [1.0, 2.0],
        "velocity": [0.5, 0.25],
        "acceleration": [0.0, 0.0],
        "health": 20.0,
        "size": 8.0,
        "radius": 4.0,
    }
    return build_worldbridge_live_dual_lane_trace(
        {
            "sim_time": 1.25,
            "capture_source": "sr_observation_before_bridge_handoff",
            "bridged_entities": [
                {"entity_id": "sr:guard", "linked_id": "ps:guard", "energy": 30.0, **shared}
            ],
        },
        {
            "tick": 4,
            "capture_source": "ps_pond_after_update_before_display_reflection",
            "bridged_organisms": [
                {"organism_id": "ps:guard", "linked_id": "sr:guard", "energy": energy, **shared}
            ],
        },
        entity_links=[{"sr_entity_id": "sr:guard", "ps_organism_id": "ps:guard"}],
        observed_sr_delta=0.05,
    )


def main() -> int:
    contract = build_worldbridge_live_trace_comparability_contract()
    if contract.get("contract_valid") is not True:
        raise SystemExit("E217 comparability contract is invalid")

    passing = evaluate_worldbridge_live_trace_fields(_producer(energy=30.0))
    mismatch = evaluate_worldbridge_live_trace_fields(_producer(energy=29.5))
    if passing.get("aggregate_comparable_status") != "comparable_pass":
        raise SystemExit("equal admitted fields must pass")
    if mismatch.get("aggregate_comparable_status") != "comparable_mismatch":
        raise SystemExit("live drift must remain a comparable mismatch")
    for result in (passing, mismatch):
        validation = validate_worldbridge_live_trace_field_evaluation(result)
        if validation.get("valid") is not True:
            raise SystemExit(f"invalid E217 evaluation: {validation.get('errors')}")
        if any(
            result.get(field) is not False
            for field in (
                "clocks_compared",
                "same_instant_parity",
                "atomic_checkpoint",
                "lossless",
                "replay_admitted",
                "default_ready",
            )
        ):
            raise SystemExit("E217 evaluation overclaimed admission")

    tampered = copy.deepcopy(passing)
    tampered["replay_admitted"] = True
    tampered_validation = validate_worldbridge_live_trace_field_evaluation(tampered)
    if tampered_validation.get("valid") is not False:
        raise SystemExit("replay tamper was not rejected")
    if "unified_replay_not_admitted" not in tampered_validation.get("errors", []):
        raise SystemExit("replay rejection evidence missing")
    if "evaluation_digest_mismatch" not in tampered_validation.get("errors", []):
        raise SystemExit("digest tamper evidence missing")

    runtime_status = build_runtime_worldbridge_status()
    if runtime_status.get("live_dual_lane_field_comparability_contract") != contract:
        raise SystemExit("runtime status does not nest E217 contract")
    if runtime_status.get("runtime_mode") != "dual" or runtime_status.get("default_ready") is not False:
        raise SystemExit("runtime status overclaimed default readiness")

    print(
        json.dumps(
            {
                "status": "ok",
                "contract_valid": True,
                "passing_status": passing["aggregate_comparable_status"],
                "mismatch_status": mismatch["aggregate_comparable_status"],
                "declared_mapping_losses": mismatch["declared_mapping_losses"],
                "replay_admitted": mismatch["replay_admitted"],
                "default_ready": mismatch["default_ready"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
