from __future__ import annotations

"""Read-only PS component-graph facts for WorldBridge admission.

The probe uses the real Organism/ComponentFactory/serializer seams but returns
only portable topology facts.  It deliberately does not map the graph into SR
or claim cross-lane replay parity.
"""

from typing import Any

from builtin.components.component_factory import ComponentFactory
from builtin.entity_types.organism import Organism
from builtin.systems.organism_serializer import OrganismSerializer
from builtin.systems.pond_serializer import PondSerializer
from core.Lotucosm.runtime.world_bridge_ps_hierarchy_contract import build_ps_hierarchy_authority_contract


def _component_ref(value: Any) -> dict[str, Any]:
    return {
        "id": str(getattr(value, "id", "")),
        "class_name": type(value).__name__,
        "component_type": str(getattr(value, "component_type", "")),
    }


def _connection_ref(source: Any, connection: Any, order: int) -> dict[str, Any]:
    target = connection
    connection_id = None
    connection_type = "direct_component_reference"
    if hasattr(connection, "target"):
        target = connection.target
        connection_id = getattr(connection, "id", None)
        connection_type = str(getattr(connection, "connection_type", type(connection).__name__))
    return {
        "order": order,
        "source_id": str(getattr(source, "id", "")),
        "target_id": str(getattr(target, "id", "")),
        "connection_id": str(connection_id) if connection_id is not None else None,
        "connection_type": connection_type,
        "source_class_name": type(source).__name__,
        "target_class_name": type(target).__name__,
    }


def _edge_ids(organism: Any) -> list[dict[str, Any]]:
    return [
        {"order": order, "source_id": component.id, "target_id": getattr(getattr(connection, "target", connection), "id", "")}
        for component in organism.components.values()
        for order, connection in enumerate(getattr(component, "connections", ()))
    ]


def _build_graph(factory: ComponentFactory) -> Organism:
    owner = Organism("e310-graph-owner", (0.0, 0.0), name="E310 Graph Owner")
    for component_type, component_id in (
        ("Sensor", "e310-sensor"),
        ("Actuator", "e310-actuator"),
        ("LightSensor", "e310-light"),
    ):
        owner.add_component(factory.create_component(component_type, component_id, organism_id=owner.id))
    owner.set_membrane(factory.create_component("Membrane", "e310-membrane", organism_id=owner.id, radius=42.0))
    owner.connect_tools("e310-sensor", "e310-actuator")
    owner.connect_tools("e310-sensor", "e310-light")
    owner.connect_tools("e310-actuator", "e310-light")
    return owner


def _round_trip(serializer: Any, owner: Organism) -> dict[str, Any]:
    payload = serializer.serialize_organism(owner)
    restored = serializer.deserialize_organism(payload)
    if restored is None:
        return {"ok": False, "payload_has_connections": "component_connections" in payload}
    restored_edges = _edge_ids(restored)
    return {
        "ok": restored_edges == payload["component_connections"] and restored.membrane is not None and restored.membrane.organism_id == restored.id,
        "payload_has_connections": "component_connections" in payload,
        "restored_edges": restored_edges,
        "restored_component_classes": [type(component).__name__ for component in restored.components.values()],
        "restored_membrane_owner": restored.membrane.organism_id == restored.id,
        "restored_membrane_child": restored.membrane in restored.children,
        "restored_is_new_object": restored is not owner,
    }


def build_worldbridge_ps_graph_corpus(*, factory: ComponentFactory | None = None) -> dict[str, Any]:
    """Build a deterministic PS membrane/component graph fact corpus."""
    active_factory = factory or ComponentFactory()
    owner = _build_graph(active_factory)
    edges = [
        _connection_ref(source, connection, order)
        for source in owner.components.values()
        for order, connection in enumerate(getattr(source, "connections", ()))
    ]
    components = [_component_ref(component) for component in owner.components.values()]
    hierarchy = build_ps_hierarchy_authority_contract(owner)
    pond_round_trip = _round_trip(PondSerializer(), owner)
    organism_round_trip = _round_trip(OrganismSerializer(), owner)
    graph_persistence_round_trip = pond_round_trip["ok"] and organism_round_trip["ok"]
    return {
        "schema_version": 2,
        "status": "worldbridge_ps_component_graph_fact_corpus",
        "read_only": True,
        "maps_live_objects": False,
        "constructed_for_fact_extraction": True,
        "owner": {
            "id": owner.id,
            "class_name": type(owner).__name__,
            "component_ids": [item["id"] for item in components],
            "membrane_id": getattr(owner.membrane, "id", None),
        },
        "components": components,
        "hierarchy": hierarchy,
        "membrane": {
            **_component_ref(owner.membrane),
            "organism_id": owner.membrane.organism_id,
            "radius": owner.membrane.radius,
            "is_owner_bound": owner.membrane.organism_id == owner.id,
            "is_entity_child": owner.membrane in owner.children,
        },
        "edges": edges,
        "persistence": {
            "pond_serializer": pond_round_trip,
            "organism_serializer": organism_round_trip,
            "legacy_missing_field_compatible": all(
                serializer.deserialize_organism(
                    {key: value for key, value in serializer.serialize_organism(owner).items() if key != "component_connections"}
                ) is not None
                for serializer in (PondSerializer(), OrganismSerializer())
            ),
        },
        "evidence": {
            "organism_component_owner": True,
            "membrane_reference_owner": owner.membrane is not None,
            "hierarchy_contract": hierarchy["membrane_relation"] == "special_owned_reference" and all(
                parent_id == owner.id for parent_id in hierarchy["component_parent_ids"].values()
            ),
            "connection_creation": len(edges) == 3,
            "ordered_directed_edges": [edge["source_id"] for edge in edges] == ["e310-sensor", "e310-sensor", "e310-actuator"],
            "graph_persistence_round_trip": graph_persistence_round_trip,
            "cross_lane_replay": False,
            "worldbridge_live_authority": False,
        },
        "persistence_gap": {
            "organism_serializer_connections_field": not organism_round_trip["ok"],
            "membrane_child_graph_restore": False,
            "required_next_contract": None if graph_persistence_round_trip else "repair_ordered_component_edge_persistence",
        },
        "do_not_claim": [
            "live_worldbridge_component_graph",
            "sr_ps_shared_topology_authority",
            "cross_lane_deterministic_replay",
        ],
    }


__all__ = ["build_worldbridge_ps_graph_corpus"]







