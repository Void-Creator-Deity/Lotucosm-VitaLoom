# -*- coding: utf-8
from __future__ import annotations

import copy
import random
from types import SimpleNamespace

import pytest

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
)
from core.Lotucosm.runtime.world_bridge_live_checkpoint import (
    validate_worldbridge_live_checkpoint,
)
from core.VitaLoom.viewports.game_viewport import GameViewport
from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource
from core.Lotucosm.runtime.world_bridge_checkpoint_artifact import (
    build_worldbridge_checkpoint_artifact,
)
from core.Lotucosm.runtime.world_bridge_component_identity_artifact import (
    build_worldbridge_component_identity_artifact,
)
from core.Lotucosm.runtime.world_bridge_component_identity_persistence import (
    build_worldbridge_component_identity_persistence_envelope,
)
from core.Lotucosm.runtime.world_bridge_live_checkpoint_admission import (
    build_worldbridge_live_checkpoint_admission_witness,
)
from core.Lotucosm.runtime.world_bridge_e508_fresh_replay_corpus import (
    build_worldbridge_e508_fresh_replay_corpus,
)


class _Pond:
    def __init__(self) -> None:
        self.payload = {"name": "pond", "time": 3, "organisms": {"ps:a": {"energy": 9}}}
        self.organisms = {"ps:a": object()}

    def restore_serialized_state_in_place(self, payload):
        self.payload = copy.deepcopy(payload)


class _Serializer:
    def __init__(self, save_format="json"):
        self.save_format = save_format

    def serialize_pond(self, pond):
        return copy.deepcopy(pond.payload)

    def deserialize_pond(self, data, pond_class):
        pond = pond_class()
        pond.payload = copy.deepcopy(data)
        return pond


class _Viewport:
    _using_scene_runtime = True
    _sr_runtime_epoch = "epoch-1"
    _sr_runtime_scene_path = "scene.pond"
    _unified_pond_mode = True
    _unified_pond = _Pond()
    scene_runtime_entities = [SimpleNamespace(id="sr:a", entity_type="organism", radius=18.0, pinned=False, scripts=[], _world_bridge_organism_id="ps:a")]
    _sr_runtime_rng = random.Random(123)
    _input = {"keys_down": [], "mouse_scene_xy": None, "mouse_left": False, "mouse_left_clicked": False}
    _scene_runtime_time = 2.0
    is_playing = True
    is_paused = False

    def capture_sr_runtime_restore_envelope(self):
        return {
            "schema_version": 1,
            "kind": "sr_runtime_restore_slice",
            "runtime_epoch": self._sr_runtime_epoch,
            "scene_path": self._sr_runtime_scene_path,
            "scene_time": self._scene_runtime_time,
            "snapshots": [],
            "digest": "fake",
        }

    def restore_sr_runtime_restore_envelope(self, value):
        self._scene_runtime_time = float(value["scene_time"])

    def capture_sr_input_state(self):
        return copy.deepcopy(self._input)

    def restore_sr_input_state(self, value):
        self._input = copy.deepcopy(value)

    SR_TOPOLOGY_OWNER_FIELDS = (
        "structural_edges",
        "connection_edges",
        "signal_edges",
        "scene_runtime_edges",
        "scene_runtime_neighbor_ids",
        "membrane_attach",
        "membrane_template",
        "spawn_seq",
    )

    def capture_sr_topology_owner_state(self):
        return {
            "structural_edges": {},
            "connection_edges": {},
            "signal_edges": {},
            "scene_runtime_edges": [],
            "scene_runtime_neighbor_ids": {},
            "membrane_attach": {},
            "membrane_template": {},
            "spawn_seq": 0,
        }

    def restore_sr_topology_owner_state(self, state):
        if not isinstance(state, dict) or set(state) != set(
            self.SR_TOPOLOGY_OWNER_FIELDS
        ):
            raise ValueError("sr_topology_owner_state_fields_invalid")


