# -*- coding: utf-8 -*-
"""Static/runtime guard for E253 ordered compatibility corpus evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
sys.path.insert(0, str(RUNTIME))

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_audit import audit_worldbridge_quarantine_operator_presentation_status_projection, build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract, encode_worldbridge_quarantine_operator_presentation_status_projection_audit
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_audit import E250_MODULE, STATUS_MODULE, audit_worldbridge_quarantine_operator_presentation_status_projection_boundary, build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract, encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit import E251_MODULE, REQUIRED_UNITS as E252_UNITS, audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility, build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract, encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit import CONTRACT_KEY, E252_MODULE, MODULE_ID, REQUIRED_SOURCE_UNITS, audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution, build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract, build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_policy, decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit, encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit, validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit, validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

AUTHORITY = RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit.py"

def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def _inputs() -> tuple[list[bytes], bytes, bytes, dict[str, str]]:
    status_path = RUNTIME / "core/VitaLoom/simulation/runtime_worldbridge_status.py"
    status = status_path.read_text(encoding="utf-8-sig")
    e250_sources = {"core.VitaLoom.commands.runtime_commands": (RUNTIME / "core/VitaLoom/commands/runtime_commands.py").read_text(encoding="utf-8-sig"), "core.VitaLoom.commands.mcp_adapter": (RUNTIME / "core/VitaLoom/commands/mcp_adapter.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: status}
    e250 = audit_worldbridge_quarantine_operator_presentation_status_projection(reset_command_registry().run("runtime.worldbridge.status", {}), mcp_adapter.get_runtime_worldbridge_status(), e250_sources)
    e251 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(encode_worldbridge_quarantine_operator_presentation_status_projection_audit(e250), _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract()), {E250_MODULE: (RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_audit.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: status})
    e251_bytes = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(e251)
    e251_contract = _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract())
    e252_base = {E252_UNITS[0]: (RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_audit.py").read_text(encoding="utf-8-sig"), E252_UNITS[1]: status}
    records = []
    for suffix in ("", "\n"):
        e252 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(e251_bytes, e251_contract, {**e252_base, E252_UNITS[1]: status + suffix}, E252_UNITS)
        records.append(encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(e252))
    records.sort(key=lambda raw: json.loads(raw)["audit_digest"])
    sources = {REQUIRED_SOURCE_UNITS[0]: (RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit.py").read_text(encoding="utf-8-sig"), REQUIRED_SOURCE_UNITS[1]: status}
    return records, _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract()), _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_policy()), sources

def main() -> int:
    records, contract, policy, sources = _inputs()
    first = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(records, contract, policy, sources, REQUIRED_SOURCE_UNITS)
    second = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(records, contract, policy, sources, REQUIRED_SOURCE_UNITS)
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit(first) != {"valid": True, "errors": []}: raise SystemExit("E253 corpus audit invalid")
    encoded = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit(first)
    if encoded != encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit(second) or decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit(encoded) != first: raise SystemExit("E253 deterministic round-trip invalid")
    for key in ("actual_process_started", "ipc_transport_created", "raw_receipt_input_admitted", "receipt_consumer_operation_admitted", "runtime_action_authority", "ui_authority", "file_written", "network_transmitted", "persistence_admitted", "replay_admitted", "restore_admitted", "recovery_admitted", "same_runtime_retry_admitted", "quarantine_clear_admitted", "mutation_executed", "default_ready"):
        if first.get(key) is not False: raise SystemExit(f"E253 policy overclaim: {key}")
    for bad_records, bad_contract, bad_policy, bad_sources, bad_order in ((list(reversed(records)), contract, policy, sources, REQUIRED_SOURCE_UNITS), ([records[0], records[0]], contract, policy, sources, REQUIRED_SOURCE_UNITS), (records, contract, policy, sources, tuple(reversed(REQUIRED_SOURCE_UNITS)),)):
        try: audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(bad_records, bad_contract, bad_policy, bad_sources, bad_order)
        except ValueError: pass
        else: raise SystemExit("E253 admitted corpus/order drift")
    drift = json.loads(contract); drift["corpus_max_records"] = 1
    try: audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(records, _canonical(drift), policy, sources, REQUIRED_SOURCE_UNITS)
    except ValueError: pass
    else: raise SystemExit("E253 admitted contract evolution drift")
    forbidden = dict(sources); forbidden[E252_MODULE] += "\nimport subprocess\n"
    try: audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution(records, contract, policy, forbidden, REQUIRED_SOURCE_UNITS)
    except ValueError: pass
    else: raise SystemExit("E253 admitted forbidden source topology")
    tampered = dict(first); tampered["deterministic_corpus_valid"] = False
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit(tampered)["valid"] is not False: raise SystemExit("E253 accepted tampered result")
    authority_source = AUTHORITY.read_text(encoding="utf-8-sig")
    for token in ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle", "subprocess", "multiprocessing"):
        if token in authority_source: raise SystemExit(f"E253 crossed boundary: {token}")
    expected_contract = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract()
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract(expected_contract) != {"valid": True, "errors": []}: raise SystemExit("E253 contract invalid")
    status = build_runtime_worldbridge_status()
    if status.get(CONTRACT_KEY) != expected_contract or MODULE_ID not in status.get("pilot_modules", []): raise SystemExit("E253 status registration missing")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False: raise SystemExit("E253 changed default boundary")
    print(json.dumps({"status": "ok", "corpus_size": first["corpus_size"], "deterministic_corpus_valid": True, "contract_evolution_valid": True, "actual_process_started": False, "ipc_transport_created": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__": raise SystemExit(main())
