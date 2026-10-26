# -*- coding: utf-8
from __future__ import annotations

from core.Lotucosm.pond import Pond
from core.Lotucosm.runtime.world_bridge_fresh_restore_parity import (
    build_worldbridge_fresh_restore_parity_contract,
    verify_fresh_ps_restore_parity,
)
from core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter import (
    PS_SIDE_OVERLAY_KEYS,
    canonical_ps_serializer_projection,
)


def test_empty_real_pond_has_exact_fresh_serializer_parity():
    pond = Pond(name="parity", size=(64.0, 48.0), initial_organisms=0, initial_components=0)
    pond.time = 7
    pond.iteration = 3
    result = verify_fresh_ps_restore_parity(pond)
    assert result["fresh_instance_created"] is True
    assert result["canonical_state_equal"] is True
    assert result["sr_state"] is False


def test_contract_keeps_partial_scope_explicit():
    contract = build_worldbridge_fresh_restore_parity_contract()
    assert contract["fresh_ps_restore"] is True
    assert contract["fresh_sr_restore"] is False
    assert contract["cross_lane_parity"] is False
    assert contract["default_ready"] is False


def test_side_overlays_are_projected_out_of_serializer_parity():
    # A checkpoint ``ps_state`` carries non-serializer side overlays; a fresh
    # Pond can never contain them.  Parity must be decided on the
    # serializer-owned projection so the extra metadata is not a false break.
    canonical = {"name": "pond", "time": 7, "organisms": {"ps:a": {"energy": 9}}}
    with_overlays = {
        **canonical,
        **{key: {"schema_version": 1, "organisms": {}} for key in PS_SIDE_OVERLAY_KEYS},
    }
    assert canonical_ps_serializer_projection(with_overlays) == canonical
    # A real serializer field change must still be visible through the
    # projection, otherwise the parity check would be vacuous.
    drifted = {**with_overlays, "time": 8}
    assert canonical_ps_serializer_projection(drifted) != canonical


def test_projection_rejects_non_mapping():
    import pytest

    with pytest.raises(TypeError):
        canonical_ps_serializer_projection(["not", "a", "mapping"])
