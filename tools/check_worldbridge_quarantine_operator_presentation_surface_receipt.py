# -*- coding: utf-8 -*-
"""Static E247 guard for canonical, source-only, non-authoritative receipts."""
from __future__ import annotations

import ast
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
sys.path.insert(0, str(RUNTIME))

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import DO_NOT_CLAIM, NEGATIVE_CAPABILITIES
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export import export_worldbridge_quarantine_operator_presentation
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export_audit import audit_worldbridge_quarantine_operator_presentation_export
from core.Lotucosm.runtime.world_bridge_quarantine_operator_evidence_bundle import consume_worldbridge_quarantine_operator_evidence_pair
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_surface_audit import audit_worldbridge_quarantine_operator_presentation_surfaces
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_surface_receipt import (
    build_worldbridge_quarantine_operator_presentation_surface_receipt_contract,
    decode_worldbridge_quarantine_operator_presentation_surface_receipt,
    encode_worldbridge_quarantine_operator_presentation_surface_receipt,
    export_worldbridge_quarantine_operator_presentation_surface_receipt,
    validate_worldbridge_quarantine_operator_presentation_surface_receipt,
    validate_worldbridge_quarantine_operator_presentation_surface_receipt_contract,
)
from core.VitaLoom.inspector.worldbridge_quarantine_operator_evidence_bundle import build_worldbridge_quarantine_operator_evidence_bundle_view_model
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

AUTHORITY = RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_surface_receipt.py"


def _source() -> dict[str, object]:
    presentation: dict[str, object] = {
        "schema_version": 1, "status": "worldbridge_quarantine_operator_presentation",
        "scope": "same_adapter_worldbridge_quarantine_operator_presentation", "read_only": True,
        "availability": "available", "operator_state": "fresh_instance_boundary_observed",
        "headline": "独立的新生命周期边界", "caveat": "这只是观测，不是恢复、重试、重准入、还原或重放。",
        "current_runtime_quarantined": False, "same_adapter_only": True,
        "evidence_summary": {"failure_lifecycle_values_redacted": True, "current_lifecycle_values_redacted": True,
                             "disposal_recorded": True, "disposal_boundary": "simulation_stop",
                             "fresh_instance_boundary_observed": True},
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES}, "do_not_claim": list(DO_NOT_CLAIM),
    }
    exported = export_worldbridge_quarantine_operator_presentation(presentation)
    bundle = consume_worldbridge_quarantine_operator_evidence_pair(exported, audit_worldbridge_quarantine_operator_presentation_export(exported))
    command = {"ok": True, "result": copy.deepcopy(bundle)}
    inspector = build_worldbridge_quarantine_operator_evidence_bundle_view_model(command).to_dict()
    return audit_worldbridge_quarantine_operator_presentation_surfaces(command, copy.deepcopy(command), inspector)


def main() -> int:
    source = _source()
    receipt = export_worldbridge_quarantine_operator_presentation_surface_receipt(source)
    if validate_worldbridge_quarantine_operator_presentation_surface_receipt(receipt, surface_audit=source) != {"valid": True, "errors": []}:
        raise SystemExit("E247 receipt parity invalid")
    encoded = encode_worldbridge_quarantine_operator_presentation_surface_receipt(receipt)
    if decode_worldbridge_quarantine_operator_presentation_surface_receipt(encoded) != receipt:
        raise SystemExit("E247 canonical receipt round-trip invalid")
    serial = encoded.decode("utf-8")
    if any(value in serial for value in ("epoch-secret", "pond-secret", "sr_runtime_epoch", "pond_lifetime_token")):
        raise SystemExit("E247 exposed opaque lifecycle values")
    for key in ("receipt_persisted", "file_written", "network_transmitted", "external_artifact_input", "runtime_action_authority", "ui_authority", "quarantine_clear_admitted", "same_runtime_retry_admitted", "recovery_admitted", "replay_or_restore_admitted", "mutation_executed", "default_ready"):
        if receipt.get(key) is not False:
            raise SystemExit(f"E247 policy overclaim: {key}")
    tampered = copy.deepcopy(receipt)
    tampered["replay_or_restore_admitted"] = True
    if validate_worldbridge_quarantine_operator_presentation_surface_receipt(tampered).get("valid") is not False:
        raise SystemExit("E247 admitted replay authority overclaim")
    try:
        decode_worldbridge_quarantine_operator_presentation_surface_receipt(b'{"schema_version":1,"schema_version":1}')
    except ValueError:
        pass
    else:
        raise SystemExit("E247 admitted duplicate JSON keys")

    forbidden = ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle", "deserialize_pond(")
    source_text = AUTHORITY.read_text(encoding="utf-8-sig")
    if any(token in source_text for token in forbidden):
        raise SystemExit("E247 crossed Qt/runtime/I/O boundary")
    tree = ast.parse(source_text)
    exporter = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "export_worldbridge_quarantine_operator_presentation_surface_receipt")
    body = ast.unparse(exporter)
    if "_validated_source_audit" not in body or any(token in body for token in ("Pond(", "GameViewport", "open(")):
        raise SystemExit("E247 receipt export gained runtime control")
    contract = build_worldbridge_quarantine_operator_presentation_surface_receipt_contract()
    if validate_worldbridge_quarantine_operator_presentation_surface_receipt_contract(contract) != {"valid": True, "errors": []}:
        raise SystemExit("E247 contract invalid")
    status = build_runtime_worldbridge_status()
    if status.get("failure_quarantine_operator_presentation_surface_receipt_contract") != contract:
        raise SystemExit("E247 status lost receipt contract")
    if "quarantine_operator_presentation_surface_receipt_module" not in status.get("pilot_modules", []):
        raise SystemExit("E247 status lost receipt module")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E247 changed default WorldBridge boundary")
    print(json.dumps({"status": "ok", "writes_files": False, "transmits_network": False, "external_artifact_input": False, "runtime_action_authority": False, "ui_authority": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
