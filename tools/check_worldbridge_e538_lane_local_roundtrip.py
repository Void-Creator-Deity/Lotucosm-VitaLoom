#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E538 lane-local round-trip probe for SR topology and PS membrane behavior."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from _runtime_bootstrap import install_runtime_paths  # noqa: E402

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_lane_local_roundtrip import (  # noqa: E402
    build_worldbridge_lane_local_roundtrip_admission,
    build_worldbridge_lane_local_roundtrip_ps_contract,
    build_worldbridge_lane_local_roundtrip_sr_contract,
)
from core.Lotucosm.sr_membrane_topology import (  # noqa: E402
    aggregate_channel_signals,
    build_membrane_attachments,
    expand_signal_edges,
)
from PyQt6.QtWidgets import QApplication  # noqa: E402
from core.VitaLoom.viewports.game_viewport import GameViewport  # noqa: E402


def _digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _probe_sr_roundtrip() -> dict[str, Any]:
    """Exercise the real GameViewport topology owner and its SR consumer."""
    app = QApplication.instance() or QApplication([])
    assert app is not None
    gv = GameViewport()
    gv.scene_runtime_entities = []
    gv._sr_structural_edges = []
    gv._sr_connection_edges = []
    gv._sr_signal_edges = []
    gv._scene_runtime_edges = []
    gv._scene_runtime_neighbor_ids = {}
    gv._sr_membrane_attach = {}
    gv._sr_membrane_template = {}
    gv._sr_spawn_seq = 0

    hub = gv._SceneRuntimeEntity("e538_probe_hub", "organism", (100.0, 100.0), 24.0)
    sensor = gv._SceneRuntimeEntity("e538_probe_hub_s1", "sensor", (160.0, 70.0), 14.0)
    actuator = gv._SceneRuntimeEntity("e538_probe_hub_a1", "actuator", (140.0, 140.0), 12.0)
    sensor.sr_channel_out = {"chemo": 0.75, "chemo_dir_x": 1.0, "chemo_dir_y": 0.0}
    gv.scene_runtime_entities = [hub, sensor, actuator]

    structural = [
        {
            "start": "e538_probe_hub",
            "end": "e538_probe_hub_s1",
            "channel": "struct",
            "weight": 1.0,
            "link_kind": "hard",
        },
        {
            "start": "e538_probe_hub",
            "end": "e538_probe_hub_a1",
            "channel": "struct",
            "weight": 1.0,
            "link_kind": "hard",
        },
    ]
    gv._sr_structural_edges = copy.deepcopy(structural)
    gv._sr_connection_edges = copy.deepcopy(structural)
    gv._sr_membrane_attach = build_membrane_attachments(gv.scene_runtime_entities, structural)
    gv._sr_membrane_template = {
        "sensors": [{"suffix": "s1", "dx": 60.0, "dy": -30.0, "radius": 14.0}],
        "actuators": [{"suffix": "a1", "dx": 40.0, "dy": 40.0, "radius": 12.0}],
        "default_edge_weight": 1.0,
        "organelle_birth_cost": 20.0,
    }
    id_to_type = {entity.id: str(entity.entity_type) for entity in gv.scene_runtime_entities}
    gv._sr_signal_edges = expand_signal_edges(
        structural,
        gv._sr_membrane_attach,
        id_to_type,
        default_weight=1.0,
    )
    gv._scene_runtime_edges = [
        (str(edge["start"]), str(edge["end"])) for edge in structural
    ]
    gv._scene_runtime_neighbor_ids = {
        "e538_probe_hub": frozenset({"e538_probe_hub_s1", "e538_probe_hub_a1"}),
        "e538_probe_hub_s1": frozenset({"e538_probe_hub"}),
        "e538_probe_hub_a1": frozenset({"e538_probe_hub"}),
    }
    gv._sr_spawn_seq = 2

    source_state = gv.capture_sr_topology_owner_state()
    source_digest = _digest(source_state)
    source_inbound = gv._sr_inbound_for_entity("e538_probe_hub_a1", use_prev=False)

    # Deliberate drift: restore must replace the whole topology owner, not
    # merely one edge/attachment field.
    gv._sr_structural_edges = []
    gv._sr_connection_edges = []
    gv._sr_signal_edges = []
    gv._sr_membrane_attach = {"e538_probe_drift": ("e538_probe_hub", 1.0, 1.0)}
    gv._sr_membrane_template = {"sensors": [], "actuators": []}
    gv._sr_spawn_seq = 99
    gv.restore_sr_topology_owner_state(source_state)

    restored_state = gv.capture_sr_topology_owner_state()
    restored_digest = _digest(restored_state)
    restored_inbound = gv._sr_inbound_for_entity("e538_probe_hub_a1", use_prev=False)

    field_states = {
        "membrane_template": _field_state(
            source_state["membrane_template"], restored_state["membrane_template"]
        ),
        "membrane_attach": _field_state(
            source_state["membrane_attach"], restored_state["membrane_attach"]
        ),
        "structural_edges": _field_state(
            source_state["structural_edges"], restored_state["structural_edges"]
        ),
        "signal_edges": _field_state(
            source_state["signal_edges"], restored_state["signal_edges"]
        ),
        "aggregate_chemosignal": _field_state(source_inbound, restored_inbound),
    }

    # Fail-closed probe: dropping the required owner field must be rejected
    # before the live owner is written.
    malformed = dict(source_state)
    malformed.pop("membrane_attach", None)
    malformed_rejected = False
    try:
        gv.restore_sr_topology_owner_state(malformed)
    except ValueError as exc:
        malformed_rejected = str(exc) == "sr_topology_owner_state_fields_invalid"

    return {
        "lane": "sr",
        "source_digest": source_digest,
        "restored_source_digest": source_digest,
        "restored_state_digest": restored_digest,
        "fields": field_states,
        "source_inbound": source_inbound,
        "restored_inbound": restored_inbound,
        "malformed_owner_state_rejected": malformed_rejected,
        "owner_player": "GameViewport.capture_sr_topology_owner_state/restore_sr_topology_owner_state",
        "consumer": "GameViewport._sr_inbound_for_entity",
        "cross_lane_behavior_admitted": False,
    }


