# -*- coding: utf-8 -*-
"""Cross-lane behavior routing and ownership witness.

The witness proves where behavior is allowed to cross the SR/PS membrane. It
admits active-state propagation, but keeps visible state SR-local, membrane and
script behavior lane-owned, and all behavior equivalence/lossless/tick-merge
claims closed.
"""
from __future__ import annotations

import copy
import ast
import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .world_bridge_e557_field_roundtrip_authority import (
    validate_worldbridge_e557_field_roundtrip_authority,
)
from .world_bridge_lane_local_roundtrip import (
    build_worldbridge_lane_local_roundtrip_admission,
)
from .world_bridge_membrane_behavior_audit import (
    build_worldbridge_membrane_behavior_audit,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e558_cross_lane_behavior_authority"
SCOPE = "explicit_behavior_routing_with_lane_local_behavior_ownership"
ADMISSION_EFFECT = "none"
PROOF_FIELDS = (
    "field_authority_valid",
    "active_sr_to_ps",
    "active_ps_to_sr",
    "visible_sr_local",
    "inactive_sr_script_gate",
    "inactive_ps_update_gate",
    "membrane_behavior_isolated",
    "membrane_behavior_live",
    "lane_local_roundtrip_valid",
    "sr_topology_consumer_parity",
    "sr_scripts_fail_closed",
    "ps_scripts_restored",
    "script_live_owner_preserved",
    "hierarchy_ps_restored",
    "no_untracked_behavior_route",
    "replay_authority_bound",
)
CLOSED_ADMISSION_FIELDS = (
    "cross_lane_behavior_admitted",
    "behavior_equivalence_admitted",
    "lossless",
    "tick_merge_admitted",
    "default_ready",
)
ACTIVE_EVIDENCE_KEYS = {
    "sr_to_ps_active",
    "ps_to_sr_active",
    "visible_sr_local",
    "inactive_sr_script_skipped",
    "inactive_ps_update_skipped",
    "untracked_behavior_routes",
}
LANE_EVIDENCE_KEYS = {
    "schema_version",
    "status",
    "read_only",
    "sr_contract",
    "ps_contract",
    "sr",
    "ps",
    "admission",
    "cross_lane_behavior_admitted",
    "tick_merge_admitted",
    "full_unified_replay_admitted",
    "lossless",
    "default_ready",
}
WITNESS_KEYS = (
    "schema_version",
    "status",
    "read_only",
    "scope",
    "field_roundtrip_witness",
    "active_behavior_evidence",
    "lane_local_roundtrip_evidence",
    "membrane_behavior_audit",
    "field_witness_digest",
    "lane_local_digest",
    "membrane_audit_digest",
    "behavior_routing",
    "remaining_behavior_blockers",
    *PROOF_FIELDS,
    "grants_admission",
    "admission_effect",
    *CLOSED_ADMISSION_FIELDS,
    "witness_digest",
)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_FIELD_MAPPER_PATH = Path(__file__).with_name("world_bridge_field_mapper.py")
_ALLOWED_ACTIVE_BEHAVIOR_METHODS = {"sync_sr_to_ps", "sync_ps_to_sr"}


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _json_copy(value: object, field: str) -> Any:
    try:
        return json.loads(_canonical(value).decode("utf-8"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be finite canonical JSON") from exc


def _mapping_copy(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a mapping")
    copied = _json_copy(dict(value), field)
    if not isinstance(copied, dict):
        raise TypeError(f"{field} must remain a mapping")
    return copied


def _witness_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["witness_digest"] = ""
    return _digest(payload)


def _untracked_behavior_route_count() -> int:
    tree = ast.parse(
        _FIELD_MAPPER_PATH.read_text(encoding="utf-8"),
        filename=str(_FIELD_MAPPER_PATH),
    )
    mapper = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "WorldBridgeFieldMapper"
        ),
        None,
    )
    if mapper is None:
        return 1
    count = 0
    for method in mapper.body:
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        allowed = method.name in _ALLOWED_ACTIVE_BEHAVIOR_METHODS
        for node in ast.walk(method):
            behavior_name = None
            if isinstance(node, ast.Attribute) and node.attr in {
                "active",
                "visible",
            }:
                behavior_name = node.attr
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"getattr", "hasattr", "setattr"}
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value in {"active", "visible"}
            ):
                behavior_name = str(node.args[1].value)
            if behavior_name == "visible" or (
                behavior_name == "active" and not allowed
            ):
                count += 1
    return count


