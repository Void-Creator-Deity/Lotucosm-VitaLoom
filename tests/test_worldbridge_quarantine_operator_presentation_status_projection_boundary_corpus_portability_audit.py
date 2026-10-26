# -*- coding: utf-8 -*-
"""Focused E254 corpus portability integrity coverage."""
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
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_policy,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit import (
    CONTRACT_KEY,
    E253_MODULE,
    MODULE_ID,
    REQUIRED_SOURCE_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract,
)
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

_RUNTIME = Path(__file__).resolve().parents[1] / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _e254_inputs() -> tuple[bytes, bytes, bytes, bytes, list[bytes], dict[str, str]]:
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
        {E250_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_audit.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: status},
    )
    e251_bytes = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(e251)
    e251_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract())
    e252_sources = {E252_UNITS[0]: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_audit.py").read_text(encoding="utf-8-sig"), E252_UNITS[1]: status}
    corpus: list[bytes] = []
    for suffix in ("", "\n"):
        record = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(
            e251_bytes, e251_contract, {**e252_sources, E252_UNITS[1]: status + suffix}, E252_UNITS
        )
        corpus.append(encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(record))
    corpus.sort(key=lambda item: json.loads(item)["audit_digest"])
    e252_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract())
    e253_policy = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_policy())
    e253 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(
        corpus,
        e252_contract,
        e253_policy,
        {E253_UNITS[0]: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit.py").read_text(encoding="utf-8-sig"), E253_UNITS[1]: status},
        E253_UNITS,
    )
    return (
        encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit(e253),
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract()),
        e253_policy,
        e252_contract,
        corpus,
        {E253_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: status},
    )


def _audit() -> dict[str, object]:
    return audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability(*_e254_inputs(), REQUIRED_SOURCE_UNITS)


def test_corpus_portability_chain_is_deterministic_and_registered() -> None:
    inputs = _e254_inputs()
    first = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability(*inputs, REQUIRED_SOURCE_UNITS)
    second = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability(*inputs, REQUIRED_SOURCE_UNITS)
    first_bytes = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit(first)
    assert first_bytes == encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit(second)
    assert decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit(first_bytes) == first
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit(first) == {"valid": True, "errors": []}
    assert first["corpus_integrity_valid"] is True
    assert first["provenance_closure_valid"] is True
    assert first["fresh_session_portability_valid"] is True
    contract = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract()
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract(contract) == {"valid": True, "errors": []}
    status = build_runtime_worldbridge_status()
    assert status[CONTRACT_KEY] == contract
    assert MODULE_ID in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False


def test_corpus_portability_rejects_corpus_contract_policy_and_closure_tampering() -> None:
    e253_bytes, e253_contract, e253_policy, e252_contract, corpus, sources = _e254_inputs()
    with pytest.raises(ValueError, match="corpus order drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability(e253_bytes, e253_contract, e253_policy, e252_contract, list(reversed(corpus)), sources, REQUIRED_SOURCE_UNITS)
    with pytest.raises(ValueError, match="duplicate corpus record"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability(e253_bytes, e253_contract, e253_policy, e252_contract, [corpus[0], corpus[0]], sources, REQUIRED_SOURCE_UNITS)
    with pytest.raises(ValueError, match="at least two"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability(e253_bytes, e253_contract, e253_policy, e252_contract, [corpus[0]], sources, REQUIRED_SOURCE_UNITS)
    with pytest.raises(ValueError, match="non-canonical"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability(e253_bytes, json.dumps(json.loads(e253_contract), indent=2).encode(), e253_policy, e252_contract, corpus, sources, REQUIRED_SOURCE_UNITS)
    changed_policy = json.loads(e253_policy)
    changed_policy["migration_admitted"] = True
    with pytest.raises(ValueError, match="policy drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability(e253_bytes, e253_contract, _canonical(changed_policy), e252_contract, corpus, sources, REQUIRED_SOURCE_UNITS)
    stale = json.loads(e253_bytes)
    stale["corpus_size"] = 1
    stale_without_digest = dict(stale)
    stale_without_digest.pop("audit_digest")
    stale["audit_digest"] = hashlib.sha256(_canonical(stale_without_digest)).hexdigest()
    with pytest.raises(ValueError, match="invalid corpus audit"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability(_canonical(stale), e253_contract, e253_policy, e252_contract, corpus, sources, REQUIRED_SOURCE_UNITS)


def test_corpus_portability_rejects_source_and_result_tampering() -> None:
    e253_bytes, e253_contract, e253_policy, e252_contract, corpus, sources = _e254_inputs()
    forbidden = dict(sources)
    forbidden[E253_MODULE] += "\nimport subprocess\n"
    with pytest.raises(ValueError, match="source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability(e253_bytes, e253_contract, e253_policy, e252_contract, corpus, forbidden, REQUIRED_SOURCE_UNITS)
    drifted_status = dict(sources)
    drifted_status[REQUIRED_SOURCE_UNITS[1]] = drifted_status[REQUIRED_SOURCE_UNITS[1]].replace(CONTRACT_KEY, "contract_key_drift", 1)
    with pytest.raises(ValueError, match="source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability(e253_bytes, e253_contract, e253_policy, e252_contract, corpus, drifted_status, REQUIRED_SOURCE_UNITS)
    tampered = copy.deepcopy(_audit())
    tampered["fresh_session_portability_valid"] = False
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit(tampered)["valid"] is False
    with pytest.raises(ValueError, match="invalid corpus portability audit"):
        encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit(tampered)
