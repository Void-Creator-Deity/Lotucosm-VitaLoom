from __future__ import annotations

"""Build read-only WorldBridge descriptor corpus from real scene/fact sources.

This module intentionally stops at a JSON descriptor.  It does not attach PS
objects, mutate SR entities, or claim that the two runtime models are equal.
"""

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .world_bridge_descriptor_contract import (
    build_worldbridge_graph_descriptor,
    canonicalize_descriptor,
    descriptor_round_trip,
)


def load_pond_scene(path: str | Path) -> dict[str, Any]:
    """Load one canonical JSON ``.pond`` scene without changing it."""
    scene_path = Path(path)
    with scene_path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(".pond root must be an object")
    return data


def _script_descriptor(script: Any) -> dict[str, Any]:
    if not isinstance(script, Mapping):
        return {"raw": script}
    return dict(script)


def _json_safe_inspectable_properties(properties: Any) -> dict[str, Any]:
    """Keep Inspector metadata portable (types become qualified names)."""
    if not isinstance(properties, Mapping):
        return {}
    normalized: dict[str, Any] = {}
    for name, metadata in properties.items():
        if not isinstance(name, str) or not isinstance(metadata, Mapping):
            continue
        row = dict(metadata)
        value_type = row.get("type")
        if isinstance(value_type, type):
            row["type"] = f"{value_type.__module__}.{value_type.__qualname__}"
        normalized[name] = row
    return normalized


def _component_fact(component: Any) -> dict[str, Any]:
    """Convert a real PS component or a status mapping into portable facts."""
    if isinstance(component, Mapping):
        fact = dict(component)
    elif hasattr(component, "get_status"):
        fact = dict(component.get_status())
        inspectable = getattr(component, "get_inspectable_properties", None)
        if callable(inspectable):
            fact["inspectable_properties"] = _json_safe_inspectable_properties(inspectable())
        fact.setdefault("class_name", component.__class__.__name__)
        fact.setdefault("component_id", getattr(component, "id", None))
    else:
        raise TypeError("PS component facts must be mappings or expose get_status()")
    return fact


def _parent_map(scene: Mapping[str, Any]) -> dict[str, str]:
    parent_by_child: dict[str, str] = {}
    for connection in scene.get("connections", ()):
        if not isinstance(connection, Mapping):
            continue
        start = connection.get("start", connection.get("start_id"))
        end = connection.get("end", connection.get("end_id"))
        if isinstance(start, str) and isinstance(end, str):
            parent_by_child.setdefault(end, start)
    return parent_by_child


def build_worldbridge_descriptor_corpus(
    scene: Mapping[str, Any],
    *,
    ps_component_facts: Iterable[Any] = (),
    source_name: str = "scene.pond",
) -> dict[str, Any]:
    """Build a corpus witness from a real ``.pond`` and real PS component facts.

    Scene list ordering is preserved.  The original script property objects,
    hierarchy edges, signal edge ordering, and unknown top-level scene fields
    are retained under explicit source extensions.
    """
    if not isinstance(scene, Mapping):
        raise TypeError("scene must be a mapping")
    parent_by_child = _parent_map(scene)
    membrane_nodes: list[dict[str, Any]] = []
    scripts: list[dict[str, Any]] = []
    scene_entities = scene.get("entities", ())
    if not isinstance(scene_entities, list):
        raise ValueError("scene.entities must be a list")
    for entity in scene_entities:
        if not isinstance(entity, Mapping):
            continue
        entity_id = entity.get("id")
        if not isinstance(entity_id, str):
            continue
        node = {
            "id": entity_id,
            "source": "pond.entity",
            "entity_type": entity.get("type"),
            "name": entity.get("name"),
            "position": entity.get("position"),
            "radius": entity.get("radius"),
            "parent_id": parent_by_child.get(entity_id),
            "scripts": [_script_descriptor(item) for item in entity.get("scripts", [])],
        }
        for key in entity:
            if key not in node:
                node.setdefault("extensions", {})[key] = entity[key]
        membrane_nodes.append(node)
        for script in node["scripts"]:
            scripts.append({"entity_id": entity_id, **script})

    component_nodes = []
    for index, component in enumerate(ps_component_facts):
        fact = _component_fact(component)
        component_id = fact.get("component_id", fact.get("id", f"ps-component-{index}"))
        component_nodes.append({
            "id": str(component_id),
            "source": "ps.component_fact",
            "component_type": fact.get("component_type", fact.get("type")),
            "class_name": fact.get("class_name"),
            "organism_id": fact.get("organism_id"),
            "location": fact.get("location"),
            "inspectable_properties": fact.get("inspectable_properties", {}),
            "properties": fact,
        })

    pond_edges = [dict(edge) for edge in scene.get("connections", []) if isinstance(edge, Mapping)]
    signal_edges = [dict(edge) for edge in scene.get("sr_signal_connections", []) if isinstance(edge, Mapping)]
    edges = pond_edges + signal_edges
    return build_worldbridge_graph_descriptor(
        membrane_nodes=membrane_nodes,
        component_nodes=component_nodes,
        edges=edges,
        scripts=scripts,
        extensions={
            "sources": {
                "pond": source_name,
                "ps_component_facts": "runtime_component_status",
            },
            "pond_top_level_unknown_fields": {
                key: value for key, value in scene.items()
                if key not in {
                    "name", "version", "entities", "connections", "sr_signal_connections",
                    "sr_membrane_template", "components",
                }
            },
            "sr_membrane_template": scene.get("sr_membrane_template", {}),
            "ps_components_are_facts_only": True,
        },
    )


