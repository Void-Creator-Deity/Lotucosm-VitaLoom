from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools._runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

from PyQt6 import sip
from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtWidgets import QApplication

from tools.check_worldbridge_e505_fresh_host_reconstruction import _new_viewport
from tools.check_worldbridge_e508_fresh_replay_corpus import _restore_portable_state

from core.Lotucosm.runtime.world_bridge_e533_capture_binding import (
    build_worldbridge_e533_capture_binding,
    build_worldbridge_e533_host_capture,
    build_worldbridge_e533_pair_id,
    build_worldbridge_e533_project_binding,
    build_worldbridge_e533_record_from_live_capture,
    decode_worldbridge_e533_capture_binding,
    encode_worldbridge_e533_capture_binding,
    validate_worldbridge_e533_capture_binding,
)


def _project_binding(project: Path, scene: Path) -> dict[str, str]:
    project_lock = json.loads((project / "project.lock.json").read_text(encoding="utf-8"))
    scene_digest = hashlib.sha256(scene.read_bytes()).hexdigest()
    return build_worldbridge_e533_project_binding(
        project_path=str(project.resolve()),
        project_lock=project_lock,
        scene_path=str(scene.resolve()),
        scene_digest=scene_digest,
    )


def _digest(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _reseal_capture(artifact: dict[str, object], role: str) -> None:
    capture = artifact[f"{role}_capture"]
    for record in capture["records"]:
        record["record_digest"] = ""
        record["record_digest"] = _digest(record)
    capture["capture_digest"] = ""
    capture["capture_digest"] = _digest(capture)
    artifact[f"{role}_capture_digest"] = capture["capture_digest"]
    artifact["artifact_digest"] = ""
    artifact["artifact_digest"] = _digest(artifact)


def _spawn_request(generation: int) -> dict[str, object]:
    hub_id = f"e533_dynamic_hub_{generation}"
    links = [
        {
            "sr_component_id": f"e533-g{generation}-sensor",
            "ps_component_id": f"bridge_{hub_id}_sensor",
            "sr_organism_id": hub_id,
            "ps_organism_id": f"bridge_{hub_id}",
        },
        {
            "sr_component_id": f"e533-g{generation}-actuator",
            "ps_component_id": f"bridge_{hub_id}_actuator",
            "sr_organism_id": hub_id,
            "ps_organism_id": f"bridge_{hub_id}",
        },
    ]
    return {
        "type": "organism_with_membrane",
        "hub_id": hub_id,
        "position": (180.0 + generation * 20.0, 140.0 + generation * 10.0),
        "radius": 20.0,
        "energy": 85.0,
        "scripts": [],
        "template": {
            "sensors": [{"suffix": "sensor", "dx": -8.0}],
            "actuators": [{"suffix": "actuator", "dx": 8.0}],
        },
        "component_identity_links": links,
    }


def _run_topology_ticks(
    viewport,
    project: Path,
    *,
    project_binding: dict[str, str],
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    runtime_epoch = str(viewport._sr_runtime_epoch)
    for index in range(4):
        if index < 3:
            generation = index + 1
            hub_id = f"e533_dynamic_hub_{generation}"
            if viewport._process_sr_spawn_requests(
                [_spawn_request(generation)], str(project)
            ) != [hub_id]:
                raise AssertionError(f"E533 source/fresh spawn {generation} failed")
            kind = "spawn"
        else:
            viewport._process_sr_removal_requests(["e533_dynamic_hub_2"])
            kind = "despawn"

        viewport._worldbridge_input_sequence.append(
            "key_down",
            {"key": f"F{index + 1}", "topology_event": kind, "event_index": index},
        )
        viewport._worldbridge_opt_in_deterministic_randomness_context.get_stream(
            "sr.runtime"
        ).random()
        viewport._update_scene_runtime_entities(0.05)
        checkpoint = viewport.capture_worldbridge_live_checkpoint(
            f"e533-topology-tick-{index + 1}"
        )
        envelope = copy.deepcopy(viewport._worldbridge_last_shared_state_envelope)
        if not isinstance(envelope, dict):
            raise AssertionError("E533 real GameViewport tick envelope is missing")
        sr_state = checkpoint["sr_state"]
        topology_receipt = copy.deepcopy(sr_state["topology_receipt"])
        event = {
            "event_index": index,
            "tick": index + 1,
            "kind": kind,
            "runtime_epoch": runtime_epoch,
            "structure_fingerprint": sr_state["structure_fingerprint"]["fingerprint"],
            "receipt_digest": topology_receipt["receipt_digest"],
            "node_ids": sorted(str(entity.id) for entity in viewport.scene_runtime_entities),
            "topology_receipt": topology_receipt,
        }
        records.append(
            build_worldbridge_e533_record_from_live_capture(
                event=event,
                checkpoint=checkpoint,
                envelope=envelope,
                project_binding=project_binding,
            )
        )
    return records


def verify() -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    scene = project / "scenes" / "challenge_scene.pond"
    project_binding = _project_binding(project, scene)
    source = _new_viewport(project, scene, "e533-root-seed")
    fresh = None
    try:
        source._update_scene_runtime_entities(0.05)
        base_checkpoint = source.capture_worldbridge_live_checkpoint("e533-source-base")
        source_epoch = str(source._sr_runtime_epoch)
        source_records = _run_topology_ticks(
            source, project, project_binding=project_binding
        )

        # The fresh host is independently initialized and receives only the
        # portable checkpoint projection; its own epoch/transport identities
        # remain local, while the same topology/input/RNG sequence is replayed.
        fresh = _new_viewport(project, scene, "e533-root-seed")
        # Initialize the fresh Pond/runtime before applying the portable base
        # checkpoint; this materializes the same scene-owned entities.
        fresh._update_scene_runtime_entities(0.05)
        _restore_portable_state(
            fresh,
            {
                "sr_state": {
                    "runtime_restore_envelope": copy.deepcopy(
                        base_checkpoint["sr_state"]["runtime_restore_envelope"]
                    )
                },
                "ps_state": copy.deepcopy(base_checkpoint["ps_state"]),
                "randomness_state": {
                    "deterministic_context": copy.deepcopy(
                        base_checkpoint["randomness_state"]["deterministic_context"]
                    )
                },
                "input_state": copy.deepcopy(base_checkpoint["input_state"]),
            },
        )
        fresh_epoch = str(fresh._sr_runtime_epoch)
        pair_id = build_worldbridge_e533_pair_id(
            project_binding=project_binding,
            source_runtime_epoch=source_epoch,
            fresh_runtime_epoch=fresh_epoch,
        )
        fresh_records = _run_topology_ticks(
            fresh, project, project_binding=project_binding
        )
        source_capture = build_worldbridge_e533_host_capture(
            pair_id=pair_id,
            role="source",
            runtime_epoch=source_epoch,
            project_binding=project_binding,
            records=source_records,
        )
        fresh_capture = build_worldbridge_e533_host_capture(
            pair_id=pair_id,
            role="fresh",
            runtime_epoch=fresh_epoch,
            project_binding=project_binding,
            records=fresh_records,
        )
        artifact = build_worldbridge_e533_capture_binding(
            pair_id=pair_id,
            project_binding=project_binding,
            source_capture=source_capture,
            fresh_capture=fresh_capture,
        )
        validation = validate_worldbridge_e533_capture_binding(artifact)
        if validation != {"valid": True, "errors": []}:
            raise AssertionError(f"E533 capture binding invalid: {validation}")
        encoded = encode_worldbridge_e533_capture_binding(artifact)
        decoded = decode_worldbridge_e533_capture_binding(encoded)
        if decoded != artifact:
            raise AssertionError("E533 canonical encode/decode changed the capture artifact")

        tampered = copy.deepcopy(artifact)
        tampered["source_capture"]["records"][0]["event"]["tick"] = 4
        _reseal_capture(tampered, "source")
        tick_validation = validate_worldbridge_e533_capture_binding(tampered)
        tamper_rejected = (
            tick_validation["valid"] is False
            and "record_0_topology_tick_link_invalid" in tick_validation["errors"]
        )
        if not tamper_rejected:
            raise AssertionError("E533 accepted a topology-to-tick binding tamper")
        mismatched_project = copy.deepcopy(artifact)
        mismatched_project["fresh_capture"]["project_binding"]["scene_path"] += ".other"
        _reseal_capture(mismatched_project, "fresh")
        project_validation = validate_worldbridge_e533_capture_binding(
            mismatched_project
        )
        project_mismatch_rejected = (
            project_validation["valid"] is False
            and "fresh_project_binding_mismatch"
            in project_validation["errors"]
        )
        if not project_mismatch_rejected:
            raise AssertionError("E533 accepted a source/fresh project/scene mismatch")

        return {
            "status": "worldbridge_e533_capture_binding",
            "contract_valid": True,
            "real_game_viewport_pair": True,
            "host_capture_pair_binding_proven": artifact[
                "host_capture_pair_binding_proven"
            ],
            "topology_tick_binding_proven": artifact["topology_tick_binding_proven"],
            "checkpoint_scene_binding_proven": artifact[
                "checkpoint_scene_binding_proven"
            ],
            "event_count": artifact["event_count"],
            "distinct_runtime_epochs": source_epoch != fresh_epoch,
            "project_lock_and_scene_digest_bound": True,
            "canonical_input_and_rng_bound_per_tick": True,
            "canonical_round_trip": True,
            "tick_tamper_rejected": tamper_rejected,
            "project_mismatch_rejected": project_mismatch_rejected,
            "replay_admitted": artifact["replay_admitted"],
            "lossless": artifact["lossless"],
            "default_ready": artifact["default_ready"],
            "artifact": artifact,
        }
    finally:
        for viewport in (source, fresh):
            if viewport is not None and not sip.isdeleted(viewport):
                viewport.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
        if any(
            viewport is not None and not sip.isdeleted(viewport)
            for viewport in (source, fresh)
        ):
            raise AssertionError("E533 GameViewport cleanup incomplete")


if __name__ == "__main__":
    result = verify()
    summary = {key: value for key, value in result.items() if key != "artifact"}
    summary["artifact_digest"] = result["artifact"]["artifact_digest"]
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] else 1)
