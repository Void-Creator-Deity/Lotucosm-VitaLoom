# -*- coding: utf-8 -*-
from __future__ import annotations

import builtins
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from core.Lotucosm.runtime.world_bridge_live_capture_artifact import (
    MAX_ARTIFACT_BYTES,
    MEDIA_TYPE,
    _artifact_digest,
    _canonical_json_bytes,
    build_worldbridge_live_capture_artifact,
    build_worldbridge_live_capture_artifact_contract,
    decode_worldbridge_live_capture_artifact,
    encode_worldbridge_live_capture_artifact,
    validate_worldbridge_live_capture_artifact,
)
from core.Lotucosm.runtime.world_bridge_live_capture_session import (
    _sample_producer,
    _session_digest,
    abort_worldbridge_live_capture_session,
    append_worldbridge_live_capture_session_evidence,
    seal_worldbridge_live_capture_session,
    start_worldbridge_live_capture_session,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / (
    "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/"
    "core/Lotucosm/runtime/world_bridge_live_capture_artifact.py"
)


def _sealed_session(session_id: str = "artifact-session") -> dict[str, object]:
    session = start_worldbridge_live_capture_session(session_id, max_samples=2)
    session = append_worldbridge_live_capture_session_evidence(
        session,
        _sample_producer(sample_number=21, ps_energy=29.0),
    )
    session = append_worldbridge_live_capture_session_evidence(
        session,
        _sample_producer(sample_number=22, ps_energy=28.5),
    )
    return seal_worldbridge_live_capture_session(session)


def _reseal_artifact(artifact: dict[str, object]) -> None:
    session = artifact["session"]
    assert isinstance(session, dict)
    payload = _canonical_json_bytes(session)
    artifact["payload_byte_length"] = len(payload)
    artifact["payload_digest"] = hashlib.sha256(payload).hexdigest()
    artifact["session_id"] = session["session_id"]
    artifact["session_digest"] = session["session_digest"]
    artifact["artifact_digest"] = _artifact_digest(artifact)


def test_builds_valid_sealed_artifact_without_admission_claims() -> None:
    session = _sealed_session()
    artifact = build_worldbridge_live_capture_artifact(
        session,
        artifact_id="capture-artifact-001",
    )

    assert validate_worldbridge_live_capture_artifact(artifact) == {
        "valid": True,
        "errors": [],
    }
    assert artifact["media_type"] == MEDIA_TYPE
    assert artifact["session_id"] == session["session_id"]
    assert artifact["session_digest"] == session["session_digest"]
    assert artifact["payload_byte_length"] == len(_canonical_json_bytes(session))
    assert artifact["artifact_scope"] == "offline_diagnostic_transport_only"
    for field in (
        "replay_input",
        "checkpoint_state",
        "persistence_authority",
        "clocks_compared",
        "time_aligned",
        "causality_inferred",
        "atomic_checkpoint",
        "lossless",
        "replay_admitted",
        "default_ready",
    ):
        assert artifact[field] is False


def test_canonical_encode_decode_and_offline_file_round_trip(tmp_path: Path) -> None:
    artifact = build_worldbridge_live_capture_artifact(
        _sealed_session(),
        artifact_id="offline-round-trip",
    )
    encoded = encode_worldbridge_live_capture_artifact(artifact)
    artifact_path = tmp_path / "capture.worldbridge.json"
    artifact_path.write_bytes(encoded)
    restored_bytes = artifact_path.read_bytes()
    decoded = decode_worldbridge_live_capture_artifact(restored_bytes)

    assert restored_bytes == encoded
    assert decoded == artifact
    assert encode_worldbridge_live_capture_artifact(decoded) == encoded
    assert len(encoded) <= MAX_ARTIFACT_BYTES


def test_build_and_decode_are_copy_isolated() -> None:
    session = _sealed_session()
    original = copy.deepcopy(session)
    artifact = build_worldbridge_live_capture_artifact(session, artifact_id="copy-isolation")
    encoded = encode_worldbridge_live_capture_artifact(artifact)
    decoded = decode_worldbridge_live_capture_artifact(encoded)

    session["samples"][0]["sample_id"] = "caller-mutated"  # type: ignore[index]
    artifact["session"]["samples"][0]["sample_id"] = "artifact-mutated"  # type: ignore[index]

    assert decoded["session"] == original
    assert encode_worldbridge_live_capture_artifact(decoded) == encoded


def test_open_and_aborted_sessions_are_not_complete_artifacts() -> None:
    open_session = start_worldbridge_live_capture_session("open-artifact", max_samples=1)
    aborted = abort_worldbridge_live_capture_session(open_session, reason="operator stop")

    with pytest.raises(ValueError, match="requires a sealed session"):
        build_worldbridge_live_capture_artifact(open_session, artifact_id="open")
    with pytest.raises(ValueError, match="requires a sealed session"):
        build_worldbridge_live_capture_artifact(aborted, artifact_id="aborted")


def test_artifact_identity_and_byte_limit_inputs_are_strict() -> None:
    session = _sealed_session()
    with pytest.raises(ValueError, match="artifact_id"):
        build_worldbridge_live_capture_artifact(session, artifact_id=" padded ")
    artifact = build_worldbridge_live_capture_artifact(session, artifact_id="bounded")
    encoded = encode_worldbridge_live_capture_artifact(artifact)

    with pytest.raises(ValueError, match="max_bytes"):
        encode_worldbridge_live_capture_artifact(artifact, max_bytes=True)
    with pytest.raises(ValueError, match="max_bytes"):
        decode_worldbridge_live_capture_artifact(encoded, max_bytes=0)
    with pytest.raises(OverflowError, match="exceeds"):
        encode_worldbridge_live_capture_artifact(artifact, max_bytes=len(encoded) - 1)
    with pytest.raises(OverflowError, match="exceeds"):
        decode_worldbridge_live_capture_artifact(encoded, max_bytes=len(encoded) - 1)


def test_decode_accepts_bytes_like_but_rejects_text_empty_and_invalid_utf8() -> None:
    artifact = build_worldbridge_live_capture_artifact(_sealed_session(), artifact_id="bytes-like")
    encoded = encode_worldbridge_live_capture_artifact(artifact)

    assert decode_worldbridge_live_capture_artifact(bytearray(encoded)) == artifact
    assert decode_worldbridge_live_capture_artifact(memoryview(encoded)) == artifact
    with pytest.raises(TypeError, match="bytes-like"):
        decode_worldbridge_live_capture_artifact(encoded.decode("utf-8"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must not be empty"):
        decode_worldbridge_live_capture_artifact(b"")
    with pytest.raises(ValueError, match="strict UTF-8"):
        decode_worldbridge_live_capture_artifact(b"\xff")


def test_noncanonical_duplicate_and_nonfinite_json_are_rejected() -> None:
    artifact = build_worldbridge_live_capture_artifact(_sealed_session(), artifact_id="strict-json")
    pretty = json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")

    with pytest.raises(ValueError, match="not canonical JSON"):
        decode_worldbridge_live_capture_artifact(pretty)
    with pytest.raises(ValueError, match="strict JSON"):
        decode_worldbridge_live_capture_artifact(b'{"schema_version":1,"schema_version":1}')
    with pytest.raises(ValueError, match="strict JSON"):
        decode_worldbridge_live_capture_artifact(b'{"value":NaN}')
    with pytest.raises(ValueError, match="root must be an object"):
        decode_worldbridge_live_capture_artifact(b"[]")


def test_payload_and_envelope_digest_tampering_are_rejected() -> None:
    artifact = build_worldbridge_live_capture_artifact(_sealed_session(), artifact_id="digest-tamper")
    payload_tamper = copy.deepcopy(artifact)
    payload_tamper["session"]["session_id"] = "changed-session"  # type: ignore[index]
    validation = validate_worldbridge_live_capture_artifact(payload_tamper)
    assert "nested_session_invalid" in validation["errors"]
    assert "payload_digest_mismatch" in validation["errors"]
    assert "artifact_digest_mismatch" in validation["errors"]

    envelope_tamper = copy.deepcopy(artifact)
    envelope_tamper["artifact_id"] = "changed-artifact"
    assert "artifact_digest_mismatch" in validate_worldbridge_live_capture_artifact(
        envelope_tamper
    )["errors"]


def test_nested_e219_tamper_rejects_even_after_all_outer_digests_are_resealed() -> None:
    artifact = build_worldbridge_live_capture_artifact(_sealed_session(), artifact_id="nested-tamper")
    tampered = copy.deepcopy(artifact)
    session = tampered["session"]
    assert isinstance(session, dict)
    session["samples"][0]["sample_id"] = "fabricated:sample-0000"  # type: ignore[index]
    session["session_digest"] = _session_digest(session)
    _reseal_artifact(tampered)

    validation = validate_worldbridge_live_capture_artifact(tampered)
    assert validation["valid"] is False
    assert "nested_session_invalid" in validation["errors"]
    with pytest.raises(ValueError, match="nested_session_invalid"):
        encode_worldbridge_live_capture_artifact(tampered)


def test_metadata_extra_missing_and_semantic_overclaims_reject_after_reseal() -> None:
    artifact = build_worldbridge_live_capture_artifact(_sealed_session(), artifact_id="metadata")

    extra = copy.deepcopy(artifact)
    extra["unexpected"] = True
    extra["artifact_digest"] = _artifact_digest(extra)
    assert "artifact_keys_mismatch" in validate_worldbridge_live_capture_artifact(extra)["errors"]

    missing = copy.deepcopy(artifact)
    missing.pop("encoding")
    missing["artifact_digest"] = _artifact_digest(missing)
    assert "artifact_keys_mismatch" in validate_worldbridge_live_capture_artifact(missing)["errors"]

    overclaim = copy.deepcopy(artifact)
    overclaim["replay_input"] = True
    overclaim["artifact_digest"] = _artifact_digest(overclaim)
    assert "replay_input_mismatch" in validate_worldbridge_live_capture_artifact(overclaim)["errors"]

    unsupported = copy.deepcopy(artifact)
    unsupported["media_type"] = "application/json"
    unsupported["schema_version"] = 2
    unsupported["artifact_digest"] = _artifact_digest(unsupported)
    errors = validate_worldbridge_live_capture_artifact(unsupported)["errors"]
    assert "media_type_mismatch" in errors
    assert "schema_version_mismatch" in errors


def test_validator_returns_errors_for_malformed_unhashable_values() -> None:
    artifact = build_worldbridge_live_capture_artifact(_sealed_session(), artifact_id="malformed")
    malformed = copy.deepcopy(artifact)
    malformed["status"] = ["unhashable"]
    malformed["payload_byte_length"] = True
    malformed["artifact_digest"] = ["not-a-digest"]

    validation = validate_worldbridge_live_capture_artifact(malformed)
    assert validation["valid"] is False
    assert "status_mismatch" in validation["errors"]
    assert "payload_byte_length_invalid" in validation["errors"]
    assert "artifact_digest_invalid" in validation["errors"]


def test_contract_is_nested_in_runtime_status_without_default_or_replay_admission() -> None:
    contract = build_worldbridge_live_capture_artifact_contract()
    status = build_runtime_worldbridge_status()

    assert contract["contract_valid"] is True
    assert contract["round_trip_equal"] is True
    assert contract["accepted_session_lifecycle"] == "sealed"
    assert contract["replay_input"] is False
    assert contract["persistence_authority"] is False
    assert contract["replay_admitted"] is False
    assert contract["default_ready"] is False
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False
    assert status["sealed_live_comparability_capture_artifact_contract"] == contract
    assert "sealed_capture_artifact_module" in status["pilot_modules"]


def test_artifact_module_imports_when_pyqt6_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise ImportError("PyQt6 intentionally blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("_qt_free_worldbridge_capture_artifact", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    contract = module.build_worldbridge_live_capture_artifact_contract()
    assert contract["contract_valid"] is True
    assert contract["round_trip_equal"] is True
