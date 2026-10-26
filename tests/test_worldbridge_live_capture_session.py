# -*- coding: utf-8 -*-
from __future__ import annotations

import builtins
import copy
import importlib.util
import inspect
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication

from core.Lotucosm.runtime.world_bridge_live_capture_session import (
    _sample_producer,
    _session_digest,
    abort_worldbridge_live_capture_session,
    append_worldbridge_live_capture_session_evidence,
    build_worldbridge_live_capture_session_contract,
    seal_worldbridge_live_capture_session,
    start_worldbridge_live_capture_session,
    validate_worldbridge_live_capture_session,
)
from core.Lotucosm.runtime.world_bridge_live_trace_comparability import (
    evaluate_worldbridge_live_trace_fields,
)
from core.Lotucosm.runtime.world_bridge_live_trace_producer import (
    build_worldbridge_live_dual_lane_trace,
)
from core.Lotucosm.runtime.world_bridge_live_trace_time_series import (
    validate_worldbridge_live_trace_time_series,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from core.VitaLoom.viewports.game_viewport import GameViewport


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
MODULE = RUNTIME / "core/Lotucosm/runtime/world_bridge_live_capture_session.py"

_APP = QApplication.instance() or QApplication([])


def _producer(
    sample_number: int,
    *,
    ps_energy: float = 30.0,
    sr_id: str = "sr:a",
    ps_id: str = "ps:a",
) -> dict[str, object]:
    shared = {
        "position": [1.0, 2.0],
        "velocity": [0.5, 0.25],
        "acceleration": [0.0, 0.0],
        "health": 20.0,
        "size": 8.0,
        "radius": 4.0,
    }
    return build_worldbridge_live_dual_lane_trace(
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
            "bridged_organisms": [
                {"organism_id": ps_id, "linked_id": sr_id, "energy": ps_energy, **shared}
            ],
        },
        entity_links=[{"sr_entity_id": sr_id, "ps_organism_id": ps_id}],
        observed_sr_delta=0.05,
    )


def test_start_append_and_seal_produces_valid_e218_evidence() -> None:
    session = start_worldbridge_live_capture_session("session-a", max_samples=2)
    first = append_worldbridge_live_capture_session_evidence(session, _producer(1))
    second = append_worldbridge_live_capture_session_evidence(
        first,
        _producer(2, ps_energy=29.5),
    )
    sealed = seal_worldbridge_live_capture_session(second)

    assert validate_worldbridge_live_capture_session(session) == {"valid": True, "errors": []}
    assert validate_worldbridge_live_capture_session(sealed) == {"valid": True, "errors": []}
    assert sealed["lifecycle"] == "sealed"
    assert sealed["sample_count"] == 2
    assert sealed["evidence_kind"] == "e216_live_producer"
    assert [item["sample_index"] for item in sealed["samples"]] == [0, 1]
    assert validate_worldbridge_live_trace_time_series(sealed["aggregation"])["valid"] is True
    assert sealed["aggregation"]["classification_counts"]["intermittent_observation"] == 1
    assert sealed["scheduler_owned"] is False
    assert sealed["time_aligned"] is False
    assert sealed["causality_inferred"] is False
    assert sealed["replay_admitted"] is False
    assert sealed["default_ready"] is False


def test_append_is_copy_isolated_and_duplicate_source_rejects_without_mutation() -> None:
    producer = _producer(1)
    session = start_worldbridge_live_capture_session("copy-session", max_samples=2)
    appended = append_worldbridge_live_capture_session_evidence(session, producer)
    before = copy.deepcopy(appended)
    duplicate = copy.deepcopy(producer)
    producer["trace"]["lanes"]["sr"]["checkpoint"]["bridged_entities"][0]["energy"] = -1  # type: ignore[index]

    assert appended == before
    assert session["sample_count"] == 0
    with pytest.raises(ValueError, match="duplicate source_trace_digest"):
        append_worldbridge_live_capture_session_evidence(appended, duplicate)
    assert appended == before


def test_mixed_e216_and_e217_evidence_kinds_are_rejected() -> None:
    session = start_worldbridge_live_capture_session("kind-session", max_samples=2)
    session = append_worldbridge_live_capture_session_evidence(session, _producer(1))
    evaluation = evaluate_worldbridge_live_trace_fields(_producer(2))

    with pytest.raises(ValueError, match="mixed session evidence kind"):
        append_worldbridge_live_capture_session_evidence(session, evaluation)


def test_capacity_empty_seal_and_post_seal_write_are_rejected() -> None:
    empty = start_worldbridge_live_capture_session("bounded-session", max_samples=1)
    with pytest.raises(ValueError, match="cannot seal an empty"):
        seal_worldbridge_live_capture_session(empty)

    full = append_worldbridge_live_capture_session_evidence(empty, _producer(1))
    with pytest.raises(OverflowError, match="capacity reached"):
        append_worldbridge_live_capture_session_evidence(full, _producer(2))

    sealed = seal_worldbridge_live_capture_session(full)
    with pytest.raises(RuntimeError, match="must be open"):
        append_worldbridge_live_capture_session_evidence(sealed, _producer(2))


