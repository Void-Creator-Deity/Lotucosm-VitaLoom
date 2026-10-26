from core.Lotucosm.runtime.world_bridge_script_mapping_audit import (
    build_worldbridge_script_mapping_audit,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


def test_script_provenance_is_closed_without_admitting_behavior_authority():
    audit = build_worldbridge_script_mapping_audit()
    assert audit["provenance_persistence_closed"] is True
    assert len(audit["provenance_fields_closed"]) == 4
    assert audit["live_behavior_admitted"] is False
    assert audit["replay_admitted"] is False
    assert audit["lossless"] is False
    assert audit["default_ready"] is False
    assert audit["fields"]["script_runtime_behavior"]["state"] == "not_admitted"


def test_runtime_status_exposes_script_mapping_audit():
    status = build_runtime_worldbridge_status()
    assert status["script_mapping_audit"] == build_worldbridge_script_mapping_audit()
