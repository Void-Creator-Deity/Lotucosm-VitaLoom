# -*- coding: utf-8 -*-
"""Standalone E259 portable corpus witness boundary guard."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
TESTS = ROOT / "tests"
sys.path[:0] = [str(RUNTIME), str(TESTS)]

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit import (
    REQUIRED_SOURCE_UNITS as E258_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_contract,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit import (
    CONTRACT_KEY,
    E258_MODULE,
    MODULE_ID,
    REQUIRED_SOURCE_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit_contract,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_policy,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status
from test_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit import _canonical, _e258_inputs

AUTHORITY = RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit.py"


def _inputs() -> tuple[list[bytes], bytes, bytes, dict[str, str]]:
    e257_records, e257_contract, e258_policy, e258_sources = _e258_inputs()
    records: list[bytes] = []
    for suffix in ("", "\n"):
        record = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution(
            e257_records, e257_contract, e258_policy,
            {**e258_sources, "core.VitaLoom.simulation.runtime_worldbridge_status": e258_sources["core.VitaLoom.simulation.runtime_worldbridge_status"] + suffix},
            E258_UNITS,
        )
        records.append(encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(record))
    records.sort(key=lambda item: json.loads(item)["audit_digest"])
    return (
        records,
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_contract()),
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_policy()),
        {
            E258_MODULE: (RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit.py").read_text(encoding="utf-8-sig"),
            "core.VitaLoom.simulation.runtime_worldbridge_status": (RUNTIME / "core/VitaLoom/simulation/runtime_worldbridge_status.py").read_text(encoding="utf-8-sig"),
        },
    )


def _must_reject(*args: object) -> None:
    try:
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness(*args)
    except (TypeError, ValueError):
        return
    raise SystemExit("E259 guard accepted invalid input")


def main() -> int:
    records, contract, policy, sources = _inputs()
    first = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness(records, contract, policy, sources, REQUIRED_SOURCE_UNITS)
    second = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness(records, contract, policy, sources, REQUIRED_SOURCE_UNITS)
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit(first) != {"valid": True, "errors": []}:
        raise SystemExit("E259 audit invalid")
    encoded = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit(first)
    if encoded != encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit(second) or decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit(encoded) != first:
        raise SystemExit("E259 deterministic round-trip invalid")
    if first.get("corpus_size") != 2 or first.get("receipt_shape_closure_valid") is not True or first.get("policy_closure_valid") is not True or first.get("provenance_closure_valid") is not True:
        raise SystemExit("E259 closure proof invalid")
    _must_reject(list(reversed(records)), contract, policy, sources, REQUIRED_SOURCE_UNITS)
    _must_reject([records[0], records[0]], contract, policy, sources, REQUIRED_SOURCE_UNITS)
    _must_reject(records[:1], contract, policy, sources, REQUIRED_SOURCE_UNITS)
    drift = json.loads(contract); drift["schema_version"] = 2
    _must_reject(records, _canonical(drift), policy, sources, REQUIRED_SOURCE_UNITS)
    drift = json.loads(policy); drift["migration_admitted"] = True
    _must_reject(records, contract, _canonical(drift), sources, REQUIRED_SOURCE_UNITS)
    forbidden = dict(sources); forbidden[E258_MODULE] += "\nimport subprocess\n"
    _must_reject(records, contract, policy, forbidden, REQUIRED_SOURCE_UNITS)
    tampered = dict(first); tampered["receipt_shape_digest"] = "0" * 64
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit(tampered)["valid"] is not False:
        raise SystemExit("E259 accepted tampered result")
    source = AUTHORITY.read_text(encoding="utf-8-sig")
    for token in ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle", "subprocess", "multiprocessing"):
        if token in source:
            raise SystemExit(f"E259 crossed boundary: {token}")
    status = build_runtime_worldbridge_status()
    if status.get(CONTRACT_KEY) != build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit_contract() or MODULE_ID not in status.get("pilot_modules", []):
        raise SystemExit("E259 status registration missing")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E259 changed default boundary")
    print(json.dumps({"status": "ok", "receipt_shape_closure_valid": True, "policy_closure_valid": True, "provenance_closure_valid": True, "actual_fresh_process_started": False, "ipc_transport_created": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
