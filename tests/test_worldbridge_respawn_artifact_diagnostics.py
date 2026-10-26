# -*- coding: utf-8 -*-
"""E228 tests for bounded parity-preserving respawn diagnostics."""
from __future__ import annotations

import copy
import json
import random

import numpy as np
import pytest

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
)
from core.Lotucosm.runtime.world_bridge_named_stream_adapter import (
    run_worldbridge_named_stream_sr_respawn_handoff,
)
from core.Lotucosm.runtime.world_bridge_respawn_artifact_diagnostics import (
    MAX_PROJECTION_BYTES,
    _projection_digest,
    build_worldbridge_respawn_artifact_diagnostic_projection_contract,
    decode_worldbridge_respawn_artifact_diagnostic_projection,
    encode_worldbridge_respawn_artifact_diagnostic_projection,
    project_worldbridge_respawn_artifact_inspection,
    validate_worldbridge_respawn_artifact_diagnostic_projection,
)
from core.Lotucosm.runtime.world_bridge_respawn_artifact_inspection import (
    _inspection_digest,
    encode_worldbridge_respawn_artifact_inspection,
    inspect_worldbridge_respawn_two_stream_artifact,
    validate_worldbridge_respawn_artifact_inspection,
)
from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import (
    build_worldbridge_respawn_two_stream_artifact,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _numpy_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def _artifact(probability: float = 1.0) -> dict[str, object]:
    context = create_worldbridge_deterministic_randomness_context("e228-context", "e228-seed")
    register_worldbridge_deterministic_random_stream(
        context, "sr.war.respawn.decision", "python_random"
    )
    register_worldbridge_deterministic_random_stream(
        context, "sr.war.respawn.mind", "python_random"
    )
    handoff = run_worldbridge_named_stream_sr_respawn_handoff(
        context,
        "sr.war.respawn.decision",
        "sr.war.respawn.mind",
        {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3},
        0.25,
        probability,
    )
    return build_worldbridge_respawn_two_stream_artifact(handoff, artifact_id="e228-artifact")


def _inspection(probability: float = 1.0) -> dict[str, object]:
    return inspect_worldbridge_respawn_two_stream_artifact(_artifact(probability))


def test_projection_is_parity_bound_copy_isolated_and_non_executable() -> None:
    summary = _inspection(1.0)
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    projection = project_worldbridge_respawn_artifact_inspection(summary)
    assert random.getstate() == python_before
    assert _numpy_equal(numpy_before, np.random.get_state())
    assert validate_worldbridge_respawn_artifact_diagnostic_projection(
        projection, inspection=summary
    ) == {"valid": True, "errors": []}
    assert projection["outcome"] == "admitted_mutation"
    assert projection["ordered_steps"] == ["decision", "mutation"]
    assert projection["stream_roles"]["decision"] == "sr.war.respawn.decision"
    assert projection["gene_counts"]["parent"] == summary["parent_gene_count"]
    assert projection["restore_performed"] is False
    assert projection["mutation_executed"] is False
    assert projection["replay_admitted"] is False
    assert "child" not in projection
    assert "before_snapshot" not in projection
    assert "inspection_digest" not in projection

    summary["snapshot_digests"]["before"] = "0" * 64
    projection["gene_counts"]["parent"] = 999
    fresh = project_worldbridge_respawn_artifact_inspection(_inspection(1.0))
    assert fresh["snapshot_digests"]["before"] != "0" * 64
    assert fresh["gene_counts"]["parent"] != 999


def test_rejected_projection_preserves_no_mutation_outcome_parity() -> None:
    summary = _inspection(0.0)
    projection = project_worldbridge_respawn_artifact_inspection(summary)
    assert projection["outcome"] == "rejected_no_mutation"
    assert projection["admitted"] is False
    assert projection["ordered_steps"] == ["decision"]
    assert projection["mutation_stream_consumed"] is False
    assert validate_worldbridge_respawn_artifact_diagnostic_projection(
        projection, inspection=summary
    )["valid"] is True


def test_projection_accepts_only_e227_summary_or_canonical_summary_bytes() -> None:
    summary = _inspection(1.0)
    projection = project_worldbridge_respawn_artifact_inspection(summary)
    encoded_projection = encode_worldbridge_respawn_artifact_diagnostic_projection(projection)
    assert len(encoded_projection) <= MAX_PROJECTION_BYTES
    assert decode_worldbridge_respawn_artifact_diagnostic_projection(encoded_projection) == projection
    assert project_worldbridge_respawn_artifact_inspection(
        encode_worldbridge_respawn_artifact_inspection(summary)
    ) == projection
    with pytest.raises(ValueError, match="inspection summary"):
        project_worldbridge_respawn_artifact_inspection(_artifact(1.0))
    with pytest.raises(ValueError, match="canonical"):
        decode_worldbridge_respawn_artifact_diagnostic_projection(
            json.dumps(projection, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        )


def test_tamper_and_semantic_parity_mismatch_fail_closed() -> None:
    summary = _inspection(1.0)
    projection = project_worldbridge_respawn_artifact_inspection(summary)

    semantic_overclaim = copy.deepcopy(projection)
    semantic_overclaim["checkpoint_state"] = True
    semantic_overclaim["projection_digest"] = _projection_digest(semantic_overclaim)
    validation = validate_worldbridge_respawn_artifact_diagnostic_projection(semantic_overclaim)
    assert validation["valid"] is False
    assert "checkpoint_state_mismatch" in validation["errors"]

    mismatched = copy.deepcopy(projection)
    mismatched["gene_counts"]["parent"] += 1
    mismatched["projection_digest"] = _projection_digest(mismatched)
    assert validate_worldbridge_respawn_artifact_diagnostic_projection(mismatched)["valid"] is True
    parity = validate_worldbridge_respawn_artifact_diagnostic_projection(
        mismatched, inspection=summary
    )
    assert parity["valid"] is False
    assert "parity_gene_counts_mismatch" in parity["errors"]


def test_projection_rejects_valid_but_unbounded_inspection_summary() -> None:
    summary = _inspection(1.0)
    oversized = copy.deepcopy(summary)
    oversized["source_artifact_id"] = "x" * MAX_PROJECTION_BYTES
    oversized["inspection_digest"] = _inspection_digest(oversized)
    assert validate_worldbridge_respawn_artifact_inspection(oversized)["valid"] is True
    with pytest.raises(RuntimeError, match="projection_exceeds_bound"):
        project_worldbridge_respawn_artifact_inspection(oversized)
    with pytest.raises(ValueError, match="exceeds bound"):
        decode_worldbridge_respawn_artifact_diagnostic_projection(b"x" * (MAX_PROJECTION_BYTES + 1))


def test_contract_and_runtime_status_remain_opt_in_read_only() -> None:
    contract = build_worldbridge_respawn_artifact_diagnostic_projection_contract()
    assert contract["contract_valid"] is True
    assert contract["round_trip_equal"] is True
    assert contract["inspection_consumer_only"] is True
    assert contract["accepts_raw_artifact"] is False
    assert contract["restores_streams"] is False
    assert contract["executes_mutation"] is False
    status = build_runtime_worldbridge_status()
    assert status["opt_in_respawn_artifact_diagnostic_projection_contract"] == contract
    assert "respawn_artifact_diagnostic_projection_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["default_ready"] is False