def build_descriptor_corpus_from_pond(
    path: str | Path,
    *,
    ps_component_facts: Iterable[Any] = (),
) -> dict[str, Any]:
    scene_path = Path(path)
    return build_worldbridge_descriptor_corpus(
        load_pond_scene(scene_path),
        ps_component_facts=ps_component_facts,
        source_name=scene_path.as_posix(),
    )


def verify_descriptor_corpus_round_trip(corpus: Mapping[str, Any]) -> dict[str, Any]:
    """Return canonical round-tripped corpus; useful as an evidence witness."""
    return descriptor_round_trip(canonicalize_descriptor(corpus))


def discover_canonical_ponds(samples_root: str | Path) -> list[Path]:
    """Return sorted sample ``.pond`` files, excluding generated test/build trees."""
    root = Path(samples_root)
    excluded = {".git", ".venv", "__pycache__"}
    return sorted(
        path for path in root.rglob("*.pond")
        if not any(part in excluded or part.startswith(".pytest-") for part in path.parts)
    )


def _scene_component_facts(scene: Mapping[str, Any]) -> list[Any]:
    raw = scene.get("components", [])
    return list(raw) if isinstance(raw, list) else []


def diagnose_descriptor_corpus(paths: Iterable[str | Path]) -> dict[str, Any]:
    """Produce read-only coverage evidence for a set of canonical scenes."""
    samples: list[dict[str, Any]] = []
    shape_keys: set[str] = set()
    for raw_path in paths:
        path = Path(raw_path)
        scene = load_pond_scene(path)
        corpus = build_worldbridge_descriptor_corpus(
            scene,
            ps_component_facts=_scene_component_facts(scene),
            source_name=path.as_posix(),
        )
        restored = verify_descriptor_corpus_round_trip(corpus)
        nodes = corpus["membrane_nodes"]
        sample = {
            "path": path.as_posix(),
            "entity_count": len(nodes),
            "edge_count": len(corpus["edges"]),
            "signal_edge_count": len([edge for edge in corpus["edges"] if "channel" in edge]),
            "script_count": len(corpus["scripts"]),
            "hierarchy_relation_count": len([node for node in nodes if node.get("parent_id")]),
            "unknown_top_level_field_count": len(corpus["extensions"]["pond_top_level_unknown_fields"]),
            "template_sensor_count": len(corpus["extensions"]["sr_membrane_template"].get("sensors", [])),
            "template_actuator_count": len(corpus["extensions"]["sr_membrane_template"].get("actuators", [])),
            "ps_component_fact_count": len(corpus["component_nodes"]),
            "round_trip_ok": restored == corpus,
            "descriptor_shape": sorted(corpus.keys()),
        }
        shape_keys.update(corpus.keys())
        samples.append(sample)
    coverage_fields = (
        "edge_count", "signal_edge_count", "script_count",
        "hierarchy_relation_count", "unknown_top_level_field_count",
        "template_sensor_count", "template_actuator_count",
        "ps_component_fact_count",
    )
    field_coverage = {
        field: {
            "sample_count": sum(1 for item in samples if item[field] > 0),
            "total": sum(item[field] for item in samples),
        }
        for field in coverage_fields
    }
    return {
        "status": "worldbridge_descriptor_corpus_diagnostic",
        "schema_version": 1,
        "read_only": True,
        "maps_live_objects": False,
        "sample_count": len(samples),
        "all_round_trip_ok": bool(samples) and all(item["round_trip_ok"] for item in samples),
        "descriptor_shape_keys": sorted(shape_keys),
        "field_coverage": field_coverage,
        "samples": samples,
        "do_not_claim": [
            "live_component_graph_mapping",
            "lossless_worldbridge_mapping",
            "unified_pond_default_ready",
            "sr_ps_tick_merge",
        ],
    }
