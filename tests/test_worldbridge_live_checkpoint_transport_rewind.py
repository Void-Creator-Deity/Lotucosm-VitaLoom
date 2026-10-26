from __future__ import annotations

from types import SimpleNamespace

from core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter import _validate_shared_transport


def test_live_checkpoint_transport_allows_same_epoch_sequence_rewind() -> None:
    viewport = SimpleNamespace(
        _sr_runtime_epoch="epoch",
        _worldbridge_shared_state_sequence=9,
    )
    _validate_shared_transport(
        viewport,
        {
            "schema_version": 1,
            "runtime_epoch": "epoch",
            "envelope_sequence": 3,
            "receiver": None,
        },
    )
