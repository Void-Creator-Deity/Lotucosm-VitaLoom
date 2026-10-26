# -*- coding: utf-8 -*-
"""Focused E257 attestation receipt-shape compatibility coverage."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_audit import (
    audit_worldbridge_quarantine_operator_presentation_status_projection,
    build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract,
    encode_worldbridge_quarantine_operator_presentation_status_projection_audit,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_audit import (
    E250_MODULE,
    STATUS_MODULE,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit import (
    REQUIRED_UNITS as E252_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit import (
    REQUIRED_SOURCE_UNITS as E253_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_policy,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit import (
    E253_MODULE,
    REQUIRED_SOURCE_UNITS as E254_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit import (
    E254_MODULE,
    REQUIRED_SOURCE_UNITS as E255_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit_contract,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit import (
    E255_MODULE,
    REQUIRED_SOURCE_UNITS as E256_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit import (
    CONTRACT_KEY,
    E256_MODULE,
    MODULE_ID,
    REQUIRED_SOURCE_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract,
)
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

_RUNTIME = Path(__file__).resolve().parents[1] / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
_AUTHORITY = _RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit.py"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _e255_inputs() -> tuple[bytes, bytes, dict[str, str]]:
    status = (_RUNTIME / "core/VitaLoom/simulation/runtime_worldbridge_status.py").read_text(encoding="utf-8-sig")
    e250 = audit_worldbridge_quarantine_operator_presentation_status_projection(
        reset_command_registry().run("runtime.worldbridge.status", {}),
        mcp_adapter.get_runtime_worldbridge_status(),
        {
            "core.VitaLoom.commands.runtime_commands": (_RUNTIME / "core/VitaLoom/commands/runtime_commands.py").read_text(encoding="utf-8-sig"),
            "core.VitaLoom.commands.mcp_adapter": (_RUNTIME / "core/VitaLoom/commands/mcp_adapter.py").read_text(encoding="utf-8-sig"),
            STATUS_MODULE: status,
        },
    )
    e251 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(
        encode_worldbridge_quarantine_operator_presentation_status_projection_audit(e250),
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract()),
        {E250_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_audit.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: status},
    )
    e251_bytes = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(e251)
    e251_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract())
    e252_sources = {E252_UNITS[0]: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_audit.py").read_text(encoding="utf-8-sig"), E252_UNITS[1]: status}
    corpus: list[bytes] = []
    for suffix in ("", "\n"):
        record = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(e251_bytes, e251_contract, {**e252_sources, E252_UNITS[1]: status + suffix}, E252_UNITS)
        corpus.append(encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(record))
    corpus.sort(key=lambda item: json.loads(item)["audit_digest"])
    e252_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract())
    e253_policy = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_policy())
    e253 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(
        corpus, e252_contract, e253_policy,
        {E253_UNITS[0]: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit.py").read_text(encoding="utf-8-sig"), E253_UNITS[1]: status}, E253_UNITS,
    )
    e253_bytes = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit(e253)
    e253_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract())
    e254 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability(
        e253_bytes, e253_contract, e253_policy, e252_contract, corpus,
        {E253_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: status}, E254_UNITS,
    )
    e254_bytes = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit(e254)
    e254_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract())
    e255 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness(
        e254_bytes, e254_contract, e253_bytes, e253_contract, e253_policy, e252_contract, corpus,
        {E254_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: status}, E255_UNITS,
    )
    return (
        encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit(e255),
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit_contract()),
        {E255_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: status},
    )


def _e257_inputs() -> tuple[list[bytes], bytes, dict[str, str]]:
    e255_bytes, e255_contract, e255_sources = _e255_inputs()
    records: list[bytes] = []
    for suffix in ("", "\n"):
        record = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation(
            e255_bytes, e255_contract, {**e255_sources, STATUS_MODULE: e255_sources[STATUS_MODULE] + suffix}, E256_UNITS,
        )
        records.append(encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(record))
    records.sort(key=lambda item: json.loads(item)["audit_digest"])
    return (
        records,
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract()),
        {E256_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: e255_sources[STATUS_MODULE]},
    )


def _audit() -> dict[str, object]:
    return audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility(*_e257_inputs(), REQUIRED_SOURCE_UNITS)


def test_attestation_receipt_shape_compatibility_is_deterministic_and_registered() -> None:
    first = _audit()
    second = _audit()
    first_bytes = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(first)
    assert first_bytes == encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(second)
    assert decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(first_bytes) == first
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(first) == {"valid": True, "errors": []}
    assert first["corpus_size"] == 2
    assert first["receipt_shape_compatibility_valid"] is True
    assert first["attestation_source_unit_digests"][0] != first["attestation_source_unit_digests"][1]
    contract = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract()
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract(contract) == {"valid": True, "errors": []}
    status = build_runtime_worldbridge_status()
    assert status[CONTRACT_KEY] == contract
    assert MODULE_ID in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False


def test_attestation_receipt_shape_compatibility_rejects_corpus_contract_and_record_tampering() -> None:
    records, e256_contract, sources = _e257_inputs()
    with pytest.raises(ValueError, match="corpus order drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility(list(reversed(records)), e256_contract, sources, REQUIRED_SOURCE_UNITS)
    with pytest.raises(ValueError, match="duplicate attestation"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility([records[0], records[0]], e256_contract, sources, REQUIRED_SOURCE_UNITS)
    with pytest.raises(ValueError, match="at least two"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility(records[:1], e256_contract, sources, REQUIRED_SOURCE_UNITS)
    drifted_contract = json.loads(e256_contract)
    drifted_contract["schema_version"] = 2
    with pytest.raises(ValueError, match="E256 contract drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility(records, _canonical(drifted_contract), sources, REQUIRED_SOURCE_UNITS)
    nested = json.loads(records[0])
    nested["component_digests"]["e255_audit"] = "0" * 64
    nested_without_digest = dict(nested)
    nested_without_digest.pop("audit_digest")
    nested["audit_digest"] = hashlib.sha256(_canonical(nested_without_digest)).hexdigest()
    with pytest.raises(ValueError):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility([_canonical(nested), records[1]], e256_contract, sources, REQUIRED_SOURCE_UNITS)
    divergent = json.loads(records[0])
    divergent["read_only"] = False
    divergent_without_digest = dict(divergent)
    divergent_without_digest.pop("audit_digest")
    divergent["audit_digest"] = hashlib.sha256(_canonical(divergent_without_digest)).hexdigest()
    with pytest.raises(ValueError):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility([_canonical(divergent), records[1]], e256_contract, sources, REQUIRED_SOURCE_UNITS)


def test_attestation_receipt_shape_compatibility_rejects_source_result_and_payload_tampering() -> None:
    records, e256_contract, sources = _e257_inputs()
    forbidden = dict(sources)
    forbidden[E256_MODULE] += "\nimport subprocess\n"
    with pytest.raises(ValueError, match="source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility(records, e256_contract, forbidden, REQUIRED_SOURCE_UNITS)
    drifted_status = dict(sources)
    drifted_status[STATUS_MODULE] = drifted_status[STATUS_MODULE].replace(CONTRACT_KEY, "contract_key_drift", 1)
    with pytest.raises(ValueError, match="source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility(records, e256_contract, drifted_status, REQUIRED_SOURCE_UNITS)
    tampered = copy.deepcopy(_audit())
    tampered["receipt_shape_digest"] = "0" * 64
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(tampered)["valid"] is False
    with pytest.raises(ValueError, match="invalid receipt shape"):
        encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(tampered)
    canonical = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(_audit())
    with pytest.raises(ValueError, match="non-canonical"):
        decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(json.dumps(json.loads(canonical), indent=2).encode())
    with pytest.raises(ValueError, match="invalid canonical"):
        decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(b'{"audit_digest":"x","audit_digest":"x"}')
    authority_source = _AUTHORITY.read_text(encoding="utf-8-sig")
    for token in ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle", "subprocess", "multiprocessing"):
        assert token not in authority_source
