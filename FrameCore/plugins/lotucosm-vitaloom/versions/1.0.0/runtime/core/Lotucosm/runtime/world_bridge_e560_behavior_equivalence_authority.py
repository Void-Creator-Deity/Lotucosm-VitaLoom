# -*- coding: utf-8 -*-
"""Scoped SR/PS behavior-equivalence witness.

Equivalence is admitted only for the observed ``active`` lifecycle contract:
bidirectional boolean propagation and the inactive execution gate. Presentation,
membrane behavior, scripts, and hierarchy remain explicitly lane-local. The
witness does not claim full behavioral equivalence, lossless mapping, or replay.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from types import SimpleNamespace
from typing import Any

from .world_bridge_e558_cross_lane_behavior_authority import (
    validate_worldbridge_e558_cross_lane_behavior_authority,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e560_behavior_equivalence_authority"
SCOPE = "declared_overlap_only_active_lifecycle_gate"
EQUIVALENCE_POLICY = "active_lifecycle_gate_observation_equivalence_v1"
ADMISSION_EFFECT = "none"
ELIGIBLE_BEHAVIOR_ROUTES = ("active",)
LANE_LOCAL_BEHAVIOR_ROUTES = {
    "visible": "sr_local_presentation_only",
    "membrane_behavior": "ps_lane_local",
    "sr_scripts": "fail_closed_on_portable_restore",
    "ps_scripts": "lane_local_transaction_restore",
    "hierarchy": "ps_local_restore_with_sr_topology_owner",
}
EVIDENCE_KEYS = {
    "schema_version",
    "status",
    "read_only",
    "active_roundtrip_cases",
    "active_gate_cases",
    "visible_probe",
    "lane_local_routes",
}
PROOF_FIELDS = (
    "routing_authority_valid",
    "routing_digest_bound",
    "active_sr_to_ps_false",
    "active_sr_to_ps_true",
    "active_ps_to_sr_false",
    "active_ps_to_sr_true",
    "sr_inactive_gate_closed",
    "sr_active_gate_open",
    "ps_inactive_gate_closed",
    "ps_active_gate_open",
    "gate_observations_non_vacuous",
    "visible_lane_local_preserved",
    "excluded_routes_not_promoted",
)
CLOSED_ADMISSION_FIELDS = (
    "cross_lane_behavior_admitted",
    "behavior_equivalence_admitted",
    "lossless",
    "tick_merge_admitted",
    "default_ready",
)
WITNESS_KEYS = (
    "schema_version",
    "status",
    "read_only",
    "scope",
    "equivalence_policy",
    "cross_lane_behavior_witness",
    "routing_witness_digest",
    "behavior_equivalence_evidence",
    "eligible_behavior_routes",
    "lane_local_behavior_routes",
    "equivalence_result_digest",
    *PROOF_FIELDS,
    "remaining_behavior_blockers",
    "grants_admission",
    "admission_effect",
    *CLOSED_ADMISSION_FIELDS,
    "witness_digest",
)


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


def _active_roundtrip_case(direction: str, active: bool) -> dict[str, Any]:
    from builtin.entity_types.organism import Organism
    from core.Lotucosm.entity import EntityBase
    from core.Lotucosm.runtime.world_bridge_field_mapper import (
        WorldBridgeFieldMapper,
    )

    entity = EntityBase(
        f"e560-sr-{direction}-{int(active)}",
        position=(0.0, 0.0),
    )
    organism = Organism(
        f"e560-ps-{direction}-{int(active)}",
        (0.0, 0.0),
        energy=10.0,
    )
    mapper = WorldBridgeFieldMapper()
    if direction == "sr_to_ps":
        entity.active = active
        mapper.sync_sr_to_ps(entity, organism)
        observed = organism.active
    elif direction == "ps_to_sr":
        organism.active = active
        mapper.sync_ps_to_sr(organism, entity)
        observed = entity.active
    else:
        raise ValueError(f"unsupported active direction: {direction}")
    return {
        "case_id": f"{direction}_{str(active).lower()}",
        "direction": direction,
        "input": active,
        "observed": observed,
        "matches": observed is active,
    }


def _sr_gate_observation(active: bool) -> int:
    from core.Lotucosm.scene_runtime.tick_phases import run_script_tick_batch

    class ScriptGateProbe:
        def __init__(self) -> None:
            self.calls = 0

        def step_scripts(self, _context: object) -> None:
            self.calls += 1

    entity = ScriptGateProbe()
    entity.id = f"e560-sr-gate-{int(active)}"
    entity.entity_type = "probe"
    entity.active = active
    entity.position = (0.0, 0.0)
    entity.radius = 1.0
    host = SimpleNamespace(
        _scene_runtime_emissions_prev={},
        _sr_field_grid=None,
        _sr_game_mode=False,
        _scene_runtime_time=0.0,
        _scene_runtime_neighbor_ids={},
        _sr_inbound_for_entity=lambda _entity_id, use_prev=False: {},
        _parent_organism_for_membrane_child=lambda _entity_id: None,
        _record_script_runtime_failure=None,
    )
    run_script_tick_batch(
        host,
        entities_batch=[entity],
        all_e=[entity],
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
    return entity.calls


def _ps_gate_observation(active: bool) -> int:
    from builtin.entity_types.organism import Organism

    class UpdateGateProbe:
        def __init__(self) -> None:
            self.calls = 0

        def update(self, _delta_time: float) -> None:
            self.calls += 1

    organism = Organism(
        f"e560-ps-gate-{int(active)}",
        (0.0, 0.0),
        energy=10.0,
    )
    organism.active = active
    probe = UpdateGateProbe()
    organism.components.update({"probe": probe})
    organism.update(1.0)
    return probe.calls


def build_behavior_equivalence_evidence() -> dict[str, Any]:
    """Exercise the declared overlap and explicit lane-local exclusions."""
    from builtin.entity_types.organism import Organism
    from core.Lotucosm.entity import EntityBase
    from core.Lotucosm.runtime.world_bridge import (
        sync_organism_to_sr_display,
    )

    entity = EntityBase("e560-visible", position=(0.0, 0.0))
    organism = Organism("e560-visible-ps", (0.0, 0.0), energy=10.0)
    entity.visible = False
    sync_organism_to_sr_display(organism, entity)
    visible_probe = {
        "before": False,
        "after": bool(getattr(entity, "visible", True)),
        "sr_local": getattr(entity, "visible", True) is False,
    }
    return {
        "schema_version": 1,
        "status": "worldbridge_e560_behavior_equivalence_evidence",
        "read_only": True,
        "active_roundtrip_cases": [
            _active_roundtrip_case("sr_to_ps", False),
            _active_roundtrip_case("sr_to_ps", True),
            _active_roundtrip_case("ps_to_sr", False),
            _active_roundtrip_case("ps_to_sr", True),
        ],
        "active_gate_cases": {
            "sr_inactive": {"expected": 0, "observed": _sr_gate_observation(False)},
            "sr_active": {"expected": 1, "observed": _sr_gate_observation(True)},
            "ps_inactive": {"expected": 0, "observed": _ps_gate_observation(False)},
            "ps_active": {"expected": 1, "observed": _ps_gate_observation(True)},
        },
        "visible_probe": visible_probe,
        "lane_local_routes": copy.deepcopy(LANE_LOCAL_BEHAVIOR_ROUTES),
    }


def _roundtrip_cases(evidence: Mapping[str, Any]) -> dict[tuple[str, bool], Mapping[str, Any]]:
    cases = evidence.get("active_roundtrip_cases")
    if not isinstance(cases, list):
        return {}
    result: dict[tuple[str, bool], Mapping[str, Any]] = {}
    for item in cases:
        if not isinstance(item, Mapping):
            continue
        direction = item.get("direction")
        active = item.get("input")
        if isinstance(direction, str) and isinstance(active, bool):
            result[(direction, active)] = item
    return result


def _gate_observed(
    gates: Mapping[str, Any],
    name: str,
) -> int | None:
    item = gates.get(name)
    if not isinstance(item, Mapping):
        return None
    observed = item.get("observed")
    return observed if isinstance(observed, int) else None


def _evaluate(
    *,
    behavior_witness: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    routing_validation = validate_worldbridge_e558_cross_lane_behavior_authority(
        behavior_witness
    )
    routing_authority_valid = routing_validation == {
        "valid": True,
        "errors": [],
    }
    if not routing_authority_valid:
        errors.extend(
            f"routing_{item}" for item in routing_validation["errors"]
        )

    expected_routing = {
        "active": "sr_to_ps_and_ps_to_sr",
        **LANE_LOCAL_BEHAVIOR_ROUTES,
    }
    routing_digest_bound = (
        behavior_witness.get("behavior_routing") == expected_routing
        and isinstance(behavior_witness.get("witness_digest"), str)
    )
    if not routing_digest_bound:
        errors.append("routing_boundary_mismatch")

    if set(evidence) != EVIDENCE_KEYS:
        errors.append("behavior_equivalence_evidence_keys_invalid")
    expected_evidence = build_behavior_equivalence_evidence()
    if dict(evidence) != expected_evidence:
        errors.append("behavior_equivalence_evidence_mismatch")

    cases = _roundtrip_cases(evidence)
    expected_case_keys = {
        ("sr_to_ps", False),
        ("sr_to_ps", True),
        ("ps_to_sr", False),
        ("ps_to_sr", True),
    }
    if set(cases) != expected_case_keys:
        errors.append("active_roundtrip_case_matrix_incomplete")
    for key, case in cases.items():
        if (
            case.get("case_id")
            != f"{key[0]}_{str(key[1]).lower()}"
            or case.get("observed") is not key[1]
            or case.get("matches") is not True
        ):
            errors.append(f"active_roundtrip_case_invalid:{key[0]}:{key[1]}")

    gates = evidence.get("active_gate_cases")
    gates = gates if isinstance(gates, Mapping) else {}
    gate_expected = {
        "sr_inactive": 0,
        "sr_active": 1,
        "ps_inactive": 0,
        "ps_active": 1,
    }
    for name, expected in gate_expected.items():
        item = gates.get(name)
        if (
            not isinstance(item, Mapping)
            or item.get("expected") != expected
            or item.get("observed") != expected
        ):
            errors.append(f"active_gate_case_invalid:{name}")

    visible = evidence.get("visible_probe")
    active_evidence = behavior_witness.get("active_behavior_evidence")
    visible_lane_local_preserved = (
        isinstance(visible, Mapping)
        and visible.get("before") is False
        and visible.get("after") is False
        and visible.get("sr_local") is True
        and isinstance(active_evidence, Mapping)
        and active_evidence.get("visible_sr_local") is True
    )
    excluded_routes_not_promoted = (
        behavior_witness.get("behavior_routing")
        == expected_routing
        and evidence.get("lane_local_routes") == LANE_LOCAL_BEHAVIOR_ROUTES
        and set(ELIGIBLE_BEHAVIOR_ROUTES) == {"active"}
    )

    proof = {
        "routing_authority_valid": routing_authority_valid,
        "routing_digest_bound": routing_digest_bound,
        "active_sr_to_ps_false": (
            cases.get(("sr_to_ps", False), {}).get("matches") is True
        ),
        "active_sr_to_ps_true": (
            cases.get(("sr_to_ps", True), {}).get("matches") is True
        ),
        "active_ps_to_sr_false": (
            cases.get(("ps_to_sr", False), {}).get("matches") is True
        ),
        "active_ps_to_sr_true": (
            cases.get(("ps_to_sr", True), {}).get("matches") is True
        ),
        "sr_inactive_gate_closed": (
            _gate_observed(gates, "sr_inactive") == 0
        ),
        "sr_active_gate_open": (
            _gate_observed(gates, "sr_active") == 1
        ),
        "ps_inactive_gate_closed": (
            _gate_observed(gates, "ps_inactive") == 0
        ),
        "ps_active_gate_open": (
            _gate_observed(gates, "ps_active") == 1
        ),
        "gate_observations_non_vacuous": (
            (_gate_observed(gates, "sr_active") or 0) > 0
            and (_gate_observed(gates, "ps_active") or 0) > 0
        ),
        "visible_lane_local_preserved": visible_lane_local_preserved,
        "excluded_routes_not_promoted": excluded_routes_not_promoted,
    }
    for field in PROOF_FIELDS:
        if proof[field] is not True:
            errors.append(f"{field}_not_proven")

    return list(dict.fromkeys(errors)), {
        **proof,
        "routing_witness_digest": behavior_witness.get("witness_digest"),
        "equivalence_result_digest": _digest(expected_evidence),
    }


def build_worldbridge_e560_behavior_equivalence_authority(
    *,
    cross_lane_behavior_witness: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a scoped behavior-equivalence witness."""
    behavior_witness = _mapping_copy(
        cross_lane_behavior_witness,
        "cross_lane_behavior_witness",
    )
    evidence = copy.deepcopy(build_behavior_equivalence_evidence())
    errors, projection = _evaluate(
        behavior_witness=behavior_witness,
        evidence=evidence,
    )
    if errors:
        raise ValueError(
            "E560 behavior-equivalence witness rejected: "
            + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "equivalence_policy": EQUIVALENCE_POLICY,
        "cross_lane_behavior_witness": behavior_witness,
        "behavior_equivalence_evidence": evidence,
        "eligible_behavior_routes": list(ELIGIBLE_BEHAVIOR_ROUTES),
        "lane_local_behavior_routes": copy.deepcopy(
            LANE_LOCAL_BEHAVIOR_ROUTES
        ),
        **projection,
        "remaining_behavior_blockers": ["lossless_mapping_not_proven"],
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e560_behavior_equivalence_authority(
    value: object,
) -> dict[str, Any]:
    """Recompute the scoped equivalence evidence from live producers."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    if set(value) != set(WITNESS_KEYS):
        errors.append("witness_keys_invalid")
    try:
        _canonical(value)
    except (TypeError, ValueError, OverflowError):
        return {
            "valid": False,
            "errors": errors + ["witness_not_canonical_json"],
        }
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_required")
    if value.get("scope") != SCOPE:
        errors.append("scope_mismatch")
    if value.get("equivalence_policy") != EQUIVALENCE_POLICY:
        errors.append("equivalence_policy_mismatch")

    behavior = value.get("cross_lane_behavior_witness")
    evidence = value.get("behavior_equivalence_evidence")
    if not isinstance(behavior, Mapping) or not isinstance(evidence, Mapping):
        return {
            "valid": False,
            "errors": errors + ["witness_payload_invalid"],
        }
    revalidation, projection = _evaluate(
        behavior_witness=behavior,
        evidence=evidence,
    )
    errors.extend(revalidation)
    for field, expected in projection.items():
        if value.get(field) != expected:
            errors.append(f"{field}_mismatch")
        if field in PROOF_FIELDS and value.get(field) is not True:
            errors.append(f"{field}_not_true")
    if value.get("eligible_behavior_routes") != list(
        ELIGIBLE_BEHAVIOR_ROUTES
    ):
        errors.append("eligible_behavior_routes_mismatch")
    if value.get("lane_local_behavior_routes") != LANE_LOCAL_BEHAVIOR_ROUTES:
        errors.append("lane_local_behavior_routes_mismatch")
    if value.get("remaining_behavior_blockers") != [
        "lossless_mapping_not_proven"
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
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        or digest != _witness_digest(value)
    ):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}


__all__ = [
    "ADMISSION_EFFECT",
    "CLOSED_ADMISSION_FIELDS",
    "ELIGIBLE_BEHAVIOR_ROUTES",
    "EQUIVALENCE_POLICY",
    "EVIDENCE_KEYS",
    "LANE_LOCAL_BEHAVIOR_ROUTES",
    "PROOF_FIELDS",
    "SCHEMA_VERSION",
    "SCOPE",
    "STATUS",
    "WITNESS_KEYS",
    "build_behavior_equivalence_evidence",
    "build_worldbridge_e560_behavior_equivalence_authority",
    "validate_worldbridge_e560_behavior_equivalence_authority",
]
