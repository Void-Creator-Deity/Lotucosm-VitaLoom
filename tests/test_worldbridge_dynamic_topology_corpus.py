from __future__ import annotations

import copy

import pytest

from core.Lotucosm.runtime.world_bridge_dynamic_topology_corpus import (
    build_worldbridge_dynamic_topology_corpus,
    validate_worldbridge_dynamic_topology_corpus,
)


def _event(index: int, kind: str = "spawn") -> dict[str, object]:
    return {
        "event_index": index,
        "kind": kind,
        "runtime_epoch": "epoch-1",
        "structure_fingerprint": "a" * 64,
        "receipt_digest": "b" * 64,
        "node_ids": ["hub", "hub_sensor"],
    }


def test_dynamic_topology_corpus_is_digest_bound_and_quarantined():
    corpus = build_worldbridge_dynamic_topology_corpus(
        runtime_epoch="epoch-1",
        scene_path="scene.pond",
        events=[_event(0), _event(1, "despawn")],
        duplicate_rejected=True,
        missing_node_rejected=True,
        epoch_drift_rejected=True,
    )
    assert validate_worldbridge_dynamic_topology_corpus(corpus) == {"valid": True, "errors": []}
    assert corpus["replay_admitted"] is False


@pytest.mark.parametrize("mutation", [
    lambda value: value["events"][1].__setitem__("event_index", 0),
    lambda value: value["events"][0].__setitem__("runtime_epoch", "epoch-2"),
    lambda value: value["events"][0].__setitem__("node_ids", ["hub", ""]),
])
def test_dynamic_topology_corpus_rejects_event_drift(mutation):
    corpus = build_worldbridge_dynamic_topology_corpus(
        runtime_epoch="epoch-1",
        scene_path="scene.pond",
        events=[_event(0), _event(1, "despawn")],
        duplicate_rejected=True,
        missing_node_rejected=True,
        epoch_drift_rejected=True,
    )
    tampered = copy.deepcopy(corpus)
    mutation(tampered)
    assert validate_worldbridge_dynamic_topology_corpus(tampered)["valid"] is False


def test_dynamic_topology_corpus_rejects_missing_rejection_evidence():
    with pytest.raises(ValueError, match="cannot admit replay"):
        build_worldbridge_dynamic_topology_corpus(
            runtime_epoch="epoch-1",
            scene_path="scene.pond",
            events=[_event(0)],
            duplicate_rejected=True,
            missing_node_rejected=True,
            epoch_drift_rejected=True,
            replay_admitted=True,
        )
