# -*- coding: utf-8 -*-
"""Cross-envelope witness for the current SR/PS shared-state boundary."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from .world_bridge_shared_state_transport import (
    WorldBridgeSharedStateReceiver,
    validate_worldbridge_shared_state_envelope,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_e497_shared_contract_witness"
BLOCKERS = (
    "shared_clock_domain_conversion_missing",
    "shared_randomness_consumption_order_missing",
    "fresh_session_replay_parity_missing",
    "live_lane_restore_authority_missing",
)


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def build_worldbridge_e497_shared_contract_witness(
    envelopes: Sequence[Mapping[str, Any]],
    *,
    fresh_session_parity: bool = False,
) -> dict[str, Any]:
    """Validate a real ordered envelope window without applying lane state."""
    if isinstance(envelopes, (str, bytes)) or not isinstance(envelopes, Sequence):
        raise TypeError("envelopes must be a sequence")
    receiver = WorldBridgeSharedStateReceiver()
    copied: list[dict[str, Any]] = []
    for envelope in envelopes:
        validation = validate_worldbridge_shared_state_envelope(envelope)
        if validation["valid"] is not True:
            raise ValueError("invalid shared envelope: " + ",".join(validation["errors"]))
        copied.append(receiver.accept(envelope))
    clock_domains = {
        domain
        for envelope in copied
        for value in envelope["clock_provenance"].values()
        for domain in (value["domain"],)
    }
    rng_snapshots = [envelope["rng_context_snapshot"] for envelope in copied]
    input_events = sum(len(envelope["input_events"]) for envelope in copied)
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "envelope_count": len(copied),
        "envelope_digests": [envelope["envelope_digest"] for envelope in copied],
        "input_event_count": input_events,
        "receiver_continuity": {
            "accepted_count": receiver.accepted_count,
            "last_sequence": receiver.last_sequence,
            "last_input_sequence": receiver.last_input_sequence,
            "last_pause_reset_epoch": receiver.last_pause_reset_epoch,
        },
        "clock": {
            "domains": sorted(clock_domains),
            "shared_domain": len(clock_domains) == 1,
            "conversion_admitted": False,
        },
        "randomness": {
            "snapshot_count": sum(snapshot is not None for snapshot in rng_snapshots),
            "all_envelopes_carry_snapshot": bool(copied) and all(snapshot is not None for snapshot in rng_snapshots),
            "shared_consumption_order_proven": False,
        },
        "fresh_session_parity": bool(fresh_session_parity),
        "blockers": list(BLOCKERS),
        "replay_admitted": False,
        "live_adapter_admitted": False,
        "default_ready": False,
    }
    witness["witness_digest"] = _digest({**witness, "witness_digest": ""})
    return copy.deepcopy(witness)


def validate_worldbridge_e497_shared_contract_witness(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_must_be_mapping"]}
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS or value.get("read_only") is not True:
        errors.append("identity_or_read_only_mismatch")
    if isinstance(value.get("envelope_count"), bool) or not isinstance(value.get("envelope_count"), int) or value.get("envelope_count", -1) < 1:
        errors.append("envelope_count_invalid")
    digests = value.get("envelope_digests")
    if not isinstance(digests, list) or len(digests) != value.get("envelope_count") or any(not isinstance(digest, str) or len(digest) != 64 for digest in digests):
        errors.append("envelope_digests_invalid")
    continuity = value.get("receiver_continuity")
    if not isinstance(continuity, Mapping) or continuity.get("accepted_count") != value.get("envelope_count"):
        errors.append("receiver_continuity_invalid")
    clock = value.get("clock")
    if not isinstance(clock, Mapping) or not isinstance(clock.get("domains"), list) or clock.get("conversion_admitted") is not False:
        errors.append("clock_witness_invalid")
    randomness = value.get("randomness")
    if not isinstance(randomness, Mapping) or randomness.get("shared_consumption_order_proven") is not False:
        errors.append("randomness_witness_invalid")
    if value.get("fresh_session_parity") is not False:
        errors.append("fresh_session_parity_overclaim")
    if value.get("blockers") != list(BLOCKERS):
        errors.append("blockers_mismatch")
    for field in ("replay_admitted", "live_adapter_admitted", "default_ready"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    if not isinstance(value.get("witness_digest"), str) or value.get("witness_digest") != _digest({**dict(value), "witness_digest": ""}):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "BLOCKERS",
    "STATUS",
    "build_worldbridge_e497_shared_contract_witness",
    "validate_worldbridge_e497_shared_contract_witness",
]
