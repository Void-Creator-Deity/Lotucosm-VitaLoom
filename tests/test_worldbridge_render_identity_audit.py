from core.Lotucosm.runtime.world_bridge_render_identity_audit import (
    build_worldbridge_render_identity_audit,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


def test_render_identity_audit_closes_provenance_without_admitting_renderer_authority():
    audit = build_worldbridge_render_identity_audit()
    assert audit["identity_provenance_closed"] is True
    assert audit["fields"]["component_identity"]["state"] == "persistence_closed"
    assert audit["fields"]["render_asset_identity"]["state"] == "not_mapped"
    assert audit["render_asset_mapping_admitted"] is False
    assert audit["renderer_authority_admitted"] is False
    assert audit["lossless"] is False
    assert audit["default_ready"] is False


def test_runtime_status_exposes_render_identity_audit():
    status = build_runtime_worldbridge_status()
    assert status["render_identity_audit"] == build_worldbridge_render_identity_audit()
