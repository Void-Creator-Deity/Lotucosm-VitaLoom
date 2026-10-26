from __future__ import annotations

from types import SimpleNamespace

from core.Lotucosm.runtime.world_bridge_mapping_audit import (
    build_worldbridge_mapping_audit,
)
from core.Lotucosm.runtime.world_bridge_field_admission import (
    build_worldbridge_field_admission_matrix,
)
from core.Lotucosm.runtime.world_bridge_mutation_authority import (
    MAPPING_FIELDS,
    OWNER_ROOTS,
    WORLD_BRIDGE_LIVE_MAPPER_PATHS,
    build_worldbridge_mutation_owner_contract,
    capture_process_owner_binding,
    validate_process_owner_binding,
    validate_worldbridge_mutation_owner_contract,
)


def test_mutation_owner_contract_covers_mapping_ledger_without_claiming_admission():
    contract = build_worldbridge_mutation_owner_contract()
    audit = build_worldbridge_mapping_audit()
    admission = build_worldbridge_field_admission_matrix()

    assert validate_worldbridge_mutation_owner_contract(contract) == {
        "valid": True,
        "errors": [],
    }
    assert audit["mutation_owner_contract_valid"] is True
    assert audit["mutation_owner_contract_errors"] == []
    assert set(contract["fields"]) == set(audit["fields"])
    assert set(contract["fields"]) == set(admission["fields"])
    for field, audit_entry in audit["fields"].items():
        owner_entry = contract["fields"][field]
        assert owner_entry["state"] == audit_entry["state"]
        assert owner_entry["direction"] == audit_entry["direction"]
        assert admission["fields"][field]["current_state"] == owner_entry["state"]
        assert admission["fields"][field]["direction"] == owner_entry["direction"]
        assert owner_entry["live_adapter_admitted"] is False
        assert owner_entry["mutation_owner"] != "worldbridge_coordinator"
    assert contract["admissions"]["owner_binding"] is True
    assert contract["admissions"]["field_scoped_live_mapping"] is False
    assert contract["admissions"]["replay_admitted"] is False
    assert contract["admissions"]["lossless"] is False
    assert contract["admissions"]["default_ready"] is False


def test_mutation_owner_contract_validator_rejects_inconsistent_field_metadata():
    contract = build_worldbridge_mutation_owner_contract()
    contract["fields"]["position"]["state"] = "not_mapped"

    result = validate_worldbridge_mutation_owner_contract(contract)

    assert result["valid"] is False
    assert "field_position_unmapped_direction_mismatch" in result["errors"]


def test_mutation_owner_contract_validator_rejects_forged_owner_and_api_metadata():
    contract = build_worldbridge_mutation_owner_contract()
    contract["fields"]["position"]["sr_owner"] = None
    contract["fields"]["position"]["mutation_api"] = "unverified_writer"

    result = validate_worldbridge_mutation_owner_contract(contract)

    assert result["valid"] is False
    assert "field_position_sr_owner_mismatch" in result["errors"]
    assert "field_position_mutation_api_mismatch" in result["errors"]


def test_mutation_owner_contract_validator_rejects_unknown_field_metadata():
    contract = build_worldbridge_mutation_owner_contract()
    contract["fields"]["position"]["unreviewed_flag"] = True

    result = validate_worldbridge_mutation_owner_contract(contract)

    assert result["valid"] is False
    assert "field_position_keys_mismatch" in result["errors"]


def test_mutation_owner_contract_rejects_non_mapping_fields_and_coordinator_state_ownership():
    invalid_fields = build_worldbridge_mutation_owner_contract()
    invalid_fields["fields"] = []
    result = validate_worldbridge_mutation_owner_contract(invalid_fields)
    assert result["valid"] is False
    assert "mapping_fields_mismatch" in result["errors"]

    invalid_owner = build_worldbridge_mutation_owner_contract()
    invalid_owner["owners"]["bridge_coordinator"]["owns"].append("ps_values")
    result = validate_worldbridge_mutation_owner_contract(invalid_owner)
    assert result["valid"] is False
    assert "coordinator_claims_lane_state_ownership" in result["errors"]


def test_mutation_api_inventory_does_not_claim_a_shared_mutation_owner():
    fields = build_worldbridge_mutation_owner_contract()["fields"]

    assert fields["position"]["mutation_api"] == (
        "ps_restore_motion_state_or_position_setter;sr_position_setter"
    )
    assert fields["max_energy"]["mutation_owner"] == "ps_constructor"
    assert fields["membrane_component_graph"]["mutation_owner"] == "none"
    assert all(
        item["mutation_owner"] != "worldbridge_coordinator"
        for item in fields.values()
    )


def test_mutation_contract_records_the_actual_creation_and_tick_mapper_paths():
    fields = build_worldbridge_mutation_owner_contract()["fields"]

    assert set(WORLD_BRIDGE_LIVE_MAPPER_PATHS) == set(MAPPING_FIELDS)
    for name in MAPPING_FIELDS:
        assert fields[name]["live_mapper_paths"] == list(WORLD_BRIDGE_LIVE_MAPPER_PATHS[name])
    assert fields["max_energy"]["live_mapper_paths"] == ["creation_seed"]
    assert "sr_to_ps" not in fields["size_radius"]["live_mapper_paths"]
    assert "visible_sr_presentation_only" in fields["active_visible_state"]["live_mapper_paths"]


def test_process_owner_binding_is_explicitly_nonportable_and_detects_root_drift():
    roots = {name: object() for name in OWNER_ROOTS}
    entities = [SimpleNamespace(id="sr:one")]
    baseline = capture_process_owner_binding(
        runtime_epoch="epoch-1", roots=roots, sr_entities=entities
    )

    assert baseline["portable"] is False
    assert all(isinstance(value, int) for value in baseline["roots"].values() if value is not None)
    assert validate_process_owner_binding(baseline, baseline) == {
        "valid": True,
        "errors": [],
    }

    replaced_roots = dict(roots)
    replaced_roots["ps_pond"] = object()
    changed = capture_process_owner_binding(
        runtime_epoch="epoch-1", roots=replaced_roots, sr_entities=entities
    )
    assert "owner_root_changed:ps_pond" in validate_process_owner_binding(
        baseline, changed
    )["errors"]

    replaced_entities = [SimpleNamespace(id="sr:one")]
    changed_entities = capture_process_owner_binding(
        runtime_epoch="epoch-1", roots=roots, sr_entities=replaced_entities
    )
    assert "sr_entity_owner_changed" in validate_process_owner_binding(
        baseline, changed_entities
    )["errors"]


def test_process_owner_binding_rejects_runtime_epoch_drift():
    roots = {name: object() for name in OWNER_ROOTS}
    baseline = capture_process_owner_binding(runtime_epoch="epoch-1", roots=roots)
    changed = capture_process_owner_binding(runtime_epoch="epoch-2", roots=roots)

    assert validate_process_owner_binding(baseline, changed) == {
        "valid": False,
        "errors": ["runtime_epoch_changed"],
    }


def test_process_owner_binding_rejects_a_different_process_identity():
    roots = {name: object() for name in OWNER_ROOTS}
    baseline = capture_process_owner_binding(runtime_epoch="epoch-1", roots=roots)
    other_process = dict(baseline)
    other_process["process_instance_id"] = "other-process:nonce"

    assert validate_process_owner_binding(baseline, other_process) == {
        "valid": False,
        "errors": ["process_instance_changed"],
    }

