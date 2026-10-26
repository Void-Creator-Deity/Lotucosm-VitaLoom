# -*- coding: utf-8
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections.abc import Mapping
from types import SimpleNamespace

import numpy as np
import pytest

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
)
from core.Lotucosm.runtime.world_bridge_input_sequence import WorldBridgeInputSequence
from core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter import (
    build_game_viewport_live_checkpoint_adapter_contract,
    canonical_ps_serializer_projection,
    create_game_viewport_live_checkpoint_adapters,
)
from core.Lotucosm.runtime.world_bridge_dynamic_topology_receipt import (
    build_worldbridge_dynamic_topology_receipt,
    validate_worldbridge_dynamic_topology_receipt,
)
from core.Lotucosm.runtime.world_bridge_component_identity_artifact import (
    build_worldbridge_component_identity_artifact,
)
from core.Lotucosm.runtime.world_bridge_live_checkpoint import (
    WorldBridgeLiveCheckpointCoordinator,
    WorldBridgeLiveCheckpointError,
    WorldBridgeOwnerBindingDrift,
    WorldBridgeTransactionCaptureError,
)
from core.Lotucosm.runtime.world_bridge_live_checkpoint import _digest as checkpoint_digest
from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource
from core.Lotucosm.sr_physics2d import PythonSrPhysics2DAdapter, SrPhysics2DWorld


class FakePond:
    def __init__(self) -> None:
        self.payload = {"name": "pond", "time": 3, "organisms": {"ps:a": {"energy": 9}}}
        self.randomness_rng = np.random.default_rng(91)
        self.organisms = {
            "ps:a": SimpleNamespace(randomness_rng=self.randomness_rng)
        }

    def serialize(self):
        return copy.deepcopy(self.payload)

    def restore_serialized_state_in_place(self, payload):
        self.payload = copy.deepcopy(payload)


class FakeViewport:
    def __init__(self) -> None:
        self._using_scene_runtime = True
        self._sr_runtime_epoch = "epoch-1"
        self._sr_runtime_scene_path = "scene.pond"
        self._unified_pond_mode = True
        self._unified_pond = FakePond()
        self.scene_runtime_entities = [SimpleNamespace(id="sr:a", entity_type="organism", radius=18.0, pinned=False, scripts=[], _world_bridge_organism_id="ps:a")]
        self._sr_runtime_rng = random.Random(123)
        self._input = {"keys_down": [], "mouse_scene_xy": None, "mouse_left": False, "mouse_left_clicked": False}
        self._worldbridge_input_sequence = WorldBridgeInputSequence()
        self._scene_runtime_time = 2.0
        self.is_playing = True
        self.is_paused = False
        self._sr_structural_edges = []
        self._sr_signal_edges = []
        self._sr_membrane_attach = {}
        self._sr_membrane_template = {}
        self._sr_connection_edges = []
        self._scene_runtime_edges = []
        self._scene_runtime_neighbor_ids = {}
        self._sr_spawn_seq = 0
        self._sr_physics_world = SrPhysics2DWorld(adapter=PythonSrPhysics2DAdapter())

    def _script_owner_registry_digest(self):
        from core.Lotucosm.runtime.world_bridge_randomness_authority import (
            build_caller_owned_stream_registry_digest,
        )

        return build_caller_owned_stream_registry_digest({
            "sr.runtime": self._sr_runtime_rng,
            "ps.pond": self._unified_pond.randomness_rng,
        })

    def capture_sr_runtime_restore_envelope(self):
        return {"schema_version": 1, "kind": "sr_runtime_restore_slice", "runtime_epoch": "epoch-1", "scene_path": "scene.pond", "scene_time": self._scene_runtime_time, "snapshots": [], "topology": {"structural_edges": copy.deepcopy(self._sr_structural_edges), "connection_edges": copy.deepcopy(self._sr_connection_edges), "signal_edges": copy.deepcopy(self._sr_signal_edges), "scene_runtime_edges": copy.deepcopy(self._scene_runtime_edges), "scene_runtime_neighbor_ids": {key: sorted(values) for key, values in self._scene_runtime_neighbor_ids.items()}, "membrane_attach": copy.deepcopy(self._sr_membrane_attach), "membrane_template": copy.deepcopy(self._sr_membrane_template), "spawn_seq": self._sr_spawn_seq}, "digest": "fake"}

    def restore_sr_runtime_restore_envelope(self, value):
        self._scene_runtime_time = float(value["scene_time"])
        topology = value.get("topology")
        if topology is not None:
            self._sr_structural_edges = copy.deepcopy(topology["structural_edges"])
            self._sr_connection_edges = copy.deepcopy(topology["connection_edges"])
            self._sr_signal_edges = copy.deepcopy(topology["signal_edges"])
            self._scene_runtime_edges = [tuple(edge) for edge in topology["scene_runtime_edges"]]
            self._scene_runtime_neighbor_ids = {
                str(key): frozenset(str(item) for item in values)
                for key, values in topology["scene_runtime_neighbor_ids"].items()
            }
            self._sr_membrane_attach = copy.deepcopy(topology["membrane_attach"])
            self._sr_membrane_template = copy.deepcopy(topology["membrane_template"])
            self._sr_spawn_seq = int(topology["spawn_seq"])

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
            "structural_edges": copy.deepcopy(self._sr_structural_edges),
            "connection_edges": copy.deepcopy(self._sr_connection_edges),
            "signal_edges": copy.deepcopy(self._sr_signal_edges),
            "scene_runtime_edges": copy.deepcopy(self._scene_runtime_edges),
            "scene_runtime_neighbor_ids": {
                str(key): sorted(str(item) for item in values)
                for key, values in self._scene_runtime_neighbor_ids.items()
            },
            "membrane_attach": copy.deepcopy(self._sr_membrane_attach),
            "membrane_template": copy.deepcopy(self._sr_membrane_template),
            "spawn_seq": int(self._sr_spawn_seq),
        }

    def restore_sr_topology_owner_state(self, state):
        if not isinstance(state, Mapping) or set(state) != set(
            self.SR_TOPOLOGY_OWNER_FIELDS
        ):
            raise ValueError("sr_topology_owner_state_fields_invalid")
        self._sr_structural_edges = copy.deepcopy(state["structural_edges"])
        self._sr_connection_edges = copy.deepcopy(state["connection_edges"])
        self._sr_signal_edges = copy.deepcopy(state["signal_edges"])
        self._scene_runtime_edges = [
            tuple(edge) for edge in copy.deepcopy(state["scene_runtime_edges"])
        ]
        self._scene_runtime_neighbor_ids = {
            str(key): frozenset(str(item) for item in values)
            for key, values in state["scene_runtime_neighbor_ids"].items()
        }
        self._sr_membrane_attach = copy.deepcopy(state["membrane_attach"])
        self._sr_membrane_template = copy.deepcopy(state["membrane_template"])
        self._sr_spawn_seq = int(state["spawn_seq"])

    def capture_sr_input_state(self):
        return copy.deepcopy(self._input)

    def restore_sr_input_state(self, value):
        self._input = copy.deepcopy(value)


