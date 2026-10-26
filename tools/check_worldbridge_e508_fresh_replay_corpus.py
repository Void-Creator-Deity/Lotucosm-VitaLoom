from __future__ import annotations

import copy
import hashlib
import json
import os
import random
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
import numpy as np

from tools.check_worldbridge_e505_fresh_host_reconstruction import _new_viewport
from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    restore_worldbridge_deterministic_randomness_context,
)
from core.Lotucosm.runtime.world_bridge_e508_fresh_replay_corpus import (
    build_worldbridge_e508_fresh_replay_corpus,
    project_worldbridge_e508_portable_state,
    validate_worldbridge_e508_fresh_replay_corpus,
)
from core.Lotucosm.runtime.world_bridge_e509_replay_persistence import (
    build_worldbridge_e509_replay_persistence_envelope,
    decode_worldbridge_e509_replay_persistence_envelope,
    encode_worldbridge_e509_replay_persistence_envelope,
)
from core.Lotucosm.runtime.world_bridge_e497_shared_contract_witness import (
    build_worldbridge_e497_shared_contract_witness,
    validate_worldbridge_e497_shared_contract_witness,
)
from core.Lotucosm.runtime.world_bridge_e498_rng_input_witness import (
    build_worldbridge_e498_rng_input_witness,
    validate_worldbridge_e498_rng_input_witness,
)
from core.Lotucosm.runtime.world_bridge_e499_fresh_session_parity import (
    build_worldbridge_e499_fresh_session_parity,
    validate_worldbridge_e499_fresh_session_parity,
)
from core.Lotucosm.runtime.world_bridge_e500_shared_clock_contract import (
    build_worldbridge_e500_shared_clock_contract,
    validate_worldbridge_e500_shared_clock_contract,
)
from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
)
from core.Lotucosm.runtime.world_bridge_e512_provenance_receipt import (
    build_worldbridge_e512_provenance_receipt,
    decode_worldbridge_e512_provenance_receipt,
    encode_worldbridge_e512_provenance_receipt,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
    present_worldbridge_quarantine_lifecycle,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export import (
    export_worldbridge_quarantine_operator_presentation,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export_audit import (
    audit_worldbridge_quarantine_operator_presentation_export,
)
from core.Lotucosm.runtime.world_bridge_fresh_restore_parity import (
    capture_canonical_ps_state,
)
from core.Lotucosm.runtime.world_bridge_input_sequence import WorldBridgeInputSequence


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


_PORTABLE_PARITY_FIELDS = (
    "topology_owner_state",
    "sr_state",
    "ps_state",
    "bridge_identity_links",
    "input_state",
    "randomness_state",
    "lifecycle",
)


def _success_diagnostic(checkpoint: dict[str, object]) -> dict[str, object]:
    diagnostic: dict[str, object] = {
        "schema_version": 1,
        "code": "restore_succeeded",
        "errors": [],
        "checkpoint_id": checkpoint["checkpoint_id"],
        "checkpoint_digest": checkpoint["digest"],
        "diagnostic_digest": "",
    }
    diagnostic["diagnostic_digest"] = _digest({key: value for key, value in diagnostic.items() if key != "diagnostic_digest"})
    return diagnostic


def _diff_paths(left: object, right: object, prefix: str = "") -> list[str]:
    if left == right:
        return []
    if isinstance(left, dict) and isinstance(right, dict):
        paths: list[str] = []
        for key in sorted(set(left) | set(right)):
            paths.extend(_diff_paths(left.get(key), right.get(key), f"{prefix}.{key}" if prefix else str(key)))
        return paths or [prefix]
    if isinstance(left, list) and isinstance(right, list):
        paths: list[str] = []
        for index in range(max(len(left), len(right))):
            paths.extend(_diff_paths(left[index] if index < len(left) else None, right[index] if index < len(right) else None, f"{prefix}[{index}]"))
        return paths or [prefix]
    return [prefix]


def _restore_portable_state(viewport, checkpoint: dict[str, object]) -> None:
    sr = checkpoint["sr_state"]["runtime_restore_envelope"]
    viewport.restore_sr_runtime_snapshot_slice(copy.deepcopy(sr["snapshots"]), scene_time=sr["scene_time"])
    viewport._unified_pond.restore_serialized_state_in_place(copy.deepcopy(checkpoint["ps_state"]))
    restore_worldbridge_deterministic_randomness_context(
        viewport._worldbridge_opt_in_deterministic_randomness_context,
        copy.deepcopy(checkpoint["randomness_state"]["deterministic_context"]),
    )
    input_state = copy.deepcopy(checkpoint["input_state"])
    canonical_sequence = input_state.pop("canonical_sequence", None)
    ps_handoff_input_events = input_state.pop("ps_handoff_input_events", None)
    input_state.pop("shared_transport", None)
    if canonical_sequence is None:
        raise AssertionError("E508 canonical input sequence missing")
    WorldBridgeInputSequence.validate_snapshot(canonical_sequence)
    viewport.restore_sr_input_state(input_state)
    viewport._worldbridge_input_sequence.restore_snapshot(canonical_sequence)
    if ps_handoff_input_events is not None:
        apply_inputs = getattr(viewport._unified_pond, "apply_worldbridge_input_events", None)
        if not callable(apply_inputs):
            raise AssertionError("fresh Pond input handoff owner missing")
        apply_inputs(ps_handoff_input_events)
    topology = copy.deepcopy(checkpoint.get("topology_owner_state") or {})
    if topology:
        restore_topology = getattr(viewport, "restore_sr_topology_owner_state", None)
        if not callable(restore_topology):
            raise AssertionError("E508 fresh host topology owner restore contract missing")
        restore_topology(topology)


def verify() -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    scene = project / "scenes" / "challenge_scene.pond"
    source = _new_viewport(project, scene, "e508-root-seed")
    fresh = None
    try:
        source._update_scene_runtime_entities(0.05)
        checkpoint = source.capture_worldbridge_live_checkpoint("e508-checkpoint")
        initial_shared_envelope = source._worldbridge_last_shared_state_envelope
        if not isinstance(initial_shared_envelope, dict):
            raise AssertionError("real GameViewport checkpoint did not publish a shared envelope")
        expected_topology_fields = set(
            getattr(source, "SR_TOPOLOGY_OWNER_FIELDS", ())
        )
        topology_owner = checkpoint.get("topology_owner_state")
        if (
            not expected_topology_fields
            or not isinstance(topology_owner, dict)
            or set(topology_owner) != expected_topology_fields
        ):
            raise AssertionError("E508 source topology owner state is incomplete")
        source_snapshot = {
            "randomness": copy.deepcopy(checkpoint["randomness_state"]["deterministic_context"]),
            "input": copy.deepcopy(checkpoint["input_state"]),
            "sr": copy.deepcopy(checkpoint["sr_state"]["runtime_restore_envelope"]),
            "ps": copy.deepcopy(checkpoint["ps_state"]),
            "topology": copy.deepcopy(topology_owner),
        }
        baseline: list[dict[str, object]] = []
        shared_envelopes: list[dict[str, object]] = [copy.deepcopy(initial_shared_envelope)]
        for tick in range(1, 4):
            source._update_scene_runtime_entities(0.05)
            state = source.capture_worldbridge_live_checkpoint(f"e508-baseline-{tick}")
            baseline.append({"tick": tick, "checkpoint": state})
            envelope = source._worldbridge_last_shared_state_envelope
            if not isinstance(envelope, dict):
                raise AssertionError("real GameViewport tick did not publish a shared envelope")
            shared_envelopes.append(copy.deepcopy(envelope))
        source._worldbridge_input_sequence.append("key_down", {"key": "W"})
        source._worldbridge_opt_in_deterministic_randomness_context.get_stream("sr.runtime").random()
        source._update_scene_runtime_entities(0.05)
        envelope = source._worldbridge_last_shared_state_envelope
        if not isinstance(envelope, dict):
            raise AssertionError("real GameViewport input/RNG tick did not publish a shared envelope")
        shared_envelopes.append(copy.deepcopy(envelope))

        fresh = _new_viewport(project, scene, "e508-root-seed")
        fresh._update_scene_runtime_entities(0.05)
        restore_checkpoint = {
            "sr_state": {"runtime_restore_envelope": source_snapshot["sr"]},
            "ps_state": source_snapshot["ps"],
            "randomness_state": {"deterministic_context": source_snapshot["randomness"]},
            "input_state": source_snapshot["input"],
            "topology_owner_state": source_snapshot["topology"],
        }
        # Corrupt the fresh host topology owner before apply so the parity
        # below proves the owner state flowed instead of matching defaults.
        fresh._sr_membrane_attach = {"sr:e508-sentinel": ("sr:a", 123.0, 0.0)}
        fresh._sr_membrane_template = {"sentinels": [{"suffix": "sentinel"}]}
        fresh._sr_spawn_seq = 9999
        _restore_portable_state(fresh, restore_checkpoint)
        fresh_epoch_checkpoint = fresh.capture_worldbridge_live_checkpoint("e508-fresh-epoch")
        source_epoch = checkpoint["input_state"]["shared_transport"]["runtime_epoch"]
        fresh_epoch = fresh_epoch_checkpoint["input_state"]["shared_transport"]["runtime_epoch"]
        restored: list[dict[str, object]] = []
        for tick in range(1, 4):
            fresh._update_scene_runtime_entities(0.05)
            state = fresh.capture_worldbridge_live_checkpoint(f"e508-restored-{tick}")
            restored.append({"tick": tick, "checkpoint": state})

        records: list[dict[str, object]] = []
        for left, right in zip(baseline, restored, strict=True):
            left_state = project_worldbridge_e508_portable_state(left["checkpoint"])
            right_state = project_worldbridge_e508_portable_state(right["checkpoint"])
            fields = {
                field: _digest(left_state[field]) == _digest(right_state[field])
                for field in _PORTABLE_PARITY_FIELDS
            }
            records.append({
                "tick": left["tick"],
                "parity": all(fields.values()),
                "sr_state_digest": _digest(left_state["sr_state"]),
                "ps_state_digest": _digest(left_state["ps_state"]),
                "input_state_digest": _digest(left_state["input_state"]),
                "randomness_state_digest": _digest(left_state["randomness_state"]),
                "bridge_identity_digest": _digest(left_state["bridge_identity_links"]),
                "baseline_digest": _digest(left_state),
                "restored_digest": _digest(right_state),
                "field_parity": fields,
                "field_diff_paths": {field: _diff_paths(left_state[field], right_state[field])[:20] for field in fields if not fields[field]},
            })
        corpus = build_worldbridge_e508_fresh_replay_corpus(
            checkpoint_digest=checkpoint["digest"],
            source_epoch=source_epoch,
            fresh_epoch=fresh_epoch,
            tick_records=records,
        )
        validation = validate_worldbridge_e508_fresh_replay_corpus(corpus)
        if validation != {"valid": True, "errors": []}:
            raise AssertionError(f"E508 corpus invalid: {validation}; records={records}")
        project_lock_path = project / "project.lock.json"
        project_lock = json.loads(project_lock_path.read_text(encoding="utf-8"))
        envelope = build_worldbridge_e509_replay_persistence_envelope(
            project_path=str(project),
            project_lock=project_lock,
            scene_path=str(scene),
            corpus=corpus,
            restore_diagnostic=_success_diagnostic(checkpoint),
        )
        encoded_envelope = encode_worldbridge_e509_replay_persistence_envelope(envelope)
        decoded_envelope = decode_worldbridge_e509_replay_persistence_envelope(
            encoded_envelope,
            project_path=str(project),
            project_lock=project_lock,
            scene_path=str(scene),
            checkpoint_digest=checkpoint["digest"],
        )
        tampered_envelope = copy.deepcopy(envelope)
        tampered_envelope["corpus_digest"] = "0" * 64
        persistence_tamper_rejected = False
        try:
            encode_worldbridge_e509_replay_persistence_envelope(tampered_envelope)
        except ValueError:
            persistence_tamper_rejected = True
        if decoded_envelope != envelope or not persistence_tamper_rejected:
            raise AssertionError("E509 persistence round-trip or tamper rejection failed")
        e497_witness = build_worldbridge_e497_shared_contract_witness(shared_envelopes)
        e498_witness = build_worldbridge_e498_rng_input_witness(shared_envelopes)
        e500_contract = build_worldbridge_e500_shared_clock_contract(shared_envelopes)
        if validate_worldbridge_e497_shared_contract_witness(e497_witness) != {"valid": True, "errors": []}:
            raise AssertionError("real E497 shared contract witness invalid")
        e498_validation = validate_worldbridge_e498_rng_input_witness(e498_witness)
        if e498_validation != {"valid": True, "errors": []}:
            raise AssertionError(f"real E498 RNG/input witness invalid: {e498_validation}; witness={e498_witness}")
        if validate_worldbridge_e500_shared_clock_contract(e500_contract) != {"valid": True, "errors": []}:
            raise AssertionError("real E500 shared clock contract invalid")
        source_context = source._worldbridge_opt_in_deterministic_randomness_context
        fresh_context = create_worldbridge_deterministic_randomness_context(source_context.context_id, "e508-root-seed")
        register_worldbridge_deterministic_random_stream(
            fresh_context, "sr.runtime", "python_random", stream=random.Random(0)
        )
        register_worldbridge_deterministic_random_stream(
            fresh_context, "ps.pond", "numpy_pcg64_generator", stream=np.random.Generator(np.random.PCG64(0))
        )
        e499_witness = build_worldbridge_e499_fresh_session_parity(
            shared_envelopes,
            source_context=source_context,
            fresh_context=fresh_context,
        )
        if validate_worldbridge_e499_fresh_session_parity(e499_witness) != {"valid": True, "errors": []}:
            raise AssertionError("real E499 fresh-session parity invalid")
        replay_diagnostic = _success_diagnostic(checkpoint)
        replay_diagnostic["code"] = "worldbridge_replay_persistence_rejected"
        replay_diagnostic["errors"] = ["replay_admission_remains_quarantined"]
        replay_diagnostic["diagnostic_digest"] = _digest({key: value for key, value in replay_diagnostic.items() if key != "diagnostic_digest"})
        source._worldbridge_restore_diagnostic = copy.deepcopy(replay_diagnostic)
        presentation = source.query_worldbridge_quarantine_operator_presentation()
        export_record = export_worldbridge_quarantine_operator_presentation(presentation)
        audit_record = audit_worldbridge_quarantine_operator_presentation_export(export_record)
        receipt = build_worldbridge_e512_provenance_receipt(
            persistence_envelope=envelope,
            presentation=presentation,
            export_record=export_record,
            audit_record=audit_record,
        )
        encoded_receipt = encode_worldbridge_e512_provenance_receipt(receipt)
        decoded_receipt = decode_worldbridge_e512_provenance_receipt(encoded_receipt)
        if decoded_receipt != receipt:
            raise AssertionError("E512 provenance receipt round-trip failed")
        source._worldbridge_e512_provenance_receipt = copy.deepcopy(decoded_receipt)
        provider_receipt = source.query_worldbridge_e512_provenance_receipt()
        provider_receipt["receipt_digest"] = "0" * 64
        if source.query_worldbridge_e512_provenance_receipt()["receipt_digest"] == "0" * 64:
            raise AssertionError("E514 receipt provider is not copy-isolated")
        tampered_receipt = copy.deepcopy(receipt)
        tampered_receipt["export_digest"] = "0" * 64
        source._worldbridge_e512_provenance_receipt = tampered_receipt
        rejected = False
        try:
            source.query_worldbridge_e512_provenance_receipt()
        except ValueError:
            rejected = True
        source._worldbridge_e512_provenance_receipt = copy.deepcopy(receipt)
        if not rejected:
            raise AssertionError("E514 provider accepted tampered receipt")
        return {
            "status": "worldbridge_e508_fresh_replay_corpus",
            "contract_valid": True,
            "real_game_viewport": True,
            "tick_count": corpus["tick_count"],
            "all_tick_parity": corpus["all_tick_parity"],
            "cross_session_replay_parity": corpus["cross_session_replay_parity"],
            "distinct_runtime_epochs": corpus["distinct_runtime_epochs"],
            "tamper_rejection": True,
            "persistence_round_trip": True,
            "persistence_tamper_rejection": persistence_tamper_rejected,
            "shared_envelope_count": len(shared_envelopes),
            "e497_shared_contract_valid": True,
            "e498_rng_input_witness_valid": True,
            "e499_fresh_session_parity": e499_witness["fresh_session_parity"],
            "e500_clock_conversion_admitted": e500_contract["conversion_admitted"],
            "provenance_receipt_round_trip": True,
            "provenance_receipt_provider_available": True,
            "provenance_receipt_tamper_rejection": rejected,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
            "corpus": corpus,
        }
    finally:
        for viewport in (source, fresh):
            if viewport is None:
                continue
            viewport.deleteLater()
            QCoreApplication.sendPostedEvents(viewport, QEvent.Type.DeferredDelete)
        app.processEvents()
        if not sip.isdeleted(source) or (fresh is not None and not sip.isdeleted(fresh)):
            raise AssertionError("E508 fresh replay viewport cleanup incomplete")


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] else 1)
