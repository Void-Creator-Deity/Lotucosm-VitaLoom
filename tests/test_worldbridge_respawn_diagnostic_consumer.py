# -*- coding: utf-8 -*-
"""E229 tests for paired bounded diagnostic consumer receipts."""
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
    _projection_digest,
    encode_worldbridge_respawn_artifact_diagnostic_projection,
    project_worldbridge_respawn_artifact_inspection,
)
from core.Lotucosm.runtime.world_bridge_respawn_artifact_inspection import (
    encode_worldbridge_respawn_artifact_inspection,
    inspect_worldbridge_respawn_two_stream_artifact,
)
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_consumer import (
    MAX_RECEIPT_BYTES,
    _receipt_digest,
    build_worldbridge_respawn_diagnostic_consumer_contract,
    consume_worldbridge_respawn_diagnostic_pair,
    decode_worldbridge_respawn_diagnostic_consumer_receipt,
    encode_worldbridge_respawn_diagnostic_consumer_receipt,
    validate_worldbridge_respawn_diagnostic_consumer_receipt,
)
from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import (
    build_worldbridge_respawn_two_stream_artifact,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _numpy_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def _pair(probability: float = 1.0, context_id: str = "e229-context") -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    context = create_worldbridge_deterministic_randomness_context(context_id, "e229-seed")
    register_worldbridge_deterministic_random_stream(context, "sr.war.respawn.decision", "python_random")
    register_worldbridge_deterministic_random_stream(context, "sr.war.respawn.mind", "python_random")
    handoff = run_worldbridge_named_stream_sr_respawn_handoff(
        context,
        "sr.war.respawn.decision",
        "sr.war.respawn.mind",
        {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3},
        0.25,
        probability,
    )
    artifact = build_worldbridge_respawn_two_stream_artifact(handoff, artifact_id=f"{context_id}-artifact")
    inspection = inspect_worldbridge_respawn_two_stream_artifact(artifact)
    projection = project_worldbridge_respawn_artifact_inspection(inspection)
    return artifact, inspection, projection


def test_admitted_pair_builds_copy_isolated_non_executable_receipt() -> None:
    _, inspection, projection = _pair()
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    receipt = consume_worldbridge_respawn_diagnostic_pair(inspection, projection)
    assert random.getstate() == python_before
    assert _numpy_equal(numpy_before, np.random.get_state())
    assert receipt["outcome"] == "admitted_mutation"
    assert receipt["source_projection_parity_valid"] is True
    assert receipt["replay_input"] is False
    assert receipt["checkpoint_state"] is False
    assert receipt["restore_performed"] is False
    assert receipt["mutation_executed"] is False
    assert receipt["live_runtime_state"] is False
    assert "child" not in receipt
    assert "before_snapshot" not in receipt
    receipt["gene_counts"]["parent"] = 999
    assert consume_worldbridge_respawn_diagnostic_pair(inspection, projection)["gene_counts"]["parent"] != 999


def test_rejected_pair_preserves_read_only_no_mutation_facts() -> None:
    _, inspection, projection = _pair(0.0)
    receipt = consume_worldbridge_respawn_diagnostic_pair(inspection, projection)
    assert receipt["outcome"] == "rejected_no_mutation"
    assert receipt["admitted"] is False
    assert receipt["ordered_steps"] == ["decision"]
    assert receipt["mutation_stream_consumed"] is False
    assert validate_worldbridge_respawn_diagnostic_consumer_receipt(
        receipt, inspection=inspection, projection=projection
    ) == {"valid": True, "errors": []}


def test_mapping_and_canonical_byte_pairs_round_trip() -> None:
    _, inspection, projection = _pair()
    receipt = consume_worldbridge_respawn_diagnostic_pair(
        encode_worldbridge_respawn_artifact_inspection(inspection),
        encode_worldbridge_respawn_artifact_diagnostic_projection(projection),
    )
    encoded = encode_worldbridge_respawn_diagnostic_consumer_receipt(receipt)
    assert len(encoded) <= MAX_RECEIPT_BYTES
    assert decode_worldbridge_respawn_diagnostic_consumer_receipt(encoded) == receipt
    with pytest.raises(ValueError, match="canonical"):
        decode_worldbridge_respawn_diagnostic_consumer_receipt(
            json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        )


def test_raw_artifact_missing_pair_and_mismatched_pair_fail_closed() -> None:
    artifact, inspection, projection = _pair()
    with pytest.raises(ValueError):
        consume_worldbridge_respawn_diagnostic_pair(artifact, projection)
    with pytest.raises(ValueError):
        consume_worldbridge_respawn_diagnostic_pair(inspection, artifact)
    _, other_inspection, other_projection = _pair(context_id="e229-other")
    with pytest.raises(ValueError, match="pair rejected"):
        consume_worldbridge_respawn_diagnostic_pair(inspection, other_projection)
    receipt = consume_worldbridge_respawn_diagnostic_pair(inspection, projection)
    assert validate_worldbridge_respawn_diagnostic_consumer_receipt(receipt, inspection=inspection)["errors"] == [
        "source_pair_incomplete"
    ]
    assert validate_worldbridge_respawn_diagnostic_consumer_receipt(receipt, projection=projection)["errors"] == [
        "source_pair_incomplete"
    ]
    assert other_inspection["context_id"] != inspection["context_id"]


def test_semantic_overclaim_and_paired_field_mismatch_are_rejected() -> None:
    _, inspection, projection = _pair()
    receipt = consume_worldbridge_respawn_diagnostic_pair(inspection, projection)
    overclaim = copy.deepcopy(receipt)
    overclaim["checkpoint_state"] = True
    overclaim["receipt_digest"] = _receipt_digest(overclaim)
    validation = validate_worldbridge_respawn_diagnostic_consumer_receipt(overclaim)
    assert validation["valid"] is False
    assert "checkpoint_state_mismatch" in validation["errors"]

    mismatched = copy.deepcopy(receipt)
    mismatched["gene_counts"]["parent"] += 1
    mismatched["receipt_digest"] = _receipt_digest(mismatched)
    assert validate_worldbridge_respawn_diagnostic_consumer_receipt(mismatched)["valid"] is True
    validation = validate_worldbridge_respawn_diagnostic_consumer_receipt(
        mismatched, inspection=inspection, projection=projection
    )
    assert validation["valid"] is False
    assert "pair_parity_gene_counts_mismatch" in validation["errors"]


def test_tampered_projection_with_recomputed_self_digest_cannot_cross_pair_boundary() -> None:
    _, inspection, projection = _pair()
    tampered = copy.deepcopy(projection)
    tampered["gene_counts"]["child"] += 1
    tampered["projection_digest"] = _projection_digest(tampered)
    with pytest.raises(ValueError, match="pair rejected"):
        consume_worldbridge_respawn_diagnostic_pair(inspection, tampered)


def test_contract_and_runtime_status_remain_opt_in_dual_and_not_default_ready() -> None:
    contract = build_worldbridge_respawn_diagnostic_consumer_contract()
    assert contract["contract_valid"] is True
    assert contract["round_trip_equal"] is True
    assert contract["requires_inspection_projection_pair"] is True
    assert contract["accepts_raw_artifact"] is False
    assert contract["restores_streams"] is False
    assert contract["executes_mutation"] is False
    status = build_runtime_worldbridge_status()
    assert status["opt_in_respawn_diagnostic_consumer_contract"] == contract
    assert "respawn_diagnostic_consumer_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["default_ready"] is False
