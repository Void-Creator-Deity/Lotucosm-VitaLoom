# -*- coding: utf-8
"""Fresh PS/Pond restore parity for the live checkpoint boundary.

This module covers only the PS serializer-owned state.  SR scene construction
and bridge identity are intentionally outside this parity claim.
"""

from __future__ import annotations

import copy
import json
from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_fresh_ps_restore_parity"


def capture_canonical_ps_state(pond: Any) -> dict[str, Any]:
    """Capture serializer-owned PS state with volatile timestamp metadata removed."""
    from builtin.systems.pond_serializer import PondSerializer

    payload = PondSerializer(save_format="json").serialize_pond(pond)
    # Serializer-owned state must compare as canonical JSON, not according to
    # incidental Python tuple/list container choices.
    payload = json.loads(json.dumps(payload, ensure_ascii=False, allow_nan=False))
    payload.pop("timestamp", None)
    return payload


def restore_ps_state_to_fresh_pond(
    ps_state: dict[str, Any],
    *,
    pond_class: type | None = None,
) -> Any:
    """Reconstruct a detached Pond from one canonical PS state payload."""
    if not isinstance(ps_state, dict):
        raise TypeError("ps_state must be a mapping")
    from builtin.systems.pond_serializer import PondSerializer
    from core.Lotucosm.pond import Pond

    target_class = Pond if pond_class is None else pond_class
    payload = copy.deepcopy(ps_state)
    candidate = PondSerializer(save_format="json").deserialize_pond(payload, target_class)
    if candidate is None:
        raise ValueError("fresh PS Pond restore returned no candidate")
    return candidate


def verify_fresh_ps_restore_parity(pond: Any) -> dict[str, Any]:
    """Run a detached round trip and report exact serializer-state equality."""
    original = capture_canonical_ps_state(pond)
    fresh = restore_ps_state_to_fresh_pond(original, pond_class=type(pond))
    restored = capture_canonical_ps_state(fresh)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "fresh_instance_created": fresh is not pond,
        "canonical_state_equal": original == restored,
        "original": original,
        "restored": restored,
        "sr_state": False,
        "bridge_identity": False,
        "default_ready": False,
    }


def build_worldbridge_fresh_restore_parity_contract() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": "serializer_owned_ps_pond_state_only",
        "fresh_ps_restore": True,
        "fresh_sr_restore": False,
        "bridge_identity_restore": False,
        "cross_lane_parity": False,
        "atomic_checkpoint": False,
        "replay_admitted": False,
        "default_ready": False,
        "contract_valid": True,
    }


__all__ = [
    "build_worldbridge_fresh_restore_parity_contract",
    "capture_canonical_ps_state",
    "restore_ps_state_to_fresh_pond",
    "verify_fresh_ps_restore_parity",
]
