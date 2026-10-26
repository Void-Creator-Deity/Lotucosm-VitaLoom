# -*- coding: utf-8 -*-
"""Focused E253 coverage for ordered compatibility corpus and contract evolution."""
from __future__ import annotations

import copy
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
    E251_MODULE,
    REQUIRED_UNITS as E252_UNITS,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit import (
    CONTRACT_KEY,
    E252_MODULE,
    MODULE_ID,
    REQUIRED_SOURCE_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_policy,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract,
)
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

_RUNTIME = Path(__file__).resolve().parents[1] / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"


def _canonical(value: object, **kwargs: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), **kwargs).encode("utf-8")


def _e252_and_sources() -> tuple[list[bytes], bytes, bytes, dict[str, str]]:
    status_path = _RUNTIME / "core/VitaLoom/simulation/runtime_worldbridge_status.py"
    status = status_path.read_text(encoding="utf-8-sig")
    e250_sources = {
        "core.VitaLoom.commands.runtime_commands": (_RUNTIME / "core/VitaLoom/commands/runtime_commands.py").read_text(encoding="utf-8-sig"),
        "core.VitaLoom.commands.mcp_adapter": (_RUNTIME / "core/VitaLoom/commands/mcp_adapter.py").read_text(encoding="utf-8-sig"),
        STATUS_MODULE: status,
    }
    e250 = audit_worldbridge_quarantine_operator_presentation_status_projection(
        reset_command_registry().run("runtime.worldbridge.status", {}),
        mcp_adapter.get_runtime_worldbridge_status(),
        e250_sources,
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
    e252_source_base = {
        E252_UNITS[0]: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_audit.py").read_text(encoding="utf-8-sig"),
        E252_UNITS[1]: status,
    }
    e252_records: list[bytes] = []
    for suffix in ("", "\n"):
        e252 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(
            e251_bytes,
            e251_contract,
            {**e252_source_base, E252_UNITS[1]: status + suffix},
            E252_UNITS,
        )
        e252_records.append(encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(e252))
    e252_records.sort(key=lambda item: json.loads(item)["audit_digest"])
    e252_sources = {
        REQUIRED_SOURCE_UNITS[0]: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit.py").read_text(encoding="utf-8-sig"),
        REQUIRED_SOURCE_UNITS[1]: status,
    }
    return (
        e252_records,
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract()),
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_policy()),
        e252_sources,
    )


def _audit() -> dict[str, object]:
    records, e252_contract, policy, sources = _e252_and_sources()
    return audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(
        records, e252_contract, policy, sources, REQUIRED_SOURCE_UNITS
    )


def test_corpus_audit_accepts_real_ordered_records_and_is_deterministic() -> None:
    first = _audit()
    second = _audit()
    assert first == second
    first_bytes = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit(first)
    assert first_bytes == encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit(second)
    assert decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit(first_bytes) == first
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit(first) == {"valid": True, "errors": []}
    assert first["corpus_size"] == 2
    assert first["unique_corpus_valid"] is True
    assert first["version_compatibility_valid"] is True
    assert first["contract_evolution_valid"] is True
    assert first["deterministic_corpus_valid"] is True

    contract = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract()
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract(contract) == {"valid": True, "errors": []}
    status = build_runtime_worldbridge_status()
    assert status[CONTRACT_KEY] == contract
    assert MODULE_ID in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False


def test_corpus_audit_rejects_order_duplicates_versions_and_contract_policy_drift() -> None:
    records, contract, policy, sources = _e252_and_sources()
    with pytest.raises(ValueError, match="corpus order drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(list(reversed(records)), contract, policy, sources, REQUIRED_SOURCE_UNITS)
    with pytest.raises(ValueError, match="duplicate corpus record"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution([records[0], records[0]], contract, policy, sources, REQUIRED_SOURCE_UNITS)
    with pytest.raises(ValueError, match="at least two"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution([records[0]], contract, policy, sources, REQUIRED_SOURCE_UNITS)

    stale = json.loads(records[0])
    stale["e251_contract_digest"] = "0" * 64
    stale_without_digest = dict(stale)
    stale_without_digest.pop("audit_digest", None)
    import hashlib
    stale["audit_digest"] = hashlib.sha256(_canonical(stale_without_digest)).hexdigest()
    stale_records = sorted([_canonical(stale), records[1]], key=lambda item: json.loads(item)["audit_digest"])
    with pytest.raises(ValueError, match="stale E251 contract digest"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(stale_records, contract, policy, sources, REQUIRED_SOURCE_UNITS)

    drift = json.loads(contract)
    drift["static_policies"]["default_ready"] = True
    with pytest.raises(ValueError, match="drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(records, _canonical(drift), policy, sources, REQUIRED_SOURCE_UNITS)
    with pytest.raises(ValueError, match="non-canonical"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(records, json.dumps(json.loads(contract), indent=2).encode(), policy, sources, REQUIRED_SOURCE_UNITS)
    changed_policy = json.loads(policy)
    changed_policy["migration_admitted"] = True
    with pytest.raises(ValueError, match="policy drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(records, contract, _canonical(changed_policy), sources, REQUIRED_SOURCE_UNITS)
    with pytest.raises(ValueError, match="non-canonical"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(records, contract, json.dumps(json.loads(policy), indent=2).encode(), sources, REQUIRED_SOURCE_UNITS)
    with pytest.raises(ValueError, match="invalid canonical contract evolution policy"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(records, contract, b'{"schema_version":1,"schema_version":1}', sources, REQUIRED_SOURCE_UNITS)


def test_corpus_audit_rejects_source_and_result_tampering() -> None:
    records, contract, policy, sources = _e252_and_sources()
    with pytest.raises(ValueError, match="source order drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(records, contract, policy, sources, tuple(reversed(REQUIRED_SOURCE_UNITS)))
    forbidden = dict(sources)
    forbidden[E252_MODULE] += "\nimport subprocess\n"
    with pytest.raises(ValueError, match="source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(records, contract, policy, forbidden, REQUIRED_SOURCE_UNITS)
    drifted_status = dict(sources)
    drifted_status[REQUIRED_SOURCE_UNITS[1]] = drifted_status[REQUIRED_SOURCE_UNITS[1]].replace(CONTRACT_KEY, "contract_key_drift", 1)
    with pytest.raises(ValueError, match="source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(records, contract, policy, drifted_status, REQUIRED_SOURCE_UNITS)

    tampered = copy.deepcopy(_audit())
    tampered["deterministic_corpus_valid"] = False
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit(tampered)["valid"] is False
    with pytest.raises(ValueError, match="invalid corpus audit"):
        encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit(tampered)
