from core.Lotucosm.runtime.world_bridge_topology_mapping_audit import (
    build_worldbridge_topology_mapping_audit,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


def test_topology_audit_closes_structure_persistence_without_live_mapping():
    audit = build_worldbridge_topology_mapping_audit()
    assert audit["topology_provenance_closed"] is True
    assert audit["fields"]["sr_structure_fingerprint"]["state"] == "checkpoint_closed"
    assert audit["fields"]["ps_local_hierarchy"]["state"] == "local_owner_closed"
    assert audit["fields"]["component_hierarchy_projection"]["state"] == "read_only_projection"
    assert audit["fields"]["sr_topology_live_owner"]["state"] == "live_owner_closed"
    assert audit["sr_topology_live_owner_closed"] is True
    assert audit["live_owner_fields_closed"] == ["sr_topology_live_owner"]
    assert audit["cross_lane_topology_admitted"] is False
    assert audit["lossless"] is False
    assert audit["default_ready"] is False


def test_topology_audit_records_membrane_behavior_isolation_without_authority():
    audit = build_worldbridge_topology_mapping_audit()
    assert audit["fields"]["membrane_behavior_boundary"]["state"] == "lane_local_isolated"
    assert audit["membrane_behavior_lane_local_isolated"] is True
    assert audit["lane_local_fields_isolated"] == ["membrane_behavior_boundary"]
    assert audit["fields"]["membrane_behavior_mapping"]["state"] == "not_admitted"
    assert audit["cross_lane_behavior_admitted"] is False
    assert audit["cross_lane_topology_admitted"] is False
    assert audit["replay_admitted"] is False
    assert audit["lossless"] is False
    assert audit["default_ready"] is False


def test_runtime_status_exposes_topology_mapping_audit():
    status = build_runtime_worldbridge_status()
    assert status["topology_mapping_audit"] == build_worldbridge_topology_mapping_audit()