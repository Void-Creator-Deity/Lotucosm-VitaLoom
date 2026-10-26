# -*- coding: utf-8 -*-
"""E227 tests for the read-only respawn artifact consumer boundary."""
from __future__ import annotations

import copy
import json
import random

import numpy as np
import pytest

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
)
from core.Lotucosm.runtime.world_bridge_named_stream_adapter import (
    run_worldbridge_named_stream_sr_respawn_handoff,
)
from core.Lotucosm.runtime.world_bridge_respawn_artifact_inspection import (
    _inspection_digest,
    build_worldbridge_respawn_artifact_inspection_contract,
    decode_worldbridge_respawn_artifact_inspection,
    encode_worldbridge_respawn_artifact_inspection,
    inspect_worldbridge_respawn_two_stream_artifact,
    validate_worldbridge_respawn_artifact_inspection,
)
from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import (
    _artifact_digest,
    build_worldbridge_respawn_two_stream_artifact,
    encode_worldbridge_respawn_two_stream_artifact,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _numpy_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def _artifact(probability: float = 1.0) -> dict[str, object]:
    context = create_worldbridge_deterministic_randomness_context("e227-context", "e227-seed")
    register_worldbridge_deterministic_random_stream(
        context, "sr.war.respawn.decision", "python_random"
    )
    register_worldbridge_deterministic_random_stream(
        context, "sr.war.respawn.mind", "python_random"
    )
    handoff = run_worldbridge_named_stream_sr_respawn_handoff(
        context,
        "sr.war.respawn.decision",
        "sr.war.respawn.mind",
        {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3},
        0.25,
        probability,
    )
    return build_worldbridge_respawn_two_stream_artifact(handoff, artifact_id="e227-artifact")


def test_inspection_summary_is_copy_isolated_and_does_not_execute_or_restore() -> None:
    artifact = _artifact(1.0)
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    summary = inspect_worldbridge_respawn_two_stream_artifact(artifact)
    assert random.getstate() == python_before
    assert _numpy_equal(np.random.get_state(), numpy_before)
    assert summary["outcome"] == "admitted_mutation"
    assert summary["ordered_steps"] == ["decision", "mutation"]
    assert summary["mutation_stream_consumed"] is True
    assert summary["restore_performed"] is False
    assert summary["mutation_executed"] is False
    assert summary["replay_admitted"] is False
    assert "before_snapshot" not in summary
    assert "child" not in summary
    artifact["context_id"] = "caller-mutated"
    summary["snapshot_digests"]["before"] = "0" * 64
    fresh = inspect_worldbridge_respawn_two_stream_artifact(_artifact(1.0))
    assert fresh["context_id"] == "e227-context"
    assert fresh["snapshot_digests"]["before"] != "0" * 64


def test_rejected_artifact_summary_reports_no_mutation() -> None:
    summary = inspect_worldbridge_respawn_two_stream_artifact(_artifact(0.0))
    assert summary["outcome"] == "rejected_no_mutation"
    assert summary["admitted"] is False
    assert summary["ordered_steps"] == ["decision"]
    assert summary["mutation_stream_consumed"] is False


def test_mapping_and_canonical_bytes_use_strict_validated_consumer_boundary() -> None:
    artifact = _artifact(1.0)
    summary = inspect_worldbridge_respawn_two_stream_artifact(artifact)
    encoded = encode_worldbridge_respawn_artifact_inspection(summary)
    assert decode_worldbridge_respawn_artifact_inspection(encoded) == summary
    assert inspect_worldbridge_respawn_two_stream_artifact(
        encode_worldbridge_respawn_two_stream_artifact(artifact)
    ) == summary
    with pytest.raises(ValueError, match="canonical"):
        decode_worldbridge_respawn_artifact_inspection(
            json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        )


def test_tampered_artifact_or_summary_fails_closed() -> None:
    artifact = _artifact(1.0)
    tampered = copy.deepcopy(artifact)
    tampered["admitted"] = False
    tampered["artifact_digest"] = _artifact_digest(tampered)
    with pytest.raises(ValueError, match="invalid worldbridge respawn artifact"):
        inspect_worldbridge_respawn_two_stream_artifact(tampered)

    summary = inspect_worldbridge_respawn_two_stream_artifact(artifact)
    tampered_summary = copy.deepcopy(summary)
    tampered_summary["restore_performed"] = True
    tampered_summary["inspection_digest"] = _inspection_digest(tampered_summary)
    validation = validate_worldbridge_respawn_artifact_inspection(tampered_summary)
    assert validation["valid"] is False
    assert "restore_performed_mismatch" in validation["errors"]


def test_contract_and_runtime_status_remain_read_only_opt_in() -> None:
    contract = build_worldbridge_respawn_artifact_inspection_contract()
    assert contract["contract_valid"] is True
    assert contract["round_trip_equal"] is True
    assert contract["artifact_consumer_only"] is True
    assert contract["restores_streams"] is False
    assert contract["executes_mutation"] is False
    status = build_runtime_worldbridge_status()
    assert status["opt_in_respawn_artifact_inspection_contract"] == contract
    assert "respawn_artifact_inspection_module" in status["pilot_modules"]
    assert status["default_ready"] is False

