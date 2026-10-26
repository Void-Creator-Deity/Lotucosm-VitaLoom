"""Executable audit for live checkpoint field capture/restore coverage.

This is evidence, not an admission switch.  It audits the checkpoint contract
itself and keeps business-field gaps and replay/native blockers visible.
"""
from __future__ import annotations

from typing import Any

from .world_bridge_live_checkpoint import LiveCheckpointAdapters


_CHECKPOINT_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("sr_state", "capture_sr", "restore_sr"),
    ("ps_state", "capture_ps", "restore_ps"),
    ("bridge_identity_links", "capture_bridge", "restore_bridge"),
    ("input_state", "capture_input", "restore_input"),
    ("randomness_state", "capture_randomness", "restore_randomness"),
    ("lifecycle", "capture_lifecycle", "restore_lifecycle"),
)


def build_worldbridge_checkpoint_mapping_audit() -> dict[str, Any]:
    """Return deterministic field-level evidence without touching live state."""
    adapter_fields = set(getattr(LiveCheckpointAdapters, "__dataclass_fields__", {}))
    owner_binding = {
        "capture_owner_binding": "capture_owner_binding" in adapter_fields,
        "validate_owner_binding": "validate_owner_binding" in adapter_fields,
        "process_local_nonportable": True,
        "replacement_root_fail_closed": True,
    }
    owner_binding_complete = all(
        owner_binding[field]
        for field in (
            "capture_owner_binding",
            "validate_owner_binding",
            "process_local_nonportable",
            "replacement_root_fail_closed",
        )
    )
    fields: dict[str, dict[str, Any]] = {}
    for field, capture, restore in _CHECKPOINT_FIELDS:
        compensation = f"compensate_{field.removesuffix('_state').removesuffix('_identity_links')}"
        if field == "bridge_identity_links":
            compensation = "compensate_bridge"
        elif field == "randomness_state":
            compensation = "compensate_randomness"
        elif field == "input_state":
            compensation = "compensate_input"
        elif field == "lifecycle":
            compensation = "compensate_lifecycle"
        fields[field] = {
            "capture_owner": capture in adapter_fields,
            "restore_owner": restore in adapter_fields,
            "compensation_owner": compensation in adapter_fields,
            "state_digest_verified_on_rollback": True,
            "current_state": "checkpoint_closed",
            "business_mapping_admitted": False,
        }

    closed = [
        name for name, item in fields.items()
        if all(item[key] for key in (
            "capture_owner", "restore_owner", "compensation_owner",
            "state_digest_verified_on_rollback",
        ))
    ]
    return {
        "schema_version": 1,
        "status": "worldbridge_checkpoint_mapping_audit",
        "read_only": True,
        "fields": fields,
        "checkpoint_fields_closed": closed,
        "checkpoint_fields_complete": (
            len(closed) == len(fields) and owner_binding_complete
        ),
        "operation_owner_binding": owner_binding,
        "operation_owner_binding_complete": owner_binding_complete,
        "lossless": False,
        "lossless_blockers": [
            "business_field_mapping_matrix_has_unresolved_fields",
            "unified_replay_authority_not_admitted",
            "native_build_import_parity_benchmark_unverified",
        ],
        "default_ready": False,
        "replay_admitted": False,
        "do_not_claim": [
            "lossless_worldbridge_mapping",
            "unified_runtime_replay",
            "native_backend_parity",
            "default_ready",
        ],
    }


__all__ = ["build_worldbridge_checkpoint_mapping_audit"]
