# -*- coding: utf-8 -*-
"""Static/runtime guard for E257 attestation receipt-shape compatibility."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
sys.path.insert(0, str(RUNTIME))

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_audit import audit_worldbridge_quarantine_operator_presentation_status_projection, build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract, encode_worldbridge_quarantine_operator_presentation_status_projection_audit
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_audit import E250_MODULE, STATUS_MODULE, audit_worldbridge_quarantine_operator_presentation_status_projection_boundary, build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract, encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit import REQUIRED_UNITS as E252_UNITS, audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility, build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract, encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit import REQUIRED_SOURCE_UNITS as E253_UNITS, audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution, build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract, build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_policy, encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit import E253_MODULE, REQUIRED_SOURCE_UNITS as E254_UNITS, audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability, build_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract, encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit import E254_MODULE, REQUIRED_SOURCE_UNITS as E255_UNITS, audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness, build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit_contract, encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit import CONTRACT_KEY, E255_MODULE, MODULE_ID, REQUIRED_SOURCE_UNITS, audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation, build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract, decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit, encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit, validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit, validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit import CONTRACT_KEY as E257_CONTRACT_KEY, E256_MODULE, MODULE_ID as E257_MODULE_ID, REQUIRED_SOURCE_UNITS as E257_UNITS, audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility, build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract, decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit, encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit, validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit, validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

AUTHORITY = RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit.py"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _inputs() -> tuple[bytes, bytes, dict[str, str]]:
    status = (RUNTIME / "core/VitaLoom/simulation/runtime_worldbridge_status.py").read_text(encoding="utf-8-sig")
    e250 = audit_worldbridge_quarantine_operator_presentation_status_projection(reset_command_registry().run("runtime.worldbridge.status", {}), mcp_adapter.get_runtime_worldbridge_status(), {"core.VitaLoom.commands.runtime_commands": (RUNTIME / "core/VitaLoom/commands/runtime_commands.py").read_text(encoding="utf-8-sig"), "core.VitaLoom.commands.mcp_adapter": (RUNTIME / "core/VitaLoom/commands/mcp_adapter.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: status})
    e251 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(encode_worldbridge_quarantine_operator_presentation_status_projection_audit(e250), _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract()), {E250_MODULE: (RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_audit.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: status})
    e251_bytes = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(e251)
    e251_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract())
    e252_sources = {E252_UNITS[0]: (RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_audit.py").read_text(encoding="utf-8-sig"), E252_UNITS[1]: status}
    corpus: list[bytes] = []
    for suffix in ("", "\n"):
        record = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(e251_bytes, e251_contract, {**e252_sources, E252_UNITS[1]: status + suffix}, E252_UNITS)
        corpus.append(encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(record))
    corpus.sort(key=lambda item: json.loads(item)["audit_digest"])
    e252_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract())
    e253_policy = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_policy())
    e253 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(corpus, e252_contract, e253_policy, {E253_UNITS[0]: (RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit.py").read_text(encoding="utf-8-sig"), E253_UNITS[1]: status}, E253_UNITS)
    e253_bytes = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit(e253)
    e253_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract())
    e254 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability(e253_bytes, e253_contract, e253_policy, e252_contract, corpus, {E253_MODULE: (RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: status}, E254_UNITS)
    e254_bytes = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit(e254)
    e254_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract())
    e255 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness(e254_bytes, e254_contract, e253_bytes, e253_contract, e253_policy, e252_contract, corpus, {E254_MODULE: (RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: status}, E255_UNITS)
    return encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit(e255), _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit_contract()), {E255_MODULE: (RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: status}


def _must_reject(*args: object) -> None:
    try:
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility(*args)
    except ValueError:
        return
    raise SystemExit("E257 admitted invalid receipt-shape corpus evidence")


def main() -> int:
    e255_audit, e255_contract, e255_sources = _inputs()
    records: list[bytes] = []
    for suffix in ("", "\n"):
        e256 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation(
            e255_audit, e255_contract, {**e255_sources, STATUS_MODULE: e255_sources[STATUS_MODULE] + suffix}, REQUIRED_SOURCE_UNITS,
        )
        records.append(encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(e256))
    records.sort(key=lambda raw: json.loads(raw)["audit_digest"])
    e256_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract())
    e257_sources = {
        E256_MODULE: (RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit.py").read_text(encoding="utf-8-sig"),
        STATUS_MODULE: e255_sources[STATUS_MODULE],
    }
    args = (records, e256_contract, e257_sources, E257_UNITS)
    first = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility(*args)
    second = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility(*args)
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(first) != {"valid": True, "errors": []}:
        raise SystemExit("E257 audit invalid")
    encoded = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(first)
    if encoded != encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(second) or decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(encoded) != first:
        raise SystemExit("E257 deterministic round-trip invalid")
    if first.get("corpus_size") != 2 or first.get("receipt_shape_compatibility_valid") is not True or len(set(first.get("attestation_source_unit_digests", ()))) != 2:
        raise SystemExit("E257 did not preserve compatible independent provenance")
    for key in ("actual_fresh_process_started", "ipc_transport_created", "dynamic_source_import_admitted", "raw_receipt_input_admitted", "receipt_consumer_operation_admitted", "runtime_action_authority", "ui_authority", "file_written", "network_transmitted", "persistence_admitted", "replay_admitted", "restore_admitted", "recovery_admitted", "same_runtime_retry_admitted", "quarantine_clear_admitted", "mutation_executed", "default_ready"):
        if first.get(key) is not False:
            raise SystemExit(f"E257 policy overclaim: {key}")
    _must_reject(list(reversed(records)), e256_contract, e257_sources, E257_UNITS)
    _must_reject([records[0], records[0]], e256_contract, e257_sources, E257_UNITS)
    _must_reject(records[:1], e256_contract, e257_sources, E257_UNITS)
    drift = json.loads(e256_contract); drift["schema_version"] = 2
    _must_reject(records, _canonical(drift), e257_sources, E257_UNITS)
    forbidden = dict(e257_sources); forbidden[E256_MODULE] += "\nimport subprocess\n"
    _must_reject(records, e256_contract, forbidden, E257_UNITS)
    tampered = dict(first); tampered["receipt_shape_digest"] = "0" * 64
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(tampered)["valid"] is not False:
        raise SystemExit("E257 accepted tampered result")
    authority_source = AUTHORITY.read_text(encoding="utf-8-sig")
    for token in ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle", "subprocess", "multiprocessing"):
        if token in authority_source:
            raise SystemExit(f"E257 crossed boundary: {token}")
    expected_contract = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract()
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract(expected_contract) != {"valid": True, "errors": []}:
        raise SystemExit("E257 contract invalid")
    status = build_runtime_worldbridge_status()
    if status.get(E257_CONTRACT_KEY) != expected_contract or E257_MODULE_ID not in status.get("pilot_modules", []):
        raise SystemExit("E257 status registration missing")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E257 changed default boundary")
    print(json.dumps({"status": "ok", "receipt_shape_compatibility_valid": True, "deterministic_corpus_valid": True, "actual_fresh_process_started": False, "ipc_transport_created": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

