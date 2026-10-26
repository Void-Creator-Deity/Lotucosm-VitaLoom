from __future__ import annotations

import copy
import json

import pytest

from core.Lotucosm.runtime.world_bridge_checkpoint_artifact import (
    build_worldbridge_checkpoint_artifact,
    decode_worldbridge_checkpoint_artifact,
    encode_worldbridge_checkpoint_artifact,
    validate_worldbridge_checkpoint_artifact,
)
from core.Lotucosm.runtime.world_bridge_component_identity_artifact import (
    build_worldbridge_component_identity_artifact,
)
from core.Lotucosm.runtime.world_bridge_component_identity_persistence import (
    build_worldbridge_component_identity_persistence_envelope,
)
from core.Lotucosm.runtime.world_bridge_live_checkpoint import build_worldbridge_live_checkpoint
from core.Lotucosm.runtime.world_bridge_live_checkpoint_admission import (
    build_worldbridge_live_checkpoint_admission_witness,
)


def _bundle():
    checkpoint = build_worldbridge_live_checkpoint(
        checkpoint_id="cp-1", sequence=1, sr_state={"time": 1},
        ps_state={"time": 1}, bridge_identity_links=[], input_state={},
        randomness_state=None, lifecycle={"runtime_epoch": "epoch-1", "scene_path": "scene.pond"},
    )
    artifact = build_worldbridge_component_identity_artifact(
        receipts=[{"generation": 1, "hub_id": "h", "links": []}],
        duplicate_rejected=True, owner_drift_rejected=True, rollback_succeeded=True,
    )
    persistence = build_worldbridge_component_identity_persistence_envelope(
        project_path="project", project_lock={"schema_version": 1},
        runtime_epoch="epoch-1", scene_path="scene.pond", artifact=artifact,
    )
    witness = build_worldbridge_live_checkpoint_admission_witness(
        checkpoint=checkpoint,
        versioned_bundle={"runtime_version": "1.0.0", "sr_schema_version": 1,
                          "ps_schema_version": 1, "bridge_schema_version": 1},
        fresh_restore={"parity": True}, in_place_restore={"parity": True},
        identity_registration={"parity": True},
        rollback={"atomic": True, "target_preserved": True},
    )
    return build_worldbridge_checkpoint_artifact(
        checkpoint=checkpoint, persistence_envelope=persistence,
        admission_witness=witness,
    )


def test_unified_checkpoint_artifact_round_trip_and_cross_links():
    artifact = _bundle()
    assert validate_worldbridge_checkpoint_artifact(artifact) == {"valid": True, "errors": []}
    encoded = encode_worldbridge_checkpoint_artifact(artifact)
    assert decode_worldbridge_checkpoint_artifact(encoded) == artifact
    assert encoded == json.dumps(
        artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


@pytest.mark.parametrize("field", ["checkpoint_digest", "persistence_digest", "witness_digest", "artifact_digest"])
def test_unified_artifact_rejects_layer_digest_tamper(field):
    tampered = copy.deepcopy(_bundle())
    tampered[field] = "0" * 64
    assert field + "_mismatch" in validate_worldbridge_checkpoint_artifact(tampered)["errors"]


def test_unified_artifact_rejects_cross_checkpoint_witness_and_noncanonical_json():
    tampered = copy.deepcopy(_bundle())
    tampered["admission_witness"]["checkpoint_identity"]["checkpoint_id"] = "other"
    assert "cross_links_invalid" in validate_worldbridge_checkpoint_artifact(tampered)["errors"]
    encoded = encode_worldbridge_checkpoint_artifact(_bundle())
    duplicate = encoded.replace(b'"status":"worldbridge_checkpoint_artifact"', b'"status":"worldbridge_checkpoint_artifact","status":"old"')
    with pytest.raises(ValueError, match="strict UTF-8 JSON"):
        decode_worldbridge_checkpoint_artifact(duplicate)