def build_active_behavior_evidence() -> dict[str, Any]:
    """Exercise the reviewed active/visible/inactive behavior routes."""
    from builtin.entity_types.organism import Organism
    from core.Lotucosm.runtime.world_bridge import (
        sync_organism_to_sr_display,
        sync_sr_entity_to_organism,
    )
    from core.Lotucosm.scene_runtime.tick_phases import run_script_tick_batch

    entity = SimpleNamespace(
        position=(0.0, 0.0),
        velocity=(0.0, 0.0),
        acceleration=(0.0, 0.0),
        energy=10.0,
        health=5.0,
        size=10.0,
        radius=10.0,
        active=False,
        visible=False,
    )
    organism = Organism("e558-active", (0.0, 0.0), energy=10.0)

    entity.active = True
    sync_sr_entity_to_organism(entity, organism)
    sr_to_ps_active = organism.active is True

    organism.active = False
    sync_organism_to_sr_display(organism, entity)
    ps_to_sr_active = entity.active is False
    visible_sr_local = entity.visible is False

    class ScriptProbe:
        def __init__(self) -> None:
            self.calls = 0

        def step_scripts(self, _context: object) -> None:
            self.calls += 1

    class InactiveEntity:
        id = "e558-inactive-sr"
        active = False
        position = [0.0, 0.0]
        scripts = [ScriptProbe()]

    inactive = InactiveEntity()
    run_script_tick_batch(
        None,
        entities_batch=[inactive],
        all_e=[inactive],
        dt=0.016,
        spawn_list=[],
        remove_ids=[],
        damage_list=[],
        fx_list=[],
        niche_p=0.0,
        deriv=0.0,
        load_before=0.0,
        peer_scale=1.0,
        min_horizon=0.0,
        sr_caps=None,
        w=100,
        h=100,
        input_snap=None,
        use_prev_inbound=False,
    )
    inactive_sr_script_skipped = inactive.scripts[0].calls == 0

    class UpdateProbe:
        def __init__(self) -> None:
            self.calls = 0

        def update(self, _delta_time: float) -> None:
            self.calls += 1

    inactive_organism = Organism(
        "e558-inactive-ps",
        (0.0, 0.0),
        energy=10.0,
    )
    inactive_organism.active = False
    update_probe = UpdateProbe()
    inactive_organism.components.update({"probe": update_probe})
    inactive_organism.update(1.0)
    inactive_ps_update_skipped = update_probe.calls == 0

    return {
        "sr_to_ps_active": sr_to_ps_active,
        "ps_to_sr_active": ps_to_sr_active,
        "visible_sr_local": visible_sr_local,
        "inactive_sr_script_skipped": inactive_sr_script_skipped,
        "inactive_ps_update_skipped": inactive_ps_update_skipped,
        "untracked_behavior_routes": _untracked_behavior_route_count(),
    }


