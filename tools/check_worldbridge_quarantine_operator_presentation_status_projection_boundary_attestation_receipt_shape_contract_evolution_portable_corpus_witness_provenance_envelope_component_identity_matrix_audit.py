# -*- coding: utf-8 -*-
"""Standalone E261 component-identity-matrix audit guard."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit import (
    CONTRACT_KEY, E260_MODULE, MODULE_ID, REQUIRED_SOURCE_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix as audit_e261,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit_contract as build_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit as decode_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit as encode_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit as validate_audit,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status
from test_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit import AUTHORITY, _canonical, _e261_inputs


def _must_reject(*args: object) -> None:
    try:
        audit_e261(*args)
    except (TypeError, ValueError):
        return
    raise SystemExit("E261 guard accepted invalid input")


def main() -> int:
    records, contract, policy, sources = _e261_inputs()
    first = audit_e261(records, contract, policy, sources, REQUIRED_SOURCE_UNITS)
    second = audit_e261(records, contract, policy, sources, REQUIRED_SOURCE_UNITS)
    if validate_audit(first) != {"valid": True, "errors": []}:
        raise SystemExit("E261 audit invalid")
    encoded = encode_audit(first)
    if encoded != encode_audit(second) or decode_audit(encoded) != first:
        raise SystemExit("E261 deterministic round-trip invalid")
    if first.get("corpus_size") != 2 or first.get("component_identity_matrix_valid") is not True or len(first.get("component_identity_matrix", ())) != 2:
        raise SystemExit("E261 component-identity matrix closure invalid")
    _must_reject(list(reversed(records)), contract, policy, sources, REQUIRED_SOURCE_UNITS)
    _must_reject([records[0], records[0]], contract, policy, sources, REQUIRED_SOURCE_UNITS)
    _must_reject(records[:1], contract, policy, sources, REQUIRED_SOURCE_UNITS)
    drift = json.loads(contract); drift["schema_version"] = 2
    _must_reject(records, _canonical(drift), policy, sources, REQUIRED_SOURCE_UNITS)
    drift = json.loads(policy); drift["migration_admitted"] = True
    _must_reject(records, contract, _canonical(drift), sources, REQUIRED_SOURCE_UNITS)
    forbidden = dict(sources); forbidden[E260_MODULE] += "\nimport subprocess\n"
    _must_reject(records, contract, policy, forbidden, REQUIRED_SOURCE_UNITS)
    tampered = dict(first); tampered["component_identity_matrix_digest"] = "0" * 64
    if validate_audit(tampered)["valid"] is not False:
        raise SystemExit("E261 accepted tampered result")
    source = AUTHORITY.read_text(encoding="utf-8-sig")
    for token in ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle", "subprocess", "multiprocessing"):
        if token in source:
            raise SystemExit(f"E261 crossed boundary: {token}")
    status = build_runtime_worldbridge_status()
    if status.get(CONTRACT_KEY) != build_contract() or MODULE_ID not in status.get("pilot_modules", []):
        raise SystemExit("E261 status registration missing")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E261 changed default boundary")
    print(json.dumps({"status": "ok", "component_identity_matrix_valid": True, "actual_fresh_process_started": False, "ipc_transport_created": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
