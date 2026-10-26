from __future__ import annotations

from pathlib import Path

from builtin.components.component_factory import ComponentFactory
from core.Lotucosm.runtime.world_bridge_descriptor_corpus import (
    build_descriptor_corpus_from_pond,
    verify_descriptor_corpus_round_trip,
)


ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化" / "scenes" / "main_scene.pond"


def _ps_facts():
    factory = ComponentFactory()
    return [
        factory.create_component("Membrane", "ps-membrane-01", organism_id="ai_organism_01", radius=32.0),
        factory.create_component("Sensor", "ps-sensor-01", organism_id="ai_organism_01", sensing_range=120.0),
        factory.create_component("Actuator", "ps-actuator-01", organism_id="ai_organism_01", max_force=10.0),
    ]


def test_real_pond_corpus_preserves_topology_order_scripts_and_hierarchy() -> None:
    corpus = build_descriptor_corpus_from_pond(SCENE, ps_component_facts=_ps_facts())
    assert len(corpus["membrane_nodes"]) >= 6
    assert [edge["start"] for edge in corpus["edges"][-3:]] == [
        "sensor_mem_01", "sensor_mem_02", "sensor_mem_03"
    ]
    sensor = next(node for node in corpus["membrane_nodes"] if node["id"] == "sensor_mem_01")
    assert sensor["scripts"][0]["properties"]["patrol"]["patrol_amp"] == 4.0
    assert sensor["parent_id"] == "ai_organism_01"


def test_real_ps_component_facts_are_status_evidence_not_live_objects() -> None:
    corpus = build_descriptor_corpus_from_pond(SCENE, ps_component_facts=_ps_facts())
    membrane = next(node for node in corpus["component_nodes"] if node["id"] == "ps-membrane-01")
    assert membrane["source"] == "ps.component_fact"
    assert membrane["component_type"] == "membrane"
    assert membrane["properties"]["connection_count"] == 0
    assert corpus["extensions"]["ps_components_are_facts_only"] is True
    assert corpus["maps_live_objects"] is False


def test_corpus_round_trip_preserves_unknown_scene_fields_and_template() -> None:
    corpus = build_descriptor_corpus_from_pond(SCENE, ps_component_facts=_ps_facts())
    restored = verify_descriptor_corpus_round_trip(corpus)
    assert restored == corpus
    assert restored["extensions"]["pond_top_level_unknown_fields"]["sr_demo_legend"]["title"] == "莲池图例"
    assert restored["extensions"]["sr_membrane_template"]["sensors"][0]["script"] == "sensor_patrol_pvaec"
