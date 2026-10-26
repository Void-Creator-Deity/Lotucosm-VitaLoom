# -*- coding: utf-8 -*-
from __future__ import annotations

import builtins
import copy
import importlib.util
from pathlib import Path

import pytest

from core.Lotucosm.runtime.world_bridge_live_trace_comparability import (
    evaluate_worldbridge_live_trace_fields,
)
from core.Lotucosm.runtime.world_bridge_live_trace_producer import (
    build_worldbridge_live_dual_lane_trace,
)
from core.Lotucosm.runtime.world_bridge_live_trace_time_series import (
    _aggregation_digest,
    aggregate_worldbridge_live_trace_evaluations,
    build_worldbridge_live_trace_time_series_contract,
    validate_worldbridge_live_trace_time_series,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
MODULE = RUNTIME / "core/Lotucosm/runtime/world_bridge_live_trace_time_series.py"


def _evaluation(
    *,
    sample_number: int,
    ps_energy: float = 30.0,
    sr_id: str = "sr:a",
    ps_id: str = "ps:a",
    ps_overrides: dict[str, object] | None = None,
) -> dict[str, object]:
    shared = {
        "position": [1.0, 2.0],
        "velocity": [0.5, 0.25],
        "acceleration": [0.0, 0.0],
        "health": 20.0,
        "size": 8.0,
        "radius": 4.0,
    }
    ps_row: dict[str, object] = {
        "organism_id": ps_id,
        "linked_id": sr_id,
        "energy": ps_energy,
        **shared,
    }
    ps_row.update(ps_overrides or {})
    producer = build_worldbridge_live_dual_lane_trace(
        {
            "sim_time": 1.0 + sample_number / 10.0,
            "capture_source": "sr_observation_before_bridge_handoff",
            "bridged_entities": [
                {"entity_id": sr_id, "linked_id": ps_id, "energy": 30.0, **shared}
            ],
        },
        {
            "tick": sample_number,
            "iteration": sample_number,
            "population": 1,
            "capture_source": "ps_pond_after_update_before_display_reflection",
            "bridged_organisms": [ps_row],
        },
        entity_links=[{"sr_entity_id": sr_id, "ps_organism_id": ps_id}],
        observed_sr_delta=0.05,
    )
    return evaluate_worldbridge_live_trace_fields(producer)


def _samples(*evaluations: dict[str, object]) -> list[dict[str, object]]:
    return [
        {"sample_id": f"sample-{index:04d}", "sample_index": index, "evaluation": evaluation}
        for index, evaluation in enumerate(evaluations)
    ]


def _pair_fields(aggregation: dict[str, object], sr_id: str = "sr:a") -> dict[str, dict[str, object]]:
    pair = next(pair for pair in aggregation["pair_results"] if pair["sr_entity_id"] == sr_id)  # type: ignore[index]
    return {item["field"]: item for item in pair["field_results"]}


def test_two_equal_samples_produce_stable_pass_without_time_claims() -> None:
    aggregation = aggregate_worldbridge_live_trace_evaluations(
        _samples(_evaluation(sample_number=1), _evaluation(sample_number=2))
    )
    validation = validate_worldbridge_live_trace_time_series(aggregation)
    fields = _pair_fields(aggregation)

    assert validation == {"valid": True, "errors": []}
    for field in ("position", "energy", "health", "size", "radius", "velocity", "acceleration"):
        assert fields[field]["classification"] == "stable_pass"
    for field in ("max_energy", "max_health", "developmental_profile", "social_enabled"):
        assert fields[field]["classification"] == "insufficient_observation"
    for field in (
        "hierarchy",
        "membrane_component_graph",
        "memory_genes",
        "render_identity",
        "scripts",
    ):
        assert fields[field]["classification"] == "insufficient_observation"
        assert {item["status"] for item in fields[field]["observations"]} == {"declared_loss"}
    assert aggregation["clocks_compared"] is False
    assert aggregation["time_aligned"] is False
    assert aggregation["causality_inferred"] is False
    assert aggregation["atomic_checkpoint"] is False
    assert aggregation["replay_admitted"] is False
    assert aggregation["default_ready"] is False


def test_repeated_mismatch_and_intermittent_observation_are_distinct() -> None:
    repeated = aggregate_worldbridge_live_trace_evaluations(
        _samples(_evaluation(sample_number=1, ps_energy=29.0), _evaluation(sample_number=2, ps_energy=28.0))
    )
    intermittent = aggregate_worldbridge_live_trace_evaluations(
        _samples(_evaluation(sample_number=3, ps_energy=30.0), _evaluation(sample_number=4, ps_energy=29.0))
    )

    assert _pair_fields(repeated)["energy"]["classification"] == "repeated_mismatch_observed"
    assert _pair_fields(intermittent)["energy"]["classification"] == "intermittent_observation"
    assert repeated["replay_admitted"] is False
    assert intermittent["causality_inferred"] is False


def test_one_sample_or_pair_set_drift_is_insufficient_not_fabricated_parity() -> None:
    single = aggregate_worldbridge_live_trace_evaluations(_samples(_evaluation(sample_number=1)))
    pair_drift = aggregate_worldbridge_live_trace_evaluations(
        _samples(
            _evaluation(sample_number=2, sr_id="sr:a", ps_id="ps:a"),
            _evaluation(sample_number=3, sr_id="sr:b", ps_id="ps:b"),
        )
    )

    assert _pair_fields(single)["energy"]["classification"] == "insufficient_observation"
    assert pair_drift["pair_count"] == 2
    for sr_id in ("sr:a", "sr:b"):
        fields = _pair_fields(pair_drift, sr_id)
        assert fields["energy"]["classification"] == "insufficient_observation"
        assert any(item["sample_pair_present"] is False for item in fields["energy"]["observations"])


def test_input_is_sorted_by_explicit_index_and_copy_isolated() -> None:
    first_eval = _evaluation(sample_number=1)
    second_eval = _evaluation(sample_number=2)
    raw = [
        {"sample_id": "later", "sample_index": 20, "evaluation": second_eval},
        {"sample_id": "earlier", "sample_index": 10, "evaluation": first_eval},
    ]
    aggregation = aggregate_worldbridge_live_trace_evaluations(raw)

    assert [sample["sample_id"] for sample in aggregation["samples"]] == ["earlier", "later"]
    raw[0]["sample_id"] = "mutated"
    second_eval["pair_results"][0]["fields"][0]["status"] = "mutated"  # type: ignore[index]
    assert aggregation["samples"][1]["sample_id"] == "later"  # type: ignore[index]
    assert validate_worldbridge_live_trace_time_series(aggregation)["valid"] is True


def test_duplicate_sample_id_index_and_source_digest_reject() -> None:
    first = _evaluation(sample_number=1)
    second = _evaluation(sample_number=2)

    with pytest.raises(ValueError, match="duplicate sample_id"):
        aggregate_worldbridge_live_trace_evaluations(
            [
                {"sample_id": "same", "sample_index": 0, "evaluation": first},
                {"sample_id": "same", "sample_index": 1, "evaluation": second},
            ]
        )
    with pytest.raises(ValueError, match="duplicate sample_index"):
        aggregate_worldbridge_live_trace_evaluations(
            [
                {"sample_id": "first", "sample_index": 0, "evaluation": first},
                {"sample_id": "second", "sample_index": 0, "evaluation": second},
            ]
        )
    with pytest.raises(ValueError, match="duplicate source_trace_digest"):
        aggregate_worldbridge_live_trace_evaluations(
            [
                {"sample_id": "first", "sample_index": 0, "evaluation": first},
                {"sample_id": "second", "sample_index": 1, "evaluation": copy.deepcopy(first)},
            ]
        )


def test_invalid_e217_evaluation_rejects_before_aggregation() -> None:
    evaluation = _evaluation(sample_number=1)
    evaluation["time_aligned"] = True

    with pytest.raises(ValueError, match="invalid E217 evaluation"):
        aggregate_worldbridge_live_trace_evaluations(_samples(evaluation))


def test_validator_rejects_time_causality_replay_default_and_digest_tampering() -> None:
    aggregation = aggregate_worldbridge_live_trace_evaluations(
        _samples(_evaluation(sample_number=1), _evaluation(sample_number=2))
    )
    tampered = copy.deepcopy(aggregation)
    tampered["clocks_compared"] = True
    tampered["time_aligned"] = True
    tampered["causality_inferred"] = True
    tampered["atomic_checkpoint"] = True
    tampered["lossless"] = True
    tampered["replay_admitted"] = True
    tampered["default_ready"] = True

    validation = validate_worldbridge_live_trace_time_series(tampered)
    assert validation["valid"] is False
    assert {
        "clock_equality_not_admitted",
        "time_alignment_not_admitted",
        "causality_not_admitted",
        "atomic_checkpoint_not_admitted",
        "lossless_mapping_not_admitted",
        "unified_replay_not_admitted",
        "default_ready_not_admitted",
        "aggregation_digest_mismatch",
    }.issubset(validation["errors"])


def test_resealed_classification_tamper_is_structurally_rejected() -> None:
    aggregation = aggregate_worldbridge_live_trace_evaluations(
        _samples(_evaluation(sample_number=1), _evaluation(sample_number=2))
    )
    tampered = copy.deepcopy(aggregation)
    field = _pair_fields(tampered)["energy"]
    field["classification"] = "repeated_mismatch_observed"
    tampered["classification_counts"] = {
        "insufficient_observation": 10,
        "intermittent_observation": 0,
        "repeated_mismatch_observed": 1,
        "stable_pass": 6,
    }
    tampered["aggregation_digest"] = _aggregation_digest(tampered)

    validation = validate_worldbridge_live_trace_time_series(tampered)
    assert validation["valid"] is False
    assert "classification_observation_mismatch" in validation["errors"]


def test_validator_returns_errors_instead_of_raising_for_malformed_nested_samples() -> None:
    aggregation = aggregate_worldbridge_live_trace_evaluations(
        _samples(_evaluation(sample_number=1), _evaluation(sample_number=2))
    )
    malformed = copy.deepcopy(aggregation)
    malformed["samples"][0]["sample_index"] = "bad"  # type: ignore[index]
    malformed["samples"][0]["evaluation"] = {}  # type: ignore[index]

    validation = validate_worldbridge_live_trace_time_series(malformed)
    assert validation["valid"] is False
    assert "sample_index_duplicate_or_invalid" in validation["errors"]
    assert "nested_evaluation_invalid" in validation["errors"]
    assert "aggregation_digest_mismatch" in validation["errors"]

def test_validator_rejects_unhashable_nested_status_without_raising() -> None:
    aggregation = aggregate_worldbridge_live_trace_evaluations(
        _samples(_evaluation(sample_number=1), _evaluation(sample_number=2))
    )
    malformed = copy.deepcopy(aggregation)
    malformed["samples"][0]["evaluation"]["pair_results"][0]["fields"][0]["status"] = []  # type: ignore[index]

    validation = validate_worldbridge_live_trace_time_series(malformed)

    assert validation["valid"] is False
    assert "nested_evaluation_invalid" in validation["errors"]
    assert "aggregation_digest_mismatch" in validation["errors"]


def test_validator_rejects_unhashable_classification_without_raising() -> None:
    aggregation = aggregate_worldbridge_live_trace_evaluations(
        _samples(_evaluation(sample_number=1), _evaluation(sample_number=2))
    )
    malformed = copy.deepcopy(aggregation)
    _pair_fields(malformed)["energy"]["classification"] = []

    validation = validate_worldbridge_live_trace_time_series(malformed)

    assert validation["valid"] is False
    assert "classification_invalid" in validation["errors"]
    assert "classification_counts_mismatch" in validation["errors"]
    assert "aggregation_digest_mismatch" in validation["errors"]


def test_contract_is_nested_in_runtime_status_without_admission() -> None:
    contract = build_worldbridge_live_trace_time_series_contract()
    status = build_runtime_worldbridge_status()

    assert contract["contract_valid"] is True
    assert contract["time_aligned"] is False
    assert contract["replay_admitted"] is False
    assert contract["default_ready"] is False
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False
    assert status["live_dual_lane_comparability_time_series_contract"] == contract


def test_time_series_module_imports_when_pyqt6_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise ImportError("PyQt6 intentionally blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("_qt_free_worldbridge_time_series", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build_worldbridge_live_trace_time_series_contract()["contract_valid"] is True