def _lane_local_validation(evidence: Mapping[str, Any]) -> dict[str, Any]:
    if set(evidence) != LANE_EVIDENCE_KEYS:
        return {
            "valid": False,
            "sr_aligned": False,
            "ps_aligned": False,
            "errors": ["lane_local_evidence_keys_invalid"],
        }
    if (
        evidence.get("schema_version") != 1
        or evidence.get("status")
        != "worldbridge_lane_local_roundtrip_evidence"
        or evidence.get("read_only") is not True
        or evidence.get("cross_lane_behavior_admitted") is not False
        or evidence.get("tick_merge_admitted") is not False
        or evidence.get("full_unified_replay_admitted") is not False
        or evidence.get("lossless") is not False
        or evidence.get("default_ready") is not False
    ):
        return {
            "valid": False,
            "sr_aligned": False,
            "ps_aligned": False,
            "errors": ["lane_local_evidence_identity_invalid"],
        }
    admission = build_worldbridge_lane_local_roundtrip_admission(
        sr_evidence=evidence.get("sr"),
        ps_evidence=evidence.get("ps"),
    )
    errors: list[str] = []
    if evidence.get("admission") != admission:
        errors.append("lane_local_admission_mismatch")
    sr = evidence.get("sr")
    ps = evidence.get("ps")
    if not isinstance(sr, Mapping) or sr.get("malformed_owner_state_rejected") is not True:
        errors.append("sr_topology_fail_closed_missing")
    if not isinstance(ps, Mapping) or ps.get("behavior_lane_local") is not True:
        errors.append("ps_behavior_lane_local_missing")
    return {
        "valid": (
            not errors
            and admission.get("sr_aligned") is True
            and admission.get("ps_aligned") is True
        ),
        "sr_aligned": admission.get("sr_aligned") is True,
        "ps_aligned": admission.get("ps_aligned") is True,
        "errors": errors,
    }


def _script_cell(
    field_witness: Mapping[str, Any],
    lane: str,
) -> Mapping[str, Any] | None:
    result = field_witness.get("field_roundtrip_result")
    matrix = result.get("matrix") if isinstance(result, Mapping) else None
    if not isinstance(matrix, list):
        return None
    for cell in matrix:
        if (
            isinstance(cell, Mapping)
            and cell.get("field") == "scripts"
            and cell.get("lane") == lane
        ):
            return cell
    return None


