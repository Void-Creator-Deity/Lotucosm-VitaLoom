"""Evidence classification for WorldBridge render identity."""
from __future__ import annotations

from typing import Any


def build_worldbridge_render_identity_audit() -> dict[str, Any]:
    """Separate persisted component identity from renderer-owned asset identity."""
    fields = {
        "sr_entity_identity": {
            "state": "checkpoint_closed",
            "evidence": ["deterministic_identity_source", "lifecycle_capture", "restore_validation"],
        },
        "ps_organism_identity": {
            "state": "checkpoint_closed",
            "evidence": ["bridge_identity_links", "pond_persistence", "restore_validation"],
        },
        "component_identity": {
            "state": "persistence_closed",
            "evidence": ["explicit_four_id_contract", "component_artifact", "project_lock_binding"],
        },
        "render_asset_identity": {
            "state": "not_mapped",
            "evidence": ["asset_owner_contract", "asset_reference_persistence", "cross_session_render_parity"],
        },
        "renderer_authority": {
            "state": "quarantined",
            "evidence": ["ui_host_adapter_boundary", "renderer_lifecycle_owner", "pixel_parity"],
        },
    }
    return {
        "schema_version": 1,
        "status": "worldbridge_render_identity_audit",
        "read_only": True,
        "fields": fields,
        "identity_provenance_closed": all(
            fields[name]["state"] in {"checkpoint_closed", "persistence_closed"}
            for name in ("sr_entity_identity", "ps_organism_identity", "component_identity")
        ),
        "render_asset_mapping_admitted": False,
        "renderer_authority_admitted": False,
        "lossless": False,
        "replay_admitted": False,
        "default_ready": False,
        "blockers": [
            "asset_owner_contract",
            "asset_reference_persistence",
            "cross_session_render_parity",
            "renderer_lifecycle_owner",
            "pixel_parity",
        ],
        "do_not_claim": [
            "render_asset_worldbridge_mapping",
            "renderer_authority_in_runtime_core",
            "lossless_worldbridge_mapping",
            "default_ready",
        ],
    }


__all__ = ["build_worldbridge_render_identity_audit"]
