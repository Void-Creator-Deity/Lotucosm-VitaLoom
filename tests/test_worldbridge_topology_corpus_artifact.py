from pathlib import Path
import copy

from core.Lotucosm.runtime.world_bridge_descriptor_corpus import build_descriptor_corpus_from_pond
from core.Lotucosm.runtime.world_bridge_ps_graph_corpus import build_worldbridge_ps_graph_corpus
from core.Lotucosm.runtime.world_bridge_topology_corpus_artifact import (
    build_worldbridge_topology_corpus_artifact,
    validate_worldbridge_topology_corpus_artifact,
)


ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化" / "scenes" / "challenge_scene.pond"


def _artifact():
    return build_worldbridge_topology_corpus_artifact(
        source_scene_path=SCENE.as_posix(),
        scene_descriptor=build_descriptor_corpus_from_pond(SCENE),
        ps_graph_corpus=build_worldbridge_ps_graph_corpus(),
    )


def test_real_scene_and_ps_corpus_artifact_is_provenance_bound():
    artifact = _artifact()
    assert validate_worldbridge_topology_corpus_artifact(artifact) == {"valid": True, "errors": []}
    assert artifact["provenance_bound"] is True
    assert artifact["cross_lane_identity_join"] == "not_performed"
    assert artifact["cross_lane_topology_admitted"] is False
    assert artifact["replay_admitted"] is False


def test_topology_artifact_rejects_nested_source_tamper():
    artifact = _artifact()
    tampered = copy.deepcopy(artifact)
    tampered["scene_descriptor"]["edges"].append({"start": "tampered", "end": "tampered"})
    assert validate_worldbridge_topology_corpus_artifact(tampered)["valid"] is False
    assert "scene_descriptor_digest_mismatch" in validate_worldbridge_topology_corpus_artifact(tampered)["errors"]
