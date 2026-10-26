# -*- coding: utf-8 -*-
"""Focused E256 portable witness chain deterministic attestation coverage."""
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
    CONTRACT_KEY,
    E255_MODULE,
    MODULE_ID,
    REQUIRED_SOURCE_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract,
)
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

_RUNTIME = Path(__file__).resolve().parents[1] / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _e256_inputs() -> tuple[bytes, bytes, dict[str, str]]:
    status_path = _RUNTIME / "core/VitaLoom/simulation/runtime_worldbridge_status.py"
    status = status_path.read_text(encoding="utf-8-sig")
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
        {
            E250_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_audit.py").read_text(encoding="utf-8-sig"),
            STATUS_MODULE: status,
        },
    )
    e251_bytes = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(e251)
    e251_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract())
    e252_sources = {
        E252_UNITS[0]: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_audit.py").read_text(encoding="utf-8-sig"),
        E252_UNITS[1]: status,
    }
    corpus: list[bytes] = []
    for suffix in ("", "\n"):
        record = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(
            e251_bytes,
            e251_contract,
            {**e252_sources, E252_UNITS[1]: status + suffix},
            E252_UNITS,
        )
        corpus.append(encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(record))
    corpus.sort(key=lambda item: json.loads(item)["audit_digest"])
    e252_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract())
    e253_policy = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_policy())
    e253 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(
        corpus,
        e252_contract,
        e253_policy,
        {
            E253_UNITS[0]: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit.py").read_text(encoding="utf-8-sig"),
            E253_UNITS[1]: status,
        },
        E253_UNITS,
    )
    e253_bytes = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit(e253)
    e253_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract())
    e254 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability(
        e253_bytes,
        e253_contract,
        e253_policy,
        e252_contract,
        corpus,
        {
            E253_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit.py").read_text(encoding="utf-8-sig"),
            STATUS_MODULE: status,
        },
        E254_UNITS,
    )
    e254_bytes = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit(e254)
    e254_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract())
    e255 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness(
        e254_bytes,
        e254_contract,
        e253_bytes,
        e253_contract,
        e253_policy,
        e252_contract,
        corpus,
        {
            E254_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit.py").read_text(encoding="utf-8-sig"),
            STATUS_MODULE: status,
        },
        E255_UNITS,
    )
    return (
        encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit(e255),
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit_contract()),
        {
            E255_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit.py").read_text(encoding="utf-8-sig"),
            STATUS_MODULE: status,
        },
    )


def _audit() -> dict[str, object]:
    return audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation(*_e256_inputs(), REQUIRED_SOURCE_UNITS)


def test_portable_witness_chain_attestation_is_deterministic_and_registered() -> None:
    inputs = _e256_inputs()
    first = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation(*inputs, REQUIRED_SOURCE_UNITS)
    second = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation(*inputs, REQUIRED_SOURCE_UNITS)
    first_bytes = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(first)
    assert first_bytes == encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(second)
    assert decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(first_bytes) == first
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(first) == {"valid": True, "errors": []}
    assert first["deterministic_attestation_valid"] is True
    assert first["portable_witness_chain_attestation_valid"] is True
    assert first["e255_audit_digest"] == first["component_digests"]["e255_audit"]
    contract = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract()
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract(contract) == {"valid": True, "errors": []}
    status = build_runtime_worldbridge_status()
    assert status[CONTRACT_KEY] == contract
    assert MODULE_ID in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False


def test_portable_witness_chain_attestation_rejects_contract_nested_and_order_tampering() -> None:
    e255_bytes, e255_contract, sources = _e256_inputs()
    with pytest.raises(ValueError, match="source order drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation(e255_bytes, e255_contract, sources, tuple(reversed(REQUIRED_SOURCE_UNITS)))
    changed_contract = json.loads(e255_contract)
    changed_contract["schema_version"] = 2
    with pytest.raises(ValueError, match="E255 contract drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation(e255_bytes, _canonical(changed_contract), sources, REQUIRED_SOURCE_UNITS)
    stale_e255 = json.loads(e255_bytes)
    stale_e255["e254_audit_digest"] = "0" * 64
    stale_without_digest = dict(stale_e255)
    stale_without_digest.pop("audit_digest")
    stale_e255["audit_digest"] = hashlib.sha256(_canonical(stale_without_digest)).hexdigest()
    with pytest.raises(ValueError, match="E255 component linkage drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation(_canonical(stale_e255), e255_contract, sources, REQUIRED_SOURCE_UNITS)


def test_portable_witness_chain_attestation_rejects_source_result_and_payload_tampering() -> None:
    e255_bytes, e255_contract, sources = _e256_inputs()
    forbidden = dict(sources)
    forbidden[E255_MODULE] += "\nimport subprocess\n"
    with pytest.raises(ValueError, match="source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation(e255_bytes, e255_contract, forbidden, REQUIRED_SOURCE_UNITS)
    drifted_status = dict(sources)
    drifted_status[STATUS_MODULE] = drifted_status[STATUS_MODULE].replace(CONTRACT_KEY, "contract_key_drift", 1)
    with pytest.raises(ValueError, match="source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation(e255_bytes, e255_contract, drifted_status, REQUIRED_SOURCE_UNITS)
    tampered = copy.deepcopy(_audit())
    tampered["portable_witness_chain_attestation_digest"] = "0" * 64
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(tampered)["valid"] is False
    with pytest.raises(ValueError, match="invalid deterministic attestation"):
        encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(tampered)
    canonical = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(_audit())
    with pytest.raises(ValueError, match="non-canonical"):
        decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(json.dumps(json.loads(canonical), indent=2).encode())
    duplicate_key_payload = b'{"audit_digest":"x","audit_digest":"x"}'
    with pytest.raises(ValueError, match="invalid canonical"):
        decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(duplicate_key_payload)
