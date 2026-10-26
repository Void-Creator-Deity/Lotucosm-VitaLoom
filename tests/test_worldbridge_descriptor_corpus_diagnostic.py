from __future__ import annotations

from pathlib import Path

from core.Lotucosm.runtime.world_bridge_descriptor_corpus import (
    diagnose_descriptor_corpus,
    discover_canonical_ponds,
)

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "workspace" / "projects" / "samples"


def test_diagnostic_scans_all_canonical_sample_ponds() -> None:
    paths = discover_canonical_ponds(SAMPLES)
    diagnostic = diagnose_descriptor_corpus(paths)
    assert len(paths) >= 4
    assert diagnostic["sample_count"] == len(paths)
    assert diagnostic["all_round_trip_ok"] is True
    assert diagnostic["read_only"] is True
    assert diagnostic["maps_live_objects"] is False
    assert "scripts" in diagnostic["descriptor_shape_keys"]
    assert diagnostic["field_coverage"]["script_count"]["sample_count"] >= 1
    assert diagnostic["field_coverage"]["edge_count"]["total"] > 0


def test_diagnostic_reports_real_coverage_without_inventing_ps_components() -> None:
    diagnostic = diagnose_descriptor_corpus(discover_canonical_ponds(SAMPLES))
    by_name = {Path(item["path"]).name: item for item in diagnostic["samples"]}
    main = by_name["main_scene.pond"]
    assert main["script_count"] > 0
    assert main["signal_edge_count"] > 0
    assert main["hierarchy_relation_count"] > 0
    assert main["template_sensor_count"] == 3
    assert main["template_actuator_count"] == 2
    assert main["ps_component_fact_count"] == 0


def test_diagnostic_accepts_explicit_subset_and_preserves_sample_identity() -> None:
    path = SAMPLES / "pvaec-细胞演化" / "scenes" / "challenge_scene.pond"
    diagnostic = diagnose_descriptor_corpus([path])
    assert diagnostic["sample_count"] == 1
    assert diagnostic["samples"][0]["path"].endswith("challenge_scene.pond")
    assert diagnostic["samples"][0]["round_trip_ok"] is True
