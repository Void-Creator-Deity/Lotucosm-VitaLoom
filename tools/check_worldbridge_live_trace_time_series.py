# -*- coding: utf-8 -*-
"""Mechanical E218 WorldBridge live comparability time-series guard."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_live_trace_time_series import (
    _sample_evaluation,
    aggregate_worldbridge_live_trace_evaluations,
    build_worldbridge_live_trace_time_series_contract,
    validate_worldbridge_live_trace_time_series,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


def _samples(first: dict[str, object], second: dict[str, object]) -> list[dict[str, object]]:
    return [
        {"sample_id": "guard-0001", "sample_index": 0, "evaluation": first},
        {"sample_id": "guard-0002", "sample_index": 1, "evaluation": second},
    ]


def _field_classification(aggregation: dict[str, object], field: str) -> str:
    pair = aggregation["pair_results"][0]  # type: ignore[index]
    result = next(item for item in pair["field_results"] if item["field"] == field)  # type: ignore[index]
    return str(result["classification"])


def main() -> int:
    contract = build_worldbridge_live_trace_time_series_contract()
    if contract.get("contract_valid") is not True:
        raise SystemExit("E218 time-series contract is invalid")

    stable = aggregate_worldbridge_live_trace_evaluations(
        _samples(_sample_evaluation(30.0), _sample_evaluation(30.0000000001))
    )
    repeated = aggregate_worldbridge_live_trace_evaluations(
        _samples(_sample_evaluation(29.5), _sample_evaluation(29.0))
    )
    if _field_classification(stable, "energy") != "stable_pass":
        raise SystemExit("stable pass classification missing")
    if _field_classification(repeated, "energy") != "repeated_mismatch_observed":
        raise SystemExit("repeated mismatch classification missing")
    for aggregation in (stable, repeated):
        validation = validate_worldbridge_live_trace_time_series(aggregation)
        if validation.get("valid") is not True:
            raise SystemExit(f"invalid E218 aggregation: {validation.get('errors')}")
        if any(
            aggregation.get(field) is not False
            for field in (
                "clocks_compared",
                "time_aligned",
                "causality_inferred",
                "atomic_checkpoint",
                "lossless",
                "replay_admitted",
                "default_ready",
            )
        ):
            raise SystemExit("E218 aggregation overclaimed admission")

    duplicate_evaluation = stable["samples"][0]["evaluation"]  # type: ignore[index]
    try:
        aggregate_worldbridge_live_trace_evaluations(
            _samples(duplicate_evaluation, copy.deepcopy(duplicate_evaluation))
        )
    except ValueError as exc:
        if "duplicate source_trace_digest" not in str(exc):
            raise
    else:
        raise SystemExit("duplicate evidence was not rejected")

    tampered = copy.deepcopy(stable)
    tampered["replay_admitted"] = True
    tampered_validation = validate_worldbridge_live_trace_time_series(tampered)
    if tampered_validation.get("valid") is not False:
        raise SystemExit("replay tamper was not rejected")
    if "unified_replay_not_admitted" not in tampered_validation.get("errors", []):
        raise SystemExit("replay rejection evidence missing")
    if "aggregation_digest_mismatch" not in tampered_validation.get("errors", []):
        raise SystemExit("aggregation digest rejection evidence missing")

    runtime_status = build_runtime_worldbridge_status()
    if runtime_status.get("live_dual_lane_comparability_time_series_contract") != contract:
        raise SystemExit("runtime status does not nest E218 contract")
    if runtime_status.get("runtime_mode") != "dual" or runtime_status.get("default_ready") is not False:
        raise SystemExit("runtime status overclaimed default readiness")

    print(
        json.dumps(
            {
                "status": "ok",
                "contract_valid": True,
                "stable_energy": _field_classification(stable, "energy"),
                "repeated_energy": _field_classification(repeated, "energy"),
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
