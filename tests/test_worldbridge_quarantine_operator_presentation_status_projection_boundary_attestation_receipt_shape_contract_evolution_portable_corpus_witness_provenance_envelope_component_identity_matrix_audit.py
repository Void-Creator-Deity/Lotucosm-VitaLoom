# -*- coding: utf-8 -*-
"""Focused E261 component-identity-matrix audit coverage."""
from __future__ import annotations

import json
import pytest

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit import (
    REQUIRED_SOURCE_UNITS as E260_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope as audit_e260,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit_contract as build_e260_contract,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit as encode_e260,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit import (
    CONTRACT_KEY, E260_MODULE, MODULE_ID, REQUIRED_SOURCE_UNITS, STATIC_POLICIES,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix as audit_e261,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit_contract as build_contract,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_policy as build_policy,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit as decode_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit as encode_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit as validate_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit_contract as validate_contract,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_policy as validate_policy,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status
from test_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit import _RUNTIME, _canonical, _e260_inputs

AUTHORITY = _RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit.py"


def _e261_inputs() -> tuple[list[bytes], bytes, bytes, dict[str, str]]:
    records, e260_contract, e260_policy, e260_sources = _e260_inputs()
    corpus: list[bytes] = []
    for suffix in ("", "\n"):
        record = audit_e260(
            records, e260_contract, e260_policy,
            {**e260_sources, "core.VitaLoom.simulation.runtime_worldbridge_status": e260_sources["core.VitaLoom.simulation.runtime_worldbridge_status"] + suffix},
            E260_UNITS,
        )
        corpus.append(encode_e260(record))
    corpus.sort(key=lambda item: json.loads(item)["audit_digest"])
    return (
        corpus,
        _canonical(build_e260_contract()),
        _canonical(build_policy()),
        {
            E260_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit.py").read_text(encoding="utf-8-sig"),
            "core.VitaLoom.simulation.runtime_worldbridge_status": (_RUNTIME / "core/VitaLoom/simulation/runtime_worldbridge_status.py").read_text(encoding="utf-8-sig"),
        },
    )


def _audit() -> dict[str, object]:
    return audit_e261(*_e261_inputs(), REQUIRED_SOURCE_UNITS)


def _must_reject(*args: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        audit_e261(*args)


def test_component_identity_matrix_is_deterministic_registered_and_read_only() -> None:
    inputs = _e261_inputs()
    first = audit_e261(*inputs, REQUIRED_SOURCE_UNITS)
    second = audit_e261(*inputs, REQUIRED_SOURCE_UNITS)
    encoded = encode_audit(first)
    assert first == second
    assert encoded == encode_audit(second)
    assert decode_audit(encoded) == first
    assert validate_audit(first) == {"valid": True, "errors": []}
    assert first["corpus_size"] == 2
    assert first["component_identity_matrix_valid"] is True
    assert len(first["component_identity_matrix"]) == 2
    assert [item["audit_digest"] for item in first["component_identity_matrix"]] == first["corpus_order"]
    assert len(set(first["e260_source_unit_digests"])) == 2
    status = build_runtime_worldbridge_status()
    assert status[CONTRACT_KEY] == build_contract()
    assert MODULE_ID in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False
    assert all(first[key] is expected for key, expected in STATIC_POLICIES.items())


def test_component_identity_matrix_rejects_corpus_contract_policy_and_record_drift() -> None:
    records, contract, policy, sources = _e261_inputs()
    _must_reject(list(reversed(records)), contract, policy, sources, REQUIRED_SOURCE_UNITS)
    _must_reject([records[0], records[0]], contract, policy, sources, REQUIRED_SOURCE_UNITS)
    _must_reject(records[:1], contract, policy, sources, REQUIRED_SOURCE_UNITS)
    stale = json.loads(contract)
    stale["schema_version"] = 2
    _must_reject(records, _canonical(stale), policy, sources, REQUIRED_SOURCE_UNITS)
    stale = json.loads(policy)
    stale["migration_admitted"] = True
    _must_reject(records, contract, _canonical(stale), sources, REQUIRED_SOURCE_UNITS)
    record = json.loads(records[0])
    record["receipt_shape_digest"] = "0" * 64
    record["audit_digest"] = "0" * 64
    _must_reject([_canonical(record), records[1]], contract, policy, sources, REQUIRED_SOURCE_UNITS)
    record = json.loads(records[0])
    record["contract_evolution_policy_digest"] = "0" * 64
    record["audit_digest"] = "0" * 64
    _must_reject([_canonical(record), records[1]], contract, policy, sources, REQUIRED_SOURCE_UNITS)


def test_component_identity_matrix_rejects_source_result_and_payload_tampering() -> None:
    records, contract, policy, sources = _e261_inputs()
    forbidden = dict(sources)
    forbidden[E260_MODULE] += "\nimport subprocess\n"
    _must_reject(records, contract, policy, forbidden, REQUIRED_SOURCE_UNITS)
    missing = dict(sources)
    missing[E260_MODULE] = missing[E260_MODULE].replace(
        "def decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit",
        "def missing_decode",
        1,
    )
    _must_reject(records, contract, policy, missing, REQUIRED_SOURCE_UNITS)
    result = _audit()
    result["component_identity_matrix_digest"] = "0" * 64
    assert validate_audit(result)["valid"] is False
    payload = encode_audit(_audit())
    pretty = b"{\n" + payload[1:-1].replace(b",", b",\n") + b"\n}"
    with pytest.raises(ValueError):
        decode_audit(pretty)
    duplicate = payload.replace(b'"schema_version":1', b'"schema_version":1,"schema_version":1', 1)
    with pytest.raises(ValueError):
        decode_audit(duplicate)
    source = AUTHORITY.read_text(encoding="utf-8-sig")
    for token in ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle", "subprocess", "multiprocessing"):
        assert token not in source
    assert validate_contract(build_contract()) == {"valid": True, "errors": []}
    assert validate_policy(build_policy()) == {"valid": True, "errors": []}