def test_game_viewport_api_is_explicit_and_sequence_bound(monkeypatch):
    class Serializer:
        def __init__(self, save_format="json"): pass
        def serialize_pond(self, pond): return copy.deepcopy(pond.payload)

    import builtin.systems.pond_serializer as serializer_module
    monkeypatch.setattr(serializer_module, "PondSerializer", Serializer)

    viewport = _Viewport()
    checkpoint = GameViewport.capture_worldbridge_live_checkpoint(viewport, "api-checkpoint")
    assert validate_worldbridge_live_checkpoint(checkpoint)["valid"] is True
    assert viewport._worldbridge_checkpoint_sequence == 1
    viewport._scene_runtime_time = 99.0
    result = GameViewport.restore_worldbridge_live_checkpoint(viewport, checkpoint)
    assert result["restored"] is True
    assert viewport._worldbridge_checkpoint_sequence == 1
    assert viewport._scene_runtime_time == 2.0


def test_game_viewport_checkpoint_artifact_export_import_is_read_only(monkeypatch):
    class Serializer:
        def __init__(self, save_format="json"): pass
        def serialize_pond(self, pond): return copy.deepcopy(pond.payload)

    import builtin.systems.pond_serializer as serializer_module
    monkeypatch.setattr(serializer_module, "PondSerializer", Serializer)
    viewport = _Viewport()
    checkpoint = GameViewport.capture_worldbridge_live_checkpoint(viewport, "artifact-api")
    component_artifact = build_worldbridge_component_identity_artifact(
        receipts=[{"generation": 1, "hub_id": "h", "links": []}],
        duplicate_rejected=True, owner_drift_rejected=True, rollback_succeeded=True,
    )
    persistence = build_worldbridge_component_identity_persistence_envelope(
        project_path="project", project_lock={"schema_version": 1},
        runtime_epoch="epoch-1", scene_path="scene.pond", artifact=component_artifact,
    )
    witness = build_worldbridge_live_checkpoint_admission_witness(
        checkpoint=checkpoint,
        versioned_bundle={"runtime_version": "1.0.0", "sr_schema_version": 1,
                          "ps_schema_version": 1, "bridge_schema_version": 1},
        fresh_restore={"parity": True}, in_place_restore={"parity": True},
        identity_registration={"parity": True}, rollback={"atomic": True, "target_preserved": True},
    )
    encoded = GameViewport.export_worldbridge_checkpoint_artifact(
        viewport, checkpoint=checkpoint, persistence_envelope=persistence,
        admission_witness=witness,
    )
    result = GameViewport.import_worldbridge_checkpoint_artifact(viewport, encoded)
    assert result["valid"] is True
    assert result["live_restore_performed"] is False
    assert viewport._scene_runtime_time == 2.0
    tampered = bytearray(encoded)
    tampered[-2] = ord(" ")
    rejected = GameViewport.import_worldbridge_checkpoint_artifact(viewport, tampered)
    assert rejected["valid"] is False
    assert rejected["live_restore_performed"] is False
    assert rejected["diagnostic"]["diagnostic_digest"]


