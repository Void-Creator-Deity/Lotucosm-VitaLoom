# -*- coding: utf-8 -*-
from __future__ import annotations

from core.Lotucosm.runtime.world_bridge_native_entropy_audit import (
    build_native_backend_selection_evidence,
    build_native_entropy_boundary_receipt,
    build_native_entropy_audit,
    validate_native_admission_evidence,
    validate_native_entropy_boundary_receipt,
)
from core.Lotucosm.runtime.world_bridge_randomness_authority import (
    build_worldbridge_randomness_authority_contract,
    build_worldbridge_randomness_authority_inventory,
)


def test_shipped_native_sources_are_audited_without_closing_opaque_boundary() -> None:
    audit = build_native_entropy_audit()
    assert audit["shipped_kernel_source_audited"] is True
    assert audit["findings"] == []
    assert audit["opaque_dependency_boundary_closed"] is False
    assert audit["native_entropy_boundary_closed"] is False
    assert audit["boundary_classification"] in {
        "optional_native_unavailable",
        "reachable_contractually_no_entropy",
        "reachable_but_quarantined",
    }
    reachable = [
        probe
        for probe in audit["extension_probes"]
        if probe["available"] and probe["has_kernel"]
    ]
    assert audit["reachable_extension_count"] == len(reachable)
    if not reachable:
        assert audit["boundary_classification"] == "optional_native_unavailable"
    elif all(probe["entropy_contract"] == "none" for probe in reachable):
        assert audit["boundary_classification"] == "reachable_contractually_no_entropy"
    else:
        assert audit["boundary_classification"] == "reachable_but_quarantined"
    assert audit["replay_admitted"] is False
    assert audit["default_ready"] is False
    assert all("sha256" in item for item in audit["source_files"])


def test_randomness_inventory_exposes_native_source_audit() -> None:
    item = next(
        entry
        for entry in build_worldbridge_randomness_authority_inventory()
        if entry["authority_id"] == "native_extension_or_third_party_rng"
    )
    assert item["shipped_source_audit"]["audit_id"] == (
        "vitalloom_sr2d_native_source_entropy"
    )
    assert item["capture_status"] == "unknown_not_captured"
    assert item["boundary_receipt"]["boundary"] == "native_extension_entropy"


def test_native_boundary_receipt_keeps_unavailable_backend_quarantined() -> None:
    receipt = build_native_entropy_boundary_receipt()
    assert receipt["status"] == "quarantined"
    assert receipt["native_entropy_boundary_closed"] is False
    assert receipt["replay_admitted"] is False
    assert validate_native_entropy_boundary_receipt(receipt) == {
        "valid": True,
        "errors": [],
    }


def test_native_boundary_receipt_rejects_admission_overclaim() -> None:
    receipt = build_native_entropy_boundary_receipt()
    receipt["status"] = "admitted"
    assert "native_boundary_receipt_overclaims_admission" in (
        validate_native_entropy_boundary_receipt(receipt)["errors"]
    )


def test_native_admission_evidence_fails_closed_when_incomplete() -> None:
    assert validate_native_admission_evidence({})["valid"] is False
    receipt = build_native_entropy_boundary_receipt(
        native_admission_evidence={}
    )
    assert receipt["status"] == "quarantined"
    assert "native_admission_evidence_invalid" in receipt["reasons"]


def test_unverified_native_backend_selection_stays_quarantined() -> None:
    evidence = build_native_backend_selection_evidence(
        {
            "backend_id": "cpp",
            "module_name": "_vitalloom_sr2d_cpp",
            "artifact_sha256": "artifact",
            "artifact_provenance": "hashed",
            "abi_version_required": 1,
            "abi_version_exported": 1,
        }
    )
    assert evidence["status"] == "quarantined"
    assert "native_boundary_not_admitted" in evidence["reasons"]


def test_randomness_contract_keeps_native_and_replay_gates_closed() -> None:
    contract = build_worldbridge_randomness_authority_contract()
    assert contract["native_entropy_audit"]["shipped_kernel_source_audited"] is True
    assert contract["native_entropy_audit"]["opaque_dependency_boundary_closed"] is False
    assert contract["native_entropy_boundary_closed"] is False
    assert contract["native_entropy_boundary_receipt"]["status"] == "quarantined"
    assert contract["replay_admitted"] is False
    assert contract["default_ready"] is False
