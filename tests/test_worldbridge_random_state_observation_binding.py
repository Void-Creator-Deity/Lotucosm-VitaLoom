# -*- coding: utf-8 -*-
from __future__ import annotations

import builtins
import copy
import importlib.util
import random
from pathlib import Path

import numpy as np
import pytest

from core.Lotucosm.runtime.world_bridge_live_capture_artifact import (
    _artifact_digest,
    build_worldbridge_live_capture_artifact_contract,
)
from core.Lotucosm.runtime.world_bridge_random_state_observation_binding import (
    BOUNDARY_SEMANTICS,
    _binding_digest,
    build_worldbridge_random_state_observation_binding,
    build_worldbridge_random_state_observation_binding_contract,
    validate_worldbridge_random_state_observation_binding,
)
from core.Lotucosm.runtime.world_bridge_randomness_authority import (
    CAPTURED_AUTHORITY_IDS,
    UNCAPTURED_AUTHORITY_IDS,
    _build_capture_from_states,
    _capture_digest,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
MODULE = RUNTIME / "core/Lotucosm/runtime/world_bridge_random_state_observation_binding.py"
VIEWPORT = RUNTIME / "core/VitaLoom/viewports/game_viewport.py"


def _numpy_state_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return (
        left[0] == right[0]
        and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


def _artifact() -> dict[str, object]:
    return copy.deepcopy(build_worldbridge_live_capture_artifact_contract()["artifact"])


def _captures(*, change_python: bool = True, change_numpy: bool = False) -> tuple[dict, dict]:
    python_before = random.Random(222)
    python_after = random.Random(222)
    if change_python:
        python_after.random()
    numpy_before = np.random.RandomState(222)
    numpy_after = np.random.RandomState(222)
    if change_numpy:
        numpy_after.random_sample()
    before = _build_capture_from_states(
        capture_id="test-before",
        python_state=python_before.getstate(),
        numpy_state=numpy_before.get_state(),
    )
    after = _build_capture_from_states(
        capture_id="test-after",
        python_state=python_after.getstate(),
        numpy_state=numpy_after.get_state(),
    )
    return before, after


def _binding(**capture_options: bool) -> dict[str, object]:
    before, after = _captures(**capture_options)
    return build_worldbridge_random_state_observation_binding(
        _artifact(),
        before,
        after,
        binding_id="test-binding",
    )


def test_builds_valid_binding_with_only_changed_unchanged_diagnostics() -> None:
    binding = _binding(change_python=True, change_numpy=False)
    assert validate_worldbridge_random_state_observation_binding(binding) == {
        "valid": True,
        "errors": [],
    }
    assert binding["artifact"]["session"]["lifecycle"] == "sealed"
    assert binding["boundary_semantics"] == BOUNDARY_SEMANTICS
    assert binding["changed_authority_ids"] == ["python_process_global_random"]
    assert binding["unchanged_authority_ids"] == ["numpy_legacy_global_randomstate"]
    assert [row["authority_id"] for row in binding["authority_changes"]] == list(
        CAPTURED_AUTHORITY_IDS
    )
    assert binding["uncaptured_authority_ids"] == list(UNCAPTURED_AUTHORITY_IDS)
    for field in (
        "draw_counts_inferred",
        "lane_attribution_inferred",
        "cross_lane_consumption_order_captured",
        "supported_globals_prove_entropy_closure",
        "clocks_compared",
        "time_aligned",
        "causality_inferred",
        "thread_atomic",
        "cross_authority_atomic",
        "atomic_checkpoint",
        "replay_input",
        "checkpoint_state",
        "lossless",
        "replay_admitted",
        "default_ready",
    ):
        assert binding[field] is False


def test_distinct_ids_can_validly_classify_both_supported_states_unchanged() -> None:
    binding = _binding(change_python=False, change_numpy=False)
    assert binding["changed_authority_ids"] == []
    assert binding["unchanged_authority_ids"] == list(CAPTURED_AUTHORITY_IDS)
    assert validate_worldbridge_random_state_observation_binding(binding)["valid"] is True
    assert binding["supported_globals_prove_entropy_closure"] is False


def test_builder_is_copy_isolated() -> None:
    artifact = _artifact()
    before, after = _captures(change_python=True, change_numpy=True)
    artifact_original = copy.deepcopy(artifact)
    before_original = copy.deepcopy(before)
    after_original = copy.deepcopy(after)
    binding = build_worldbridge_random_state_observation_binding(
        artifact,
        before,
        after,
        binding_id="copy-isolation",
    )
    artifact["artifact_id"] = "mutated"
    before["capture_id"] = "mutated"
    after["capture_id"] = "mutated"
    assert binding["artifact"] == artifact_original
    assert binding["boundaries"]["before"] == before_original
    assert binding["boundaries"]["after"] == after_original


def test_builder_rejects_invalid_artifacts_captures_duplicate_ids_and_bad_binding_ids() -> None:
    before, after = _captures()
    with pytest.raises(ValueError, match="validated sealed E220 artifact"):
        build_worldbridge_random_state_observation_binding(
            {"not": "artifact"}, before, after, binding_id="bad-artifact"
        )
    invalid_before = copy.deepcopy(before)
    invalid_before["replay_admitted"] = True
    invalid_before["capture_digest"] = _capture_digest(invalid_before)
    with pytest.raises(ValueError, match="before capture"):
        build_worldbridge_random_state_observation_binding(
            _artifact(), invalid_before, after, binding_id="bad-before"
        )
    duplicate_after = copy.deepcopy(after)
    duplicate_after["capture_id"] = before["capture_id"]
    duplicate_after["capture_digest"] = _capture_digest(duplicate_after)
    with pytest.raises(ValueError, match="must be distinct"):
        build_worldbridge_random_state_observation_binding(
            _artifact(), before, duplicate_after, binding_id="duplicate"
        )
    for bad_id in ("", "has space", "../escape", "x" * 129):
        with pytest.raises(ValueError):
            build_worldbridge_random_state_observation_binding(
                _artifact(), before, after, binding_id=bad_id
            )


def test_validator_rejects_boundary_swap_and_reference_mismatch() -> None:
    binding = _binding(change_python=True, change_numpy=False)
    swapped = copy.deepcopy(binding)
    swapped["boundaries"]["before"], swapped["boundaries"]["after"] = (
        swapped["boundaries"]["after"],
        swapped["boundaries"]["before"],
    )
    swapped["binding_digest"] = _binding_digest(swapped)
    errors = validate_worldbridge_random_state_observation_binding(swapped)["errors"]
    assert "before_capture_id_reference_mismatch" in errors
    assert "after_capture_id_reference_mismatch" in errors
    assert "authority_changes_mismatch" in errors


def test_validator_rejects_nested_e220_tamper_even_when_outer_digests_are_resealed() -> None:
    binding = _binding()
    tampered = copy.deepcopy(binding)
    artifact = tampered["artifact"]
    artifact["replay_input"] = True
    artifact["artifact_digest"] = _artifact_digest(artifact)
    tampered["artifact_digest"] = artifact["artifact_digest"]
    tampered["binding_digest"] = _binding_digest(tampered)
    errors = validate_worldbridge_random_state_observation_binding(tampered)["errors"]
    assert "artifact_invalid" in errors


def test_validator_rejects_nested_e221_tamper_even_when_digests_are_resealed() -> None:
    binding = _binding()
    tampered = copy.deepcopy(binding)
    before = tampered["boundaries"]["before"]
    before["replay_admitted"] = True
    before["capture_digest"] = _capture_digest(before)
    tampered["before_capture_digest"] = before["capture_digest"]
    tampered["binding_digest"] = _binding_digest(tampered)
    errors = validate_worldbridge_random_state_observation_binding(tampered)["errors"]
    assert "before_capture_invalid" in errors


def test_validator_rejects_semantic_overclaims_extra_keys_and_digest_tamper() -> None:
    binding = _binding()
    overclaim = copy.deepcopy(binding)
    overclaim["lane_attribution_inferred"] = True
    overclaim["binding_digest"] = _binding_digest(overclaim)
    assert "lane_attribution_inferred_mismatch" in validate_worldbridge_random_state_observation_binding(
        overclaim
    )["errors"]

    extra = copy.deepcopy(binding)
    extra["extra"] = True
    extra["binding_digest"] = _binding_digest(extra)
    assert "binding_keys_mismatch" in validate_worldbridge_random_state_observation_binding(extra)[
        "errors"
    ]

    digest = copy.deepcopy(binding)
    digest["binding_digest"] = "0" * 64
    assert "binding_digest_mismatch" in validate_worldbridge_random_state_observation_binding(
        digest
    )["errors"]


def test_validator_handles_malformed_values_without_raising() -> None:
    assert validate_worldbridge_random_state_observation_binding(None) == {
        "valid": False,
        "errors": ["binding_not_mapping"],
    }
    malformed = _binding()
    malformed["authority_changes"] = {1, 2}
    validation = validate_worldbridge_random_state_observation_binding(malformed)
    assert validation["valid"] is False
    assert "authority_changes_mismatch" in validation["errors"]
    assert "binding_not_canonical_json" in validation["errors"]


def test_contract_is_deterministic_and_does_not_read_or_advance_global_rngs() -> None:
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    first = build_worldbridge_random_state_observation_binding_contract()
    second = build_worldbridge_random_state_observation_binding_contract()
    python_after = random.getstate()
    numpy_after = np.random.get_state()
    assert first == second
    assert python_before == python_after
    assert _numpy_state_equal(numpy_before, numpy_after)
    assert first["contract_valid"] is True
    assert first["binding_validation"] == {"valid": True, "errors": []}
    assert first["status_construction_reads_global_rng_state"] is False
    assert first["status_construction_advances_global_rng_state"] is False


def test_default_viewport_does_not_import_or_own_e222_binding_lifecycle() -> None:
    source = VIEWPORT.read_text(encoding="utf-8")
    assert "world_bridge_random_state_observation_binding" not in source
    assert "build_worldbridge_random_state_observation_binding" not in source
    assert "pre_post_random_state_observation_binding" not in source


def test_runtime_status_nests_static_e222_contract_and_stays_dual() -> None:
    contract = build_worldbridge_random_state_observation_binding_contract()
    status = build_runtime_worldbridge_status()
    assert status["pre_post_random_state_observation_binding_contract"] == contract
    assert "random_state_observation_binding_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False


def test_binding_module_imports_when_pyqt6_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise ImportError("PyQt6 intentionally blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("_qt_free_worldbridge_rng_binding", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    contract = module.build_worldbridge_random_state_observation_binding_contract()
    assert contract["qt_free"] is True
    assert contract["contract_valid"] is True
