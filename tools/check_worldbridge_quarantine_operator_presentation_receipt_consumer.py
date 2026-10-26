# -*- coding: utf-8 -*-
"""Static E248 guard for receipt-only consumption and replay exclusion."""
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
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_surface_receipt import export_worldbridge_quarantine_operator_presentation_surface_receipt
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_receipt_consumer import (
    build_worldbridge_quarantine_operator_presentation_receipt_consumer_contract,
    consume_worldbridge_quarantine_operator_presentation_receipt,
    decode_worldbridge_quarantine_operator_presentation_receipt_consumer,
    encode_worldbridge_quarantine_operator_presentation_receipt_consumer,
    validate_worldbridge_quarantine_operator_presentation_receipt_consumer,
    validate_worldbridge_quarantine_operator_presentation_receipt_consumer_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

AUTHORITY = RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_receipt_consumer.py"


def _receipt() -> dict[str, object]:
    presentation: dict[str, object] = {
        "schema_version": 1,
        "status": "worldbridge_quarantine_operator_presentation",
        "scope": "same_adapter_worldbridge_quarantine_operator_presentation",
        "read_only": True,
        "availability": "available",
        "operator_state": "fresh_instance_boundary_observed",
        "headline": "独立的新生命周期边界",
        "caveat": "这只是观测，不是恢复、重试、重准入、还原或重放。",
        "current_runtime_quarantined": False,
        "same_adapter_only": True,
        "evidence_summary": {
            "failure_lifecycle_values_redacted": True,
            "current_lifecycle_values_redacted": True,
            "disposal_recorded": True,
            "disposal_boundary": "simulation_stop",
            "fresh_instance_boundary_observed": True,
        },
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES},
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    exported = export_worldbridge_quarantine_operator_presentation(presentation)
    audited = audit_worldbridge_quarantine_operator_presentation_export(exported)
    bundle = consume_worldbridge_quarantine_operator_evidence_pair(exported, audited)
    command = {"ok": True, "result": copy.deepcopy(bundle)}
    from core.VitaLoom.inspector.worldbridge_quarantine_operator_evidence_bundle import build_worldbridge_quarantine_operator_evidence_bundle_view_model
    inspector = build_worldbridge_quarantine_operator_evidence_bundle_view_model(command).to_dict()
    surface = audit_worldbridge_quarantine_operator_presentation_surfaces(command, copy.deepcopy(command), inspector)
    return export_worldbridge_quarantine_operator_presentation_surface_receipt(surface)


def main() -> int:
    receipt = _receipt()
    consumer = consume_worldbridge_quarantine_operator_presentation_receipt(receipt)
    if validate_worldbridge_quarantine_operator_presentation_receipt_consumer(consumer, receipt=receipt) != {"valid": True, "errors": []}:
        raise SystemExit("E248 consumer parity invalid")
    encoded = encode_worldbridge_quarantine_operator_presentation_receipt_consumer(consumer)
    if decode_worldbridge_quarantine_operator_presentation_receipt_consumer(encoded) != consumer:
        raise SystemExit("E248 canonical consumer round-trip invalid")
    if any(value in encoded.decode("utf-8") for value in ("sr_runtime_epoch", "pond_lifetime_token", "failure_sr_runtime_epoch", "current_pond_lifetime_token")):
        raise SystemExit("E248 exposed state/replay material")
    for key in ("receipt_persisted", "file_written", "network_transmitted", "external_artifact_input", "checkpoint_state_consumed", "replay_cursor_consumed", "replay_input_admitted", "replay_admitted", "restore_admitted", "recovery_admitted", "same_runtime_retry_admitted", "quarantine_clear_admitted", "mutation_executed", "runtime_action_authority", "ui_authority", "default_ready"):
        if consumer.get(key) is not False:
            raise SystemExit(f"E248 policy overclaim: {key}")
    tampered = copy.deepcopy(consumer)
    tampered["restore_admitted"] = True
    if validate_worldbridge_quarantine_operator_presentation_receipt_consumer(tampered).get("valid") is not False:
        raise SystemExit("E248 admitted restore authority overclaim")
    try:
        decode_worldbridge_quarantine_operator_presentation_receipt_consumer(b'{"status":1,"status":1}')
    except ValueError:
        pass
    else:
        raise SystemExit("E248 admitted duplicate JSON keys")

    source_text = AUTHORITY.read_text(encoding="utf-8-sig")
    for token in ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle", "deserialize_pond("):
        if token in source_text:
            raise SystemExit(f"E248 crossed Qt/runtime/I/O boundary: {token}")
    tree = ast.parse(source_text)
    consumer_function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "consume_worldbridge_quarantine_operator_presentation_receipt")
    body = ast.unparse(consumer_function)
    if "_validated_receipt" not in body or any(token in body for token in ("Pond(", "GameViewport", "open(")):
        raise SystemExit("E248 consumer gained runtime control")
    contract = build_worldbridge_quarantine_operator_presentation_receipt_consumer_contract()
    if validate_worldbridge_quarantine_operator_presentation_receipt_consumer_contract(contract) != {"valid": True, "errors": []}:
        raise SystemExit("E248 contract invalid")
    status = build_runtime_worldbridge_status()
    if status.get("failure_quarantine_operator_presentation_receipt_consumer_contract") != contract:
        raise SystemExit("E248 status lost receipt consumer contract")
    if "quarantine_operator_presentation_receipt_consumer_module" not in status.get("pilot_modules", []):
        raise SystemExit("E248 status lost consumer module")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E248 changed default WorldBridge boundary")
    print(json.dumps({"status": "ok", "replay_admitted": False, "restore_admitted": False, "runtime_state_reconstructed": False, "writes_files": False, "transmits_network": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
