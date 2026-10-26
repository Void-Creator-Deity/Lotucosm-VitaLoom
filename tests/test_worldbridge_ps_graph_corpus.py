from core.Lotucosm.runtime.world_bridge_ps_graph_corpus import (
    build_worldbridge_ps_graph_corpus,
)


def test_ps_graph_corpus_exercises_real_owner_membrane_and_ordered_directed_edges() -> None:
    corpus = build_worldbridge_ps_graph_corpus()
    assert corpus["read_only"] is True
    assert corpus["maps_live_objects"] is False
    assert corpus["evidence"]["organism_component_owner"] is True
    assert corpus["evidence"]["membrane_reference_owner"] is True
    assert corpus["evidence"]["connection_creation"] is True
    assert corpus["evidence"]["ordered_directed_edges"] is True
    assert [(edge["source_id"], edge["target_id"], edge["order"]) for edge in corpus["edges"]] == [
        ("e310-sensor", "e310-actuator", 0),
        ("e310-sensor", "e310-light", 1),
        ("e310-actuator", "e310-light", 0),
    ]


def test_ps_graph_corpus_records_local_persistence_without_replay_claim() -> None:
    corpus = build_worldbridge_ps_graph_corpus()
    assert corpus["evidence"]["graph_persistence_round_trip"] is True
    assert corpus["evidence"]["cross_lane_replay"] is False
    assert corpus["persistence"]["legacy_missing_field_compatible"] is True
    assert corpus["persistence"]["pond_serializer"]["restored_is_new_object"] is True
    assert corpus["persistence"]["organism_serializer"]["restored_is_new_object"] is True
    assert corpus["persistence_gap"]["organism_serializer_connections_field"] is False
    assert corpus["persistence_gap"]["membrane_child_graph_restore"] is False
    assert "sr_ps_shared_topology_authority" in corpus["do_not_claim"]


def test_ps_graph_corpus_is_deterministic() -> None:
    assert build_worldbridge_ps_graph_corpus() == build_worldbridge_ps_graph_corpus()
