from __future__ import annotations

"""Read-only PS component corpus for WorldBridge admission evidence.

Instances are created only in a short-lived probe and reduced to JSON-safe
facts.  The resulting corpus never exposes or stores live component objects and
does not imply that PS lifecycle or replay is shared with SR.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from builtin.components.component_factory import ComponentFactory
from builtin.systems.pond_serializer import PondSerializer
from builtin.entity_types.organism import Organism
from .world_bridge_descriptor_corpus import _json_safe_inspectable_properties


_LIFECYCLE_METHODS = (
    "on_attach", "on_detach", "update", "process_signal", "act", "mutate",
    "restore_persistent_state", "add_connection", "remove_connection",
)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "tolist"):
        return _json_safe(value.tolist())
    return repr(value)


def _probe_component(factory: ComponentFactory, type_name: str) -> dict[str, Any]:
    component = factory.create_component(
        type_name,
        f"e308-{type_name.lower()}",
        organism_id="e308-probe-organism",
    )
    status = _json_safe(component.get_status())
    inspectable = getattr(component, "get_inspectable_properties", None)
    metadata = _json_safe_inspectable_properties(inspectable()) if callable(inspectable) else {}
    return {
        "type_name": type_name,
        "class_name": type(component).__name__,
        "component_type": status.get("component_type"),
        "status": status,
        "status_keys": sorted(status),
        "inspectable_properties": _json_safe(metadata),
        "lifecycle_methods": {
            name: callable(getattr(component, name, None)) for name in _LIFECYCLE_METHODS
        },
    }



def _probe_lifecycle_ownership(factory: ComponentFactory, type_name: str) -> dict[str, Any]:
    """Exercise the PS owner attach/detach seam on a short-lived organism."""
    component = factory.create_component(
        type_name, f"e309-lifecycle-{type_name.lower()}", organism_id="unbound"
    )
    owner = Organism(f"e309-owner-{type_name.lower()}", (0.0, 0.0))
    events: list[str] = []
    original_attach = getattr(component, "on_attach", None)
    original_detach = getattr(component, "on_detach", None)

    def attach_probe(entity: Any) -> None:
        events.append(f"attach:{entity.id}")
        if callable(original_attach):
            original_attach(entity)

    def detach_probe(entity: Any) -> None:
        events.append(f"detach:{entity.id}")
        if callable(original_detach):
            original_detach(entity)

    component.on_attach = attach_probe
    component.on_detach = detach_probe
    added = owner.add_component(component)
    bound_after_attach = component.organism_id == owner.id and component.id in owner.components
    removed = owner.remove_component(component.id)
    return {
        "type_name": type_name,
        "owner_class": type(owner).__name__,
        "add_component_succeeded": added,
        "remove_component_succeeded": removed,
        "attach_hook_called": any(item.startswith("attach:") for item in events),
        "detach_hook_called": any(item.startswith("detach:") for item in events),
        "event_order": events,
        "owner_binding_after_attach": bound_after_attach,
        "owner_lifecycle_authority": True,
    }

def build_worldbridge_ps_component_corpus(
    *, factory: ComponentFactory | None = None,
) -> dict[str, Any]:
    """Probe every registered PS component type and return fact-only evidence."""
    active_factory = factory or ComponentFactory()
    type_names = active_factory.get_available_component_types()
    records = [_probe_component(active_factory, name) for name in type_names]
    lifecycle = [_probe_lifecycle_ownership(active_factory, name) for name in type_names]
    return {
        "schema_version": 1,
        "status": "worldbridge_ps_component_fact_corpus",
        "read_only": True,
        "maps_live_objects": False,
        "constructed_for_fact_extraction": True,
        "component_type_count": len(records),
        "component_types": records,
        "lifecycle_ownership": lifecycle,
        "evidence": {
            "factory_construction": True,
            "status_projection": True,
            "inspector_metadata": True,
            "persistence_hydration_api": all(
                item["lifecycle_methods"]["restore_persistent_state"] for item in records
            ),
            "lifecycle_ownership": all(
                item["owner_lifecycle_authority"]
                and item["owner_binding_after_attach"]
                and item["attach_hook_called"]
                and item["detach_hook_called"]
                for item in lifecycle
            ),
            "cross_lane_replay": False,
            "worldbridge_live_authority": False,
            "live_membrane_graph": False,
            "live_connection_objects": False,
        },
        "source_contracts": {
            "factory": "builtin.components.component_factory.ComponentFactory",
            "status": "ComponentBase.get_status()",
            "inspector": "Component.get_inspectable_properties()",
            "persistence": "Component.restore_persistent_state()",
        },
        "do_not_claim": [
            "live_component_graph_mapping",
            "worldbridge_lossless_mapping",
            "shared_ps_sr_lifecycle",
            "cross_lane_deterministic_replay",
        ],
    }


def build_worldbridge_ps_component_persistence_audit(
    *, factory: ComponentFactory | None = None, serializer: PondSerializer | None = None,
) -> dict[str, Any]:
    """Audit PS component serializer hydration without exposing live objects.

    A failed or lossy local round-trip is evidence against admission; it is not
    repaired here and must not be hidden by descriptor projection.
    """
    active_factory = factory or ComponentFactory()
    active_serializer = serializer or PondSerializer()
    records: list[dict[str, Any]] = []
    for type_name in active_factory.get_available_component_types():
        original = active_factory.create_component(
            type_name, f"e309-{type_name.lower()}", organism_id="e309-probe-organism"
        )
        payload = _json_safe(active_serializer.serialize_component(original))
        restored = active_serializer.deserialize_component(payload)
        original_status = _json_safe(original.get_status())
        restored_status = _json_safe(restored.get_status()) if restored is not None else None
        mismatches = []
        # deserialize_component intentionally uses a temporary organism id;
        # the host is responsible for rebinding it after component hydration.
        # It is therefore lifecycle context, not component persistence data.
        for key in ("type", "component_type", "location", "congenital", "acquired"):
            if (original_status or {}).get(key) != (restored_status or {}).get(key):
                mismatches.append(key)
        records.append({
            "type_name": type_name,
            "serialized_type": payload.get("type"),
            "restored_class_name": type(restored).__name__ if restored is not None else None,
            "restored": restored is not None,
            "round_trip_ok": restored is not None and not mismatches,
            "mismatches": mismatches,
            "payload_keys": sorted(payload),
        })
    return {
        "schema_version": 1,
        "status": "worldbridge_ps_component_persistence_audit",
        "read_only": True,
        "maps_live_objects": False,
        "records": records,
        "all_round_trip_ok": bool(records) and all(item["round_trip_ok"] for item in records),
        "lossy_or_failed_types": [item["type_name"] for item in records if not item["round_trip_ok"]],
        "evidence": {
            "serializer_path_exercised": True,
            "restore_persistent_state_path_exercised": True,
            "persistence_authority_admitted": False,
            "cross_lane_replay": False,
        },
        "do_not_claim": [
            "lossless_ps_component_persistence",
            "worldbridge_live_component_mapping",
            "cross_lane_deterministic_replay",
        ],
    }


__all__ = ["build_worldbridge_ps_component_corpus", "build_worldbridge_ps_component_persistence_audit"]
