"""Evidence classification for the SR script WorldBridge boundary."""
from __future__ import annotations

from typing import Any


def build_worldbridge_script_mapping_audit() -> dict[str, Any]:
    """Separate script provenance persistence from behavior authority."""
    fields = {
        "declared_script_paths": {
            "state": "checkpoint_closed",
            "evidence": ["lifecycle_capture", "lifecycle_restore", "epoch_validation"],
        },
        "entropy_audits": {
            "state": "checkpoint_closed",
            "evidence": ["lifecycle_capture", "lifecycle_restore", "digest_validation"],
        },
        "entropy_receipts": {
            "state": "checkpoint_closed",
            "evidence": ["owner_binding", "lifecycle_capture", "receipt_validation"],
        },
        "failure_receipts": {
            "state": "checkpoint_closed",
            "evidence": ["structured_failure_sink", "lifecycle_capture", "epoch_validation"],
        },
        "script_runtime_behavior": {
            "state": "not_admitted",
            "evidence": ["cross_lane_behavior_authority", "deterministic_replay"],
        },
        "script_command_binding": {
            "state": "not_admitted",
            "evidence": ["command_registry_contract", "cross_lane_behavior_authority"],
        },
    }
    closed = [name for name, item in fields.items() if item["state"] == "checkpoint_closed"]
    return {
        "schema_version": 1,
        "status": "worldbridge_script_mapping_audit",
        "read_only": True,
        "fields": fields,
        "provenance_persistence_closed": len(closed) == 4,
        "provenance_fields_closed": closed,
        "live_behavior_admitted": False,
        "replay_admitted": False,
        "lossless": False,
        "default_ready": False,
        "blockers": [
            "cross_lane_behavior_authority",
            "command_registry_contract",
            "deterministic_replay",
        ],
        "do_not_claim": [
            "script_behavior_worldbridge_authority",
            "lossless_worldbridge_mapping",
            "unified_runtime_replay",
            "default_ready",
        ],
    }


__all__ = ["build_worldbridge_script_mapping_audit"]
