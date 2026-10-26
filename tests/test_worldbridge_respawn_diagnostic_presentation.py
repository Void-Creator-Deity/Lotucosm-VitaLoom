# -*- coding: utf-8 -*-
"""E230 tests for receipt-only read-only diagnostic presentations."""
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
    project_worldbridge_respawn_artifact_inspection,
)
from core.Lotucosm.runtime.world_bridge_respawn_artifact_inspection import (
    inspect_worldbridge_respawn_two_stream_artifact,
)
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_consumer import (
    consume_worldbridge_respawn_diagnostic_pair,
)
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_presentation import (
    MAX_PRESENTATION_BYTES,
    _presentation_digest,
    build_worldbridge_respawn_diagnostic_presentation_contract,
    decode_worldbridge_respawn_diagnostic_presentation,
    encode_worldbridge_respawn_diagnostic_presentation,
    present_worldbridge_respawn_diagnostic_receipt,
    validate_worldbridge_respawn_diagnostic_presentation,
)
from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import (
    build_worldbridge_respawn_two_stream_artifact,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _numpy_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def _sources(probability: float = 1.0, context_id: str = "e230-context") -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    context = create_worldbridge_deterministic_randomness_context(context_id, "e230-seed")
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
    receipt = consume_worldbridge_respawn_diagnostic_pair(inspection, projection)
    return artifact, inspection, projection, receipt


def test_admitted_receipt_presentation_is_copy_isolated_and_non_ui() -> None:
    _, _, _, receipt = _sources()
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    presentation = present_worldbridge_respawn_diagnostic_receipt(receipt)
    assert random.getstate() == python_before
    assert _numpy_equal(numpy_before, np.random.get_state())
    assert presentation["outcome"] == "admitted_mutation"
    assert presentation["receipt_integrity_valid"] is True
    assert presentation["ui_authority"] is False
    assert presentation["replay_input"] is False
    assert presentation["checkpoint_state"] is False
    assert presentation["restore_performed"] is False
    assert presentation["mutation_executed"] is False
    assert "receipt" not in presentation
    assert "before_snapshot" not in presentation
    presentation["gene_counts"]["parent"] = 999
    assert present_worldbridge_respawn_diagnostic_receipt(receipt)["gene_counts"]["parent"] != 999


def test_rejected_receipt_preserves_read_only_no_mutation_facts() -> None:
    _, _, _, receipt = _sources(0.0)
    presentation = present_worldbridge_respawn_diagnostic_receipt(receipt)
    assert presentation["outcome"] == "rejected_no_mutation"
    assert presentation["admitted"] is False
    assert presentation["ordered_steps"] == ["decision"]
    assert presentation["mutation_stream_consumed"] is False
    assert validate_worldbridge_respawn_diagnostic_presentation(presentation, receipt=receipt) == {"valid": True, "errors": []}


def test_mapping_and_canonical_receipt_bytes_round_trip() -> None:
    _, _, _, receipt = _sources()
    presentation = present_worldbridge_respawn_diagnostic_receipt(receipt)
    encoded = encode_worldbridge_respawn_diagnostic_presentation(presentation)
    assert len(encoded) <= MAX_PRESENTATION_BYTES
    assert decode_worldbridge_respawn_diagnostic_presentation(encoded) == presentation
    with pytest.raises(ValueError, match="canonical"):
        decode_worldbridge_respawn_diagnostic_presentation(
            json.dumps(presentation, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        )


def test_raw_artifact_inspection_and_projection_are_rejected() -> None:
    artifact, inspection, projection, _ = _sources()
    for value in (artifact, inspection, projection):
        with pytest.raises(ValueError):
            present_worldbridge_respawn_diagnostic_receipt(value)


def test_semantic_overclaim_and_source_receipt_parity_mismatch_fail_closed() -> None:
    _, _, _, receipt = _sources()
    presentation = present_worldbridge_respawn_diagnostic_receipt(receipt)
    overclaim = copy.deepcopy(presentation)
    overclaim["ui_authority"] = True
    overclaim["presentation_digest"] = _presentation_digest(overclaim)
    validation = validate_worldbridge_respawn_diagnostic_presentation(overclaim)
    assert validation["valid"] is False
    assert "ui_authority_mismatch" in validation["errors"]

    mismatched = copy.deepcopy(presentation)
    mismatched["gene_counts"]["parent"] += 1
    mismatched["presentation_digest"] = _presentation_digest(mismatched)
    assert validate_worldbridge_respawn_diagnostic_presentation(mismatched)["valid"] is True
    validation = validate_worldbridge_respawn_diagnostic_presentation(mismatched, receipt=receipt)
    assert validation["valid"] is False
    assert "receipt_parity_gene_counts_mismatch" in validation["errors"]


def test_source_identity_mismatch_and_oversized_presentation_fail_closed() -> None:
    _, _, _, receipt = _sources()
    _, _, _, other_receipt = _sources(context_id="e230-other")
    presentation = present_worldbridge_respawn_diagnostic_receipt(receipt)
    validation = validate_worldbridge_respawn_diagnostic_presentation(presentation, receipt=other_receipt)
    assert validation["valid"] is False
    assert "receipt_parity_source_receipt_digest_mismatch" in validation["errors"]

    oversized = copy.deepcopy(presentation)
    oversized["source_artifact_id"] = "x" * MAX_PRESENTATION_BYTES
    oversized["presentation_digest"] = _presentation_digest(oversized)
    validation = validate_worldbridge_respawn_diagnostic_presentation(oversized)
    assert validation["valid"] is False
    assert "presentation_oversized" in validation["errors"]
    with pytest.raises(ValueError, match="presentation_oversized"):
        encode_worldbridge_respawn_diagnostic_presentation(oversized)


def test_contract_and_runtime_status_remain_opt_in_dual_and_not_default_ready() -> None:
    contract = build_worldbridge_respawn_diagnostic_presentation_contract()
    assert contract["contract_valid"] is True
    assert contract["round_trip_equal"] is True
    assert contract["receipt_consumer_only"] is True
    assert contract["accepts_raw_artifact"] is False
    assert contract["accepts_inspection"] is False
    assert contract["accepts_projection"] is False
    assert contract["ui_authority"] is False
    status = build_runtime_worldbridge_status()
    assert status["opt_in_respawn_diagnostic_presentation_contract"] == contract
    assert "respawn_diagnostic_presentation_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["default_ready"] is False
