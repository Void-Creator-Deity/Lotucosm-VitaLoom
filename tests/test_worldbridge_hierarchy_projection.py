from __future__ import annotations

from core.Lotucosm.runtime.world_bridge_hierarchy_projection import (
    build_worldbridge_hierarchy_projection,
    validate_worldbridge_hierarchy_projection,
)
from core.Lotucosm.runtime.world_bridge_component_identity import (
    capture_worldbridge_component_identity_links,
)


def test_projection_maps_only_identity_witnessed_organism_relations() -> None:
    value = build_worldbridge_hierarchy_projection(
        entity_links=[
            {"sr_entity_id": "sr-parent", "ps_organism_id": "ps-parent"},
            {"sr_entity_id": "sr-child", "ps_organism_id": "ps-child"},
        ],
        sr_structural_edges=[
            {"start": "sr-parent", "end": "sr-child"},
            {"start": "sr-parent", "end": "sr-sensor"},
        ],
        ps_hierarchy_contracts=[{"owner_id": "ps-parent"}, {"owner_id": "ps-child"}],
    )
    assert validate_worldbridge_hierarchy_projection(value) == {"valid": True, "errors": []}
    assert value["mapped_organism_relations"][0]["ps_child_organism_id"] == "ps-child"
    assert value["unresolved_sr_relations"] == [{"start": "sr-parent", "end": "sr-sensor"}]
    assert value["live_hierarchy_authority"] is False


def test_projection_rejects_duplicate_or_tampered_identity() -> None:
    try:
        build_worldbridge_hierarchy_projection(
            entity_links=[
                {"sr_entity_id": "sr-a", "ps_organism_id": "ps-a"},
                {"sr_entity_id": "sr-a", "ps_organism_id": "ps-b"},
            ]
        )
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate bridge identity must fail")

    value = build_worldbridge_hierarchy_projection(entity_links=[])
    value["live_hierarchy_authority"] = True
    assert validate_worldbridge_hierarchy_projection(value)["valid"] is False


def test_projection_maps_component_relation_only_with_explicit_identity_contract() -> None:
    value = build_worldbridge_hierarchy_projection(
        entity_links=[{"sr_entity_id": "sr-org", "ps_organism_id": "ps-org"}],
        sr_structural_edges=[{"start": "sr-parent", "end": "sr-child"}],
        component_identity_links=[
            {"sr_component_id": "sr-parent", "ps_component_id": "ps-parent",
             "sr_organism_id": "sr-org", "ps_organism_id": "ps-org"},
            {"sr_component_id": "sr-child", "ps_component_id": "ps-child",
             "sr_organism_id": "sr-org", "ps_organism_id": "ps-org"},
        ],
    )
    assert value["mapped_component_relations"][0]["ps_child_component_id"] == "ps-child"
    assert value["mapped_organism_relations"] == []
    assert validate_worldbridge_hierarchy_projection(value)["valid"] is True


def test_component_identity_rejects_duplicate_and_owner_mismatch() -> None:
    base = {"sr_component_id": "sr-c", "ps_component_id": "ps-c",
            "sr_organism_id": "sr-org", "ps_organism_id": "ps-org"}
    try:
        build_worldbridge_hierarchy_projection(
            entity_links=[{"sr_entity_id": "sr-org", "ps_organism_id": "ps-org"}],
            component_identity_links=[base, {**base, "sr_component_id": "sr-other"}],
        )
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate component identity must fail")
    try:
        build_worldbridge_hierarchy_projection(
            entity_links=[{"sr_entity_id": "sr-org", "ps_organism_id": "ps-org"}],
            component_identity_links=[{**base, "ps_organism_id": "ps-other"}],
        )
    except ValueError as exc:
        assert "owner" in str(exc)
    else:
        raise AssertionError("owner mismatch must fail")


def test_component_identity_is_explicitly_persisted_and_captured() -> None:
    from builtin.components.component_factory import ComponentFactory
    from builtin.entity_types.organism import Organism

    organism = Organism("ps-org", (0.0, 0.0))
    component = ComponentFactory().create_component(
        "Sensor", "ps-component", organism_id=organism.id,
        sr_component_id="sr-component",
    )
    organism.add_component(component)
    entity = type("Entity", (), {
        "id": "sr-org",
        "_world_bridge_component_identity_links": [{
            "sr_component_id": "sr-component",
            "ps_component_id": "ps-component",
            "sr_organism_id": "sr-org",
            "ps_organism_id": "ps-org",
        }],
    })()
    pond = type("Pond", (), {"organisms": {organism.id: organism}})()
    assert capture_worldbridge_component_identity_links([entity], pond) == [{
        "sr_component_id": "sr-component",
        "ps_component_id": "ps-component",
        "sr_organism_id": "sr-org",
        "ps_organism_id": "ps-org",
    }]

    from builtin.systems.pond_serializer import PondSerializer
    from core.Lotucosm.pond import Pond
    real_pond = Pond(name="identity", size=(20, 20), initial_organisms=0)
    real_pond.organisms[organism.id] = organism
    payload = PondSerializer(save_format="json").serialize_pond(real_pond)
    restored = PondSerializer(save_format="json").deserialize_pond(payload, Pond)
    assert restored.organisms[organism.id].components[component.id].sr_component_id == "sr-component"


def test_real_worldbridge_spawn_binds_declared_component_receipt() -> None:
    from core.Lotucosm.pond import Pond
    from core.Lotucosm.runtime.world_bridge import (
        sr_entity_to_organism,
    )

    class Entity:
        id = "sr-organism"
        position = [1.0, 2.0]
        energy = 80.0
        _world_bridge_component_identity_links = [
            {"sr_component_id": "sr-sensor", "ps_component_id": "bridge_sr-organism_sensor",
             "sr_organism_id": "sr-organism", "ps_organism_id": "bridge_sr-organism"},
            {"sr_component_id": "sr-actuator", "ps_component_id": "bridge_sr-organism_actuator",
             "sr_organism_id": "sr-organism", "ps_organism_id": "bridge_sr-organism"},
        ]

    entity = Entity()
    pond = Pond(name="spawn-receipt", size=(100, 100), initial_organisms=0)
    organism = sr_entity_to_organism(entity, pond, equip_pvaec=True)
    assert organism.components["bridge_sr-organism_sensor"].sr_component_id == "sr-sensor"
    assert organism.components["bridge_sr-organism_actuator"].sr_component_id == "sr-actuator"
    assert capture_worldbridge_component_identity_links([entity], pond) == sorted(
        entity._world_bridge_component_identity_links,
        key=lambda item: (item["sr_component_id"], item["ps_component_id"]),
    )
