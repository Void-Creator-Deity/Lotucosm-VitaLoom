# -*- coding: utf-8 -*-
"""Static E249 guard for status-only registration and legacy non-consumption."""
from __future__ import annotations

import ast
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
sys.path.insert(0, str(RUNTIME))

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_consumer_non_consumption_audit import (
    REGISTRATION_SYMBOL,
    STATUS_MODULE,
    TARGET_MODULE,
    audit_worldbridge_quarantine_operator_presentation_consumer_non_consumption,
    build_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract,
    decode_worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit,
    encode_worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit,
    validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption,
    validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _source_units() -> dict[str, str]:
    units: dict[str, str] = {}
    files = {
        TARGET_MODULE: RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_receipt_consumer.py",
        STATUS_MODULE: RUNTIME / "core/VitaLoom/simulation/runtime_worldbridge_status.py",
        "core.VitaLoom.viewports.game_viewport": RUNTIME / "core/VitaLoom/viewports/game_viewport.py",
        "core.VitaLoom.viewports.scene_viewport": RUNTIME / "core/VitaLoom/viewports/scene_viewport.py",
        "core.VitaLoom.commands.runtime_commands": RUNTIME / "core/VitaLoom/commands/runtime_commands.py",
        "core.VitaLoom.commands.mcp_adapter": RUNTIME / "core/VitaLoom/commands/mcp_adapter.py",
        "core.VitaLoom.inspector.worldbridge_quarantine_operator_evidence_bundle": RUNTIME / "core/VitaLoom/inspector/worldbridge_quarantine_operator_evidence_bundle.py",
    }
    for module, path in files.items():
        units[module] = path.read_text(encoding="utf-8-sig")
    return units


def main() -> int:
    units = _source_units()
    audit = audit_worldbridge_quarantine_operator_presentation_consumer_non_consumption(units)
    if validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption(audit, source_units=units) != {"valid": True, "errors": []}:
        raise SystemExit("E249 source non-consumption audit invalid")
    if audit["non_consumption_valid"] is not True or audit["forbidden_edges"]:
        raise SystemExit(f"E249 forbidden production consumer edge: {audit['forbidden_edges']}")
    encoded = encode_worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit(audit)
    if decode_worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit(encoded) != audit:
        raise SystemExit("E249 canonical audit round-trip invalid")

    synthetic = dict(units)
    synthetic["core.VitaLoom.viewports.game_viewport"] = (
        f"from {TARGET_MODULE} import consume_worldbridge_quarantine_operator_presentation_receipt\n"
        "class GameViewport:\n"
        "    def tick(self, value):\n"
        "        return consume_worldbridge_quarantine_operator_presentation_receipt(value)\n"
    )
    forbidden = audit_worldbridge_quarantine_operator_presentation_consumer_non_consumption(synthetic)
    if forbidden["non_consumption_valid"] is not False or not forbidden["forbidden_edges"]:
        raise SystemExit("E249 failed to reject synthetic legacy consumer edge")
    tampered = copy.deepcopy(audit)
    tampered["consumer_invocation_admitted"] = True
    if validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption(tampered)["valid"] is not False:
        raise SystemExit("E249 admitted consumer invocation")
    try:
        decode_worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit(b'{"status":1,"status":1}')
    except ValueError:
        pass
    else:
        raise SystemExit("E249 admitted duplicate JSON keys")

    contract = build_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract()
    if validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract(contract) != {"valid": True, "errors": []}:
        raise SystemExit("E249 contract invalid")
    status = build_runtime_worldbridge_status()
    if status.get("failure_quarantine_operator_presentation_consumer_non_consumption_audit_contract") != contract:
        raise SystemExit("E249 status lost non-consumption contract")
    if STATUS_MODULE not in audit["registration_edges"][0]["module"] or audit["registration_edges"][0]["symbol"] != REGISTRATION_SYMBOL:
        raise SystemExit("E249 registration edge changed")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E249 changed default WorldBridge boundary")

    authority = RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_consumer_non_consumption_audit.py"
    source = authority.read_text(encoding="utf-8-sig")
    for token in ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle"):
        if token in source:
            raise SystemExit(f"E249 crossed audit boundary: {token}")
    tree = ast.parse(source)
    audit_function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "audit_worldbridge_quarantine_operator_presentation_consumer_non_consumption")
    if "_validated_source_units" not in ast.unparse(audit_function):
        raise SystemExit("E249 audit lost bounded source validation")
    print(json.dumps({"status": "ok", "non_consumption_valid": True, "consumer_invocation_admitted": False, "legacy_ui_consumption_admitted": False, "command_registry_consumption_admitted": False, "mcp_consumption_admitted": False, "inspector_consumption_admitted": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
