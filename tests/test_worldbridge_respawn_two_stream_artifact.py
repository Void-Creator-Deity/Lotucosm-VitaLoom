# -*- coding: utf-8 -*-
"""E226 tests for canonical opt-in respawn two-stream hand-off artifacts."""
from __future__ import annotations

import copy
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
from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import (
    _artifact_digest,
    build_worldbridge_respawn_two_stream_artifact,
    build_worldbridge_respawn_two_stream_artifact_contract,
    decode_worldbridge_respawn_two_stream_artifact,
    encode_worldbridge_respawn_two_stream_artifact,
    validate_worldbridge_respawn_two_stream_artifact,
    validate_worldbridge_respawn_two_stream_handoff_evidence,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


PARENT = {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3}


def _context(seed: str = "e226-seed"):
    context = create_worldbridge_deterministic_randomness_context("e226-context", seed)
    register_worldbridge_deterministic_random_stream(
        context, "sr.war.respawn.decision", "python_random"
    )
    register_worldbridge_deterministic_random_stream(
        context, "sr.war.respawn.mind", "python_random"
    )
    return context


def _handoff(probability: float = 1.0):
    return run_worldbridge_named_stream_sr_respawn_handoff(
        _context(),
        "sr.war.respawn.decision",
        "sr.war.respawn.mind",
        PARENT,
        0.25,
        probability,
    )


def _numpy_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def test_admitted_handoff_seals_to_canonical_round_trip_artifact_without_global_rng_use() -> None:
    handoff = _handoff(1.0)
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    artifact = build_worldbridge_respawn_two_stream_artifact(
        handoff, artifact_id="e226-admitted"
    )
    assert random.getstate() == python_before
    assert _numpy_equal(np.random.get_state(), numpy_before)
    assert validate_worldbridge_respawn_two_stream_handoff_evidence(handoff) == {
        "valid": True,
        "errors": [],
    }
    assert validate_worldbridge_respawn_two_stream_artifact(artifact) == {
        "valid": True,
        "errors": [],
    }
    assert artifact["admitted"] is True
    assert artifact["ordered_steps"] == ["decision", "mutation"]
    assert artifact["mutation_stream_consumed"] is True
    encoded = encode_worldbridge_respawn_two_stream_artifact(artifact)
    assert decode_worldbridge_respawn_two_stream_artifact(encoded) == artifact

    handoff["before_snapshot"]["context_id"] = "tampered"
    artifact["child"]["wander_amp"] = -999.0
    assert decode_worldbridge_respawn_two_stream_artifact(encoded)["child"]["wander_amp"] != -999.0


def test_rejected_handoff_is_complete_evidence_and_keeps_mutation_boundary_unchanged() -> None:
    handoff = _handoff(0.0)
    artifact = build_worldbridge_respawn_two_stream_artifact(
        handoff, artifact_id="e226-rejected"
    )
    assert handoff["admitted"] is False
    assert handoff["after_decision_snapshot"] == handoff["after_snapshot"]
    assert artifact["admitted"] is False
    assert artifact["ordered_steps"] == ["decision"]
    assert artifact["mutation_stream_consumed"] is False
    assert artifact["parent"] == artifact["child"]
    assert artifact["deltas"] == {}
    assert validate_worldbridge_respawn_two_stream_artifact(artifact)["valid"] is True


def test_tampering_or_semantic_overclaim_rejects_even_with_recomputed_outer_digest() -> None:
    artifact = build_worldbridge_respawn_two_stream_artifact(
        _handoff(1.0), artifact_id="e226-tamper"
    )
    changed_order = copy.deepcopy(artifact)
    changed_order["ordered_steps"] = ["mutation", "decision"]
    changed_order["artifact_digest"] = _artifact_digest(changed_order)
    validation = validate_worldbridge_respawn_two_stream_artifact(changed_order)
    assert validation["valid"] is False
    assert "handoff_ordered_steps_mismatch" in validation["errors"]

    changed_snapshot = copy.deepcopy(artifact)
    changed_snapshot["after_snapshot"]["streams"][1]["state"]["internal_state"][0] += 1
    changed_snapshot["artifact_digest"] = _artifact_digest(changed_snapshot)
    validation = validate_worldbridge_respawn_two_stream_artifact(changed_snapshot)
    assert validation["valid"] is False
    assert "handoff_after_snapshot_invalid" in validation["errors"]

    overclaim = copy.deepcopy(artifact)
    overclaim["replay_input"] = True
    overclaim["artifact_digest"] = _artifact_digest(overclaim)
    validation = validate_worldbridge_respawn_two_stream_artifact(overclaim)
    assert validation["valid"] is False
    assert "replay_input_mismatch" in validation["errors"]


def test_malformed_or_partial_handoff_fails_closed_before_any_artifact_exists() -> None:
    handoff = _handoff(1.0)
    handoff.pop("after_snapshot")
    assert validate_worldbridge_respawn_two_stream_handoff_evidence(handoff)["valid"] is False
    with pytest.raises(ValueError, match="invalid respawn two-stream handoff"):
        build_worldbridge_respawn_two_stream_artifact(handoff, artifact_id="e226-bad")


def test_contract_is_read_only_opt_in_and_runtime_status_nests_it() -> None:
    contract = build_worldbridge_respawn_two_stream_artifact_contract()
    assert contract["contract_valid"] is True
    assert contract["round_trip_equal"] is True
    assert contract["artifact"]["default_ready"] is False
    assert contract["artifact"]["replay_admitted"] is False
    status = build_runtime_worldbridge_status()
    assert status["opt_in_respawn_two_stream_artifact_contract"] == contract
    assert "respawn_two_stream_artifact_module" in status["pilot_modules"]
    assert status["default_ready"] is False

