# -*- coding: utf-8 -*-
"""E232 tests for the final in-memory diagnostic export audit sink."""
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
from core.Lotucosm.runtime.world_bridge_named_stream_adapter import run_worldbridge_named_stream_sr_respawn_handoff
from core.Lotucosm.runtime.world_bridge_respawn_artifact_diagnostics import project_worldbridge_respawn_artifact_inspection
from core.Lotucosm.runtime.world_bridge_respawn_artifact_inspection import inspect_worldbridge_respawn_two_stream_artifact
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_consumer import consume_worldbridge_respawn_diagnostic_pair
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_export import export_worldbridge_respawn_diagnostic_presentation
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_export_audit import (
    MAX_AUDIT_BYTES,
    _audit_digest,
    audit_worldbridge_respawn_diagnostic_export,
    build_worldbridge_respawn_diagnostic_export_audit_contract,
    decode_worldbridge_respawn_diagnostic_export_audit,
    encode_worldbridge_respawn_diagnostic_export_audit,
    validate_worldbridge_respawn_diagnostic_export_audit,
)
from core.Lotucosm.runtime.world_bridge_respawn_diagnostic_presentation import present_worldbridge_respawn_diagnostic_receipt
from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import build_worldbridge_respawn_two_stream_artifact
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _numpy_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def _sources(probability: float = 1.0, context_id: str = "e232-context") -> tuple[dict[str, object], ...]:
    context = create_worldbridge_deterministic_randomness_context(context_id, "e232-seed")
    register_worldbridge_deterministic_random_stream(context, "sr.war.respawn.decision", "python_random")
    register_worldbridge_deterministic_random_stream(context, "sr.war.respawn.mind", "python_random")
    handoff = run_worldbridge_named_stream_sr_respawn_handoff(context, "sr.war.respawn.decision", "sr.war.respawn.mind", {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3}, 0.25, probability)
    artifact = build_worldbridge_respawn_two_stream_artifact(handoff, artifact_id=f"{context_id}-artifact")
    inspection = inspect_worldbridge_respawn_two_stream_artifact(artifact)
    projection = project_worldbridge_respawn_artifact_inspection(inspection)
    receipt = consume_worldbridge_respawn_diagnostic_pair(inspection, projection)
    presentation = present_worldbridge_respawn_diagnostic_receipt(receipt)
    export_record = export_worldbridge_respawn_diagnostic_presentation(presentation)
    audit = audit_worldbridge_respawn_diagnostic_export(export_record)
    return artifact, inspection, projection, receipt, presentation, export_record, audit


def test_admitted_audit_is_copy_isolated_read_only_and_no_io() -> None:
    *_, export_record, audit = _sources()
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    assert audit["outcome"] == "admitted_mutation"
    assert audit["export_integrity_valid"] is True
    assert audit["audit_persisted"] is False
    assert audit["file_written"] is False
    assert audit["network_transmitted"] is False
    assert audit["ui_authority"] is False
    assert random.getstate() == python_before
    assert _numpy_equal(numpy_before, np.random.get_state())
    audit["gene_counts"]["parent"] = 999
    assert audit_worldbridge_respawn_diagnostic_export(export_record)["gene_counts"]["parent"] != 999


def test_rejected_export_preserves_no_mutation_audit_facts() -> None:
    *_, export_record, audit = _sources(0.0)
    assert audit["outcome"] == "rejected_no_mutation"
    assert audit["admitted"] is False
    assert audit["ordered_steps"] == ["decision"]
    assert audit["mutation_stream_consumed"] is False
    assert validate_worldbridge_respawn_diagnostic_export_audit(audit, export_record=export_record) == {"valid": True, "errors": []}


def test_mapping_and_canonical_audit_bytes_round_trip() -> None:
    *_, audit = _sources()
    encoded = encode_worldbridge_respawn_diagnostic_export_audit(audit)
    assert len(encoded) <= MAX_AUDIT_BYTES
    assert decode_worldbridge_respawn_diagnostic_export_audit(encoded) == audit
    with pytest.raises(ValueError, match="canonical"):
        decode_worldbridge_respawn_diagnostic_export_audit(json.dumps(audit, sort_keys=True, indent=2).encode("utf-8"))


def test_all_pre_audit_sources_are_rejected() -> None:
    artifact, inspection, projection, receipt, presentation, export_record, _ = _sources()
    for value in (artifact, inspection, projection, receipt, presentation):
        with pytest.raises(ValueError):
            audit_worldbridge_respawn_diagnostic_export(value)
    assert validate_worldbridge_respawn_diagnostic_export_audit(export_record)["valid"] is False


def test_semantic_overclaim_and_export_parity_mismatch_fail_closed() -> None:
    *_, export_record, audit = _sources()
    overclaim = copy.deepcopy(audit)
    overclaim["network_transmitted"] = True
    overclaim["audit_digest"] = _audit_digest(overclaim)
    validation = validate_worldbridge_respawn_diagnostic_export_audit(overclaim)
    assert validation["valid"] is False
    assert "network_transmitted_mismatch" in validation["errors"]

    mismatched = copy.deepcopy(audit)
    mismatched["gene_counts"]["parent"] += 1
    mismatched["audit_digest"] = _audit_digest(mismatched)
    assert validate_worldbridge_respawn_diagnostic_export_audit(mismatched)["valid"] is True
    validation = validate_worldbridge_respawn_diagnostic_export_audit(mismatched, export_record=export_record)
    assert validation["valid"] is False
    assert "export_parity_gene_counts_mismatch" in validation["errors"]


def test_source_identity_mismatch_and_oversized_audit_fail_closed() -> None:
    *_, export_record, audit = _sources()
    *_, other_export, _ = _sources(context_id="e232-other")
    validation = validate_worldbridge_respawn_diagnostic_export_audit(audit, export_record=other_export)
    assert validation["valid"] is False
    assert "export_parity_source_export_digest_mismatch" in validation["errors"]

    oversized = copy.deepcopy(audit)
    oversized["source_artifact_id"] = "x" * MAX_AUDIT_BYTES
    oversized["audit_digest"] = _audit_digest(oversized)
    validation = validate_worldbridge_respawn_diagnostic_export_audit(oversized)
    assert validation["valid"] is False
    assert "audit_oversized" in validation["errors"]
    with pytest.raises(ValueError, match="audit_oversized"):
        encode_worldbridge_respawn_diagnostic_export_audit(oversized)


def test_contract_and_runtime_status_remain_opt_in_dual_and_not_default_ready() -> None:
    contract = build_worldbridge_respawn_diagnostic_export_audit_contract()
    assert contract["contract_valid"] is True
    assert contract["round_trip_equal"] is True
    assert contract["export_consumer_only"] is True
    assert contract["accepts_raw_receipt"] is False
    assert contract["accepts_raw_artifact"] is False
    assert contract["accepts_inspection"] is False
    assert contract["accepts_projection"] is False
    assert contract["accepts_presentation"] is False
    assert contract["audit_persisted"] is False
    assert contract["file_written"] is False
    assert contract["network_transmitted"] is False
    status = build_runtime_worldbridge_status()
    assert status["opt_in_respawn_diagnostic_export_audit_contract"] == contract
    assert "respawn_diagnostic_export_audit_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["default_ready"] is False