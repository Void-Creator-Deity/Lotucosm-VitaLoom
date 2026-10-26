# -*- coding: utf-8 -*-
"""Static E242 guard for bounded WorldBridge quarantine operator presentation."""
from __future__ import annotations

import ast
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
sys.path.insert(0, str(RUNTIME))

from core.Lotucosm.runtime.world_bridge_quarantine_diagnostic_provenance import (
    project_worldbridge_quarantine_diagnostic,
)
from core.Lotucosm.runtime.world_bridge_quarantine_lifecycle_correlation import (
    build_worldbridge_quarantine_disposal_observation,
    build_worldbridge_quarantine_lifecycle_evidence,
    project_worldbridge_quarantine_lifecycle_correlation,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
    NEGATIVE_CAPABILITIES,
    build_worldbridge_quarantine_operator_presentation_contract,
    present_worldbridge_quarantine_lifecycle,
    validate_worldbridge_quarantine_operator_presentation,
    validate_worldbridge_quarantine_operator_presentation_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_readmission_authority import (
    classify_worldbridge_opt_in_bridge_admission,
)
from core.Lotucosm.runtime.world_bridge_recovery_authority import (
    classify_worldbridge_handoff_failure_containment,
)
from core.Lotucosm.runtime.world_bridge_transaction_authority import (
    build_worldbridge_handoff_failure_receipt,
)
from core.VitaLoom.commands.registry import get_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)

AUTHORITY = RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation.py"
INSPECTOR = RUNTIME / "core/VitaLoom/inspector/worldbridge_quarantine_operator_presentation.py"
COMMANDS = RUNTIME / "core/VitaLoom/commands/runtime_commands.py"


def _diagnostic(quarantined: bool) -> dict[str, object]:
    receipt = build_worldbridge_handoff_failure_receipt(
        "pond_update", trace_requested=False, preflight_completed=True,
        sr_to_ps_sync_started=True, pond_update_started=True,
        ps_to_sr_reflection_started=False, cause=RuntimeError("guard"),
    )
    return project_worldbridge_quarantine_diagnostic(
        handoff_suspended=quarantined,
        failure_receipt=receipt,
        recovery_decision=classify_worldbridge_handoff_failure_containment(receipt),
        quarantine_admission=classify_worldbridge_opt_in_bridge_admission(
            "tick_handoff", unified_pond_mode=True,
            handoff_suspended=quarantined, current_pond_present=True,
        ),
    )


def _lifecycle(epoch: str, pond: str) -> dict[str, object]:
    result = build_worldbridge_quarantine_lifecycle_evidence(
        sr_runtime_epoch=epoch, pond_lifetime_token=pond,
    )
    if result is None:
        raise SystemExit("E242 lifecycle fixture unexpectedly absent")
    return result


