# -*- coding: utf-8 -*-
"""Static E250 guard for the existing read-only WorldBridge status projection."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
sys.path.insert(0, str(RUNTIME))

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_audit import (
    COMMAND_ID,
    COMMAND_MODULE,
    CONSUMER_CONTRACT_KEY,
    MCP_MODULE,
    STATUS_MODULE,
    audit_worldbridge_quarantine_operator_presentation_status_projection,
    build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_audit_contract,
)
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

AUTHORITY = RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_audit.py"
SOURCE_PATHS = {
    COMMAND_MODULE: RUNTIME / "core/VitaLoom/commands/runtime_commands.py",
    MCP_MODULE: RUNTIME / "core/VitaLoom/commands/mcp_adapter.py",
    STATUS_MODULE: RUNTIME / "core/VitaLoom/simulation/runtime_worldbridge_status.py",
}


def _source_units() -> dict[str, str]:
    return {name: path.read_text(encoding="utf-8-sig") for name, path in SOURCE_PATHS.items()}


def main() -> int:
    command = reset_command_registry().run(COMMAND_ID, {})
    mcp = mcp_adapter.get_runtime_worldbridge_status()
    if command.get("ok") is not True or mcp.get("ok") is not True:
        raise SystemExit("E250 existing command/MCP status surface failed")

    units = _source_units()
    audit = audit_worldbridge_quarantine_operator_presentation_status_projection(command, mcp, units)
    if validate_worldbridge_quarantine_operator_presentation_status_projection_audit(audit) != {"valid": True, "errors": []}:
        raise SystemExit("E250 status projection audit invalid")
    encoded = encode_worldbridge_quarantine_operator_presentation_status_projection_audit(audit)
    if decode_worldbridge_quarantine_operator_presentation_status_projection_audit(encoded) != audit:
        raise SystemExit("E250 canonical audit round-trip invalid")

    leaked = copy.deepcopy(command)
    leaked["result"]["receipt"] = {"opaque": True}
    try:
        audit_worldbridge_quarantine_operator_presentation_status_projection(leaked, mcp, units)
    except ValueError:
        pass
    else:
        raise SystemExit("E250 admitted raw receipt projection")

    operation = dict(units)
    operation[COMMAND_MODULE] = operation[COMMAND_MODULE].replace(
        "return command_ok(build_runtime_worldbridge_status(project_path=project_path))",
        "consume_worldbridge_quarantine_operator_presentation_receipt(None)\n    return command_ok(build_runtime_worldbridge_status(project_path=project_path))",
        1,
    )
    try:
        audit_worldbridge_quarantine_operator_presentation_status_projection(command, mcp, operation)
    except ValueError:
        pass
    else:
        raise SystemExit("E250 admitted command consumer operation")

    tampered = copy.deepcopy(audit)
    tampered["quarantine_clear_admitted"] = True
    if validate_worldbridge_quarantine_operator_presentation_status_projection_audit(tampered).get("valid") is not False:
        raise SystemExit("E250 admitted quarantine-clear policy overclaim")

    source_text = AUTHORITY.read_text(encoding="utf-8-sig")
    for token in ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle"):
        if token in source_text:
            raise SystemExit(f"E250 crossed Qt/runtime/I/O boundary: {token}")

    contract = build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract()
    if validate_worldbridge_quarantine_operator_presentation_status_projection_audit_contract(contract) != {"valid": True, "errors": []}:
        raise SystemExit("E250 contract invalid")
    status = build_runtime_worldbridge_status()
    if status.get("failure_quarantine_operator_presentation_status_projection_audit_contract") != contract:
        raise SystemExit("E250 status lost projection audit contract")
    if "quarantine_operator_presentation_status_projection_audit_module" not in status.get("pilot_modules", []):
        raise SystemExit("E250 status lost projection audit module")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E250 changed default WorldBridge boundary")

    print(json.dumps({"status": "ok", "read_only": True, "raw_receipt_input_admitted": False, "consumer_operation_admitted": False, "mutation_executed": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
