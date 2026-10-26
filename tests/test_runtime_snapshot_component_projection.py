# -*- coding: utf-8 -*-
"""Track-specific runtime snapshot component projection contract."""
from __future__ import annotations

from copy import deepcopy

from core.Lotucosm.runtime.runtime_snapshot_component_projection import (
    project_ps_runtime_snapshot_components,
    project_sr_runtime_snapshot_components,
)


def _ps_envelope(*, component_facts=...):
    snapshot = {
        "source": "read_only_json_snapshot",
        "organism_id": "org_1",
        "entity_type": "Organism",
    }
    if component_facts is not ...:
        snapshot["component_facts"] = component_facts
    return {
        "schema_version": 1,
        "status": "ok",
        "scope": "ps_runtime_organism",
        "authority": "ps_runtime_snapshot_authority",
        "track": "ps_batch",
        "read_only": True,
        "identity_relation": "run_scoped_not_cross_track",
        "identity": {
            "track": "ps_batch",
            "run_id": "ps_run",
            "organism_id": "org_1",
        },
        "revision": 7,
        "snapshot": snapshot,
    }


def _sr_envelope(*, component_facts=...):
    snapshot = {
        "source": "read_only_json_snapshot",
        "entity_id": "org_1",
        "entity_type": "organism",
    }
    if component_facts is not ...:
        snapshot["component_facts"] = component_facts
    return {
        "schema_version": 1,
        "status": "ok",
        "scope": "selected_sr_runtime_entity",
        "authority": "sr_selected_identity_correlation",
        "track": "sr_play",
        "read_only": True,
        "selection_relation": "scene_correlated_not_unified",
        "identity": {
            "track": "sr_play",
            "runtime_epoch": "sr_epoch",
            "scene_path": "scenes/demo.pond",
            "entity_id": "org_1",
        },
        "revision": 3,
        "snapshot": snapshot,
    }


def test_ok_snapshot_without_component_facts_is_not_proven_not_empty() -> None:
    result = project_ps_runtime_snapshot_components(_ps_envelope())

    assert result["status"] == "not_proven"
    assert result["reason"] == "component_facts_unavailable"
    assert result["component_count"] is None
    assert result["components"] == []
    assert result["maps_live_runtime_snapshot_facts"] is False


def test_ps_projection_uses_fixed_whitelist_and_deterministic_order() -> None:
    facts = [
        {
            "source": "ps_component_registry",
            "identity_relation": "ps_component_registry_member",
            "component_id": "sensor_b",
            "component_type": "touch_sensor",
            "location": "external",
            "acquired": False,
            "congenital": True,
            "attach_point": "north",
            "connection_count": 2,
            "inspectable_properties": {"signal_threshold": 0.3},
            "component_fields": {"signal_threshold": 0.3, "sensing_range": 24.0},
            "forbidden_extra": "must not leak",
        },
        {
            "source": "ps_component_registry",
            "identity_relation": "ps_component_registry_member",
            "component_id": "membrane_a",
            "component_type": "membrane",
            "location": "external",
            "acquired": True,
            "congenital": False,
            "attach_point": None,
            "connection_count": 1,
            "inspectable_properties": {"radius": 30.0},
            "component_fields": {
                "radius": 30.0,
                "ingest_threshold": 0.4,
                "efficiency": 1.2,
            },
        },
    ]
    result = project_ps_runtime_snapshot_components(
        _ps_envelope(component_facts=facts)
    )

    assert result["status"] == "ok"
    assert result["track"] == "ps_batch"
    assert result["revision"] == 7
    assert result["identity"]["organism_id"] == "org_1"
    assert result["component_count"] == 2
    assert result["coverage"] == {"membrane": 1, "touch_sensor": 1}
    assert [item["component_id"] for item in result["components"]] == [
        "membrane_a",
        "sensor_b",
    ]
    assert result["maps_live_components"] is False
    assert result["maps_live_runtime_snapshot_facts"] is True
    assert "forbidden_extra" not in result["components"][1]
    assert result["components"][1]["connection_count"] == 2


