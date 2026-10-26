"""Versioned, read-only SR/PS clock conversion evidence for E500."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

from .world_bridge_shared_state_transport import (
    WorldBridgeSharedStateReceiver,
    validate_worldbridge_shared_state_envelope,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_e500_shared_clock_contract"
PS_TICK_SECONDS = 0.05
CONVERSION_POLICY = "ps_tick_to_sr_seconds_v1"
PHASE_ORDER = ("sr_snapshot", "ps_update")


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: Mapping[str, Any]) -> str:
    clean = dict(value)
    clean["contract_digest"] = ""
    return hashlib.sha256(_canonical(clean)).hexdigest()


def build_worldbridge_e500_shared_clock_contract(
    envelopes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if isinstance(envelopes, (str, bytes)) or not isinstance(envelopes, Sequence):
        raise TypeError("envelopes must be a sequence")
    if not envelopes:
        raise ValueError("E500 requires at least one envelope")
    receiver = WorldBridgeSharedStateReceiver()
    copied: list[dict[str, Any]] = []
    for envelope in envelopes:
        validation = validate_worldbridge_shared_state_envelope(envelope)
        if validation != {"valid": True, "errors": []}:
            raise ValueError("invalid E500 envelope: " + ", ".join(validation["errors"]))
        copied.append(receiver.accept(envelope))

    samples: list[dict[str, Any]] = []
    previous: tuple[int, int, float] | None = None
    for envelope in copied:
        sr = envelope["clock_provenance"]["sr"]
        ps = envelope["clock_provenance"]["ps"]
        if sr["source"] != "viewport_snapshot" or ps["source"] != "pond_update":
            raise ValueError("clock phase source ordering is not proven")
        shared_time = float(ps["tick"]) * PS_TICK_SECONDS
        sr_time = float(sr["time"])
        if not math.isclose(shared_time, sr_time, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("SR/PS converted clock mismatch")
        cursor = (int(sr["tick"]), int(ps["tick"]), shared_time)
        if previous is not None and (
            cursor[0] < previous[0] or cursor[1] < previous[1] or cursor[2] < previous[2]
        ):
            raise ValueError("shared clock ordering regression")
        previous = cursor
        samples.append({
            "sequence": envelope["sequence"],
            "sr_tick": cursor[0],
            "ps_tick": cursor[1],
            "sr_time": sr_time,
            "shared_time": shared_time,
            "phase_order": list(PHASE_ORDER),
        })

    conversion_exercised = any(
        sample["ps_tick"] != samples[0]["ps_tick"] for sample in samples[1:]
    )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "conversion_policy": CONVERSION_POLICY,
        "reference_domain": "sr_scaled_scene_seconds",
        "ps_tick_seconds": PS_TICK_SECONDS,
        "phase_order": list(PHASE_ORDER),
        "envelope_count": len(copied),
        "envelope_digests": [item["envelope_digest"] for item in copied],
        "samples": samples,
        "ordering_proven": True,
        "conversion_consistent": True,
        "conversion_exercised": conversion_exercised,
        "conversion_admitted": conversion_exercised,
        "replay_admitted": False,
        "default_ready": False,
        "contract_digest": "",
    }
    witness["contract_digest"] = _digest(witness)
    return copy.deepcopy(witness)


def validate_worldbridge_e500_shared_clock_contract(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["contract_not_mapping"]}
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("identity_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_mismatch")
    if value.get("conversion_policy") != CONVERSION_POLICY or value.get("reference_domain") != "sr_scaled_scene_seconds":
        errors.append("conversion_policy_mismatch")
    if value.get("ps_tick_seconds") != PS_TICK_SECONDS or value.get("phase_order") != list(PHASE_ORDER):
        errors.append("clock_rule_mismatch")
    count = value.get("envelope_count")
    digests = value.get("envelope_digests")
    samples = value.get("samples")
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        errors.append("envelope_count_invalid")
    if not isinstance(digests, list) or len(digests) != count or any(not isinstance(item, str) or len(item) != 64 for item in digests):
        errors.append("envelope_digests_invalid")
    if not isinstance(samples, list) or len(samples) != count:
        errors.append("samples_invalid")
    if value.get("ordering_proven") is not True or value.get("conversion_consistent") is not True:
        errors.append("conversion_not_proven")
    if value.get("conversion_admitted") is not value.get("conversion_exercised"):
        errors.append("conversion_admission_mismatch")
    if value.get("replay_admitted") is not False or value.get("default_ready") is not False:
        errors.append("admission_overclaim")
    if not isinstance(value.get("contract_digest"), str) or value.get("contract_digest") != _digest(value):
        errors.append("contract_digest_mismatch")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "CONVERSION_POLICY",
    "PHASE_ORDER",
    "PS_TICK_SECONDS",
    "build_worldbridge_e500_shared_clock_contract",
    "validate_worldbridge_e500_shared_clock_contract",
]
