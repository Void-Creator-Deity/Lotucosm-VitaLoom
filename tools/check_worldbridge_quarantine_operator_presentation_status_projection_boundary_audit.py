# -*- coding: utf-8 -*-
"""Static E251 guard for canonical read-only status-projection boundary evidence."""
from __future__ import annotations

import copy
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
    CONTRACT_KEY,
    E250_MODULE,
    STATUS_MODULE,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract,
)
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

AUTHORITY = RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_audit.py"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _audit_inputs() -> tuple[bytes, bytes, dict[str, str]]:
    status_path = RUNTIME / "core/VitaLoom/simulation/runtime_worldbridge_status.py"
    e250_sources = {
        "core.VitaLoom.commands.runtime_commands": (RUNTIME / "core/VitaLoom/commands/runtime_commands.py").read_text(encoding="utf-8-sig"),
        "core.VitaLoom.commands.mcp_adapter": (RUNTIME / "core/VitaLoom/commands/mcp_adapter.py").read_text(encoding="utf-8-sig"),
        STATUS_MODULE: status_path.read_text(encoding="utf-8-sig"),
    }
    e250 = audit_worldbridge_quarantine_operator_presentation_status_projection(
        reset_command_registry().run("runtime.worldbridge.status", {}), mcp_adapter.get_runtime_worldbridge_status(), e250_sources
    )
    return (
        encode_worldbridge_quarantine_operator_presentation_status_projection_audit(e250),
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract()),
        {E250_MODULE: (RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_audit.py").read_text(encoding="utf-8-sig"), STATUS_MODULE: status_path.read_text(encoding="utf-8-sig")},
    )


def main() -> int:
    e250_audit, e250_contract, sources = _audit_inputs()
    audit = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(e250_audit, e250_contract, sources)
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(audit) != {"valid": True, "errors": []}:
        raise SystemExit("E251 boundary audit invalid")
    if decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(audit)) != audit:
        raise SystemExit("E251 canonical round-trip invalid")
    for key in ("actual_process_started", "ipc_transport_created", "raw_receipt_input_admitted", "receipt_consumer_operation_admitted", "runtime_action_authority", "ui_authority", "file_written", "network_transmitted", "persistence_admitted", "replay_admitted", "restore_admitted", "recovery_admitted", "same_runtime_retry_admitted", "quarantine_clear_admitted", "mutation_executed", "default_ready"):
        if audit.get(key) is not False:
            raise SystemExit(f"E251 policy overclaim: {key}")

    drift = json.loads(e250_contract)
    drift["static_policies"]["default_ready"] = True
    try:
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(e250_audit, _canonical(drift), sources)
    except ValueError:
        pass
    else:
        raise SystemExit("E251 admitted E250 contract drift")
    forbidden = dict(sources)
    forbidden[E250_MODULE] += "\nimport subprocess\n"
    try:
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(e250_audit, e250_contract, forbidden)
    except ValueError:
        pass
    else:
        raise SystemExit("E251 admitted boundary process seam")

    authority_source = AUTHORITY.read_text(encoding="utf-8-sig")
    for token in ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle", "subprocess", "multiprocessing"):
        if token in authority_source:
            raise SystemExit(f"E251 crossed Qt/runtime/I/O/process boundary: {token}")
    contract = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract()
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract(contract) != {"valid": True, "errors": []}:
        raise SystemExit("E251 contract invalid")
    status = build_runtime_worldbridge_status()
    if status.get(CONTRACT_KEY) != contract or "quarantine_operator_presentation_status_projection_boundary_audit_module" not in status.get("pilot_modules", []):
        raise SystemExit("E251 status registration missing")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E251 changed default WorldBridge boundary")
    print(json.dumps({"status": "ok", "actual_process_started": False, "ipc_transport_created": False, "read_only": True, "contract_drift_free": True, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