def test_sr_projection_preserves_attachment_semantics_without_ps_equivalence() -> None:
    result = project_sr_runtime_snapshot_components(
        _sr_envelope(
            component_facts=[
                {
                    "source": "sr_attached_runtime_entity",
                    "identity_relation": "attached_projection_not_ps_component_equivalence",
                    "component_id": "sensor_1",
                    "component_type": "sensor",
                    "location": "attached",
                    "attach_point": [5.0, -2.0],
                    "connection_count": 3,
                    "inspectable_properties": {},
                    "component_fields": {},
                }
            ]
        )
    )

    assert result["status"] == "ok"
    assert result["identity_relation"] == (
        "attached_projection_not_ps_component_equivalence"
    )
    component = result["components"][0]
    assert component["source"] == "sr_attached_runtime_entity"
    assert component["attach_point"] == [5.0, -2.0]
    assert "acquired" not in component
    assert "congenital" not in component
    assert "lossless_worldbridge_mapping" in result["do_not_claim"]
    assert "ps_component_equivalence" in result["do_not_claim"]


def test_non_success_status_passes_through_before_snapshot_validation() -> None:
    envelope = _ps_envelope(component_facts=[])
    envelope["status"] = "stale"
    envelope.pop("snapshot")

    result = project_ps_runtime_snapshot_components(envelope)

    assert result["status"] == "stale"
    assert result["revision"] == 7
    assert result["identity"]["run_id"] == "ps_run"
    assert result["component_count"] is None


def test_projection_is_copy_isolated() -> None:
    source = _ps_envelope(
        component_facts=[
            {
                "source": "ps_component_registry",
                "identity_relation": "ps_component_registry_member",
                "component_id": "sensor_1",
                "component_type": "sensor",
                "location": "external",
                "acquired": False,
                "congenital": True,
                "attach_point": None,
                "connection_count": 0,
                "inspectable_properties": {"signal_threshold": 0.2},
                "component_fields": {"signal_threshold": 0.2},
            }
        ]
    )
    original = deepcopy(source)

    first = project_ps_runtime_snapshot_components(source)
    first["identity"]["organism_id"] = "mutated"
    first["components"][0]["component_fields"]["signal_threshold"] = 99.0
    second = project_ps_runtime_snapshot_components(source)

    assert source == original
    assert second["identity"]["organism_id"] == "org_1"
    assert second["components"][0]["component_fields"]["signal_threshold"] == 0.2


def test_wrong_track_and_malformed_facts_fail_deterministically() -> None:
    wrong_track = _ps_envelope(component_facts=[])
    wrong_track["track"] = "sr_play"
    assert project_ps_runtime_snapshot_components(wrong_track)["status"] == (
        "unsupported_track"
    )

    non_finite = _ps_envelope(
        component_facts=[
            {
                "source": "ps_component_registry",
                "identity_relation": "ps_component_registry_member",
                "component_id": "bad",
                "component_type": "sensor",
                "location": "external",
                "acquired": False,
                "congenital": True,
                "attach_point": None,
                "connection_count": 0,
                "inspectable_properties": {},
                "component_fields": {"signal_threshold": float("nan")},
            }
        ]
    )
    malformed = project_ps_runtime_snapshot_components(non_finite)
    assert malformed["status"] == "error"
    assert malformed["reason"] == "invalid_component_facts"

    duplicate = _sr_envelope(
        component_facts=[
            {
                "source": "sr_attached_runtime_entity",
                "identity_relation": "attached_projection_not_ps_component_equivalence",
                "component_id": "sensor_1",
                "component_type": "sensor",
                "location": "attached",
                "attach_point": [0.0, 0.0],
                "connection_count": 0,
                "inspectable_properties": {},
                "component_fields": {},
            },
            {
                "source": "sr_attached_runtime_entity",
                "identity_relation": "attached_projection_not_ps_component_equivalence",
                "component_id": "sensor_1",
                "component_type": "sensor",
                "location": "attached",
                "attach_point": [1.0, 1.0],
                "connection_count": 0,
                "inspectable_properties": {},
                "component_fields": {},
            },
        ]
    )
    duplicated = project_sr_runtime_snapshot_components(duplicate)
    assert duplicated["status"] == "error"
    assert duplicated["reason"] == "invalid_component_facts"
