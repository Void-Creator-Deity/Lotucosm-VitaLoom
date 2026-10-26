from __future__ import annotations

from core.Lotucosm.runtime.world_bridge_ps_component_corpus import (
    build_worldbridge_ps_component_corpus,
    build_worldbridge_ps_component_persistence_audit,
)


def test_ps_component_corpus_probes_all_registered_types_as_facts() -> None:
    corpus = build_worldbridge_ps_component_corpus()
    assert corpus["read_only"] is True
    assert corpus["maps_live_objects"] is False
    assert corpus["component_type_count"] >= 8
    names = [item["type_name"] for item in corpus["component_types"]]
    assert names == sorted(names)
    assert "Membrane" in names
    assert "Sensor" in names
    assert "Actuator" in names
    assert all(item["status_keys"] for item in corpus["component_types"])


def test_ps_component_corpus_proves_local_surfaces_but_not_shared_replay() -> None:
    corpus = build_worldbridge_ps_component_corpus()
    evidence = corpus["evidence"]
    assert evidence["factory_construction"] is True
    assert evidence["status_projection"] is True
    assert evidence["inspector_metadata"] is True
    assert evidence["persistence_hydration_api"] is True
    assert evidence["lifecycle_ownership"] is True
    assert evidence["cross_lane_replay"] is False
    assert evidence["worldbridge_live_authority"] is False
    assert "cross_lane_deterministic_replay" in corpus["do_not_claim"]


def test_ps_component_corpus_is_deterministic_and_contains_json_safe_metadata() -> None:
    first = build_worldbridge_ps_component_corpus()
    second = build_worldbridge_ps_component_corpus()
    assert first == second
    membrane = next(item for item in first["component_types"] if item["type_name"] == "Membrane")
    assert "radius" in membrane["inspectable_properties"]
    assert membrane["lifecycle_methods"]["restore_persistent_state"] is True


def test_ps_component_persistence_audit_proves_local_round_trip_without_replay_claim() -> None:
    audit = build_worldbridge_ps_component_persistence_audit()
    assert audit["read_only"] is True
    assert audit["maps_live_objects"] is False
    assert audit["evidence"]["serializer_path_exercised"] is True
    assert audit["evidence"]["restore_persistent_state_path_exercised"] is True
    assert audit["evidence"]["persistence_authority_admitted"] is False
    assert audit["all_round_trip_ok"] is True
    assert audit["lossy_or_failed_types"] == []
    actuator = next(item for item in audit["records"] if item["type_name"] == "Actuator")
    assert actuator["serialized_type"] == "Actuator"
    assert actuator["restored_class_name"] == "MuscleActuator"
    assert actuator["round_trip_ok"] is True
    assert audit["evidence"]["cross_lane_replay"] is False


def test_ps_component_lifecycle_probe_records_owner_hook_order() -> None:
    corpus = build_worldbridge_ps_component_corpus()
    for item in corpus["lifecycle_ownership"]:
        assert item["add_component_succeeded"] is True
        assert item["remove_component_succeeded"] is True
        assert item["owner_binding_after_attach"] is True
        assert item["event_order"] == [
            f"attach:e309-owner-{item['type_name'].lower()}",
            f"detach:e309-owner-{item['type_name'].lower()}",
        ]