def test_game_viewport_e509_replay_envelope_is_read_only_and_project_bound(monkeypatch):
    viewport = _Viewport()
    viewport._sr_runtime_project_path = "project"
    import FrameCore.project_lock as project_lock_module
    monkeypatch.setattr(project_lock_module, "load_project_lock", lambda _path: {"schema_version": 1})
    digest = "1" * 64
    record = {"tick": 1, "parity": True, **{field: digest for field in (
        "sr_state_digest", "ps_state_digest", "input_state_digest", "randomness_state_digest",
        "bridge_identity_digest", "baseline_digest", "restored_digest",
    )}}
    corpus = build_worldbridge_e508_fresh_replay_corpus(
        checkpoint_digest="2" * 64, source_epoch="source", fresh_epoch="fresh", tick_records=[record]
    )
    diagnostic = {
        "schema_version": 1,
        "code": "restore_succeeded",
        "errors": [],
        "checkpoint_id": "e509-checkpoint",
        "checkpoint_digest": corpus["checkpoint_digest"],
        "diagnostic_digest": "",
    }
    import hashlib
    import json
    diagnostic["diagnostic_digest"] = hashlib.sha256(
        json.dumps({key: value for key, value in diagnostic.items() if key != "diagnostic_digest"}, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    encoded = GameViewport.export_worldbridge_replay_persistence_envelope(
        viewport, corpus=corpus, restore_diagnostic=diagnostic
    )
    result = GameViewport.import_worldbridge_replay_persistence_envelope(viewport, encoded)
    assert result["valid"] is True
    assert result["live_restore_performed"] is False
    assert result["replay_admitted"] is False
    tampered = bytearray(encoded)
    tampered[-2] = ord(" ")
    rejected = GameViewport.import_worldbridge_replay_persistence_envelope(viewport, tampered)
    assert rejected["valid"] is False
    assert rejected["live_restore_performed"] is False
    assert viewport._scene_runtime_time == 2.0


def test_game_viewport_operator_presentation_keeps_artifact_rejection_reason_bounded():
    viewport = GameViewport.__new__(GameViewport)
    viewport.query_worldbridge_quarantine_lifecycle_correlation = lambda: {
        "schema_version": 1,
        "status": "worldbridge_quarantine_lifecycle_correlation",
        "scope": "same_adapter_worldbridge_quarantine_lifecycle_evidence",
        "read_only": True,
        "availability": "available",
        "current_runtime_quarantined": True,
        "correlation": {
            "state": "current_quarantined_failure_tuple_observed",
            "same_adapter_only": True,
            "fresh_instance_boundary_observed": False,
        },
        "negative_capabilities": {
            "may_clear_quarantine": False,
            "may_retry_same_runtime_handoff": False,
            "may_construct_or_reuse_pond": False,
            "may_call_sr_ps_bridge_mutator": False,
            "fresh_boundary_is_state_recovery": False,
            "rollback_performed": False,
            "compensation_performed": False,
            "in_place_restore": False,
            "replay_admitted": False,
            "cross_adapter_lifecycle_correlation": False,
            "operator_action_admitted": False,
            "ui_authority": False,
            "default_ready": False,
        },
    }
    viewport._worldbridge_restore_diagnostic = {
        "schema_version": 1,
        "code": "worldbridge_checkpoint_artifact_rejected",
        "errors": ["artifact_digest_mismatch"],
        "diagnostic_digest": "b" * 64,
    }

    presentation = GameViewport.query_worldbridge_quarantine_operator_presentation(viewport)

    assert presentation["artifact_import_diagnostic"]["errors"] == ["artifact_digest_mismatch"]
    assert presentation["negative_capabilities"]["replay_admitted"] is False
    assert "ps_state" not in str(presentation)

def test_game_viewport_api_rejects_tampered_checkpoint_before_sequence_change():
    viewport = _Viewport()
    viewport._worldbridge_checkpoint_sequence = 4
    with pytest.raises(ValueError):
        GameViewport.restore_worldbridge_live_checkpoint(viewport, {"sequence": 0})
    assert viewport._worldbridge_checkpoint_sequence == 4


def test_viewport_named_stream_context_binding_is_explicit():
    viewport = GameViewport.__new__(GameViewport)
    viewport._sr_runtime_rng = random.Random(321)
    context = create_worldbridge_deterministic_randomness_context("viewport-context", "seed")
    viewport.set_worldbridge_opt_in_deterministic_randomness_context(context)
    assert viewport._worldbridge_opt_in_deterministic_randomness_context is context
    assert context.get_stream("sr.runtime") is viewport._sr_runtime_rng
    viewport.set_worldbridge_opt_in_deterministic_randomness_context(None)
    assert "_worldbridge_opt_in_deterministic_randomness_context" not in vars(viewport)


def test_game_viewport_exposes_qt_free_project_addon_evidence_provider():
    evidence = {"schema_version": 1, "digest": "evidence"}
    host = SimpleNamespace(lifecycle_evidence=lambda: evidence)
    viewport = GameViewport.__new__(GameViewport)
    viewport.editor_context = SimpleNamespace(
        plugin_loader=SimpleNamespace(project_scoped_plugin_host=host)
    )
    assert viewport._project_addon_lifecycle_evidence() is evidence


def test_game_viewport_builds_explicit_admission_witness_without_opening_runtime(
    monkeypatch,
):
    import builtin.systems.pond_serializer as serializer_module

    monkeypatch.setattr(serializer_module, "PondSerializer", _Serializer)
    viewport = _Viewport()
    checkpoint = GameViewport.capture_worldbridge_live_checkpoint(viewport, "admission")
    witness = GameViewport.build_worldbridge_live_checkpoint_admission_witness(
        viewport,
        checkpoint,
        rollback_evidence={"atomic": True, "target_preserved": True},
    )
    assert witness["contract_valid"] is True
    assert witness["opt_in_live_adapter_admitted"] is True
    assert witness["live_adapter_admitted"] is False
    assert witness["replay_admitted"] is False
    assert viewport._scene_runtime_time == 2.0


def test_game_viewport_admission_witness_compares_json_container_semantics(
    monkeypatch,
):
    import builtin.systems.pond_serializer as serializer_module

    monkeypatch.setattr(serializer_module, "PondSerializer", _Serializer)
    viewport = _Viewport()
    viewport._unified_pond.payload["size"] = (400.0, 300.0)
    checkpoint = GameViewport.capture_worldbridge_live_checkpoint(viewport, "json-state")
    witness = GameViewport.build_worldbridge_live_checkpoint_admission_witness(
        viewport,
        checkpoint,
        rollback_evidence={"atomic": True, "target_preserved": True},
    )
    assert checkpoint["ps_state"]["size"] == [400.0, 300.0]
    assert witness["evidence"]["in_place_restore_parity"] is True


def test_game_viewport_restore_failure_produces_target_preserved_rollback_witness(
    monkeypatch,
):
    import builtin.systems.pond_serializer as serializer_module
    from dataclasses import replace

    from core.Lotucosm.runtime.world_bridge_live_checkpoint import (
        WorldBridgeLiveCheckpointError,
    )
    import core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter as adapter_module

    monkeypatch.setattr(serializer_module, "PondSerializer", _Serializer)
    viewport = _Viewport()
    checkpoint = GameViewport.capture_worldbridge_live_checkpoint(viewport, "rollback")
    viewport._scene_runtime_time = 91.0
    viewport._unified_pond.payload["time"] = 91
    before = {
        "scene_time": viewport._scene_runtime_time,
        "pond": copy.deepcopy(viewport._unified_pond.payload),
        "input": copy.deepcopy(viewport._input),
        "rng": viewport._sr_runtime_rng.getstate(),
    }
    real_adapters = adapter_module.create_game_viewport_live_checkpoint_adapters(viewport)

    def fail_ps(_state):
        viewport._unified_pond.payload["time"] = 77
        raise RuntimeError("injected PS restore failure")

    monkeypatch.setattr(
        adapter_module,
        "create_game_viewport_live_checkpoint_adapters",
        lambda _viewport: replace(real_adapters, restore_ps=fail_ps),
    )
    with pytest.raises(WorldBridgeLiveCheckpointError) as raised:
        GameViewport.restore_worldbridge_live_checkpoint(viewport, checkpoint)

    report = raised.value.report
    assert report["phase"] == "ps"
    assert report["compensation_complete"] is True
    assert viewport._scene_runtime_time == before["scene_time"]
    assert viewport._unified_pond.payload == before["pond"]
    assert viewport._input == before["input"]
    assert viewport._sr_runtime_rng.getstate() == before["rng"]
    current_checkpoint = GameViewport.capture_worldbridge_live_checkpoint(
        viewport, "rollback-target"
    )
    witness = GameViewport.build_worldbridge_live_checkpoint_admission_witness(
        viewport,
        current_checkpoint,
        rollback_evidence={
            "atomic": report["compensation_complete"],
            "target_preserved": (
                viewport._scene_runtime_time == before["scene_time"]
                and viewport._unified_pond.payload == before["pond"]
            ),
        },
    )
    assert witness["evidence"]["atomic_failure_rollback"] is True
    assert witness["opt_in_live_adapter_admitted"] is True
    assert witness["live_adapter_admitted"] is False


def test_restore_failure_rejects_false_successful_compensation(monkeypatch):
    import builtin.systems.pond_serializer as serializer_module
    from dataclasses import replace
    from core.Lotucosm.runtime.world_bridge_live_checkpoint import (
        WorldBridgeLiveCheckpointError,
    )
    import core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter as adapter_module

    monkeypatch.setattr(serializer_module, "PondSerializer", _Serializer)
    viewport = _Viewport()
    checkpoint = GameViewport.capture_worldbridge_live_checkpoint(viewport, "verify")
    real_adapters = adapter_module.create_game_viewport_live_checkpoint_adapters(viewport)

    def fail_ps(_state):
        viewport._unified_pond.payload["time"] = 77
        raise RuntimeError("injected PS restore failure")

    def no_op_ps(_state):
        # Deliberately report success without restoring the mutated owner.
        return None

    monkeypatch.setattr(
        adapter_module,
        "create_game_viewport_live_checkpoint_adapters",
        lambda _viewport: replace(
            real_adapters, restore_ps=fail_ps, compensate_ps=no_op_ps
        ),
    )
    with pytest.raises(WorldBridgeLiveCheckpointError) as raised:
        GameViewport.restore_worldbridge_live_checkpoint(viewport, checkpoint)

    report = raised.value.report
    assert report["compensation_complete"] is False
    assert "rollback_verification" in report["compensation_errors"]


def test_restore_failure_compensates_identity_and_script_failure_history(
    monkeypatch,
):
    import builtin.systems.pond_serializer as serializer_module
    from dataclasses import replace
    from core.Lotucosm.runtime.world_bridge_live_checkpoint import (
        WorldBridgeLiveCheckpointError,
    )
    import core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter as adapter_module

    monkeypatch.setattr(serializer_module, "PondSerializer", _Serializer)
    viewport = _Viewport()
    viewport._sr_identity_source = DeterministicIdentitySource("e430")
    viewport._sr_identity_source.next("entity")
    viewport._sr_script_failure_receipts = [{
        "schema_version": 1,
        "status": "script_runtime_failure",
        "path": "scripts/target.py",
        "phase": "trust",
        "reason": "script_not_trusted",
        "exception_type": None,
        "runtime_epoch": "epoch-1",
        "entropy_evidence_committed": False,
        "identity_or_pond_mutation": False,
    }]
    viewport._sr_script_declared_paths = ["scripts/target.py"]
    checkpoint = GameViewport.capture_worldbridge_live_checkpoint(viewport, "joint")

    viewport._sr_identity_source.next("entity")
    viewport._sr_script_failure_receipts = []
    viewport._sr_script_declared_paths = []
    before_identity = viewport._sr_identity_source.snapshot()
    before_failures = []
    real_adapters = adapter_module.create_game_viewport_live_checkpoint_adapters(viewport)

    def fail_ps(_state):
        raise RuntimeError("injected PS restore failure")

    monkeypatch.setattr(
        adapter_module,
        "create_game_viewport_live_checkpoint_adapters",
        lambda _viewport: replace(real_adapters, restore_ps=fail_ps),
    )
    with pytest.raises(WorldBridgeLiveCheckpointError) as raised:
        GameViewport.restore_worldbridge_live_checkpoint(viewport, checkpoint)

    assert raised.value.report["phase"] == "ps"
    assert raised.value.report["compensation_complete"] is True
    assert viewport._sr_identity_source.snapshot() == before_identity
    assert viewport._sr_script_failure_receipts == before_failures
