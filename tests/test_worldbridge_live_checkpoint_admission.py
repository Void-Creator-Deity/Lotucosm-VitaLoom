from __future__ import annotations

import copy

from core.Lotucosm.runtime.world_bridge_live_checkpoint_admission import (
    build_worldbridge_live_checkpoint_admission_witness,
    validate_worldbridge_live_checkpoint_admission_witness,
)


def _witness(**overrides):
    values = {
        "checkpoint": {"checkpoint_id": "cp-1", "sequence": 4, "digest": "digest"},
        "versioned_bundle": {
            "runtime_version": "1.0.0",
            "sr_schema_version": 1,
            "ps_schema_version": 1,
            "bridge_schema_version": 1,
        },
        "fresh_restore": {"parity": True},
        "in_place_restore": {"parity": True},
        "identity_registration": {"parity": True},
        "rollback": {"atomic": True, "target_preserved": True},
    }
    values.update(overrides)
    return build_worldbridge_live_checkpoint_admission_witness(**values)


def test_complete_opt_in_witness_is_valid_but_never_default_ready():
    witness = _witness()
    assert witness["contract_valid"] is True
    assert witness["opt_in_live_adapter_admitted"] is True
    assert witness["live_adapter_admitted"] is False
    assert witness["replay_admitted"] is False
    assert witness["default_ready"] is False


def test_missing_parity_keeps_opt_in_admission_closed():
    witness = _witness(in_place_restore={"parity": False})
    assert witness["opt_in_live_adapter_admitted"] is False
    assert witness["contract_valid"] is True


def test_validator_rejects_boundary_overclaim():
    witness = _witness()
    tampered = copy.deepcopy(witness)
    tampered["default_ready"] = True
    result = validate_worldbridge_live_checkpoint_admission_witness(tampered)
    assert result["valid"] is False
    assert "default_ready_overclaim" in result["errors"]


def test_restore_diagnostic_is_preserved_without_admission():
    diagnostic = {
        "schema_version": 1,
        "checkpoint_id": "cp-1",
        "checkpoint_digest": "digest",
        "code": "project_runtime_binding_rejected",
        "errors": ["runtime_binding_project_lock_digest_mismatch"],
    }
    witness = _witness(restore_diagnostic=diagnostic)
    assert witness["restore_diagnostic"]["schema_version"] == 1
    assert witness["restore_diagnostic"]["checkpoint_id"] == "cp-1"
    assert witness["restore_diagnostic"]["diagnostic_digest"]
    assert witness["opt_in_live_adapter_admitted"] is True
    assert witness["live_adapter_admitted"] is False
    witness["restore_diagnostic"]["errors"].append("mutated")
    assert diagnostic["errors"] == ["runtime_binding_project_lock_digest_mismatch"]
    assert validate_worldbridge_live_checkpoint_admission_witness(witness)["valid"] is False
    assert "restore_diagnostic_digest_mismatch" in validate_worldbridge_live_checkpoint_admission_witness(witness)["errors"]


def test_restore_diagnostic_rejects_cross_checkpoint_binding():
    witness = _witness(
        restore_diagnostic={
            "schema_version": 1,
            "checkpoint_id": "cp-1",
            "checkpoint_digest": "digest",
            "code": "project_runtime_binding_rejected",
            "errors": ["runtime_binding_project_lock_digest_mismatch"],
        }
    )
    tampered = copy.deepcopy(witness)
    tampered["checkpoint_identity"]["checkpoint_id"] = "other"
    result = validate_worldbridge_live_checkpoint_admission_witness(tampered)
    assert result["valid"] is False
    assert "restore_diagnostic_invalid" in result["errors"]
