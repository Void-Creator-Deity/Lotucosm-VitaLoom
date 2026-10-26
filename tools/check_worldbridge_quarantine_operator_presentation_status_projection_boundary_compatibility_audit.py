# -*- coding: utf-8 -*-
"""Static/runtime guard for E252 deterministic E251 provenance compatibility evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
sys.path.insert(0, str(RUNTIME))

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
    CONTRACT_KEY,
    E251_MODULE,
    MODULE_ID,
    REQUIRED_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract,
)
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

AUTHORITY = RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit.py"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _inputs() -> tuple[bytes, bytes, dict[str, str]]:
    status_path = RUNTIME / "core/VitaLoom/simulation/runtime_worldbridge_status.py"
    e250_sources = {
        "core.VitaLoom.commands.runtime_commands": (RUNTIME / "core/VitaLoom/commands/runtime_commands.py").read_text(encoding="utf-8-sig"),
        "core.VitaLoom.commands.mcp_adapter": (RUNTIME / "core/VitaLoom/commands/mcp_adapter.py").read_text(encoding="utf-8-sig"),
        STATUS_MODULE: status_path.read_text(encoding="utf-8-sig"),
    }
    e250 = audit_worldbridge_quarantine_operator_presentation_status_projection(
        reset_command_registry().run("runtime.worldbridge.status", {}), mcp_adapter.get_runtime_worldbridge_status(), e250_sources
    )
    e251 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(
        encode_worldbridge_quarantine_operator_presentation_status_projection_audit(e250),
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract()),
        {E250_MODULE: (RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_audit.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: e250_sources[STATUS_MODULE]},
    )
    return (
        encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(e251),
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract()),
        {E251_MODULE: (RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_audit.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: e250_sources[STATUS_MODULE]},
    )


def main() -> int:
    e251_audit, e251_contract, sources = _inputs()
    first = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(e251_audit, e251_contract, sources, REQUIRED_UNITS)
    second = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(e251_audit, e251_contract, sources, REQUIRED_UNITS)
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(first) != {"valid": True, "errors": []}:
        raise SystemExit("E252 compatibility audit invalid")
    encoded = encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(first)
    if encoded != encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(second) or decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(encoded) != first:
        raise SystemExit("E252 deterministic canonical evidence invalid")
    for key in ("actual_process_started", "ipc_transport_created", "raw_receipt_input_admitted", "receipt_consumer_operation_admitted", "runtime_action_authority", "ui_authority", "file_written", "network_transmitted", "persistence_admitted", "replay_admitted", "restore_admitted", "recovery_admitted", "same_runtime_retry_admitted", "quarantine_clear_admitted", "mutation_executed", "default_ready"):
        if first.get(key) is not False:
            raise SystemExit(f"E252 policy overclaim: {key}")
    drift = json.loads(e251_contract)
    drift["static_policies"]["default_ready"] = True
    for contract, order, source_map in ((_canonical(drift), REQUIRED_UNITS, sources), (e251_contract, tuple(reversed(REQUIRED_UNITS)), sources), (e251_contract, REQUIRED_UNITS, {**sources, E251_MODULE: sources[E251_MODULE] + "\nimport subprocess\n"})):
        try:
            audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(e251_audit, contract, source_map, order)
        except ValueError:
            pass
        else:
            raise SystemExit("E252 admitted contract/order/topology drift")
    authority_source = AUTHORITY.read_text(encoding="utf-8-sig")
    for token in ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle", "subprocess", "multiprocessing"):
        if token in authority_source:
            raise SystemExit(f"E252 crossed Qt/runtime/I/O/process boundary: {token}")
    contract = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract()
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract(contract) != {"valid": True, "errors": []}:
        raise SystemExit("E252 contract invalid")
    status = build_runtime_worldbridge_status()
    if status.get(CONTRACT_KEY) != contract or MODULE_ID not in status.get("pilot_modules", []):
        raise SystemExit("E252 status registration missing")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E252 changed default WorldBridge boundary")
    print(json.dumps({"status": "ok", "read_only": True, "deterministic_compatibility_valid": True, "actual_process_started": False, "ipc_transport_created": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
