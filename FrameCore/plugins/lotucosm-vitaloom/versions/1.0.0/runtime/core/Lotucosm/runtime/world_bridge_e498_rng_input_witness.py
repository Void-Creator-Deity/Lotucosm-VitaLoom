"""E498 witness for continuous input and caller-owned RNG transport.

This is evidence only.  It proves that a receiver can bind consecutive
envelopes to one RNG context while preserving canonical input continuity; it
does not make the transport a replay or live-restore authority.
"""
from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from typing import Any

from .world_bridge_shared_state_transport import (
    WorldBridgeSharedStateReceiver,
    validate_worldbridge_shared_state_envelope,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_e498_rng_input_witness"
BLOCKERS = (
    "shared_clock_conversion_missing",
    "shared_rng_consumption_order_unproven",
    "fresh_session_replay_parity_missing",
    "live_lane_restore_authority_missing",
)


def build_worldbridge_e498_rng_input_witness(
    envelopes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a detached witness from at least two consecutive envelopes."""
    if isinstance(envelopes, (str, bytes)) or not isinstance(envelopes, Sequence):
        raise TypeError("envelopes must be a sequence")
    copied = [copy.deepcopy(dict(envelope)) for envelope in envelopes]
    if len(copied) < 2:
        raise ValueError("E498 requires at least two envelope generations")
    receiver = WorldBridgeSharedStateReceiver()
    for envelope in copied:
        validation = validate_worldbridge_shared_state_envelope(envelope)
        if validation != {"valid": True, "errors": []}:
            raise ValueError("invalid E498 envelope: " + ", ".join(validation["errors"]))
        receiver.accept(envelope)

    snapshots = [envelope["rng_context_snapshot"] for envelope in copied]
    if any(snapshot is None for snapshot in snapshots):
        raise ValueError("E498 requires an RNG snapshot in every envelope")
    context_ids = {snapshot["context_id"] for snapshot in snapshots}
    if len(context_ids) != 1:
        raise ValueError("E498 RNG context mismatch")
    snapshot_digests = [snapshot["snapshot_digest"] for snapshot in snapshots]
    input_sequences = [
        event["payload"]["canonical_sequence"]
        for envelope in copied
        for event in envelope["input_events"]
    ]
    witness = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "envelope_count": len(copied),
        "envelope_digests": [envelope["envelope_digest"] for envelope in copied],
        "rng_context_id": next(iter(context_ids)),
        "rng_snapshot_digests": snapshot_digests,
        "rng_generation_count": len(set(snapshot_digests)),
        "input_sequences": input_sequences,
        "input_event_count": len(input_sequences),
        "receiver": receiver.continuity_snapshot(),
        "fresh_session_parity": False,
        "replay_admitted": False,
        "default_ready": False,
        "blockers": list(BLOCKERS),
    }
    return witness


def validate_worldbridge_e498_rng_input_witness(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("identity_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_mismatch")
    count = value.get("envelope_count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 2:
        errors.append("envelope_count_invalid")
    digests = value.get("envelope_digests")
    if not isinstance(digests, list) or len(digests) != count or any(not isinstance(item, str) or len(item) != 64 for item in digests):
        errors.append("envelope_digests_invalid")
    rng_digests = value.get("rng_snapshot_digests")
    if not isinstance(rng_digests, list) or len(rng_digests) != count or any(not isinstance(item, str) or len(item) != 64 for item in rng_digests):
        errors.append("rng_snapshot_digests_invalid")
    if value.get("rng_generation_count", 0) < 2:
        errors.append("rng_generation_count_invalid")
    sequences = value.get("input_sequences")
    if not isinstance(sequences, list) or any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in sequences):
        errors.append("input_sequences_invalid")
    if not isinstance(sequences, list) or value.get("input_event_count") != len(sequences):
        errors.append("input_event_count_invalid")
    receiver = value.get("receiver")
    if not isinstance(receiver, Mapping) or receiver.get("accepted_count") != count:
        errors.append("receiver_invalid")
    if value.get("fresh_session_parity") is not False:
        errors.append("fresh_session_parity_overclaim")
    if value.get("replay_admitted") is not False or value.get("default_ready") is not False:
        errors.append("admission_overclaim")
    if value.get("blockers") != list(BLOCKERS):
        errors.append("blockers_mismatch")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "BLOCKERS",
    "SCHEMA_VERSION",
    "STATUS",
    "build_worldbridge_e498_rng_input_witness",
    "validate_worldbridge_e498_rng_input_witness",
]
