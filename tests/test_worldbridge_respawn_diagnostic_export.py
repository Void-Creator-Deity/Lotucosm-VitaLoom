# -*- coding: utf-8 -*-
"""E231 tests for presentation-only in-memory diagnostic exports."""
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
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_export import (
    MAX_EXPORT_BYTES,
    _export_digest,
    build_worldbridge_respawn_diagnostic_export_contract,
    decode_worldbridge_respawn_diagnostic_export_record,
    encode_worldbridge_respawn_diagnostic_export_record,
    export_worldbridge_respawn_diagnostic_presentation,
    validate_worldbridge_respawn_diagnostic_export_record,
)
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_presentation import (
    present_worldbridge_respawn_diagnostic_receipt,
)
from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import (
    build_worldbridge_respawn_two_stream_artifact,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _numpy_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def _sources(
    probability: float = 1.0,
    context_id: str = "e231-context",
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    context = create_worldbridge_deterministic_randomness_context(context_id, "e231-seed")
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
    presentation = present_worldbridge_respawn_diagnostic_receipt(receipt)
    return artifact, inspection, projection, receipt, presentation


def test_admitted_presentation_exports_copy_isolated_in_memory_record() -> None:
    _, _, _, _, presentation = _sources()
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    export_record = export_worldbridge_respawn_diagnostic_presentation(presentation)
    assert random.getstate() == python_before
    assert _numpy_equal(numpy_before, np.random.get_state())
    assert export_record["outcome"] == "admitted_mutation"
    assert export_record["presentation_integrity_valid"] is True
    assert export_record["export_persisted"] is False
    assert export_record["file_written"] is False
    assert export_record["network_transmitted"] is False
    assert export_record["ui_authority"] is False
    assert "presentation" not in export_record
    assert "snapshot" not in export_record
    export_record["gene_counts"]["parent"] = 999
    assert export_worldbridge_respawn_diagnostic_presentation(presentation)["gene_counts"]["parent"] != 999


def test_rejected_presentation_preserves_read_only_no_mutation_facts() -> None:
    _, _, _, _, presentation = _sources(0.0)
    export_record = export_worldbridge_respawn_diagnostic_presentation(presentation)
    assert export_record["outcome"] == "rejected_no_mutation"
    assert export_record["admitted"] is False
    assert export_record["ordered_steps"] == ["decision"]
    assert export_record["mutation_stream_consumed"] is False
    assert validate_worldbridge_respawn_diagnostic_export_record(export_record, presentation=presentation) == {"valid": True, "errors": []}


def test_mapping_and_canonical_presentation_bytes_round_trip() -> None:
    _, _, _, _, presentation = _sources()
    export_record = export_worldbridge_respawn_diagnostic_presentation(presentation)
    encoded = encode_worldbridge_respawn_diagnostic_export_record(export_record)
    assert len(encoded) <= MAX_EXPORT_BYTES
    assert decode_worldbridge_respawn_diagnostic_export_record(encoded) == export_record
    with pytest.raises(ValueError, match="canonical"):
        decode_worldbridge_respawn_diagnostic_export_record(
            json.dumps(export_record, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        )


def test_raw_artifact_inspection_projection_and_receipt_are_rejected() -> None:
    artifact, inspection, projection, receipt, _ = _sources()
    for value in (artifact, inspection, projection, receipt):
        with pytest.raises(ValueError):
            export_worldbridge_respawn_diagnostic_presentation(value)


def test_semantic_overclaim_and_source_presentation_parity_mismatch_fail_closed() -> None:
    _, _, _, _, presentation = _sources()
    export_record = export_worldbridge_respawn_diagnostic_presentation(presentation)
    overclaim = copy.deepcopy(export_record)
    overclaim["file_written"] = True
    overclaim["export_digest"] = _export_digest(overclaim)
    validation = validate_worldbridge_respawn_diagnostic_export_record(overclaim)
    assert validation["valid"] is False
    assert "file_written_mismatch" in validation["errors"]

    mismatched = copy.deepcopy(export_record)
    mismatched["gene_counts"]["parent"] += 1
    mismatched["export_digest"] = _export_digest(mismatched)
    assert validate_worldbridge_respawn_diagnostic_export_record(mismatched)["valid"] is True
    validation = validate_worldbridge_respawn_diagnostic_export_record(mismatched, presentation=presentation)
    assert validation["valid"] is False
    assert "presentation_parity_gene_counts_mismatch" in validation["errors"]


def test_source_identity_mismatch_and_oversized_export_fail_closed() -> None:
    _, _, _, _, presentation = _sources()
    _, _, _, _, other_presentation = _sources(context_id="e231-other")
    export_record = export_worldbridge_respawn_diagnostic_presentation(presentation)
    validation = validate_worldbridge_respawn_diagnostic_export_record(export_record, presentation=other_presentation)
    assert validation["valid"] is False
    assert "presentation_parity_source_presentation_digest_mismatch" in validation["errors"]

    oversized = copy.deepcopy(export_record)
    oversized["source_artifact_id"] = "x" * MAX_EXPORT_BYTES
    oversized["export_digest"] = _export_digest(oversized)
    validation = validate_worldbridge_respawn_diagnostic_export_record(oversized)
    assert validation["valid"] is False
    assert "export_record_oversized" in validation["errors"]
    with pytest.raises(ValueError, match="export_record_oversized"):
        encode_worldbridge_respawn_diagnostic_export_record(oversized)


def test_contract_and_runtime_status_remain_opt_in_dual_and_not_default_ready() -> None:
    contract = build_worldbridge_respawn_diagnostic_export_contract()
    assert contract["contract_valid"] is True
    assert contract["round_trip_equal"] is True
    assert contract["presentation_consumer_only"] is True
    assert contract["accepts_raw_receipt"] is False
    assert contract["accepts_raw_artifact"] is False
    assert contract["accepts_inspection"] is False
    assert contract["accepts_projection"] is False
    assert contract["writes_files"] is False
    assert contract["transmits_network"] is False
    assert contract["ui_authority"] is False
    status = build_runtime_worldbridge_status()
    assert status["opt_in_respawn_diagnostic_export_contract"] == contract
    assert "respawn_diagnostic_export_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["default_ready"] is False
