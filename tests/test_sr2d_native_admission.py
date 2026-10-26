from __future__ import annotations

import pytest

from core.Lotucosm.runtime.world_bridge_native_entropy_audit import (
    build_native_admission_evidence,
    build_native_entropy_boundary_receipt,
    validate_native_admission_evidence,
    validate_native_entropy_boundary_receipt,
)
from core.Lotucosm.sr_physics2d import is_native_sr2d_available
from tools.check_sr2d_native_admission import verify


@pytest.mark.skipif(
    not is_native_sr2d_available(),
    reason="native SR2D artifact is not installed",
)
def test_native_sr2d_provenance_parity_and_benchmark_admission() -> None:
    result = verify(repeats=1)

    assert result["provenance"]["abi_version"] == 1
    assert result["provenance"]["entropy_contract"] == "none"
    assert result["provenance_proven"] is True
    assert result["parity_proven"] is True
    assert result["benchmark_proven"] is True
    assert result["native_admitted"] is True
    for scenario in result["parity"]:
        assert scenario["ticks_compared"] == 120
        assert scenario["maximum_delta"] == 0.0
        assert scenario["first_mismatch_tick"] is None
    for benchmark in result["benchmarks"]:
        assert benchmark["first_position_close"] is True
        assert benchmark["speedup"] > 1.0

    evidence = build_native_admission_evidence(result)
    assert validate_native_admission_evidence(evidence) == {
        "valid": True,
        "errors": [],
    }
    receipt = build_native_entropy_boundary_receipt(
        native_admission_evidence=evidence
    )
    assert validate_native_entropy_boundary_receipt(receipt) == {
        "valid": True,
        "errors": [],
    }
    assert receipt["status"] == "admitted"
    assert receipt["build_verified"] is True
    assert receipt["parity_verified"] is True
    assert receipt["native_entropy_boundary_closed"] is True
