from __future__ import annotations

import copy

import pytest

from core.Lotucosm.runtime.world_bridge_dynamic_topology_corpus import (
    build_worldbridge_dynamic_topology_corpus,
)
from core.Lotucosm.runtime.world_bridge_dynamic_topology_fresh_provenance import (
    build_worldbridge_dynamic_topology_fresh_provenance,
    validate_worldbridge_dynamic_topology_fresh_provenance,
)
from core.Lotucosm.runtime.world_bridge_dynamic_topology_receipt import (
    build_worldbridge_dynamic_topology_receipt,
)


def _corpus():
    receipt = build_worldbridge_dynamic_topology_receipt(
        runtime_epoch="source-epoch",
        generation=1,
        structure_fingerprint={"fingerprint": "a" * 64},
    )
    events = [{
        "event_index": 0,
        "kind": "spawn",
        "runtime_epoch": "source-epoch",
        "structure_fingerprint": "a" * 64,
        "receipt_digest": receipt["receipt_digest"],
        "node_ids": ["hub", "sensor"],
    }]
    return build_worldbridge_dynamic_topology_corpus(
        runtime_epoch="source-epoch",
        scene_path="scene.pond",
        events=events,
        duplicate_rejected=True,
        missing_node_rejected=True,
        epoch_drift_rejected=True,
    )


def _fresh_events():
    structure = {"fingerprint": "a" * 64}
    receipt = build_worldbridge_dynamic_topology_receipt(
        runtime_epoch="fresh-epoch",
        generation=1,
        structure_fingerprint=structure,
    )
    return [{
        "event_index": 0,
        "kind": "spawn",
        "runtime_epoch": "fresh-epoch",
        "structure_fingerprint": "a" * 64,
        "receipt_digest": receipt["receipt_digest"],
        "node_ids": ["hub", "sensor"],
        "topology_receipt": receipt,
    }]


def _build():
    corpus = _corpus()
    source_receipt = build_worldbridge_dynamic_topology_receipt(
        runtime_epoch="source-epoch",
        generation=1,
        structure_fingerprint={"fingerprint": "a" * 64},
    )
    return build_worldbridge_dynamic_topology_fresh_provenance(
        source_corpus=corpus,
        source_receipts=[source_receipt],
        fresh_runtime_epoch="fresh-epoch",
        fresh_events=_fresh_events(),
        old_receipt_rejected=True,
        old_receipt_restore_non_mutating=True,
        old_receipt_restore_error="dynamic topology receipt rejected: receipt_runtime_epoch_mismatch",
    )


def test_fresh_topology_provenance_binds_epochs_receipts_and_parity():
    artifact = _build()
    assert validate_worldbridge_dynamic_topology_fresh_provenance(artifact) == {
        "valid": True,
        "errors": [],
    }
    assert artifact["replay_admitted"] is False
    assert artifact["source_runtime_epoch"] != artifact["fresh_runtime_epoch"]


def test_fresh_provenance_rejects_source_epoch_reuse():
    with pytest.raises(ValueError, match="must differ"):
        build_worldbridge_dynamic_topology_fresh_provenance(
            source_corpus=_corpus(),
            source_receipts=[build_worldbridge_dynamic_topology_receipt(runtime_epoch="source-epoch", generation=1, structure_fingerprint={"fingerprint": "a" * 64})],
            fresh_runtime_epoch="source-epoch",
            fresh_events=_fresh_events(),
            old_receipt_rejected=True,
            old_receipt_restore_non_mutating=True,
            old_receipt_restore_error="dynamic topology receipt rejected: receipt_runtime_epoch_mismatch",
        )


def test_fresh_provenance_rejects_unproven_old_receipt_rejection():
    with pytest.raises(ValueError, match="rejection is required"):
        build_worldbridge_dynamic_topology_fresh_provenance(
            source_corpus=_corpus(),
            source_receipts=[build_worldbridge_dynamic_topology_receipt(runtime_epoch="source-epoch", generation=1, structure_fingerprint={"fingerprint": "a" * 64})],
            fresh_runtime_epoch="fresh-epoch",
            fresh_events=_fresh_events(),
            old_receipt_rejected=False,
            old_receipt_restore_non_mutating=True,
            old_receipt_restore_error="not rejected",
        )


def test_fresh_provenance_validator_rejects_receipt_reuse_and_epoch_drift():
    artifact = _build()
    tampered = copy.deepcopy(artifact)
    tampered["events"][0]["fresh_receipt"]["runtime_epoch"] = "source-epoch"
    validation = validate_worldbridge_dynamic_topology_fresh_provenance(tampered)
    assert validation["valid"] is False
    assert "event_0_fresh_receipt_invalid" in validation["errors"]