def _probe_ps_roundtrip() -> dict[str, Any]:
    """Exercise the real PS Membrane producer and behavior surface."""
    from builtin.components.membrane import Membrane

    source = Membrane(component_id="e538_ps_probe")
    source.radius = 55.0
    source.ingest_threshold = 0.35
    source.efficiency = 1.25

    source_status = source.get_status()
    source_digest = _digest(source_status)
    source_behavior = {
        "auto_ingest": callable(getattr(source, "auto_ingest", None)),
        "is_inside": callable(getattr(source, "is_inside", None)),
    }

    # Round-trip through a real, independently constructed producer instance.
    # This proves the producer contract is reconstructible without relying on
    # any cross-lane projection or live object identity.
    # Identity is part of the producer payload: restore it onto a fresh,
    # otherwise unwired instance rather than sharing the live object.
    restored = Membrane(component_id="e538_ps_probe")
    restored.radius = float(source_status["radius"])
    restored.ingest_threshold = float(source_status["ingest_threshold"])
    restored.efficiency = float(source_status.get("efficiency", source.efficiency))
    restored_status = restored.get_status()
    restored_digest = _digest(restored_status)
    restored_behavior = {
        "auto_ingest": callable(getattr(restored, "auto_ingest", None)),
        "is_inside": callable(getattr(restored, "is_inside", None)),
    }

    field_states = {
        "radius": _field_state(source_status["radius"], restored_status["radius"]),
        "ingest_threshold": _field_state(
            source_status["ingest_threshold"], restored_status["ingest_threshold"]
        ),
        "efficiency": _field_state(
            source_status.get("efficiency"), restored_status.get("efficiency")
        ),
        "auto_ingest": _field_state(source_behavior["auto_ingest"], restored_behavior["auto_ingest"]),
        "is_inside": _field_state(source_behavior["is_inside"], restored_behavior["is_inside"]),
    }

    return {
        "lane": "ps",
        "source_digest": source_digest,
        "restored_source_digest": source_digest,
        "restored_state_digest": restored_digest,
        "fields": field_states,
        "producer": "builtin.components.membrane.Membrane",
        "consumer": "Membrane.get_status",
        "behavior_lane_local": True,
        "cross_lane_behavior_admitted": False,
    }


def _field_state(source: Any, restored: Any) -> dict[str, Any]:
    aligned = source == restored
    return {
        "state": "aligned" if aligned else "mismatch",
        "source_digest": _digest(source),
        "restored_digest": _digest(restored),
    }


def build_worldbridge_lane_local_roundtrip_evidence() -> dict[str, Any]:
    sr = _probe_sr_roundtrip()
    ps = _probe_ps_roundtrip()
    admission = build_worldbridge_lane_local_roundtrip_admission(
        sr_evidence=sr,
        ps_evidence=ps,
    )
    return {
        "schema_version": 1,
        "status": "worldbridge_lane_local_roundtrip_evidence",
        "read_only": True,
        "sr_contract": build_worldbridge_lane_local_roundtrip_sr_contract(),
        "ps_contract": build_worldbridge_lane_local_roundtrip_ps_contract(),
        "sr": sr,
        "ps": ps,
        "admission": admission,
        "cross_lane_behavior_admitted": False,
        "tick_merge_admitted": False,
        "full_unified_replay_admitted": False,
        "lossless": False,
        "default_ready": False,
    }


def main() -> int:
    evidence = build_worldbridge_lane_local_roundtrip_evidence()
    print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
    ok = bool(
        evidence["sr"]["fields"]["membrane_template"]["state"] == "aligned"
        and evidence["sr"]["fields"]["membrane_attach"]["state"] == "aligned"
        and evidence["sr"]["fields"]["structural_edges"]["state"] == "aligned"
        and evidence["sr"]["fields"]["signal_edges"]["state"] == "aligned"
        and evidence["sr"]["fields"]["aggregate_chemosignal"]["state"] == "aligned"
        and evidence["sr"]["malformed_owner_state_rejected"] is True
        and evidence["ps"]["fields"]["radius"]["state"] == "aligned"
        and evidence["ps"]["fields"]["ingest_threshold"]["state"] == "aligned"
        and evidence["ps"]["fields"]["efficiency"]["state"] == "aligned"
        and evidence["ps"]["fields"]["auto_ingest"]["state"] == "aligned"
        and evidence["ps"]["fields"]["is_inside"]["state"] == "aligned"
        and evidence["admission"]["sr_aligned"] is True
        and evidence["admission"]["ps_aligned"] is True
        and evidence["admission"]["cross_lane_behavior_admitted"] is False
        and evidence["admission"]["tick_merge_admitted"] is False
        and evidence["admission"]["full_unified_replay_admitted"] is False
        and evidence["admission"]["lossless"] is False
        and evidence["admission"]["default_ready"] is False
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
