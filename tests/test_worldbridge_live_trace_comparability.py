# -*- coding: utf-8 -*-
from __future__ import annotations

import builtins
import copy
import importlib.util
from pathlib import Path

import pytest

from core.Lotucosm.runtime.world_bridge_live_trace_comparability import (
    build_worldbridge_live_trace_comparability_contract,
    evaluate_worldbridge_live_trace_fields,
    validate_worldbridge_live_trace_field_evaluation,
    _evaluation_digest,
)
from core.Lotucosm.runtime.world_bridge_live_trace_producer import (
    build_worldbridge_live_dual_lane_trace,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
EVALUATOR = RUNTIME / "core/Lotucosm/runtime/world_bridge_live_trace_comparability.py"


def _subject(identity_field: str, identity: str, linked_id: str) -> dict[str, object]:
    return {
        identity_field: identity,
        "linked_id": linked_id,
        "position": [1.0, 2.0],
        "velocity": [0.5, 0.25],
        "acceleration": [0.0, 0.0],
        "energy": 30.0,
        "health": 20.0,
        "size": 8.0,
        "radius": 4.0,
        "max_energy": 100.0,
        "max_health": 80.0,
        "generation": 3,
    }


def _producer(
    *,
    sr_overrides: dict[str, object] | None = None,
    ps_overrides: dict[str, object] | None = None,
) -> dict[str, object]:
    sr_row = _subject("entity_id", "sr:a", "ps:a")
    ps_row = _subject("organism_id", "ps:a", "sr:a")
    sr_row.update(sr_overrides or {})
    ps_row.update(ps_overrides or {})
    return build_worldbridge_live_dual_lane_trace(
        {
            "sim_time": 1.25,
            "capture_source": "sr_observation_before_bridge_handoff",
            "bridged_entities": [sr_row],
        },
        {
            "tick": 4,
            "iteration": 2,
            "population": 1,
            "capture_source": "ps_pond_after_update_before_display_reflection",
            "bridged_organisms": [ps_row],
        },
        entity_links=[{"sr_entity_id": "sr:a", "ps_organism_id": "ps:a"}],
        observed_sr_delta=0.05,
    )


def _fields(evaluation: dict[str, object]) -> dict[str, dict[str, object]]:
    pair = evaluation["pair_results"][0]  # type: ignore[index]
    return {item["field"]: item for item in pair["fields"]}  # type: ignore[index]


def test_equal_live_fields_pass_with_declared_non_comparable_ledger() -> None:
    evaluation = evaluate_worldbridge_live_trace_fields(_producer())
    validation = validate_worldbridge_live_trace_field_evaluation(evaluation)
    fields = _fields(evaluation)

    assert validation == {"valid": True, "errors": []}
    assert evaluation["comparison_scope"] == "ordered_cross_boundary_observation_not_same_instant_parity"
    assert evaluation["aggregate_comparable_status"] == "comparable_pass"
    assert evaluation["field_status_counts"] == {
        "comparable_mismatch": 0,
        "comparable_pass": 7,
        "declared_loss": 5,
        "not_observed": 4,
    }
    for field in ("position", "energy", "health", "size", "radius", "velocity", "acceleration"):
        assert fields[field]["status"] == "comparable_pass"
    for field in ("max_energy", "max_health", "developmental_profile", "social_enabled"):
        assert fields[field]["status"] == "not_observed"
    for field in (
        "hierarchy",
        "membrane_component_graph",
        "memory_genes",
        "render_identity",
        "scripts",
    ):
        assert fields[field]["status"] == "declared_loss"


def test_position_and_energy_drift_are_mismatch_not_error_or_admission() -> None:
    evaluation = evaluate_worldbridge_live_trace_fields(
        _producer(ps_overrides={"position": [1.25, 2.0], "energy": 29.5})
    )
    fields = _fields(evaluation)

    assert fields["position"]["status"] == "comparable_mismatch"
    assert fields["position"]["max_absolute_delta"] == 0.25
    assert fields["energy"]["status"] == "comparable_mismatch"
    assert fields["energy"]["absolute_delta"] == 0.5
    assert evaluation["aggregate_comparable_status"] == "comparable_mismatch"
    assert evaluation["same_instant_parity"] is False
    assert evaluation["atomic_checkpoint"] is False
    assert evaluation["lossless"] is False
    assert evaluation["replay_admitted"] is False
    assert evaluation["default_ready"] is False


def test_float_tolerance_only_absorbs_representation_noise() -> None:
    within = evaluate_worldbridge_live_trace_fields(
        _producer(ps_overrides={"energy": 30.0 + 5e-10})
    )
    outside = evaluate_worldbridge_live_trace_fields(
        _producer(ps_overrides={"energy": 30.0 + 2e-9})
    )

    assert _fields(within)["energy"]["status"] == "comparable_pass"
    assert _fields(outside)["energy"]["status"] == "comparable_mismatch"
    assert within["field_tolerance_policy"]["semantic_drift_budget"] is None  # type: ignore[index]


def test_missing_projection_is_not_observed() -> None:
    missing = evaluate_worldbridge_live_trace_fields(
        _producer(sr_overrides={"health": None}, ps_overrides={"velocity": None})
    )
    fields = _fields(missing)

    assert fields["health"]["status"] == "not_observed"
    assert fields["health"]["sr_observed"] is False
    assert fields["velocity"]["status"] == "not_observed"
    assert fields["velocity"]["ps_observed"] is False
    assert missing["aggregate_comparable_status"] == "comparable_pass"


def test_invalid_e216_payload_is_rejected_before_evaluation() -> None:
    payload = _producer()
    payload["atomic_checkpoint"] = True

    with pytest.raises(ValueError, match="invalid live trace producer payload"):
        evaluate_worldbridge_live_trace_fields(payload)


def test_inconsistent_row_linked_id_is_rejected_before_field_comparison() -> None:
    payload = _producer(sr_overrides={"linked_id": "ps:wrong"})

    with pytest.raises(ValueError, match="sr bridge pair identity mismatch"):
        evaluate_worldbridge_live_trace_fields(payload)


def test_structural_field_tampering_is_rejected_even_with_resealed_digest() -> None:
    evaluation = evaluate_worldbridge_live_trace_fields(_producer())
    tampered = copy.deepcopy(evaluation)
    tampered["pair_results"][0]["fields"][0]["field"] = "unadmitted_field"  # type: ignore[index]
    tampered["evaluation_digest"] = _evaluation_digest(tampered)

    validation = validate_worldbridge_live_trace_field_evaluation(tampered)
    assert validation["valid"] is False
    assert "field_name_unexpected" in validation["errors"]
    assert "field_set_mismatch" in validation["errors"]

def test_validator_rejects_no_claim_and_digest_tampering() -> None:
    evaluation = evaluate_worldbridge_live_trace_fields(_producer())
    tampered = copy.deepcopy(evaluation)
    tampered["same_instant_parity"] = True
    tampered["atomic_checkpoint"] = True
    tampered["clocks_compared"] = True
    tampered["lossless"] = True
    tampered["replay_admitted"] = True
    tampered["default_ready"] = True

    validation = validate_worldbridge_live_trace_field_evaluation(tampered)
    assert validation["valid"] is False
    assert {
        "clock_equality_not_admitted",
        "same_instant_parity_not_admitted",
        "atomic_checkpoint_not_admitted",
        "lossless_mapping_not_admitted",
        "unified_replay_not_admitted",
        "default_ready_not_admitted",
        "evaluation_digest_mismatch",
    }.issubset(validation["errors"])


def test_validator_rejects_status_count_pair_aggregate_and_digest_tampering() -> None:
    evaluation = evaluate_worldbridge_live_trace_fields(_producer())
    tampered = copy.deepcopy(evaluation)
    tampered["pair_results"][0]["comparable_status"] = "comparable_mismatch"  # type: ignore[index]
    tampered["field_status_counts"]["comparable_pass"] = 999  # type: ignore[index]
    tampered["aggregate_comparable_status"] = "not_observed"
    tampered["evaluation_digest"] = "0" * 64

    validation = validate_worldbridge_live_trace_field_evaluation(tampered)
    assert validation["valid"] is False
    assert "pair_comparable_status_mismatch" in validation["errors"]
    assert "field_status_counts_mismatch" in validation["errors"]
    assert "aggregate_comparable_status_mismatch" in validation["errors"]
    assert "evaluation_digest_mismatch" in validation["errors"]


def test_evaluation_is_deterministic_sorted_and_copy_isolated() -> None:
    payload = _producer()
    first = evaluate_worldbridge_live_trace_fields(payload)
    second = evaluate_worldbridge_live_trace_fields(copy.deepcopy(payload))

    assert first == second
    fields = first["pair_results"][0]["fields"]  # type: ignore[index]
    assert [item["field"] for item in fields] == sorted(item["field"] for item in fields)
    first["pair_results"][0]["fields"][0]["status"] = "changed"  # type: ignore[index]
    assert payload["trace"]["lanes"]["sr"]["checkpoint"]["bridged_entities"][0]["position"] == [1.0, 2.0]  # type: ignore[index]
    assert second != first


def test_contract_and_runtime_status_nest_without_runtime_admission() -> None:
    contract = build_worldbridge_live_trace_comparability_contract()
    status = build_runtime_worldbridge_status()

    assert contract["contract_valid"] is True
    assert contract["evaluation"]["aggregate_comparable_status"] == "comparable_mismatch"
    assert contract["tick_merge_admitted"] is False
    assert contract["replay_admitted"] is False
    assert contract["default_ready"] is False
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False
    assert status["live_dual_lane_field_comparability_contract"] == contract


def test_evaluator_module_imports_when_pyqt6_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise ImportError("PyQt6 intentionally blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("_qt_free_worldbridge_live_trace_comparability", EVALUATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build_worldbridge_live_trace_comparability_contract()["contract_valid"] is True


