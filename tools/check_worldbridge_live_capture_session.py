# -*- coding: utf-8 -*-
"""Mechanical E219 bounded live comparability capture-session guard."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_live_capture_session import (
    _sample_producer,
    abort_worldbridge_live_capture_session,
    append_worldbridge_live_capture_session_evidence,
    build_worldbridge_live_capture_session_contract,
    seal_worldbridge_live_capture_session,
    start_worldbridge_live_capture_session,
    validate_worldbridge_live_capture_session,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


def main() -> int:
    contract = build_worldbridge_live_capture_session_contract()
    if contract.get("contract_valid") is not True:
        raise SystemExit("E219 capture-session contract is invalid")
    session = contract["session"]
    if session.get("lifecycle") != "sealed" or session.get("sample_count") != 2:
        raise SystemExit("E219 sealed bounded lifecycle evidence missing")
    if any(
        session.get(field) is not False
        for field in (
            "scheduler_owned",
            "clocks_compared",
            "time_aligned",
            "causality_inferred",
            "atomic_checkpoint",
            "lossless",
            "replay_admitted",
            "default_ready",
        )
    ):
        raise SystemExit("E219 session overclaimed runtime admission")

    open_session = start_worldbridge_live_capture_session("guard-session", max_samples=1)
    appended = append_worldbridge_live_capture_session_evidence(
        open_session,
        _sample_producer(sample_number=11, ps_energy=29.0),
    )
    before = copy.deepcopy(appended)
    try:
        append_worldbridge_live_capture_session_evidence(
            appended,
            _sample_producer(sample_number=12, ps_energy=28.0),
        )
    except OverflowError:
        pass
    else:
        raise SystemExit("E219 bounded overflow was not rejected")
    if appended != before:
        raise SystemExit("E219 overflow mutated retained evidence")

    aborted = abort_worldbridge_live_capture_session(
        start_worldbridge_live_capture_session("guard-abort", max_samples=1),
        reason="guard stop",
    )
    if validate_worldbridge_live_capture_session(aborted).get("valid") is not True:
        raise SystemExit("E219 aborted partial evidence invalid")
    if aborted.get("aggregation") is not None or aborted.get("partial_evidence") is not True:
        raise SystemExit("E219 abort semantics overclaimed completeness")

    runtime_status = build_runtime_worldbridge_status()
    if runtime_status.get("bounded_live_comparability_capture_session_contract") != contract:
        raise SystemExit("runtime status does not nest E219 contract")
    if runtime_status.get("runtime_mode") != "dual" or runtime_status.get("default_ready") is not False:
        raise SystemExit("runtime status overclaimed default readiness")

    print(
        json.dumps(
            {
                "status": "ok",
                "contract_valid": True,
                "lifecycle": session["lifecycle"],
                "sample_count": session["sample_count"],
                "bounded": session["bounded"],
                "scheduler_owned": False,
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
