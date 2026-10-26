from __future__ import annotations

from core.Lotucosm.runtime.world_bridge_checkpoint_mapping_audit import (
    build_worldbridge_checkpoint_mapping_audit,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


def test_checkpoint_mapping_audit_closes_all_owner_fields_without_claiming_lossless():
    audit = build_worldbridge_checkpoint_mapping_audit()

    assert audit["read_only"] is True
    assert audit["checkpoint_fields_complete"] is True
    assert set(audit["checkpoint_fields_closed"]) == {
        "sr_state",
        "ps_state",
        "bridge_identity_links",
        "input_state",
        "randomness_state",
        "lifecycle",
    }
    assert audit["lossless"] is False
    assert audit["replay_admitted"] is False
    assert audit["default_ready"] is False
    assert all(
        field["business_mapping_admitted"] is False
        for field in audit["fields"].values()
    )


def test_runtime_status_exposes_checkpoint_mapping_audit():
    status = build_runtime_worldbridge_status()
    audit = build_worldbridge_checkpoint_mapping_audit()
    assert status["checkpoint_mapping_audit"] == audit