def _hierarchy_cell(
    field_witness: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    result = field_witness.get("field_roundtrip_result")
    matrix = result.get("matrix") if isinstance(result, Mapping) else None
    if not isinstance(matrix, list):
        return None
    for cell in matrix:
        if (
            isinstance(cell, Mapping)
            and cell.get("field") == "hierarchy"
            and cell.get("lane") == "ps"
        ):
            return cell
    return None


def _evaluate(
    *,
    field_witness: Mapping[str, Any],
    active_evidence: Mapping[str, Any],
    lane_evidence: Mapping[str, Any],
    membrane_audit: Mapping[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    field_validation = validate_worldbridge_e557_field_roundtrip_authority(
        field_witness
    )
    field_authority_valid = (
        field_validation == {"valid": True, "errors": []}
    )
    if not field_authority_valid:
        errors.extend(f"field_{item}" for item in field_validation["errors"])

    if set(active_evidence) != ACTIVE_EVIDENCE_KEYS:
        errors.append("active_behavior_evidence_keys_invalid")
    expected_active = build_active_behavior_evidence()
    if active_evidence != expected_active:
        errors.append("active_behavior_evidence_mismatch")
    active_sr_to_ps = active_evidence.get("sr_to_ps_active") is True
    active_ps_to_sr = active_evidence.get("ps_to_sr_active") is True
    visible_sr_local = active_evidence.get("visible_sr_local") is True
    inactive_sr_script_gate = (
        active_evidence.get("inactive_sr_script_skipped") is True
    )
    inactive_ps_update_gate = (
        active_evidence.get("inactive_ps_update_skipped") is True
    )
    no_untracked_behavior_route = (
        active_evidence.get("untracked_behavior_routes") == 0
    )

    lane_validation = _lane_local_validation(lane_evidence)
    lane_local_roundtrip_valid = lane_validation["valid"] is True
    if not lane_local_roundtrip_valid:
        errors.extend(lane_validation["errors"])
    sr_topology_consumer_parity = lane_validation["sr_aligned"] is True

    membrane_expected = build_worldbridge_membrane_behavior_audit()
    if dict(membrane_audit) != membrane_expected:
        errors.append("membrane_behavior_audit_mismatch")
    membrane_behavior_isolated = (
        membrane_expected.get("cross_lane_behavior_isolated") is True
        and membrane_expected.get("producer_projection_bound") is True
    )
    membrane_behavior_live = (
        membrane_expected.get("behavior_is_lane_local") is True
        and bool(membrane_expected.get("ps_lane_usage", {}).get("calls"))
    )
    if not membrane_behavior_isolated:
        errors.append("membrane_behavior_not_isolated")
    if not membrane_behavior_live:
        errors.append("membrane_behavior_not_live")

    sr_script = _script_cell(field_witness, "sr")
    ps_script = _script_cell(field_witness, "ps")
    sr_scripts_fail_closed = (
        isinstance(sr_script, Mapping)
        and sr_script.get("verdict") == "fail_closed_restore"
    )
    ps_scripts_restored = (
        isinstance(ps_script, Mapping)
        and ps_script.get("verdict") == "restored"
    )
    script_live_owner_preserved = (
        isinstance(sr_script, Mapping)
        and sr_script.get("live_preserved_on_reject") is True
    )
    if not sr_scripts_fail_closed:
        errors.append("sr_script_policy_mismatch")
    if not ps_scripts_restored:
        errors.append("ps_script_restore_mismatch")
    if not script_live_owner_preserved:
        errors.append("script_live_owner_not_preserved")

    hierarchy = _hierarchy_cell(field_witness)
    hierarchy_ps_restored = (
        isinstance(hierarchy, Mapping)
        and hierarchy.get("verdict") == "restored"
    )
    if not hierarchy_ps_restored:
        errors.append("ps_hierarchy_restore_mismatch")

    replay_authority_bound = (
        field_witness.get("replay_authority_bound") is True
        and field_witness.get("remaining_mapping_blockers")
        is not None
    )

    proof = {
        "field_authority_valid": field_authority_valid,
        "active_sr_to_ps": active_sr_to_ps,
        "active_ps_to_sr": active_ps_to_sr,
        "visible_sr_local": visible_sr_local,
        "inactive_sr_script_gate": inactive_sr_script_gate,
        "inactive_ps_update_gate": inactive_ps_update_gate,
        "membrane_behavior_isolated": membrane_behavior_isolated,
        "membrane_behavior_live": membrane_behavior_live,
        "lane_local_roundtrip_valid": lane_local_roundtrip_valid,
        "sr_topology_consumer_parity": sr_topology_consumer_parity,
        "sr_scripts_fail_closed": sr_scripts_fail_closed,
        "ps_scripts_restored": ps_scripts_restored,
        "script_live_owner_preserved": script_live_owner_preserved,
        "hierarchy_ps_restored": hierarchy_ps_restored,
        "no_untracked_behavior_route": no_untracked_behavior_route,
        "replay_authority_bound": replay_authority_bound,
    }
    for field in PROOF_FIELDS:
        if proof[field] is not True:
            errors.append(f"{field}_not_proven")

    routing = {
        "active": "sr_to_ps_and_ps_to_sr",
        "visible": "sr_local_presentation_only",
        "membrane_behavior": "ps_lane_local",
        "sr_scripts": "fail_closed_on_portable_restore",
        "ps_scripts": "lane_local_transaction_restore",
        "hierarchy": "ps_local_restore_with_sr_topology_owner",
    }
    return list(dict.fromkeys(errors)), {
        **proof,
        "field_witness_digest": field_witness.get("witness_digest"),
        "lane_local_digest": _digest(lane_evidence),
        "membrane_audit_digest": _digest(membrane_expected),
        "behavior_routing": routing,
    }


def build_worldbridge_e558_cross_lane_behavior_authority(
    *,
    field_roundtrip_witness: Mapping[str, Any],
    lane_local_roundtrip_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a behavior-routing witness without claiming equivalence."""
    field_witness = _mapping_copy(
        field_roundtrip_witness,
        "field_roundtrip_witness",
    )
    lane_evidence = _mapping_copy(
        lane_local_roundtrip_evidence,
        "lane_local_roundtrip_evidence",
    )
    active_evidence = copy.deepcopy(build_active_behavior_evidence())
    membrane_audit = copy.deepcopy(build_worldbridge_membrane_behavior_audit())
    errors, projection = _evaluate(
        field_witness=field_witness,
        active_evidence=active_evidence,
        lane_evidence=lane_evidence,
        membrane_audit=membrane_audit,
    )
    if errors:
        raise ValueError(
            "E558 behavior witness rejected: " + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "field_roundtrip_witness": field_witness,
        "active_behavior_evidence": active_evidence,
        "lane_local_roundtrip_evidence": lane_evidence,
        "membrane_behavior_audit": membrane_audit,
        **projection,
        "remaining_behavior_blockers": [
            "behavior_equivalence_not_proven",
            "lossless_mapping_not_proven",
            "sr_ps_tick_merge_not_proven",
        ],
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e558_cross_lane_behavior_authority(
    value: object,
) -> dict[str, Any]:
    """Recompute active and membrane behavior evidence from producers."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    if set(value) != set(WITNESS_KEYS):
        errors.append("witness_keys_invalid")
    try:
        _canonical(value)
    except (TypeError, ValueError, OverflowError):
        return {"valid": False, "errors": errors + ["witness_not_canonical_json"]}
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_required")
    if value.get("scope") != SCOPE:
        errors.append("scope_mismatch")

    field_witness = value.get("field_roundtrip_witness")
    active = value.get("active_behavior_evidence")
    lane = value.get("lane_local_roundtrip_evidence")
    membrane = value.get("membrane_behavior_audit")
    if not all(
        isinstance(item, Mapping)
        for item in (field_witness, active, lane, membrane)
    ):
        return {
            "valid": False,
            "errors": errors + ["witness_payload_invalid"],
        }
    revalidation, projection = _evaluate(
        field_witness=field_witness,
        active_evidence=active,
        lane_evidence=lane,
        membrane_audit=membrane,
    )
    errors.extend(revalidation)
    for field, expected in projection.items():
        if value.get(field) != expected:
            errors.append(f"{field}_mismatch")
        if field in PROOF_FIELDS and value.get(field) is not True:
            errors.append(f"{field}_not_true")
    if value.get("remaining_behavior_blockers") != [
        "behavior_equivalence_not_proven",
        "lossless_mapping_not_proven",
        "sr_ps_tick_merge_not_proven",
    ]:
        errors.append("remaining_behavior_blockers_mismatch")
    if value.get("grants_admission") is not False:
        errors.append("grants_admission_overclaim")
    if value.get("admission_effect") != ADMISSION_EFFECT:
        errors.append("admission_effect_mismatch")
    for field in CLOSED_ADMISSION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    digest = value.get("witness_digest")
    if (
        not isinstance(digest, str)
        or _DIGEST_RE.fullmatch(digest) is None
        or digest != _witness_digest(value)
    ):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}


__all__ = [
    "ACTIVE_EVIDENCE_KEYS",
    "ADMISSION_EFFECT",
    "CLOSED_ADMISSION_FIELDS",
    "LANE_EVIDENCE_KEYS",
    "PROOF_FIELDS",
    "SCHEMA_VERSION",
    "SCOPE",
    "STATUS",
    "WITNESS_KEYS",
    "build_active_behavior_evidence",
    "build_worldbridge_e558_cross_lane_behavior_authority",
    "validate_worldbridge_e558_cross_lane_behavior_authority",
]