def _function(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise SystemExit(f"E242 missing function {name}")


def main() -> int:
    contract = build_worldbridge_quarantine_operator_presentation_contract()
    if validate_worldbridge_quarantine_operator_presentation_contract(contract).get("valid") is not True:
        raise SystemExit("E242 baseline contract invalid")
    for key in NEGATIVE_CAPABILITIES:
        if contract.get("negative_capabilities", {}).get(key) is not False:
            raise SystemExit(f"E242 contract overclaimed {key}")
        tampered = copy.deepcopy(contract)
        tampered["negative_capabilities"][key] = True
        if validate_worldbridge_quarantine_operator_presentation_contract(tampered).get("valid") is not False:
            raise SystemExit(f"E242 validator accepted {key} overclaim")

    failure = _lifecycle("epoch-secret", "pond-secret")
    disposal = build_worldbridge_quarantine_disposal_observation(
        failure_lifecycle=failure, active_lifecycle=failure,
        disposal_boundary="simulation_stop", handoff_suspended=True,
    )
    if disposal is None:
        raise SystemExit("E242 fixture disposal absent")
    source = project_worldbridge_quarantine_lifecycle_correlation(
        diagnostic=_diagnostic(False), failure_lifecycle=failure,
        disposal_observation=disposal,
        current_lifecycle=_lifecycle("epoch-new", "pond-new"),
    )
    presentation = present_worldbridge_quarantine_lifecycle(source)
    encoded = json.dumps(presentation, ensure_ascii=False, sort_keys=True)
    if "epoch-secret" in encoded or "pond-secret" in encoded or "epoch-new" in encoded or "pond-new" in encoded:
        raise SystemExit("E242 exposed opaque lifecycle values")
    if presentation.get("operator_state") != "fresh_instance_boundary_observed":
        raise SystemExit("E242 fresh instance state mapping lost")
    if chr(0x4E0D) not in presentation.get("caveat", "") or chr(0x6062) + chr(0x590D) not in presentation.get("caveat", ""):
        raise SystemExit("E242 fresh boundary caveat overclaimed recovery")
    if presentation.get("negative_capabilities", {}).get("fresh_boundary_is_state_recovery") is not False:
        raise SystemExit("E242 fresh boundary became recovery")
    if validate_worldbridge_quarantine_operator_presentation(presentation).get("valid") is not True:
        raise SystemExit("E242 fresh presentation invalid")

    unavailable = {
        "schema_version": 1, "status": "unavailable", "read_only": True,
        "availability": "unavailable", "reason": "host_unavailable",
        "negative_capabilities": {
            **{key: False for key in NEGATIVE_CAPABILITIES[:10]}, "default_ready": False,
        },
    }
    unavailable_presentation = present_worldbridge_quarantine_lifecycle(unavailable)
    if unavailable_presentation.get("availability") != "unavailable" or unavailable_presentation.get("operator_state") != "unavailable":
        raise SystemExit("E242 unavailable behavior lost")

    forbidden_authority = (
        "PyQt6", "QWidget", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib",
        "socket", "threading", "asyncio", "pickle", "deserialize_pond(",
    )
    forbidden_inspector = ("PyQt6", "QWidget", "Pond(", "GameViewport", "command_binding")
    for path, forbidden in ((AUTHORITY, forbidden_authority), (INSPECTOR, forbidden_inspector)):
        source_text = path.read_text(encoding="utf-8-sig")
        if any(token in source_text for token in forbidden):
            raise SystemExit(f"E242 read-only boundary crossed in {path.name}")

    inspector_tree = ast.parse(INSPECTOR.read_text(encoding="utf-8-sig"))
    loader = ast.unparse(_function(inspector_tree, "load_worldbridge_quarantine_operator_presentation_view_model"))
    if "registry.run(WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_COMMAND_ID, {})" not in loader:
        raise SystemExit("E242 Inspector loader no longer calls only the read-only command")
    for forbidden in ("_start_simulation", "_stop_simulation", "Pond(", "GameViewport"):
        if forbidden in loader:
            raise SystemExit("E242 Inspector loader gained runtime control")

    command = get_command_registry().describe("runtime.worldbridge.quarantine_operator_presentation")
    if command.get("mutates") is not False or command.get("requires_gui") is not False:
        raise SystemExit("E242 presentation command is not headless/read-only")
    commands_tree = ast.parse(COMMANDS.read_text(encoding="utf-8-sig"))
    handler = ast.unparse(_function(commands_tree, "_runtime_worldbridge_quarantine_operator_presentation"))
    if "get_worldbridge_quarantine_lifecycle_host" not in handler or "present_worldbridge_quarantine_lifecycle" not in handler:
        raise SystemExit("E242 command lost bounded source-consumer path")
    if any(token in handler for token in ("_start_simulation", "_stop_simulation", "Pond(", "GameViewport")):
        raise SystemExit("E242 command gained runtime control")

    status = build_runtime_worldbridge_status()
    if status.get("failure_quarantine_operator_presentation_contract") != contract:
        raise SystemExit("E242 runtime status does not nest presentation contract")
    if "quarantine_operator_presentation_module" not in status.get("pilot_modules", []):
        raise SystemExit("E242 runtime status lost presentation module")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E242 changed dual/default-ready boundary")

    print(json.dumps({
        "status": "ok", "opaque_lifecycle_values_exposed": False,
        "fresh_boundary_is_state_recovery": False, "operator_action_admitted": False,
        "ui_authority": False, "default_ready": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
