# -*- coding: utf-8 -*-
"""Focused E258 receipt-shape corpus contract-evolution coverage."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit import (
    E256_MODULE,
    REQUIRED_SOURCE_UNITS as E257_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit import (
    CONTRACT_KEY,
    E257_MODULE,
    MODULE_ID,
    REQUIRED_SOURCE_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_contract,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_policy,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_contract,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_policy,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status
from test_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit import (
    _RUNTIME,
    _canonical,
    _e257_inputs,
)

_AUTHORITY = _RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit.py"


def _e258_inputs() -> tuple[list[bytes], bytes, bytes, dict[str, str]]:
    e256_records, e256_contract, e257_sources = _e257_inputs()
    records: list[bytes] = []
    for suffix in ("", "\n"):
        record = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility(
            e256_records,
            e256_contract,
            {**e257_sources, "core.VitaLoom.simulation.runtime_worldbridge_status": e257_sources["core.VitaLoom.simulation.runtime_worldbridge_status"] + suffix},
            E257_UNITS,
        )
        records.append(encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(record))
    records.sort(key=lambda item: json.loads(item)["audit_digest"])
    return (
        records,
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract()),
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_policy()),
        {
            E257_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit.py").read_text(encoding="utf-8-sig"),
            "core.VitaLoom.simulation.runtime_worldbridge_status": e257_sources["core.VitaLoom.simulation.runtime_worldbridge_status"],
        },
    )


def _audit() -> dict[str, object]:
    return audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution(*_e258_inputs(), REQUIRED_SOURCE_UNITS)


def test_receipt_shape_contract_evolution_is_deterministic_and_registered() -> None:
    first = _audit()
    second = _audit()
    encoded = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(first)
    assert encoded == encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(second)
    assert decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(encoded) == first
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(first) == {"valid": True, "errors": []}
    assert first["corpus_size"] == 2
    assert first["receipt_shape_closure_valid"] is True
    assert first["e257_source_unit_digests"][0] != first["e257_source_unit_digests"][1]
    contract = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_contract()
    policy = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_policy()
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_contract(contract) == {"valid": True, "errors": []}
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_policy(policy) == {"valid": True, "errors": []}
    status = build_runtime_worldbridge_status()
    assert status[CONTRACT_KEY] == contract
    assert MODULE_ID in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False


def test_receipt_shape_contract_evolution_rejects_corpus_contract_policy_and_record_tampering() -> None:
    records, e257_contract, policy, sources = _e258_inputs()
    with pytest.raises(ValueError, match="corpus order drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution(list(reversed(records)), e257_contract, policy, sources, REQUIRED_SOURCE_UNITS)
    with pytest.raises(ValueError, match="duplicate receipt-shape"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution([records[0], records[0]], e257_contract, policy, sources, REQUIRED_SOURCE_UNITS)
    with pytest.raises(ValueError, match="at least two"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution(records[:1], e257_contract, policy, sources, REQUIRED_SOURCE_UNITS)
    drifted_contract = json.loads(e257_contract)
    drifted_contract["schema_version"] = 2
    with pytest.raises(ValueError, match="E257 contract drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution(records, _canonical(drifted_contract), policy, sources, REQUIRED_SOURCE_UNITS)
    drifted_policy = json.loads(policy)
    drifted_policy["migration_admitted"] = True
    with pytest.raises(ValueError, match="policy drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution(records, e257_contract, _canonical(drifted_policy), sources, REQUIRED_SOURCE_UNITS)
    stale = json.loads(records[0])
    stale["e256_contract_digest"] = "0" * 64
    stale_without_digest = dict(stale)
    stale_without_digest.pop("audit_digest")
    stale["audit_digest"] = hashlib.sha256(_canonical(stale_without_digest)).hexdigest()
    stale_records = sorted([_canonical(stale), records[1]], key=lambda item: json.loads(item)["audit_digest"])
    with pytest.raises(ValueError, match="stale E256 contract"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution(stale_records, e257_contract, policy, sources, REQUIRED_SOURCE_UNITS)


def test_receipt_shape_contract_evolution_rejects_source_result_and_payload_tampering() -> None:
    records, e257_contract, policy, sources = _e258_inputs()
    forbidden = dict(sources)
    forbidden[E257_MODULE] += "\nimport subprocess\n"
    with pytest.raises(ValueError, match="source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution(records, e257_contract, policy, forbidden, REQUIRED_SOURCE_UNITS)
    drifted_status = dict(sources)
    drifted_status["core.VitaLoom.simulation.runtime_worldbridge_status"] = drifted_status["core.VitaLoom.simulation.runtime_worldbridge_status"].replace(CONTRACT_KEY, "contract_key_drift", 1)
    with pytest.raises(ValueError, match="source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution(records, e257_contract, policy, drifted_status, REQUIRED_SOURCE_UNITS)
    tampered = copy.deepcopy(_audit())
    tampered["receipt_shape_digest"] = "0" * 64
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(tampered)["valid"] is False
    with pytest.raises(ValueError, match="invalid receipt-shape"):
        encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(tampered)
    canonical = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(_audit())
    with pytest.raises(ValueError, match="non-canonical"):
        decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(json.dumps(json.loads(canonical), indent=2).encode())
    with pytest.raises(ValueError, match="invalid canonical"):
        decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(b'{"audit_digest":"x","audit_digest":"x"}')
    authority_source = _AUTHORITY.read_text(encoding="utf-8-sig")
    for token in ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle", "subprocess", "multiprocessing"):
        assert token not in authority_source
