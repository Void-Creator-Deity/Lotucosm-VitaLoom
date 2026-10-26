from builtin.components.component_factory import ComponentFactory
from builtin.entity_types.organism import Organism
from core.Lotucosm.runtime.world_bridge_ps_hierarchy_contract import (
    build_ps_hierarchy_authority_contract,
    validate_ps_hierarchy_authority_contract,
)


def test_ps_hierarchy_contract_has_single_local_owner_and_special_membrane_relation() -> None:
    organism = Organism("hierarchy-test", (0.0, 0.0))
    factory = ComponentFactory()
    organism.add_component(factory.create_component("Sensor", "sensor", organism_id=organism.id))
    organism.set_membrane(factory.create_component("Membrane", "membrane", organism_id=organism.id))
    contract = build_ps_hierarchy_authority_contract(organism)
    assert validate_ps_hierarchy_authority_contract(contract) == {"valid": True, "errors": []}
    assert contract["component_parent_authority"] == "organism"
    assert contract["membrane_reference_authority"] == "organism"
    assert contract["membrane_relation"] == "special_owned_reference"
    assert contract["evidence"]["cross_lane_hierarchy_authority"] is False
    assert contract["evidence"]["worldbridge_live_authority"] is False


def test_ps_hierarchy_contract_rejects_authority_escalation() -> None:
    organism = Organism("hierarchy-test", (0.0, 0.0))
    contract = build_ps_hierarchy_authority_contract(organism)
    contract["evidence"]["worldbridge_live_authority"] = True
    result = validate_ps_hierarchy_authority_contract(contract)
    assert result["valid"] is False
    assert "WorldBridge live authority must remain blocked" in result["errors"]