def _patch_serializer(monkeypatch):
    class Serializer:
        def __init__(self, save_format="json"): pass
        def serialize_pond(self, pond): return pond.serialize()
    import builtin.systems.pond_serializer as module
    monkeypatch.setattr(module, "PondSerializer", Serializer)


def test_real_owner_adapter_captures_and_restores_existing_owners(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    coordinator = WorldBridgeLiveCheckpointCoordinator(create_game_viewport_live_checkpoint_adapters(viewport))
    checkpoint = coordinator.capture(checkpoint_id="cp", sequence=0)
    viewport._scene_runtime_time = 77.0
    viewport._unified_pond.payload["time"] = 77
    result = coordinator.restore(checkpoint)
    assert result["restored"] is True
    assert viewport._scene_runtime_time == 2.0
    assert viewport._unified_pond.payload["time"] == 3


def test_game_viewport_owner_binding_rejects_replaced_pond_before_restore(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    original_pond = viewport._unified_pond
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    coordinator = WorldBridgeLiveCheckpointCoordinator(adapters)
    checkpoint = coordinator.capture(checkpoint_id="owner-drift-before", sequence=0)
    replacement = FakePond()
    replacement.payload["time"] = 101
    viewport._unified_pond = replacement

    with pytest.raises(WorldBridgeOwnerBindingDrift, match="owner_root_changed:ps_pond"):
        coordinator.restore(checkpoint)

    assert original_pond.payload["time"] == 3
    assert replacement.payload["time"] == 101


def test_game_viewport_owner_drift_during_restore_stops_without_false_compensation(
    monkeypatch,
):
    from dataclasses import replace

    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    original_pond = viewport._unified_pond
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    coordinator = WorldBridgeLiveCheckpointCoordinator(adapters)
    checkpoint = coordinator.capture(checkpoint_id="owner-drift-mid", sequence=0)
    checkpoint_pond_state = copy.deepcopy(checkpoint["ps_state"])
    replacement = FakePond()
    replacement.payload["time"] = 202
    original_restore_ps = adapters.restore_ps

    def restore_ps_then_replace_owner(state):
        original_restore_ps(state)
        viewport._unified_pond = replacement

    coordinator = WorldBridgeLiveCheckpointCoordinator(
        replace(adapters, restore_ps=restore_ps_then_replace_owner)
    )
    with pytest.raises(WorldBridgeLiveCheckpointError) as raised:
        coordinator.restore(checkpoint)

    report = raised.value.report
    assert report["phase"] == "ps"
    assert report["owner_binding_validated"] is True
    assert "owner_root_changed:ps_pond" in report["owner_binding_errors"]
    assert report["compensation_complete"] is False
    assert "owner_binding" in report["compensation_errors"]
    assert original_pond.payload == checkpoint_pond_state
    assert replacement.payload["time"] == 202


def test_dynamic_topology_receipt_binds_epoch_structure_and_component_artifact(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    artifact = build_worldbridge_component_identity_artifact(
        receipts=[{"generation": 3, "hub_id": "hub", "links": []}],
        duplicate_rejected=True,
        owner_drift_rejected=True,
        rollback_succeeded=True,
    )
    viewport._worldbridge_component_identity_artifact = artifact
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_sr()
    receipt = state["topology_receipt"]
    assert receipt["generation"] == 3
    assert receipt["component_identity_artifact"] == artifact
    assert validate_worldbridge_dynamic_topology_receipt(
        receipt, runtime_epoch="epoch-1"
    )["valid"] is True
    viewport._worldbridge_component_identity_artifact = None
    with pytest.raises(RuntimeError, match="component artifact mismatch"):
        adapters.restore_sr(state)


def test_checkpoint_restore_rolls_back_membrane_topology_owner_state(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    source_edges = [{"start": "sr:a", "end": "sr:sensor", "channel": "struct"}]
    viewport._sr_structural_edges = copy.deepcopy(source_edges)
    viewport._sr_connection_edges = copy.deepcopy(source_edges)
    viewport._sr_signal_edges = [{"start": "sr:sensor", "end": "sr:a", "channel": "chemo"}]
    viewport._scene_runtime_edges = [("sr:a", "sr:sensor")]
    viewport._scene_runtime_neighbor_ids = {"sr:a": frozenset({"sr:sensor"})}
    viewport._sr_membrane_attach = {"sr:sensor": ("sr:a", 2.0, 3.0)}
    viewport._sr_membrane_template = {"sensors": [{"suffix": "sensor"}]}
    viewport._sr_spawn_seq = 4
    coordinator = WorldBridgeLiveCheckpointCoordinator(
        create_game_viewport_live_checkpoint_adapters(viewport)
    )
    checkpoint = coordinator.capture(checkpoint_id="membrane-topology", sequence=0)

    viewport._sr_structural_edges = []
    viewport._sr_connection_edges = []
    viewport._sr_signal_edges = []
    viewport._scene_runtime_edges = []
    viewport._scene_runtime_neighbor_ids = {}
    viewport._sr_membrane_attach = {}
    viewport._sr_membrane_template = {}
    viewport._sr_spawn_seq = 0

    result = coordinator.restore(checkpoint)

    assert result["restored"] is True
    assert viewport._sr_structural_edges == source_edges
    assert viewport._sr_signal_edges == checkpoint["sr_state"]["structure_fingerprint"]["signal_edges"]
    assert viewport._sr_membrane_attach == checkpoint["sr_state"]["structure_fingerprint"]["membrane_attach"]
    assert viewport._sr_spawn_seq == 4


def test_topology_restore_is_compensated_when_later_bridge_phase_fails(monkeypatch):
    from dataclasses import replace
    from core.Lotucosm.runtime.world_bridge_live_checkpoint import (
        WorldBridgeLiveCheckpointError,
    )

    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport._sr_structural_edges = [{"start": "sr:a", "end": "sr:old", "channel": "struct"}]
    viewport._sr_connection_edges = copy.deepcopy(viewport._sr_structural_edges)
    viewport._sr_membrane_attach = {"sr:old": ("sr:a", 1.0, 0.0)}
    viewport._scene_runtime_edges = [("sr:a", "sr:old")]
    viewport._scene_runtime_neighbor_ids = {"sr:a": frozenset({"sr:old"})}
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    coordinator = WorldBridgeLiveCheckpointCoordinator(adapters)
    checkpoint = coordinator.capture(checkpoint_id="topology-target", sequence=0)

    viewport._sr_structural_edges = [{"start": "sr:a", "end": "sr:new", "channel": "struct"}]
    viewport._sr_connection_edges = copy.deepcopy(viewport._sr_structural_edges)
    viewport._sr_membrane_attach = {"sr:new": ("sr:a", 2.0, 0.0)}
    viewport._scene_runtime_edges = [("sr:a", "sr:new")]
    viewport._scene_runtime_neighbor_ids = {"sr:a": frozenset({"sr:new"})}
    before = coordinator.capture(checkpoint_id="topology-before-failure", sequence=1)

    def fail_bridge(_links):
        raise RuntimeError("injected bridge phase failure")

    coordinator._adapters = replace(adapters, restore_bridge=fail_bridge)
    with pytest.raises(WorldBridgeLiveCheckpointError) as raised:
        coordinator.restore(checkpoint)

    assert raised.value.report["phase"] == "bridge"
    assert raised.value.report["compensation_complete"] is True
    after = coordinator.capture(checkpoint_id="topology-after-failure", sequence=1)
    from core.Lotucosm.runtime.world_bridge_live_checkpoint import _state_digest

    assert _state_digest(after) == _state_digest(before)


def test_dynamic_topology_receipt_rejects_digest_and_epoch_drift():
    structure = {"fingerprint": "a" * 64}
    receipt = build_worldbridge_dynamic_topology_receipt(
        runtime_epoch="epoch-1", generation=0, structure_fingerprint=structure
    )
    assert validate_worldbridge_dynamic_topology_receipt(receipt)["valid"] is True
    tampered = copy.deepcopy(receipt)
    tampered["generation"] = 1
    assert "receipt_digest_mismatch" in validate_worldbridge_dynamic_topology_receipt(
        tampered
    )["errors"]
    assert "receipt_runtime_epoch_mismatch" in validate_worldbridge_dynamic_topology_receipt(
        receipt, runtime_epoch="epoch-2"
    )["errors"]


def test_dynamic_topology_receipt_rejects_invalid_nested_artifact_and_epoch():
    import hashlib
    import json

    artifact = build_worldbridge_component_identity_artifact(
        receipts=[],
        duplicate_rejected=True,
        owner_drift_rejected=True,
        rollback_succeeded=True,
    )
    receipt = build_worldbridge_dynamic_topology_receipt(
        runtime_epoch="epoch-1",
        generation=0,
        structure_fingerprint={"fingerprint": "a" * 64},
        component_identity_artifact=artifact,
    )
    receipt["component_identity_artifact"] = {"status": "forged"}
    receipt["component_identity_artifact_digest"] = hashlib.sha256(
        json.dumps(
            receipt["component_identity_artifact"],
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    receipt["receipt_digest"] = ""
    receipt["receipt_digest"] = hashlib.sha256(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    validation = validate_worldbridge_dynamic_topology_receipt(receipt)
    assert validation["valid"] is False
    assert "receipt_component_artifact_invalid" in validation["errors"]

    receipt["runtime_epoch"] = "   "
    receipt["receipt_digest"] = ""
    receipt["receipt_digest"] = hashlib.sha256(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    validation = validate_worldbridge_dynamic_topology_receipt(receipt)
    assert validation["valid"] is False
    assert "receipt_runtime_epoch_invalid" in validation["errors"]


def test_component_identity_receipt_is_revalidated_before_checkpoint_restore(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    component = SimpleNamespace(id="ps:component", sr_component_id="sr:component")
    viewport._unified_pond.organisms["ps:a"].components = {component.id: component}
    viewport.scene_runtime_entities[0]._world_bridge_component_identity_links = [{
        "sr_component_id": "sr:component",
        "ps_component_id": "ps:component",
        "sr_organism_id": "sr:a",
        "ps_organism_id": "ps:a",
    }]
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_lifecycle()
    component.sr_component_id = "sr:drifted"
    with pytest.raises(RuntimeError, match="component identity receipt mismatch"):
        adapters.restore_lifecycle(state)
    component.sr_component_id = "sr:component"
    adapters.restore_lifecycle(state)


def test_component_identity_artifact_is_carried_and_revalidated(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    artifact = build_worldbridge_component_identity_artifact(
        receipts=[{
            "generation": 1,
            "hub_id": "hub",
            "sr_component_id": "sr:component",
            "ps_component_id": "ps:component",
            "sr_organism_id": "sr:a",
            "ps_organism_id": "ps:a",
        }],
        duplicate_rejected=True,
        owner_drift_rejected=True,
        rollback_succeeded=True,
    )
    viewport._worldbridge_component_identity_artifact = artifact
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_lifecycle()
    assert state["component_identity_artifact"] == artifact
    tampered = copy.deepcopy(state)
    tampered["component_identity_artifact"]["provenance"]["runtime_status"] = "tampered"
    with pytest.raises(ValueError, match="component identity artifact is invalid"):
        adapters.restore_lifecycle(tampered)


def test_checkpoint_restore_restores_component_artifact_before_sr_receipt_check(
    monkeypatch,
):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    artifact_a = build_worldbridge_component_identity_artifact(
        receipts=[{"generation": 1, "hub_id": "a", "links": []}],
        duplicate_rejected=True,
        owner_drift_rejected=True,
        rollback_succeeded=True,
    )
    artifact_b = build_worldbridge_component_identity_artifact(
        receipts=[{"generation": 2, "hub_id": "b", "links": []}],
        duplicate_rejected=True,
        owner_drift_rejected=True,
        rollback_succeeded=True,
    )
    viewport._worldbridge_component_identity_artifact = artifact_a
    coordinator = WorldBridgeLiveCheckpointCoordinator(
        create_game_viewport_live_checkpoint_adapters(viewport)
    )
    checkpoint = coordinator.capture(checkpoint_id="artifact-restore", sequence=0)
    viewport._worldbridge_component_identity_artifact = artifact_b

    result = coordinator.restore(checkpoint)

    assert result["restored"] is True
    assert viewport._worldbridge_component_identity_artifact == artifact_a


def test_project_runtime_binding_is_carried_and_rejected_with_structured_diagnostic(
    monkeypatch, tmp_path
):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport._sr_runtime_project_path = str(tmp_path)
    (tmp_path / "project.lock.json").write_text(
        json.dumps({"schema_version": 1, "product": "test"}), encoding="utf-8"
    )
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_lifecycle()
    assert state["project_runtime_binding"]["runtime_epoch"] == "epoch-1"
    changed_lock = {"schema_version": 1, "product": "changed"}
    (tmp_path / "project.lock.json").write_text(json.dumps(changed_lock), encoding="utf-8")
    with pytest.raises(RuntimeError, match="worldbridge_project_runtime_binding_rejected"):
        adapters.restore_lifecycle(state)
    assert viewport._worldbridge_restore_diagnostic["code"] == "project_runtime_binding_rejected"
    assert "runtime_binding_project_lock_digest_mismatch" in viewport._worldbridge_restore_diagnostic["errors"]


def test_addon_lifecycle_evidence_is_bound_to_checkpoint_restore(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    evidence = {
        "schema_version": 1,
        "project_path": "world",
        "discovery": {"status": "ready", "sources": []},
        "lifecycle": {"status": "settled", "completed": {"activated": [], "deactivated": []}},
        "addon_runtime_receipts": [],
    }
    evidence["digest"] = hashlib.sha256(json.dumps(
        {**evidence, "digest": ""}, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    viewport._project_addon_lifecycle_evidence = lambda: copy.deepcopy(evidence)
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_lifecycle()
    assert state["project_addon_lifecycle_evidence"]["digest"] == evidence["digest"]

    changed = copy.deepcopy(evidence)
    changed["project_path"] = "other-world"
    changed["digest"] = hashlib.sha256(json.dumps(
        {**changed, "digest": ""}, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    viewport._project_addon_lifecycle_evidence = lambda: changed
    with pytest.raises(RuntimeError, match="lifecycle evidence digest mismatch"):
        adapters.restore_lifecycle(state)


def test_checkpoint_restores_caller_owned_pond_generator(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    coordinator = WorldBridgeLiveCheckpointCoordinator(
        create_game_viewport_live_checkpoint_adapters(viewport)
    )
    checkpoint = coordinator.capture(checkpoint_id="pond-rng", sequence=0)
    expected = float(viewport._unified_pond.randomness_rng.random())
    viewport._unified_pond.randomness_rng.random(4)
    coordinator.restore(checkpoint)
    assert float(viewport._unified_pond.randomness_rng.random()) == expected
    assert "pond_runtime" in checkpoint["randomness_state"]
    assert set(checkpoint["randomness_state"]["caller_owned_streams"]) == {
        "sr.runtime",
        "ps.pond",
    }


def test_caller_owned_stream_registry_tampering_is_rejected(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    checkpoint = adapters.capture_randomness()
    tampered = copy.deepcopy(checkpoint)
    tampered["caller_owned_streams"]["ps.pond"]["family"] = "python_random"
    with pytest.raises(ValueError, match="invalid SR runtime randomness state"):
        adapters.restore_randomness(tampered)


def test_native_boundary_receipt_tampering_is_rejected_before_restore(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_randomness()
    tampered = copy.deepcopy(state)
    tampered["native_boundary_receipt"]["status"] = "admitted"
    from core.Lotucosm.runtime.world_bridge_randomness_authority import (
        _rng_checkpoint_digest,
    )
    tampered["checkpoint_digest"] = _rng_checkpoint_digest(tampered)
    with pytest.raises(ValueError, match="invalid SR runtime randomness state"):
        adapters.restore_randomness(tampered)


def test_caller_owned_owner_mode_receipt_is_bound_to_live_runtime(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_randomness()
    state["caller_owned_stream_receipt"]["streams"][0]["mode"] = "detached"
    from core.Lotucosm.runtime.world_bridge_randomness_authority import (
        _canonical_json_bytes,
        _rng_checkpoint_digest,
    )

    import hashlib

    state["caller_owned_stream_receipt"]["registry_digest"] = hashlib.sha256(
        _canonical_json_bytes(state["caller_owned_stream_receipt"]["streams"])
    ).hexdigest()
    state["checkpoint_digest"] = _rng_checkpoint_digest(state)
    with pytest.raises(RuntimeError, match="owner receipt mismatch"):
        adapters.restore_randomness(state)


def test_live_checkpoint_rejects_script_bound_to_foreign_owner(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport.scene_runtime_entities[0].scripts = [
        SimpleNamespace(randomness_rng=np.random.default_rng(444))
    ]
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    with pytest.raises(RuntimeError, match="SR script randomness owner graph"):
        adapters.capture_randomness()


def test_live_checkpoint_rejects_script_with_detached_owner_mode(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport.scene_runtime_entities[0].scripts = [
        SimpleNamespace(
            randomness_rng=viewport._sr_runtime_rng,
            randomness_owner_mode="detached",
        )
    ]
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    with pytest.raises(RuntimeError, match="SR script randomness owner graph"):
        adapters.capture_randomness()


def test_script_owner_graph_digest_binds_execution_path_and_owner_stream(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport.scene_runtime_entities[0].scripts = [
        SimpleNamespace(
            randomness_rng=viewport._sr_runtime_rng,
            randomness_owner_mode="runtime",
        )
    ]
    from core.Lotucosm.runtime.world_bridge_randomness_authority import (
        build_sr_script_owner_graph_digest,
    )

    first = build_sr_script_owner_graph_digest(viewport.scene_runtime_entities)
    viewport.scene_runtime_entities[0].scripts[0].randomness_owner_mode = "detached"
    second = build_sr_script_owner_graph_digest(viewport.scene_runtime_entities)
    assert first != second


def test_script_execution_cursors_round_trip_without_requiring_equal_live_cursor(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    script = SimpleNamespace(
        randomness_rng=viewport._sr_runtime_rng,
        randomness_owner_mode="runtime",
        _randomness_execution_ticks=7,
        _randomness_consumption_count=3,
    )
    viewport.scene_runtime_entities[0].scripts = [script]
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_lifecycle()
    script._randomness_execution_ticks = 42
    script._randomness_consumption_count = 19
    adapters.restore_lifecycle(state)
    assert script._randomness_execution_ticks == 7
    assert script._randomness_consumption_count == 3


def test_deterministic_identity_source_is_part_of_lifecycle_checkpoint(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport._sr_identity_source = DeterministicIdentitySource("e418")
    first = viewport._sr_identity_source.next("sr")
    coordinator = WorldBridgeLiveCheckpointCoordinator(
        create_game_viewport_live_checkpoint_adapters(viewport)
    )
    checkpoint = coordinator.capture(checkpoint_id="identity", sequence=0)
    assert checkpoint["lifecycle"]["identity_source"]["counters"] == {"sr": 1}
    viewport._sr_identity_source.next("sr")
    coordinator.restore(checkpoint)
    assert viewport._sr_identity_source.next("sr") != first
    assert viewport._sr_identity_source.snapshot()["counters"] == {"sr": 2}


def test_script_failure_receipts_round_trip_with_lifecycle_checkpoint(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport._sr_script_failure_receipts = [{
        "schema_version": 1,
        "status": "script_runtime_failure",
        "path": "scripts/blocked.py",
        "phase": "trust",
        "reason": "script_not_trusted",
        "exception_type": None,
        "runtime_epoch": "epoch-1",
        "entropy_evidence_committed": False,
        "identity_or_pond_mutation": False,
    }]
    viewport._sr_script_declared_paths = ["scripts/blocked.py"]
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_lifecycle()
    viewport._sr_script_failure_receipts = []
    adapters.restore_lifecycle(state)
    assert viewport._sr_script_failure_receipts == state["script_failure_receipts"]
    assert state["script_evidence"]["owner_stream_name"] == "sr.runtime"


def test_script_evidence_owner_registry_mismatch_is_rejected_before_identity_restore(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport._sr_identity_source = DeterministicIdentitySource("e436")
    viewport._sr_identity_source.next("entity")
    state = create_game_viewport_live_checkpoint_adapters(viewport).capture_lifecycle()
    original = viewport._sr_identity_source.snapshot()
    state["script_evidence"]["owner_registry_digest"] = "b" * 64
    with pytest.raises(RuntimeError, match="owner registry mismatch"):
        create_game_viewport_live_checkpoint_adapters(viewport).restore_lifecycle(state)
    assert viewport._sr_identity_source.snapshot() == original


def test_script_owner_graph_digest_rejects_runtime_script_structure_change(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport._sr_identity_source = DeterministicIdentitySource("e446")
    viewport._sr_identity_source.next("entity")
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_lifecycle()
    original = viewport._sr_identity_source.snapshot()
    viewport.scene_runtime_entities[0].scripts = [
        SimpleNamespace(randomness_rng=viewport._sr_runtime_rng)
    ]
    with pytest.raises(RuntimeError, match="script owner graph digest mismatch"):
        adapters.restore_lifecycle(state)
    assert viewport._sr_identity_source.snapshot() == original


def test_script_evidence_digest_rejects_receipt_replacement_before_identity_restore(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport._sr_identity_source = DeterministicIdentitySource("e447")
    viewport._sr_identity_source.next("entity")
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_lifecycle()
    original = viewport._sr_identity_source.snapshot()
    state["script_evidence"]["receipts"] = [{"path": "replacement.py"}]
    with pytest.raises(ValueError, match="script evidence corpus is incomplete"):
        adapters.restore_lifecycle(state)
    assert viewport._sr_identity_source.snapshot() == original


def test_tampered_script_failure_receipts_are_rejected_before_identity_restore(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport._sr_identity_source = DeterministicIdentitySource("e428")
    viewport._sr_identity_source.next("entity")
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_lifecycle()
    original_identity = viewport._sr_identity_source.snapshot()
    state["script_failure_receipts"] = {"bad": True}
    with pytest.raises(ValueError, match="failure receipts"):
        adapters.restore_lifecycle(state)
    assert viewport._sr_identity_source.snapshot() == original_identity


def test_script_failure_receipt_from_another_epoch_is_rejected(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_lifecycle()
    state["script_failure_receipts"] = [{
        "schema_version": 1,
        "status": "script_runtime_failure",
        "path": "scripts/blocked.py",
        "phase": "trust",
        "reason": "script_not_trusted",
        "exception_type": None,
        "runtime_epoch": "old-epoch",
        "entropy_evidence_committed": False,
        "identity_or_pond_mutation": False,
    }]
    with pytest.raises(RuntimeError, match="epoch mismatch"):
        adapters.restore_lifecycle(state)


def test_deterministic_identity_checkpoint_rejects_tamper_without_mutation(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport._sr_identity_source = DeterministicIdentitySource("e418")
    viewport._sr_identity_source.next("sr")
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_lifecycle()
    original = viewport._sr_identity_source.snapshot()
    state["identity_source"]["seed_digest"] = "tampered"
    with pytest.raises(ValueError, match="seed mismatch"):
        adapters.restore_lifecycle(state)
    assert viewport._sr_identity_source.snapshot() == original


def test_deterministic_viewport_rejects_legacy_lifecycle_envelope(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport._sr_identity_source = DeterministicIdentitySource("e418")
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_lifecycle()
    state.pop("identity_source")
    with pytest.raises(RuntimeError, match="identity checkpoint state is missing"):
        adapters.restore_lifecycle(state)


def test_checkpoint_records_and_requires_selected_sr2d_backend(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    checkpoint = WorldBridgeLiveCheckpointCoordinator(
        create_game_viewport_live_checkpoint_adapters(viewport)
    ).capture(checkpoint_id="backend", sequence=0)
    assert checkpoint["sr_state"]["physics_backend"]["backend_id"] == "python"
    assert checkpoint["sr_state"]["physics_backend"]["artifact_provenance"] == "not_applicable"

    class OtherBackend:
        backend_id = "other"

        def step(self, *args, **kwargs):
            pass

    viewport._sr_physics_world = SrPhysics2DWorld(adapter=OtherBackend())
    with pytest.raises(
        WorldBridgeOwnerBindingDrift,
        match="owner_root_changed:sr_physics_world",
    ):
        WorldBridgeLiveCheckpointCoordinator(
            create_game_viewport_live_checkpoint_adapters(viewport)
        ).restore(checkpoint)


def test_checkpoint_binds_selected_backend_to_native_receipt(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    checkpoint = WorldBridgeLiveCheckpointCoordinator(
        create_game_viewport_live_checkpoint_adapters(viewport)
    ).capture(checkpoint_id="backend-receipt", sequence=0)
    evidence = checkpoint["sr_state"]["native_backend_selection"]
    assert evidence["selected_backend_id"] == "python"
    assert evidence["status"] == "reference_python"
    assert evidence["native_receipt_status"] == "quarantined"
    assert evidence["native_receipt_digest"]

    tampered = copy.deepcopy(checkpoint)
    tampered["sr_state"]["native_backend_selection"]["native_receipt_digest"] = "tampered"
    with pytest.raises(ValueError, match="digest_mismatch"):
        WorldBridgeLiveCheckpointCoordinator(
            create_game_viewport_live_checkpoint_adapters(viewport)
        ).restore(tampered)


def test_checkpoint_restores_with_explicit_project_backend_request(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport._sr2d_backend_request = "python"
    checkpoint = WorldBridgeLiveCheckpointCoordinator(
        create_game_viewport_live_checkpoint_adapters(viewport)
    ).capture(checkpoint_id="backend-request", sequence=0)
    assert checkpoint["sr_state"]["native_backend_selection"]["requested_backend_id"] == "python"
    result = WorldBridgeLiveCheckpointCoordinator(
        create_game_viewport_live_checkpoint_adapters(viewport)
    ).restore(checkpoint)
    assert result["restored"] is True


def test_adapter_rejects_without_active_unified_pond():
    viewport = FakeViewport()
    viewport._unified_pond_mode = False
    with pytest.raises(RuntimeError, match="unified Pond"):
        create_game_viewport_live_checkpoint_adapters(viewport).capture_sr()


class _E542LiveState:
    def __init__(self, payload):
        self.payload = copy.deepcopy(payload)
        self.digest = hashlib.sha256(
            json.dumps(
                self.payload, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()




def test_e542_production_adapter_exposes_combined_transaction_capture(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    calls = {"live": 0}

    def capture_live():
        calls["live"] += 1
        return _E542LiveState(viewport._unified_pond.payload)

    viewport._unified_pond.capture_worldbridge_live_transaction_state = capture_live
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)

    portable, live = adapters.capture_transaction_state()

    assert calls["live"] == 3
    assert canonical_ps_serializer_projection(portable) == viewport._unified_pond.payload
    assert portable["worldbridge_organism_lifecycle"]["organisms"] == {}
    assert isinstance(live, _E542LiveState)
    assert live.payload == viewport._unified_pond.payload


def test_e542_production_adapter_exposes_whole_owner_snapshot(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport._unified_pond.capture_worldbridge_live_transaction_state = (
        lambda: _E542LiveState(viewport._unified_pond.payload)
    )
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)

    snapshot = adapters.capture_transaction_snapshot()

    assert snapshot.sr_state["runtime_restore_envelope"]["scene_time"] == 2.0
    assert canonical_ps_serializer_projection(snapshot.ps_state) == viewport._unified_pond.payload
    assert snapshot.live_ps_state.payload == viewport._unified_pond.payload
    assert snapshot.bridge_identity_links == [
        {"sr_entity_id": "sr:a", "ps_organism_id": "ps:a"}
    ]
    assert snapshot.input_state["canonical_sequence"]["next_sequence"] == 1
    assert snapshot.randomness_state["schema_version"] == 1
    assert snapshot.lifecycle["runtime_epoch"] == "epoch-1"
    assert snapshot.topology_owner_state["spawn_seq"] == 0

def test_e542_production_adapter_rejects_other_owner_drift_during_capture(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport._unified_pond.capture_worldbridge_live_transaction_state = (
        lambda: _E542LiveState(viewport._unified_pond.payload)
    )

    import core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter as adapter_module

    original_evidence = adapter_module._capture_transaction_owner_evidence
    calls = {"evidence": 0}

    def capture_evidence(target, capture_live):
        calls["evidence"] += 1
        if calls["evidence"] == 2:
            target._scene_runtime_time = 3.0
        return original_evidence(target, capture_live)

    monkeypatch.setattr(
        adapter_module, "_capture_transaction_owner_evidence", capture_evidence
    )

    adapters = create_game_viewport_live_checkpoint_adapters(viewport)

    with pytest.raises(
        WorldBridgeTransactionCaptureError,
        match="transaction_owner_changed_during_capture",
    ) as raised:
        WorldBridgeLiveCheckpointCoordinator(adapters)._capture_transaction_snapshot()
    assert raised.value.details["owners"] == ["sr", "lifecycle"]


@pytest.mark.parametrize(
    ("owners", "mutate"),
    [
        (["bridge"], lambda viewport: viewport.scene_runtime_entities[0].__setattr__("_world_bridge_organism_id", None)),
        (["input"], lambda viewport: viewport._input.__setitem__("cursor", 1)),
        (["randomness"], lambda viewport: viewport._sr_runtime_rng.seed(999)),
        (["lifecycle"], lambda viewport: setattr(viewport, "is_paused", True)),
        (["sr", "topology"], lambda viewport: setattr(viewport, "_sr_spawn_seq", 1)),
    ],
)
def test_e542_production_adapter_reports_each_owner_drift(
    monkeypatch, owners, mutate
):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport._unified_pond.capture_worldbridge_live_transaction_state = (
        lambda: _E542LiveState(viewport._unified_pond.payload)
    )

    import core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter as adapter_module

    original_evidence = adapter_module._capture_transaction_owner_evidence
    calls = {"evidence": 0}

    def capture_evidence(target, capture_live):
        calls["evidence"] += 1
        if calls["evidence"] == 2:
            mutate(target)
        return original_evidence(target, capture_live)

    monkeypatch.setattr(
        adapter_module, "_capture_transaction_owner_evidence", capture_evidence
    )
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)

    with pytest.raises(
        WorldBridgeTransactionCaptureError,
        match="transaction_owner_changed_during_capture",
    ) as raised:
        WorldBridgeLiveCheckpointCoordinator(adapters)._capture_transaction_snapshot()

    assert raised.value.details["owners"] == owners


def test_e542_production_adapter_contract_keeps_admission_closed():
    contract = build_game_viewport_live_checkpoint_adapter_contract()

    assert contract["transaction_owner_evidence_fenced"] is True
    assert contract["transaction_owner_snapshot_count"] == 1
    assert contract["transaction_owner_evidence_probe_rounds"] == 2
    assert contract["transaction_capture_uses_combined_owner_callback"] is True
    assert contract["transaction_ps_capture_digest_fenced"] is True
    assert contract["atomic_checkpoint"] is False
    assert contract["replay_admitted"] is False
    assert contract["default_ready"] is False


def test_e542_production_adapter_ordinary_capture_keeps_legacy_compatibility(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    coordinator = WorldBridgeLiveCheckpointCoordinator(adapters)

    checkpoint = coordinator.capture(checkpoint_id="e542-ordinary", sequence=0)

    assert (
        canonical_ps_serializer_projection(checkpoint["ps_state"])
        == viewport._unified_pond.payload
    )
    assert "worldbridge_organism_lifecycle" in checkpoint["ps_state"]
    assert "worldbridge_organism_scripts" in checkpoint["ps_state"]
    assert "worldbridge_organism_hierarchy" in checkpoint["ps_state"]


def test_randomness_adapter_restores_sr_and_supported_global_streams():
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    try:
        viewport = FakeViewport()
        adapters = create_game_viewport_live_checkpoint_adapters(viewport)
        snapshot = adapters.capture_randomness()
        expected_local = viewport._sr_runtime_rng.random()
        expected_python = random.random()
        expected_numpy = float(np.random.random())

        viewport._sr_runtime_rng.random()
        random.random()
        np.random.random()
        adapters.restore_randomness(snapshot)

        assert viewport._sr_runtime_rng.random() == expected_local
        assert random.random() == expected_python
        assert float(np.random.random()) == expected_numpy
    finally:
        random.setstate(python_before)
        np.random.set_state(numpy_before)


def test_randomness_adapter_restores_opt_in_named_python_and_numpy_streams():
    viewport = FakeViewport()
    context = create_worldbridge_deterministic_randomness_context("adapter-context", "seed")
    python_stream = register_worldbridge_deterministic_random_stream(
        context, "script", "python_random"
    )
    numpy_stream = register_worldbridge_deterministic_random_stream(
        context, "ps.resource", "numpy_pcg64_generator"
    )
    viewport._worldbridge_opt_in_deterministic_randomness_context = context
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    snapshot = adapters.capture_randomness()
    expected_python = python_stream.random()
    expected_numpy = float(numpy_stream.random())
    python_stream.random()
    numpy_stream.random()
    adapters.restore_randomness(snapshot)
    assert python_stream.random() == expected_python
    assert float(numpy_stream.random()) == expected_numpy


def test_randomness_adapter_rejects_context_owner_mismatch_without_mutation():
    viewport = FakeViewport()
    source = create_worldbridge_deterministic_randomness_context("source", "seed")
    register_worldbridge_deterministic_random_stream(source, "script", "python_random")
    viewport._worldbridge_opt_in_deterministic_randomness_context = source
    snapshot = create_game_viewport_live_checkpoint_adapters(viewport).capture_randomness()
    target = create_worldbridge_deterministic_randomness_context("target", "seed")
    register_worldbridge_deterministic_random_stream(target, "script", "python_random")
    viewport._worldbridge_opt_in_deterministic_randomness_context = target
    before = target.snapshot()
    with pytest.raises(ValueError, match="invalid SR runtime randomness state"):
        create_game_viewport_live_checkpoint_adapters(viewport).restore_randomness(snapshot)
    assert target.snapshot() == before


def test_input_checkpoint_binds_canonical_cursor_and_epoch():
    viewport = FakeViewport()
    viewport._worldbridge_input_sequence.append("key_down", {"key": "W"})
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_input()
    assert state["canonical_sequence"]["next_sequence"] == 2
    assert state["canonical_sequence"]["pause_reset_epoch"] == 0

    viewport._worldbridge_input_sequence.lifecycle("pause")
    viewport._worldbridge_input_sequence.append("key_down", {"key": "A"})
    adapters.restore_input(state)
    restored = viewport._worldbridge_input_sequence.snapshot()
    assert restored == state["canonical_sequence"]


def test_input_checkpoint_round_trips_shared_transport_receiver_cursor():
    from core.Lotucosm.runtime.world_bridge_shared_state_transport import (
        WorldBridgeSharedStateReceiver,
        build_worldbridge_shared_state_envelope,
    )

    viewport = FakeViewport()
    envelope = build_worldbridge_shared_state_envelope(
        envelope_id="checkpoint-transport-1",
        capture_epoch=1,
        sequence=0,
        input_events=[],
        pause_reset_epoch=0,
        clock_provenance={
            "sr": {"domain": "sr", "tick": 1, "delta": 0.05, "time": 0.05, "source": "test"},
            "ps": {"domain": "ps", "tick": 1, "delta": 0.05, "time": 0.05, "source": "test"},
        },
        bridge_identity_links=[],
    )
    receiver = WorldBridgeSharedStateReceiver()
    receiver.accept(envelope)
    viewport._worldbridge_shared_state_receiver = receiver
    viewport._worldbridge_shared_state_sequence = 1
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_input()

    viewport._worldbridge_shared_state_receiver = None
    viewport._worldbridge_shared_state_sequence = 0
    adapters.restore_input(state)

    restored = viewport._worldbridge_shared_state_receiver
    assert restored is not None
    assert restored.last_sequence == 0
    assert restored.last_capture_epoch == 1
    assert restored.accepted_count == 1
    assert viewport._worldbridge_shared_state_sequence == 1


def test_input_checkpoint_rejects_tampered_pending_event_before_state_change():
    viewport = FakeViewport()
    viewport._worldbridge_input_sequence.append("key_down", {"key": "W"})
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_input()
    state["canonical_sequence"]["pending"][0]["payload"]["key"] = "A"
    before_input = copy.deepcopy(viewport._input)
    before_sequence = viewport._worldbridge_input_sequence.snapshot()
    with pytest.raises(ValueError, match="pending events invalid"):
        adapters.restore_input(state)
    assert viewport._input == before_input
    assert viewport._worldbridge_input_sequence.snapshot() == before_sequence


def test_input_checkpoint_rejects_pending_sequence_beyond_cursor():
    viewport = FakeViewport()
    viewport._worldbridge_input_sequence.append("key_down", {"key": "W"})
    state = create_game_viewport_live_checkpoint_adapters(viewport).capture_input()
    state["canonical_sequence"]["next_sequence"] = 2
    state["canonical_sequence"]["pending"][0]["sequence"] = 9
    with pytest.raises(ValueError, match="pending events invalid"):
        create_game_viewport_live_checkpoint_adapters(viewport).restore_input(state)


def test_randomness_adapter_rejects_tampered_or_cross_epoch_bundle_before_mutation():
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    viewport = FakeViewport()
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    snapshot = adapters.capture_randomness()
    local_before = viewport._sr_runtime_rng.getstate()

    tampered = copy.deepcopy(snapshot)
    tampered["sr_runtime"]["internal_state"][0] ^= 1
    with pytest.raises(ValueError, match="checkpoint_digest_mismatch"):
        adapters.restore_randomness(tampered)

    wrong_epoch = copy.deepcopy(snapshot)
    wrong_epoch["runtime_epoch"] = "epoch-other"
    from core.Lotucosm.runtime.world_bridge_randomness_authority import (
        _rng_checkpoint_digest,
    )
    wrong_epoch["checkpoint_digest"] = _rng_checkpoint_digest(wrong_epoch)
    with pytest.raises(RuntimeError, match="checkpoint epoch mismatch"):
        adapters.restore_randomness(wrong_epoch)

    assert viewport._sr_runtime_rng.getstate() == local_before
    assert random.getstate() == python_before
    assert np.array_equal(np.random.get_state()[1], numpy_before[1])
    assert np.random.get_state()[2:] == numpy_before[2:]


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        ("lifecycle.runtime_epoch", "epoch-other", "runtime epoch mismatch"),
        ("input_state.canonical_sequence.pause_reset_epoch", 7, "input epoch mismatch"),
        ("input_state.shared_transport.runtime_epoch", "epoch-other", "runtime epoch mismatch"),
        ("randomness_state.runtime_epoch", "epoch-other", "randomness runtime epoch mismatch"),
    ],
)
def test_coordinator_rejects_cross_lane_epoch_mismatch_before_restore(
    path, value, message
):
    monkeypatch = pytest.MonkeyPatch()
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    viewport._worldbridge_input_sequence.append("key_down", {"key": "W"})
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    checkpoint = WorldBridgeLiveCheckpointCoordinator(adapters).capture(
        checkpoint_id="cross-lane", sequence=0
    )
    target = copy.deepcopy(checkpoint)
    section, field = path.split(".", 1)
    if "." in field:
        nested, leaf = field.rsplit(".", 1)
        target[section][nested][leaf] = value
    else:
        target[section][field] = value
    target["digest"] = checkpoint_digest(target)

    before = viewport._scene_runtime_time
    with pytest.raises(ValueError, match=message):
        WorldBridgeLiveCheckpointCoordinator(adapters).restore(target)
    assert viewport._scene_runtime_time == before
    monkeypatch.undo()


def test_randomness_adapter_failure_restores_local_and_global_pre_call_states(monkeypatch):
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    try:
        viewport = FakeViewport()
        adapters = create_game_viewport_live_checkpoint_adapters(viewport)
        snapshot = adapters.capture_randomness()
        viewport._sr_runtime_rng.random()
        random.random()
        np.random.random()

        local_at_call = viewport._sr_runtime_rng.getstate()
        python_at_call = random.getstate()
        numpy_at_call = np.random.get_state()
        original_set_state = np.random.set_state
        call_count = 0

        def fail_first_apply(state):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("injected NumPy restore failure")
            return original_set_state(state)

        monkeypatch.setattr(np.random, "set_state", fail_first_apply)
        with pytest.raises(RuntimeError, match="rolled back"):
            adapters.restore_randomness(snapshot)

        assert viewport._sr_runtime_rng.getstate() == local_at_call
        assert random.getstate() == python_at_call
        assert np.array_equal(np.random.get_state()[1], numpy_at_call[1])
        assert np.random.get_state()[2:] == numpy_at_call[2:]
    finally:
        random.setstate(python_before)
        np.random.set_state(numpy_before)


def test_ps_scripts_overlay_rejects_drift_instead_of_silently_dropping(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    pond = viewport._unified_pond
    organism = pond.organisms["ps:a"]

    class _LiveScript:
        pass

    # Capture with no PS scripts attached.
    state = adapters.capture_ps()
    assert state["worldbridge_organism_scripts"] == {
        "schema_version": 1,
        "organisms": {},
    }

    # A script attached after capture is executable owner state the portable
    # payload cannot recreate.  Restore must fail closed, not drop it silently.
    script = _LiveScript()
    script.randomness_rng = pond.randomness_rng
    script.randomness_owner_mode = "runtime"
    organism.scripts = [script]
    before_payload = copy.deepcopy(pond.payload)
    with pytest.raises(RuntimeError, match="script owner graph is not checkpointable"):
        adapters.restore_ps(state)
    assert organism.scripts == [script]
    assert pond.payload == before_payload

    # A live script graph identical to the captured graph stays admissible.
    captured = adapters.capture_ps()
    assert captured["worldbridge_organism_scripts"]["organisms"]["ps:a"]
    adapters.restore_ps(captured)

    # Malformed overlay is rejected without touching the live owner.
    bad = copy.deepcopy(captured)
    bad["worldbridge_organism_scripts"]["organisms"]["ps:a"][0]["owner_family"] = 7
    with pytest.raises(ValueError, match="owner_family must be str"):
        adapters.restore_ps(bad)
    assert pond.organisms["ps:a"].scripts == [script]


def test_ps_lifecycle_overlay_roundtrips_and_fails_closed(monkeypatch):
    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    pond = viewport._unified_pond
    organism = pond.organisms["ps:a"]
    organism.active = False
    organism.visible = False
    organism.developmental_stage = 3

    state = adapters.capture_ps()
    assert state["worldbridge_organism_lifecycle"] == {
        "schema_version": 1,
        "organisms": {
            "ps:a": {"active": False, "visible": False, "developmental_stage": 3}
        },
    }

    # Perturb the live owners, then restore: the overlay must bring them back.
    organism.active = True
    organism.visible = True
    organism.developmental_stage = 0
    adapters.restore_ps(state)
    restored = pond.organisms["ps:a"]
    assert (
        restored.active,
        restored.visible,
        restored.developmental_stage,
    ) == (False, False, 3)

    before = copy.deepcopy(pond.payload)

    wrong_schema = copy.deepcopy(state)
    wrong_schema["worldbridge_organism_lifecycle"]["schema_version"] = 99
    with pytest.raises(ValueError, match="schema_version"):
        adapters.restore_ps(wrong_schema)
    assert pond.payload == before

    bad_type = copy.deepcopy(state)
    bad_type["worldbridge_organism_lifecycle"]["organisms"]["ps:a"]["active"] = "yes"
    with pytest.raises(ValueError, match="flags must be bool"):
        adapters.restore_ps(bad_type)
    assert pond.payload == before

    unknown_owner = copy.deepcopy(state)
    unknown_owner["worldbridge_organism_lifecycle"]["organisms"]["ps:ghost"] = {
        "active": True,
        "visible": True,
        "developmental_stage": 1,
    }
    with pytest.raises(ValueError, match="does not match serialized organisms"):
        adapters.restore_ps(unknown_owner)
    assert pond.payload == before
def test_ps_hierarchy_overlay_roundtrips_child_order_and_fails_closed(monkeypatch):
    from core.Lotucosm.entity import EntityBase

    _patch_serializer(monkeypatch)
    viewport = FakeViewport()
    pond = viewport._unified_pond

    # Use real EntityBase owners so parent/children semantics are exercised.
    organism = EntityBase(entity_id="ps:a")
    organism.components = {}
    pond.organisms = {"ps:a": organism}
    first = EntityBase(entity_id="ps:a:first")
    second = EntityBase(entity_id="ps:a:second")
    organism.components = {"ps:a:first": first, "ps:a:second": second}
    # Child order deliberately differs from the serialized component order.
    organism.add_child(second)
    organism.add_child(first)
    pond.payload = {
        "name": "pond",
        "time": 3,
        "organisms": [
            {
                "id": "ps:a",
                "components": [{"id": "ps:a:first"}, {"id": "ps:a:second"}],
            }
        ],
    }

    adapters = create_game_viewport_live_checkpoint_adapters(viewport)
    state = adapters.capture_ps()
    captured = state["worldbridge_organism_hierarchy"]["organisms"]["ps:a"]
    assert captured == {
        "parent": None,
        "children": ["ps:a:second", "ps:a:first"],
    }

    # The portable payload rebuilds component children in component order, so
    # the overlay must replay the captured entity-child order on restore.
    organism.remove_child(first)
    organism.remove_child(second)
    organism.add_child(first)
    organism.add_child(second)
    adapters.restore_ps(state)
    restored = pond.organisms["ps:a"]
    assert [child.id for child in restored.children] == ["ps:a:second", "ps:a:first"]

    # An entity child the portable payload cannot recreate fails closed before
    # any live owner is touched.
    extra = EntityBase(entity_id="ps:a:extra")
    restored.add_child(extra)
    before_payload = copy.deepcopy(pond.payload)
    before_children = [child.id for child in restored.children]
    extra_state = adapters.capture_ps()
    with pytest.raises(ValueError, match="portable payload cannot restore"):
        adapters.restore_ps(extra_state)
    assert pond.payload == before_payload
    assert [child.id for child in restored.children] == before_children

    # Malformed overlays are rejected without touching the live owner.
    bad_schema = copy.deepcopy(state)
    bad_schema["worldbridge_organism_hierarchy"]["schema_version"] = 99
    with pytest.raises(ValueError, match="schema_version"):
        adapters.restore_ps(bad_schema)
    assert pond.payload == before_payload

    bad_parent = copy.deepcopy(state)
    bad_parent["worldbridge_organism_hierarchy"]["organisms"]["ps:a"]["parent"] = "ps:ghost"
    with pytest.raises(ValueError, match="not a serialized organism"):
        adapters.restore_ps(bad_parent)
    assert pond.payload == before_payload