def test_abort_retains_labeled_partial_evidence_without_aggregation() -> None:
    session = start_worldbridge_live_capture_session("abort-session", max_samples=3)
    session = append_worldbridge_live_capture_session_evidence(session, _producer(1))
    aborted = abort_worldbridge_live_capture_session(session, reason="adapter stopped")

    assert validate_worldbridge_live_capture_session(aborted)["valid"] is True
    assert aborted["lifecycle"] == "aborted"
    assert aborted["sample_count"] == 1
    assert aborted["partial_evidence"] is True
    assert aborted["session_complete"] is False
    assert aborted["aggregation"] is None
    with pytest.raises(RuntimeError, match="must be open"):
        append_worldbridge_live_capture_session_evidence(aborted, _producer(2))


def test_pair_churn_remains_explicit_absence_in_sealed_aggregation() -> None:
    session = start_worldbridge_live_capture_session("pair-session", max_samples=2)
    session = append_worldbridge_live_capture_session_evidence(
        session,
        _producer(1, sr_id="sr:a", ps_id="ps:a"),
    )
    session = append_worldbridge_live_capture_session_evidence(
        session,
        _producer(2, sr_id="sr:b", ps_id="ps:b"),
    )
    sealed = seal_worldbridge_live_capture_session(session)

    assert sealed["aggregation"]["pair_count"] == 2
    for pair in sealed["aggregation"]["pair_results"]:
        for field in pair["field_results"]:
            assert field["classification"] == "insufficient_observation"
            assert {item["sample_pair_present"] for item in field["observations"]} == {False, True}


def test_resealed_sample_identity_tamper_is_structurally_rejected() -> None:
    session = start_worldbridge_live_capture_session("tamper-session", max_samples=1)
    sealed = seal_worldbridge_live_capture_session(
        append_worldbridge_live_capture_session_evidence(session, _producer(1))
    )
    tampered = copy.deepcopy(sealed)
    tampered["samples"][0]["sample_id"] = "forged"
    tampered["session_digest"] = _session_digest(tampered)

    validation = validate_worldbridge_live_capture_session(tampered)
    assert validation["valid"] is False
    assert "sample_id_mismatch" in validation["errors"]


def test_validator_returns_errors_for_unhashable_nested_values() -> None:
    session = start_worldbridge_live_capture_session("malformed-session", max_samples=1)
    sealed = seal_worldbridge_live_capture_session(
        append_worldbridge_live_capture_session_evidence(session, _producer(1))
    )
    malformed = copy.deepcopy(sealed)
    malformed["samples"][0]["evaluation"]["pair_results"][0]["fields"][0]["status"] = []
    malformed["aggregation"]["pair_results"][0]["field_results"][0]["classification"] = []

    validation = validate_worldbridge_live_capture_session(malformed)
    assert validation["valid"] is False
    assert "nested_evaluation_invalid" in validation["errors"]
    assert "nested_aggregation_invalid" in validation["errors"]
    assert "session_digest_mismatch" in validation["errors"]


def test_contract_is_nested_in_runtime_status_without_admission() -> None:
    contract = build_worldbridge_live_capture_session_contract()
    status = build_runtime_worldbridge_status()

    assert contract["contract_valid"] is True
    assert contract["scheduler_owned"] is False
    assert contract["time_aligned"] is False
    assert contract["causality_inferred"] is False
    assert contract["replay_admitted"] is False
    assert contract["default_ready"] is False
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False
    assert status["bounded_live_comparability_capture_session_contract"] == contract
    assert "bounded_capture_session_module" in status["pilot_modules"]


def test_real_game_viewport_feeds_session_only_through_explicit_adapter() -> None:
    _APP.processEvents()
    viewport = GameViewport()
    viewport._using_scene_runtime = True
    viewport.is_playing = True
    viewport.is_paused = False
    viewport._scene_runtime_time = 1.5
    viewport._unified_pond_mode = True
    entity = viewport._SceneRuntimeEntity("hub_session", "organism", (4.0, 6.0), 12.0)
    entity.energy = 55.0
    viewport.scene_runtime_entities = [entity]
    session = start_worldbridge_live_capture_session("viewport-session", max_samples=2)

    first = viewport._append_unified_pond_bridge_capture_session_sample(0.05, session)
    assert first is not None
    second = viewport._append_unified_pond_bridge_capture_session_sample(0.05, first)
    assert second is not None
    sealed = seal_worldbridge_live_capture_session(second)

    assert validate_worldbridge_live_capture_session(sealed)["valid"] is True
    assert sealed["sample_count"] == 2
    assert len(set(sealed["source_trace_digests"])) == 2
    assert viewport._run_unified_pond_bridge_tick(0.05) is None


def test_default_scene_tick_does_not_own_capture_session_lifecycle() -> None:
    source = inspect.getsource(GameViewport._update_scene_runtime_entities)

    assert "_append_unified_pond_bridge_capture_session_sample" not in source
    assert "capture_trace=True" not in source


def test_capture_session_module_imports_when_pyqt6_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise ImportError("PyQt6 intentionally blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("_qt_free_worldbridge_capture_session", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build_worldbridge_live_capture_session_contract()["contract_valid"] is True


def test_start_rejects_unbounded_or_ambiguous_identity() -> None:
    with pytest.raises(ValueError, match="session_id"):
        start_worldbridge_live_capture_session(" padded ", max_samples=1)
    with pytest.raises(ValueError, match="max_samples"):
        start_worldbridge_live_capture_session("session", max_samples=0)
    with pytest.raises(ValueError, match="max_samples"):
        start_worldbridge_live_capture_session("session", max_samples=True)

