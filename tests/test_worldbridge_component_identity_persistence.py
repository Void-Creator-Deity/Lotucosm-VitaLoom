from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_component_identity_artifact import (
    build_worldbridge_component_identity_artifact,
)
from core.Lotucosm.runtime.world_bridge_component_identity_persistence import (
    build_worldbridge_component_identity_persistence_envelope,
    decode_worldbridge_component_identity_persistence_envelope,
    encode_worldbridge_component_identity_persistence_envelope,
    read_worldbridge_component_identity_persistence_envelope,
    validate_worldbridge_component_identity_persistence_envelope,
    write_worldbridge_component_identity_persistence_envelope,
)


def _artifact() -> dict[str, object]:
    return build_worldbridge_component_identity_artifact(
        receipts=[{"generation": 1, "hub_id": "h", "links": []}],
        duplicate_rejected=True,
        owner_drift_rejected=True,
        rollback_succeeded=True,
    )


def _envelope() -> tuple[dict[str, object], dict[str, object]]:
    lock = {"schema_version": 1, "product": {"id": "Lotucosm-VitaLoom", "version": "1.0.0"}}
    envelope = build_worldbridge_component_identity_persistence_envelope(
        project_path="sample-project",
        project_lock=lock,
        runtime_epoch="epoch-1",
        scene_path="scenes/challenge_scene.pond",
        artifact=_artifact(),
    )
    return envelope, lock


def _diagnostic() -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": 1,
        "code": "project_runtime_binding_rejected",
        "errors": ["runtime_binding_project_lock_digest_mismatch"],
        "checkpoint_id": "cp-1",
        "checkpoint_digest": "a" * 64,
    }
    value["diagnostic_digest"] = hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return value


def test_project_bound_envelope_round_trip_and_atomic_file_write(tmp_path):
    envelope, lock = _envelope()
    assert validate_worldbridge_component_identity_persistence_envelope(
        envelope,
        project_path="sample-project",
        project_lock=lock,
        runtime_epoch="epoch-1",
        scene_path="scenes/challenge_scene.pond",
    ) == {"valid": True, "errors": []}
    encoded = encode_worldbridge_component_identity_persistence_envelope(envelope)
    decoded = decode_worldbridge_component_identity_persistence_envelope(
        encoded,
        project_path="sample-project",
        project_lock=lock,
        runtime_epoch="epoch-1",
        scene_path="scenes/challenge_scene.pond",
    )
    assert decoded == envelope
    path = write_worldbridge_component_identity_persistence_envelope(tmp_path / "identity.json", envelope)
    assert read_worldbridge_component_identity_persistence_envelope(
        path,
        project_path="sample-project",
        project_lock=lock,
        runtime_epoch="epoch-1",
        scene_path="scenes/challenge_scene.pond",
    ) == envelope


def test_restore_diagnostic_survives_persistence_round_trip_and_tamper_is_rejected():
    envelope, lock = _envelope()
    envelope = build_worldbridge_component_identity_persistence_envelope(
        project_path="sample-project", project_lock=lock, runtime_epoch="epoch-1",
        scene_path="scenes/challenge_scene.pond", artifact=envelope["artifact"],
        restore_diagnostic=_diagnostic(),
    )
    encoded = encode_worldbridge_component_identity_persistence_envelope(envelope)
    decoded = decode_worldbridge_component_identity_persistence_envelope(
        encoded, project_path="sample-project", project_lock=lock,
        runtime_epoch="epoch-1", scene_path="scenes/challenge_scene.pond",
    )
    assert decoded["restore_diagnostic"] == envelope["restore_diagnostic"]
    tampered = copy.deepcopy(envelope)
    tampered["restore_diagnostic"]["errors"].append("tampered")
    with pytest.raises(ValueError, match="invalid component identity persistence envelope"):
        encode_worldbridge_component_identity_persistence_envelope(tampered)


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("project_path", "other-project", "project_path_binding_mismatch"),
        ("runtime_epoch", "epoch-2", "runtime_epoch_binding_mismatch"),
        ("scene_path", "scenes/other.pond", "scene_path_binding_mismatch"),
    ],
)
def test_stale_runtime_binding_is_rejected(field, value, error):
    envelope, lock = _envelope()
    assert error in validate_worldbridge_component_identity_persistence_envelope(
        envelope,
        project_path=value if field == "project_path" else "sample-project",
        project_lock=lock,
        runtime_epoch=value if field == "runtime_epoch" else "epoch-1",
        scene_path=value if field == "scene_path" else "scenes/challenge_scene.pond",
    )["errors"]


def test_project_lock_drift_and_tamper_are_rejected():
    envelope, lock = _envelope()
    changed_lock = copy.deepcopy(lock)
    changed_lock["product"]["version"] = "9.9.9"
    validation = validate_worldbridge_component_identity_persistence_envelope(
        envelope, project_path="sample-project", project_lock=changed_lock,
        runtime_epoch="epoch-1", scene_path="scenes/challenge_scene.pond",
    )
    assert "project_lock_binding_mismatch" in validation["errors"]

    tampered = copy.deepcopy(envelope)
    tampered["artifact"]["provenance"]["runtime_status"] = "old-runtime"
    with pytest.raises(ValueError, match="invalid component identity persistence envelope"):
        encode_worldbridge_component_identity_persistence_envelope(tampered)


def test_duplicate_keys_and_non_finite_values_are_rejected():
    envelope, _ = _envelope()
    encoded = encode_worldbridge_component_identity_persistence_envelope(envelope)
    duplicate = encoded.replace(b'"status":"worldbridge_component_identity_persistence_envelope"', b'"status":"worldbridge_component_identity_persistence_envelope","status":"old"')
    with pytest.raises(ValueError, match="strict UTF-8 JSON"):
        decode_worldbridge_component_identity_persistence_envelope(duplicate)
    non_finite = encoded.replace(b'"scene_path":"scenes/challenge_scene.pond"', b'"scene_path":NaN')
    with pytest.raises(ValueError, match="strict UTF-8 JSON"):
        decode_worldbridge_component_identity_persistence_envelope(non_finite)
